"""
controller.py
ReAct Research Controller - orchestrates all tools to generate leads
"""

import json
import logging
from typing import List
from agent.react_agent import ReActAgent
from agent.tools.llm_helpers import extract_icp, generate_search_queries, score_company
from agent.tools.searxng_tool import searxng_search
from agent.tools.normalize_tool import normalize_candidates
from agent.tools.firecrawl_tool import firecrawl_enrich
from agent.tools.database_tools import save_lead_tool
from agent.tools.complete_task_tool import complete_task
from agent.state import CompanyLead, add_lead, get_leads_by_product
from langchain_openai import ChatOpenAI
import os

logger = logging.getLogger(__name__)

# LLM for ReAct controller
controller_llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
    model=os.getenv("OPENAI_MODEL", "gpt-4"),
    temperature=0.2,
    max_tokens=4000
)

# All tools available to controller
ALL_TOOLS = [
    extract_icp,
    generate_search_queries,
    searxng_search,
    normalize_candidates,
    firecrawl_enrich,
    score_company,
    save_lead_tool,  # MongoDB tool to persist scored leads
    complete_task    # Tool to end task with final summary
]

# Controller system prompt
CONTROLLER_PROMPT = """You are a Lead Research Controller AI. Find and save high-quality company leads.

**AVAILABLE TOOLS:**
1. **extract_icp** - Extract ICP from product (call ONCE at start)
2. **generate_search_queries** - Generate search queries 
3. **searxng_search** - Search web for companies
4. **normalize_candidates** - Extract domains from search results
5. **firecrawl_enrich** - Get company data from domain
6. **score_company** - Score company vs ICP (returns score + fit_label)
7. **save_lead_tool** - Save lead to database (ONLY if score >= 65 AND fit "high")
8. **complete_task** - **END THE TASK** (call when done OR target reached)

**QUALITY CRITERIA:**
- Score >= 65 (from score_company)
- fit_label = "high" (NOT medium or low)
- **ONLY save companies meeting BOTH criteria**

**WORKFLOW:**
1. extract_icp (once)
2. generate_search_queries → searxng_search → normalize_candidates
3. For each domain:
   - firecrawl_enrich → get company data
   - score_company → get score & fit
   - IF score >= 65 AND fit "high": save_lead_tool (IMMEDIATELY when qualified)
   - Track: how many saved
4. **WHEN TO CALL complete_task:**
   - ✅ You saved {target_count} quality leads → call complete_task(total_found, quality_saved, summary)
   - ✅ You completed {max_iterations} search iterations → call complete_task
   - ❌ **DO NOT give "Final Answer"** - always use complete_task to end

**CURRENT TASK:**
- Product: {product_description}
- Target: {target_count} quality leads (score >= 65, fit "high")
- Max Iterations: {max_iterations}

**IMPORTANT:**
- After EVERY save_lead_tool: count your saved leads
- When saved count >= {target_count}: IMMEDIATELY call complete_task
- If you can't find enough quality leads after {max_iterations} iterations: call complete_task anyway
- complete_task ends execution - agent stops after this tool

Begin by extracting ICP!"""


