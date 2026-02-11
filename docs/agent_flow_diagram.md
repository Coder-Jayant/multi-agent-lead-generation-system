# 🤖 LeadGenAgent - Agent Execution Flow

## Overview
Detailed visualization of the ReAct agent's decision-making process, tool execution patterns, and lead generation workflow.

---

## 🔄 Complete Agent Flow (End-to-End)

```mermaid
flowchart TD
    Start([User Clicks Generate Leads]) --> SelectProduct[Select Product from Dropdown]
    SelectProduct --> APICall[POST /api/generate/stream<br/>product_id + product_name]
    
    APICall --> InitController[Initialize LeadResearchController<br/>with product context]
    InitController --> CreateAgent[Create ReAct Agent<br/>Inject system prompt]
    CreateAgent --> SetupTools[Load Tools:<br/>search, scrape, email, score, save]
    
    SetupTools --> StartLoop{Start ReAct Loop<br/>Iteration 0}
    
    StartLoop --> Thought1[💭 THOUGHT<br/>LLM: Analyze current state<br/>Plan next action]
    
    Thought1 --> StreamThought[📡 Stream to UI<br/>SSE: thought event]
    StreamThought --> Action1[⚙️ ACTION<br/>LLM: Select tool + inputs<br/>e.g., searxng_search]
    
    Action1 --> StreamAction[📡 Stream to UI<br/>SSE: action event]
    StreamAction --> CheckTool{Which Tool?}
    
    CheckTool -->|Search| SearchTool[🔍 searxng_search<br/>Query: "AI infrastructure companies"]
    CheckTool -->|Scrape| ScrapeTool[🌐 firecrawl_enrich<br/>domain, extract emails]
    CheckTool -->|Score| ScoreTool[📊 score_company<br/>ICP matching via LLM]
    CheckTool -->|Save| SaveTool[💾 save_lead_tool<br/>MongoDB with product_id]
    CheckTool -->|Complete| CompleteTool[🏁 complete_task<br/>End generation]
    
    SearchTool --> Observation1[👁️ OBSERVATION<br/>Results from tool]
    ScrapeTool --> Observation1
    ScoreTool --> Observation1
    SaveTool --> LeadEvent[📡 Stream to UI<br/>SSE: lead event]
    
    LeadEvent --> Observation1
    
    Observation1 --> StreamObs[📡 Stream to UI<br/>SSE: observation event]
    StreamObs --> Increment{Iteration++<br/>< max_iterations?}
    
    Increment -->|Yes| Thought1
    Increment -->|No| ForceComplete[⚠️ Max iterations reached<br/>Force completion]
    
    CompleteTool --> CompleteEvent[📡 Stream to UI<br/>SSE: complete event<br/>quality_saved count]
    ForceComplete --> CompleteEvent
    
    CompleteEvent --> CloseSSE[Close SSE Stream]
    CloseSSE --> End([UI Shows Completion])
    
    style Start fill:#667eea,color:#fff
    style Thought1 fill:#f093fb,color:#fff
    style Action1 fill:#764ba2,color:#fff
    style Observation1 fill:#4bc0c0,color:#fff
    style CompleteTool fill:#10b981,color:#fff
    style End fill:#667eea,color:#fff
```

---

## 🧠 ReAct Agent Decision Loop

```mermaid
stateDiagram-v2
    [*] --> Initialize
    
    Initialize --> Thought: System prompt loaded
    
    state Thought {
        [*] --> LLM_Reasoning
        LLM_Reasoning --> Generate_Thought
        Generate_Thought --> [*]
    }
    
    Thought --> Action: Extract action from LLM
    
    state Action {
        [*] --> Parse_Tool_Call
        Parse_Tool_Call --> Validate_Inputs
        Validate_Inputs --> [*]
    }
    
    Action --> ToolDispatch: Tool name + args
    
    state ToolDispatch {
        [*] --> Route_to_Tool
        Route_to_Tool --> Execute
        Execute --> [*]
    }
    
    ToolDispatch --> Observation: Return results
    
    state Observation {
        [*] --> Format_Results
        Format_Results --> Add_to_Context
        Add_to_Context --> [*]
    }
    
    Observation --> Check_Termination
    
    state Check_Termination <<choice>>
    Check_Termination --> Thought: Continue loop
    Check_Termination --> Complete: complete_task called
    Check_Termination --> MaxIterations: Iteration limit
    
    Complete --> [*]
    MaxIterations --> [*]
    
    note right of Thought
        LLM has full conversation history
        System prompt + all previous thoughts/actions/observations
    end note
    
    note right of Action
        Expected format:
        Action: tool_name
        Input: {"param": "value"}
    end note
```

