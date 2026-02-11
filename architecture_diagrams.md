# Lead Generator AI Agent - Architecture & Flow Diagrams

## System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        UI[Web UI<br/>HTML/JS SPA]
        API[FastAPI Backend<br/>REST API]
    end
    
    subgraph "Agent Layer"
        Controller[ReAct Research Controller<br/>Decision Making & Orchestration]
        
        subgraph "LLM Helper Tools"
            ICP[extract_icp<br/>One-shot LLM]
            QueryGen[generate_search_queries<br/>One-shot LLM]
            Scorer[score_company<br/>One-shot LLM]
        end
        
        subgraph "Deterministic Tools"
            Search[searxng_search<br/>HTTP Search]
            Normalize[normalize_candidates<br/>Domain Logic]
            Enrich[firecrawl_enrich<br/>HTTP Scraping]
        end
    end
    
    subgraph "State Management"
        StateManager[State Manager<br/>JSON Persistence]
        LeadsDB[(leads.json<br/>Deduplicated)]
        StateDB[(state.json<br/>Agent Context)]
    end
    
    subgraph "External Services"
        SearxNG[SearxNG<br/>Self-Hosted Search]
        Firecrawl[Firecrawl<br/>Self-Hosted Scraper]
        LLM[Scout LLM<br/>Self-Hosted Model]
    end
    
    UI -->|POST /api/generate| API
    API -->|Create & Run| Controller
    
    Controller -->|Uses| ICP
    Controller -->|Uses| QueryGen
    Controller -->|Uses| Search
    Controller -->|Uses| Normalize
    Controller -->|Uses| Enrich
    Controller -->|Uses| Scorer
    
    ICP -->|API Call| LLM
    QueryGen -->|API Call| LLM
    Scorer -->|API Call| LLM
    
    Search -->|HTTP| SearxNG
    Enrich -->|HTTP| Firecrawl
    
    Controller -->|Save/Load| StateManager
    StateManager -->|Persist| LeadsDB
    StateManager -->|Persist| StateDB
    
    Controller -->|Return Results| API
    API -->|JSON Response| UI
    
    style Controller fill:#667eea,stroke:#333,stroke-width:3px,color:#fff
    style UI fill:#10b981,stroke:#333,stroke-width:2px,color:#fff
    style LeadsDB fill:#f59e0b,stroke:#333,stroke-width:2px
```

## ReAct Controller Flow

```mermaid
flowchart TD
    Start([User Submits Product<br/>Target: N Leads]) --> Init[Initialize Controller<br/>product_description<br/>target_count<br/>max_iterations]
    
    Init --> ExtractICP[Tool: extract_icp<br/>LLM extracts ICP from product]
    ExtractICP --> ICPStore[Store ICP in Context]
    
    ICPStore --> CheckProgress{Quality Leads >= Target?}
    
    CheckProgress -->|No| CheckBudget{Iterations < Max?}
    CheckProgress -->|Yes| Done[Final Answer:<br/>Return Leads]
    
    CheckBudget -->|No| Done
    CheckBudget -->|Yes| GenQueries[Tool: generate_search_queries<br/>LLM creates queries based on ICP + progress]
    
    GenQueries --> SearchLoop[Loop: Each Query]
    
    SearchLoop --> SearchTool[Tool: searxng_search<br/>HTTP search via SearxNG]
    SearchTool --> NormalizeTool[Tool: normalize_candidates<br/>Extract unique domains<br/>Filter noise]
    
    NormalizeTool --> EnrichLoop[Loop: Each Domain]
    
    EnrichLoop --> EnrichTool[Tool: firecrawl_enrich<br/>HTTP scrape company data]
    EnrichTool --> ScoreTool[Tool: score_company<br/>LLM scores against ICP]
    
    ScoreTool --> SaveLead{Score >= 50?}
    SaveLead -->|Yes| AddLead[Persist to leads.json<br/>Deduplicate by domain]
    SaveLead -->|No| SkipLead[Skip Low-Quality Lead]
    
    AddLead --> CountIncrement[Increment Quality Count]
    SkipLead --> CountIncrement
    
    CountIncrement --> MoreDomains{More Domains?}
    MoreDomains -->|Yes| EnrichLoop
    MoreDomains -->|No| MoreQueries{More Queries?}
    
    MoreQueries -->|Yes| SearchLoop
    MoreQueries -->|No| IncIteration[Increment Iteration Counter]
    
    IncIteration --> CheckProgress
    
    Done --> ReturnAPI[Return Leads to API]
    ReturnAPI --> End([Display in UI])
    
    style Start fill:#10b981,stroke:#333,stroke-width:3px,color:#fff
    style Done fill:#10b981,stroke:#333,stroke-width:3px,color:#fff
    style End fill:#10b981,stroke:#333,stroke-width:3px,color:#fff
    style ExtractICP fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style GenQueries fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style ScoreTool fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style SearchTool fill:#fbbf24,stroke:#333,stroke-width:2px
    style NormalizeTool fill:#fbbf24,stroke:#333,stroke-width:2px
    style EnrichTool fill:#fbbf24,stroke:#333,stroke-width:2px