class LeadResearchController:
    """
    ReAct-based Research Controller for lead generation.
    
    Orchestrates all tools to discover, enrich, and score company leads
    until target count or budget reached.
    """
    
    def __init__(
        self, 
        product_description: str,
        target_count: int = 30,
        max_iterations: int = 5,
        cancellation_callback = None,
        product_id: str = "default",  # NEW
        product_name: str = None  # NEW
    ):
        self.product_description = product_description
        self.target_count = target_count  
        self.max_iterations = max_iterations
        self.cancellation_callback = cancellation_callback
        self.product_id = product_id  # Store for agent to use
        self.product_name = product_name  # Store for agent to use
        
        self.llm = ChatOpenAI(
            model=os.getenv("OPENAI_MODEL", "gpt-4"),
            temperature=0.2,
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        )
        self.step_callback = None  # For real-time progress streaming
        
        logger.info(f"Initialized controller: target={target_count}, max_iterations={max_iterations}, product_id={product_id}")
        
        # Update system prompt to include product context
        system_prompt = CONTROLLER_PROMPT.format(
            product_description=product_description,
            target_count=target_count,
            max_iterations=max_iterations
        )
        
        # Add product context reminder to prompt
        if product_id and product_id != "default":
            system_prompt += f"\n\n**IMPORTANT**: When saving leads, ALWAYS include product context: product_id='{product_id}', product_name='{product_name}'"
        
        # Create ReAct agent with controller prompt
        self.agent = ReActAgent(
            llm=self.llm,
            tools=ALL_TOOLS,
            system_prompt=system_prompt
        )
    
    def set_step_callback(self, callback):
        """Set callback for real-time step updates (for UI streaming)"""
        self.step_callback = callback
    
    def run(self) -> List[CompanyLead]:
        """
        Execute lead research loop.
        Returns list of discovered quality leads.
        """
        logger.info(f"🚀 Starting lead research: target={self.target_count}, max_iter={self.max_iterations}")
        
        # Initial prompt for controller
        initial_prompt = f"""Find {self.target_count} quality leads (score >= 50) for this product.

**Product Description:**
{self.product_description}

**Your Mission:**
1. Extract ICP first
2. Generate search queries and begin search-enrich-score cycles
3. Track progress after each company scored
4. Generate NEW queries and continue if needed
5. Stop when you have {self.target_count}+ quality leads OR completed {self.max_iterations} iterations

Start now by extracting the ICP!"""
        
        # Run ReAct agent with streaming
        logger.info("💭 ReAct controller starting...")
        
        saved_count = 0
        max_steps = self.max_iterations * 15
        
        for step_num, step in enumerate(self.agent.run_streaming(
            initial_prompt, 
            max_iterations=max_steps,
            cancellation_callback=self.cancellation_callback
        )):
            # Check for external cancellation (from UI stop button)
            if self.cancellation_callback and self.cancellation_callback():
                logger.warning("🛑 External cancellation detected - stopping agent")
                break
                
            # Log step
            if step.step_type == "thought":
                logger.info(f"💭 Thought: {step.content[:150]}...")
            elif step.step_type == "action":
                logger.info(f"⚙️ Action: {step.tool_name}")
                
                # Check if agent called complete_task - end gracefully
                if step.tool_name == "complete_task":
                    logger.info("🏁 Agent called complete_task - ending gracefully")
                    
            elif step.step_type == "observation":
                obs_preview = step.content[:200] if len(step.content) > 200 else step.content
                logger.info(f"📊 Observation: {obs_preview}...")
                
                # Track saved leads from observations
                if '"status": "saved"' in step.content or 'Saved lead successfully' in step.content:
                    saved_count += 1
                    logger.info(f"✅ Lead count: {saved_count}/{self.target_count}")
                    
                # Check if complete_task was called
                if '"task_completed": true' in step.content:
                    logger.info("🏁 Task completion confirmed - breaking loop")
                    if self.step_callback:
                        self.step_callback(step)
                    break
                    
            elif step.step_type == "final_answer":
                logger.info(f"✅ Final Answer: {step.content[:200]}...")
            
            # Callback for UI streaming
            if self.step_callback:
                self.step_callback(step)
        
        # Retrieve collected leads for this product
        product_leads = get_leads_by_product(self.product_description)
        
        # Filter quality leads
        quality_leads = [
            lead for lead in product_leads
            if lead.get('relevance_score', 0) >= 50
        ]
        
        logger.info(f"✅ Research complete: {saved_count} quality leads saved")
        return quality_leads


# Helper function for controller to add leads during research
def save_scored_lead(company_data_json: str, score_data_json: str, source_urls: List[str], product_description: str) -> bool:
    """
    Helper called by controller to save a scored company as a lead.
    Returns True if lead was successfully added (not duplicate).
    """
    try:
        company_data = json.loads(company_data_json)
        score_data = json.loads(score_data_json)
        
        lead = CompanyLead(
            company_name=company_data.get('company_name', 'Unknown'),
            homepage_url=company_data.get('homepage_url', ''),
            domain=company_data.get('domain', ''),
            short_company_description=company_data.get('description', '') or '',
            extracted_emails=[company_data.get('email')] if company_data.get('email') else [],
            extracted_phone=company_data.get('phone'),
            linkedin_url=company_data.get('linkedin_url'),
            relevance_score=score_data.get('relevance_score', 0),
            fit_label=score_data.get('fit_label', 'low'),
            short_reason_for_score=score_data.get('short_reason', ''),
            source_urls=source_urls,
            discovered_at='',  # Will be set by add_lead
            product_context=''  # Will be set by add_lead
        )
        
        return add_lead(lead, product_description)
    
    except Exception as e:
        logger.error(f"Failed to save lead: {e}")
        return False