---

## 🛠️ Tool Execution Workflows

### 1. Search Tool Flow

```mermaid
sequenceDiagram
    participant Agent
    participant SearchTool as searxng_search
    participant SearXNG
    
    Agent->>SearchTool: searxng_search(<br/>query="AI DevOps companies",<br/>max_results=10<br/>)
    
    SearchTool->>SearXNG: GET /search?q=AI+DevOps+companies
    SearXNG-->>SearchTool: HTML results page
    
    SearchTool->>SearchTool: Parse HTML<br/>Extract domains, titles, snippets
    SearchTool->>SearchTool: Deduplicate by domain
    SearchTool->>SearchTool: Limit to max_results
    
    SearchTool-->>Agent: [<br/>{domain, title, snippet},<br/>{domain, title, snippet},<br/>...<br/>]
    
    Agent->>Agent: 👁️ Observation:<br/>"Found 10 companies"
```

---

### 2. Firecrawl Enrichment Flow

```mermaid
flowchart TD
    A[Agent calls firecrawl_enrich] --> B[Extract domain from URL]
    B --> C[POST to Firecrawl API v2<br/>/scrape endpoint]
    C --> D{Success?}
    
    D -->|Yes| E[Extract markdown content]
    D -->|No| Z[Return error observation]
    
    E --> F[Parse company metadata<br/>name, description, phone]
    F --> G[Extract emails from markdown]
    
    G --> H{Emails found?}
    H -->|Yes| I[Use scraped emails]
    H -->|No| J[Generate common patterns<br/>sales@, info@, contact@]
    
    I --> K[Validate all emails<br/>DNS MX lookup]
    J --> K
    
    K --> L[Calculate confidence scores<br/>70% for DNS + common pattern<br/>60% for DNS only]
    
    L --> M[Build email_details array<br/>email, confidence, status, has_mx]
    
    M --> N[Return observation:<br/>domain, name, emails,<br/>email_details, email_source]
    
    N --> O[Agent receives enriched data]
    
    style A fill:#667eea,color:#fff
    style C fill:#764ba2,color:#fff
    style K fill:#f093fb,color:#fff
    style O fill:#4bc0c0,color:#fff
```

---

### 3. Company Scoring Flow

```mermaid
sequenceDiagram
    participant Agent
    participant ScoreTool as score_company
    participant LLM as OpenAI GPT-4
    
    Agent->>ScoreTool: score_company(<br/>company_data_json,<br/>icp_json<br/>)
    
    ScoreTool->>ScoreTool: Parse company data<br/>(domain, description, industry)
    ScoreTool->>ScoreTool: Parse ICP<br/>(target industries, pain points, buyer roles)
    
    ScoreTool->>ScoreTool: Build scoring prompt:<br/>"Analyze if company matches ICP..."
    
    ScoreTool->>LLM: ChatCompletion API<br/>Prompt + structured output
    
    LLM-->>ScoreTool: {<br/>"relevance_score": 85,<br/>"fit_label": "high",<br/>"short_reason": "Perfect match..."<br/>}
    
    ScoreTool->>ScoreTool: Validate score (0-100)
    ScoreTool->>ScoreTool: Validate fit_label<br/>(low/medium/high)
    
    ScoreTool-->>Agent: {<br/>"relevance_score": 85,<br/>"fit_label": "high",<br/>"short_reason": "..."<br/>}
    
    Agent->>Agent: 👁️ Observation:<br/>"Score: 85/100 (high)"
    
    alt Score >= 65 AND fit == "high"
        Agent->>Agent: 💭 Thought:<br/>"This is a quality lead, save it"
        Agent->>Agent: ⚙️ Action: save_lead_tool
    else Score < 65 OR fit != "high"
        Agent->>Agent: 💭 Thought:<br/>"Not a good match, continue searching"
        Agent->>Agent: ⚙️ Action: searxng_search
    end
```

---

### 4. Save Lead Flow