```

## Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant UI
    participant API
    participant Controller
    participant LLM Tools
    participant Det Tools
    participant Services
    participant State
    
    User->>UI: Enter Product + Target
    UI->>API: POST /api/generate
    API->>Controller: Create & Run
    
    Note over Controller: ReAct Loop Starts
    
    Controller->>LLM Tools: extract_icp(product)
    LLM Tools->>Services: Scout LLM API
    Services-->>LLM Tools: ICP JSON
    LLM Tools-->>Controller: ICP Data
    
    loop Until Target Reached or Max Iterations
        Controller->>LLM Tools: generate_search_queries(ICP, progress)
        LLM Tools->>Services: Scout LLM API
        Services-->>LLM Tools: Query List
        LLM Tools-->>Controller: Queries
        
        loop Each Query
            Controller->>Det Tools: searxng_search(query)
            Det Tools->>Services: SearxNG HTTP
            Services-->>Det Tools: Search Results
            Det Tools-->>Controller: URLs
            
            Controller->>Det Tools: normalize_candidates(results)
            Det Tools-->>Controller: Unique Domains
            
            loop Each Domain
                Controller->>Det Tools: firecrawl_enrich(domain)
                Det Tools->>Services: Firecrawl HTTP
                Services-->>Det Tools: Company Data
                Det Tools-->>Controller: Enriched Data
                
                Controller->>LLM Tools: score_company(data, ICP)
                LLM Tools->>Services: Scout LLM API
                Services-->>LLM Tools: Score + Reason
                LLM Tools-->>Controller: Scored Lead
                
                alt Score >= 50
                    Controller->>State: add_lead(lead)
                    State-->>Controller: Saved (or duplicate)
                end
            end
        end
        
        Controller->>Controller: Check Progress
    end
    
    Note over Controller: Target Reached or Budget Hit
    
    Controller->>State: get_leads_by_product()
    State-->>Controller: Quality Leads
    Controller-->>API: Leads List
    API-->>UI: JSON Response
    UI-->>User: Display Results
```

## Tool Interaction Pattern

```mermaid
graph LR
    subgraph "Controller's Tool Arsenal"
        direction TB
        
        subgraph "Phase 1: Understanding"
            T1[extract_icp]
        end
        
        subgraph "Phase 2: Discovery"
            T2[generate_search_queries]
            T3[searxng_search]
            T4[normalize_candidates]
        end
        
        subgraph "Phase 3: Enrichment"
            T5[firecrawl_enrich]
        end
        
        subgraph "Phase 4: Qualification"
            T6[score_company]
        end
    end
    
    T1 -->|ICP Context| T2
    T2 -->|Queries| T3
    T3 -->|Raw URLs| T4
    T4 -->|Clean Domains| T5
    T5 -->|Company Data| T6
    T6 -->|Scored Leads| DB[(leads.json)]
    
    DB -->|Progress Count| T2
    
    style T1 fill:#667eea,color:#fff
    style T2 fill:#667eea,color:#fff
    style T6 fill:#667eea,color:#fff
    style T3 fill:#fbbf24
    style T4 fill:#fbbf24
    style T5 fill:#fbbf24
    style DB fill:#10b981,color:#fff
```