```mermaid
flowchart TD
    A[Agent calls save_lead_tool] --> B[Prepare lead document]
    B --> C{Emails format?}
    
    C -->|List of strings| D[Convert to simple format]
    C -->|List of dicts| E[Use as email_details]
    
    D --> F[Build MongoDB document]
    E --> F
    
    F --> G[Add product context<br/>product_id, product_name]
    G --> H[Add timestamps<br/>created_at, updated_at]
    
    H --> I[Check for duplicate<br/>db.leads.find_one domain]
    
    I --> J{Duplicate?}
    J -->|Yes| K[Return duplicate status<br/>existing lead_id]
    J -->|No| L[Insert into MongoDB]
    
    L --> M[Get inserted_id]
    M --> N[Return success<br/>lead_id, domain]
    
    K --> O[Agent receives observation]
    N --> O
    
    O --> P{Success?}
    P -->|Yes| Q[Increment saved_count]
    P -->|Duplicate| R[Log: Already saved]
    
    Q --> S[Continue searching for more leads]
    R --> S
    
    style A fill:#667eea,color:#fff
    style I fill:#764ba2,color:#fff
    style L fill:#4bc0c0,color:#fff
    style Q fill:#10b981,color:#fff
```

---

## 📊 Agent State Management

```mermaid
stateDiagram-v2
    [*] --> Idle
    
    Idle --> Searching: First iteration
    
    state Searching {
        [*] --> Query_Companies
        Query_Companies --> Parse_Results
        Parse_Results --> Select_Candidate
    }
    
    Searching --> Enriching: Found company
    
    state Enriching {
        [*] --> Scrape_Homepage
        Scrape_Homepage --> Extract_Emails
        Extract_Emails --> Validate_Emails
    }
    
    Enriching --> Scoring: Enrichment complete
    
    state Scoring {
        [*] --> Build_ICP_Context
        Build_ICP_Context --> LLM_Evaluation
        LLM_Evaluation --> Calculate_Score
    }
    
    Scoring --> Decision: Score received
    
    state Decision <<choice>>
    Decision --> Saving: score >= 65 AND fit == "high"
    Decision --> Searching: score < 65 OR fit != "high"
    
    state Saving {
        [*] --> Prepare_Document
        Prepare_Document --> Check_Duplicate
        Check_Duplicate --> Insert_MongoDB
        Insert_MongoDB --> Increment_Counter
    }
    
    Saving --> Check_Completion: Lead saved
    
    state Check_Completion <<choice>>
    Check_Completion --> Complete: quality_saved >= target
    Check_Completion --> Searching: quality_saved < target
    Check_Completion --> Complete: iterations >= max
    
    Complete --> [*]
    
    note right of Searching
        Uses searxng_search tool
        Queries multiple search engines
    end note
    
    note right of Scoring
        Uses score_company tool
        LLM evaluates ICP match
    end note
    
    note right of Saving
        Uses save_lead_tool
        MongoDB with product_id
    end note
```

---

## 🎯 Quality Lead Filtering Logic

```mermaid
flowchart TD
    Start[Company Data Received] --> ExtractInfo[Extract:<br/>- Domain<br/>- Description<br/>- Industry<br/>- Emails]
    
    ExtractInfo --> Score[Call score_company tool]
    Score --> GetScore[Receive:<br/>- relevance_score 0-100<br/>- fit_label low/medium/high<br/>- reasoning]
    
    GetScore --> CheckScore{Score >= 65?}
    
    CheckScore -->|No| Reject1[❌ Reject:<br/>Score too low]
    CheckScore -->|Yes| CheckFit{Fit == "high"?}
    
    CheckFit -->|No| Reject2[❌ Reject:<br/>Fit not optimal]
    CheckFit -->|Yes| CheckEmails{Has emails?}
    
    CheckEmails -->|No| Reject3[❌ Reject:<br/>No contact info]
    CheckEmails -->|Yes| CheckEmailQuality{Email confidence<br/>>= 60%?}
    
    CheckEmailQuality -->|No| Reject4[❌ Reject:<br/>Low email quality]
    CheckEmailQuality -->|Yes| QualityLead[✅ QUALITY LEAD<br/>Save to MongoDB]
    
    QualityLead --> AddProduct[Tag with product_id<br/>+ product_name]
    AddProduct --> SaveDB[(MongoDB Insert)]
    SaveDB --> StreamUI[📡 Stream lead to UI<br/>SSE: lead event]
    
    Reject1 --> SearchMore[Continue searching]
    Reject2 --> SearchMore
    Reject3 --> SearchMore
    Reject4 --> SearchMore
    
    SearchMore --> CheckIterations{More iterations<br/>remaining?}
    CheckIterations -->|Yes| Start
    CheckIterations -->|No| Complete[🏁 Complete Task]
    
    style QualityLead fill:#10b981,color:#fff
    style Reject1 fill:#ef4444,color:#fff
    style Reject2 fill:#ef4444,color:#fff
    style Reject3 fill:#ef4444,color:#fff
    style Reject4 fill:#ef4444,color:#fff
    style Complete fill:#667eea,color:#fff
```

**Quality Criteria:**
1. ✅ Relevance Score >= 65/100
2. ✅ Fit Label == "high"
3. ✅ Has valid email addresses
4. ✅ Email confidence >= 60%

---

## 🔁 Iteration Management

```mermaid
gantt
    title Agent Iteration Timeline (Max 5 Iterations)
    dateFormat X
    axisFormat %s
    
    section Iteration 1
    Thought 1: 0, 2
    Action: searxng_search: 2, 5
    Observation: Results: 5, 6
    
    section Iteration 2
    Thought 2: 6, 8
    Action: firecrawl_enrich: 8, 15
    Observation: Enriched data: 15, 16
    
    section Iteration 3
    Thought 3: 16, 18
    Action: score_company: 18, 22
    Observation: Score 85: 22, 23
    
    section Iteration 4
    Thought 4: 23, 25
    Action: save_lead_tool: 25, 27
    Observation: Lead saved: 27, 28
    
    section Iteration 5
    Thought 5: 28, 30
    Action: complete_task: 30, 31
    Task Complete: 31, 32
```

**Iteration Limits:**
- **Max Iterations**: 5 (configurable via `max_iterations`)
- **Target Count**: 30 leads (configurable via `target_count`)
- **Early Termination**: Agent calls `complete_task` when satisfied
- **Forced Termination**: System stops after max iterations

---

## 📡 Real-Time Streaming Events

```mermaid
sequenceDiagram
    participant UI
    participant SSE as EventSource
    participant API as FastAPI /generate/stream
    participant Agent as ReAct Agent
    
    UI->>SSE: Open connection
    SSE->>API: GET /api/generate/stream
    
    API->>Agent: Start execution
    
    loop Every ReAct Step
        Agent->>API: Thought event
        API->>SSE: data: {"step": "thought", "message": "..."}
        SSE->>UI: Update activity log
        
        Agent->>API: Action event
        API->>SSE: data: {"step": "action", "tool_name": "..."}
        SSE->>UI: Update activity log
        
        Agent->>API: Observation event
        API->>SSE: data: {"step": "observation", "message": "..."}
        SSE->>UI: Update activity log
        
        alt Lead Saved
            Agent->>API: Lead event
            API->>SSE: data: {"event_type": "lead", "lead_data": {...}}
            SSE->>UI: Show new lead card
        end
    end
    
    Agent->>API: Complete event
    API->>SSE: data: {"event_type": "complete", "total_leads": 5}
    SSE->>UI: Show completion message
    
    API->>SSE: Close stream
    SSE->>UI: Disconnect
```

**SSE Event Types:**
- `step`: Agent thought/action/observation
- `lead`: New lead discovered and saved
- `complete`: Generation finished
- `error`: Execution error

---

## 🧩 Tool Dependencies Graph

```mermaid
graph LR
    Agent[ReAct Agent] --> T1[searxng_search]
    Agent --> T2[firecrawl_enrich]
    Agent --> T3[score_company]
    Agent --> T4[save_lead_tool]
    Agent --> T5[complete_task]
    
    T1 -->|Provides| D1[Company domains]
    D1 --> T2
    
    T2 -->|Provides| D2[Enriched data<br/>emails, description]
    D2 --> T3
    
    T3 -->|Provides| D3[Relevance score<br/>fit label]
    D3 --> Decision{Score >= 65<br/>Fit == high?}
    
    Decision -->|Yes| T4
    Decision -->|No| T1
    
    T4 -->|Provides| D4[Saved lead count]
    D4 --> Check{Target reached?}
    
    Check -->|Yes| T5
    Check -->|No| T1
    
    style Agent fill:#f093fb,color:#fff
    style T1 fill:#667eea,color:#fff
    style T2 fill:#764ba2,color:#fff
    style T3 fill:#ff6384,color:#fff
    style T4 fill:#4bc0c0,color:#fff
    style T5 fill:#10b981,color:#fff
```