## Component Responsibilities

### 🎯 ReAct Controller
**Role:** Decision-making and orchestration  
**Responsibilities:**
- Track progress toward target lead count
- Decide when to search more vs. stop
- Generate reasoning for each action
- Manage iteration budget
- Coordinate tool execution

**Why ReAct?**
- **Thought:** Reasons about current state and next action
- **Action:** Invokes appropriate tool
- **Observation:** Processes tool result
- **Loop:** Repeats until goal met

### 🧠 LLM Helper Tools (3)

**1. extract_icp**
- **Input:** Product description (string)
- **Process:** One-shot LLM call
- **Output:** ICP JSON (industries, regions, size, roles, pain points)

**2. generate_search_queries**
- **Input:** ICP JSON + current progress
- **Process:** One-shot LLM call
- **Output:** Array of search query strings

**3. score_company**
- **Input:** Company data JSON + ICP JSON
- **Process:** One-shot LLM call with scoring criteria
- **Output:** Score (0-100) + fit label + reasoning

### ⚙️ Deterministic Tools (3)

**1. searxng_search**
- **Input:** Query string
- **Process:** HTTP GET to SearxNG
- **Output:** List of {url, title, snippet}

**2. normalize_candidates**
- **Input:** Search results JSON
- **Process:** Domain extraction, filtering, deduplication
- **Output:** List of unique valid domains

**3. firecrawl_enrich**
- **Input:** Domain string
- **Process:** HTTP POST to Firecrawl with schema
- **Output:** Structured company data (name, description, contacts)

### 💾 State Management

**Persistence:**
- `leads.json` - All discovered leads (deduplicated by domain)
- [state.json](file:///c:/Users/JayantVerma/AA/SSH_AGENT/SOLO_AGENTS/SalesAgent/v19-backup/v19/salesagent-pop-ews-new/rag_state.json) - Agent context (optional checkpointing)

**Deduplication:**
- Domain-based (case-insensitive)
- Prevents duplicate company entries
- Preserves highest-scored version

## Key Design Principles

### 1. Single Controller Pattern
```
❌ NOT: Separate agents for ICP, search, scoring
✅ YES: One controller orchestrates all tools
```

**Benefits:**
- Unified reasoning stream
- Central progress tracking
- Simpler debugging
- Better stopping logic

### 2. Tool Categorization
```
🧠 LLM Tools: Need reasoning (ICP, queries, scoring)
⚙️ Deterministic: Pure HTTP/logic (search, normalize, enrich)
```

**Benefits:**
- Clear separation of concerns
- Easy to test independently
- No LLM calls in data operations

### 3. Progressive Refinement
```
Iteration 1: Broad queries → Some leads
Iteration 2: Refined queries → More targeted leads
Iteration N: Stop when target reached
```

**Benefits:**
- Better coverage
- Quality improves over iterations
- Budget-aware termination

## Presentation Talking Points

### Problem Statement
- Manual lead research is time-consuming
- Sales teams need qualified leads, not just lists
- Scalability requires automation

### Solution
- AI-powered research controller
- Autonomous search-enrich-score cycle
- Self-hosted for data privacy

### Technical Innovation
1. **ReAct Pattern** - Reasoning + Action loop
2. **Hybrid Tools** - LLM for reasoning, HTTP for data
3. **Progressive Discovery** - Refines strategy based on results

### Differentiators
- ✅ No SaaS dependencies (fully self-hosted)
- ✅ Deduplication prevents wasted effort
- ✅ Scored leads (not just raw lists)
- ✅ Extensible (add CRM, email, LinkedIn tools)

### Demo Flow
1. Show UI with product input
2. Explain ReAct controller reasoning
3. Display live search → enrich → score cycle
4. Present scored leads with reasoning
5. Export to CRM (future enhancement)

## Success Metrics

**Quality:**
- % of leads with relevance score >= 80
- Contact info completeness (email, phone)

**Efficiency:**
- Time to generate N leads
- Cost per lead (LLM tokens + compute)

**Coverage:**
- Domain diversity (not just G2 listings)
- Geographic distribution match to ICP