---

## 🎬 Example Execution Trace

```mermaid
sequenceDiagram
    autonumber
    
    participant Agent
    participant Search as searxng_search
    participant Scrape as firecrawl_enrich
    participant Score as score_company
    participant Save as save_lead_tool
    participant Complete as complete_task
    
    Note over Agent: 💭 Thought: "I need to search for AI infrastructure companies"
    Agent->>Search: query="AI infrastructure companies", max_results=10
    Search-->>Agent: 👁️ Observation: Found 10 companies
    
    Note over Agent: 💭 Thought: "Let me enrich the first company: acme.com"
    Agent->>Scrape: domain="acme.com"
    Scrape-->>Agent: 👁️ Observation: {name: "Acme AI", emails: [...], description: "..."}
    
    Note over Agent: 💭 Thought: "Evaluate if Acme AI matches our ICP"
    Agent->>Score: company_data={...}, icp={...}
    Score-->>Agent: 👁️ Observation: {score: 85, fit: "high", reason: "..."}
    
    Note over Agent: 💭 Thought: "Score 85 and high fit - save this lead!"
    Agent->>Save: domain="acme.com", emails=[...], score=85, product_id="123"
    Save-->>Agent: 👁️ Observation: {status: "success", lead_id: "abc"}
    
    Note over Agent: 💭 Thought: "Retrieved target count, complete the task"
    Agent->>Complete: total_found=1, quality_saved=1
    Complete-->>Agent: 👁️ Observation: Task completed successfully
```

---

## ⚡ Performance Optimizations

### Parallel Processing Opportunities

```mermaid
graph TB
    A[Search Results: 10 companies] --> B{Process in Parallel?}
    
    B -->|Current: Sequential| C1[Enrich company 1]
    C1 --> C2[Enrich company 2]
    C2 --> C3[Enrich company 3]
    C3 --> C4[...]
    
    B -->|Future: Parallel| D1[Enrich company 1]
    B -->|Future: Parallel| D2[Enrich company 2]
    B -->|Future: Parallel| D3[Enrich company 3]
    B -->|Future: Parallel| D4[...]
    
    D1 --> E[Merge results]
    D2 --> E
    D3 --> E
    D4 --> E
    
    C4 --> F[Sequential Time: 10 x 5s = 50s]
    E --> G[Parallel Time: max 5s]
    
    style G fill:#10b981,color:#fff
    style F fill:#ef4444,color:#fff
```

**Current Bottlenecks:**
1. Sequential enrichment (Firecrawl API: ~5s per company)
2. Sequential scoring (LLM API: ~2-3s per company)
3. Single-threaded ReAct loop

**Optimization Ideas:**
- Batch enrichment with async/await
- Parallel scoring for multiple candidates
- Multi-agent architecture (coordinator + workers)

---

## 🏁 Completion Conditions

```mermaid
flowchart TD
    Start[Agent Running] --> Check1{quality_saved<br/>>= target_count?}
    
    Check1 -->|Yes| Complete1[✅ Target Reached<br/>complete_task]
    Check1 -->|No| Check2{iterations<br/>>= max_iterations?}
    
    Check2 -->|Yes| Complete2[⏱️ Max Iterations<br/>complete_task]
    Check2 -->|No| Check3{Agent calls<br/>complete_task?}
    
    Check3 -->|Yes| Complete3[🎯 Agent Decision<br/>complete_task]
    Check3 -->|No| Continue[Continue ReAct Loop]
    
    Continue --> Start
    
    Complete1 --> End[📊 Generate Summary<br/>Stream complete event]
    Complete2 --> End
    Complete3 --> End
    
    style Complete1 fill:#10b981,color:#fff
    style Complete2 fill:#f59e0b,color:#fff
    style Complete3 fill:#667eea,color:#fff
```

**Termination Triggers:**
1. ✅ **Target Reached**: `quality_saved >= target_count`
2. ⏱️ **Iteration Limit**: `iterations >= max_iterations`
3. 🎯 **Agent Choice**: Explicitly calls `complete_task` tool
