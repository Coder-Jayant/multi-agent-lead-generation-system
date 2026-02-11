# 🏗️ LeadGenAgent - System Architecture

## Overview
AI-powered B2B lead generation system using ReAct agent pattern with real-time streaming capabilities.

---

## 🎯 High-Level Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        UI[Web UI<br/>HTML/CSS/JS<br/>SSE Streaming]
    end
    
    subgraph "API Layer"
        FastAPI[FastAPI Server<br/>Port 8001]
        SSE[Server-Sent Events<br/>Real-time Streaming]
    end
    
    subgraph "Agent Layer"
        Controller[LeadResearchController<br/>Orchestration Logic]
        Agent[ReAct Agent<br/>LLM-Powered Decision Making]
        Prompt[System Prompts<br/>Task Instructions]
    end
    
    subgraph "Tools Layer"
        Search[searxng_search<br/>Company Discovery]
        Scrape[firecrawl_enrich<br/>Data Extraction]
        Email[email_validation<br/>DNS/SMTP Verification]
        Score[score_company<br/>ICP Matching]
        Save[save_lead_tool<br/>MongoDB Storage]
        Complete[complete_task<br/>Termination Signal]
    end
    
    subgraph "Data Layer"
        MongoDB[(MongoDB<br/>Leads & Products)]
    end
    
    subgraph "External Services"
        SearXNG[SearXNG Instance<br/>Meta-Search Engine]
        Firecrawl[Firecrawl API<br/>Web Scraping]
        LLM[OpenAI API<br/>GPT-4]
    end
    
    UI -->|HTTP Requests| FastAPI
    UI <-->|SSE Stream| SSE
    FastAPI --> Controller
    SSE --> Controller
    Controller --> Agent
    Agent --> Prompt
    
    Agent <--> Search
    Agent <--> Scrape
    Agent <--> Email
    Agent <--> Score
    Agent <--> Save
    Agent <--> Complete
    
    Search --> SearXNG
    Scrape --> Firecrawl
    Score --> LLM
    Agent --> LLM
    Save --> MongoDB
    
    style UI fill:#667eea,stroke:#333,stroke-width:2px,color:#fff
    style FastAPI fill:#764ba2,stroke:#333,stroke-width:2px,color:#fff
    style Agent fill:#f093fb,stroke:#333,stroke-width:2px,color:#fff
    style MongoDB fill:#4bc0c0,stroke:#333,stroke-width:2px,color:#fff
    style LLM fill:#ff6384,stroke:#333,stroke-width:2px,color:#fff
```

---

## 🔄 Data Flow Architecture

```mermaid
sequenceDiagram
    participant User
    participant UI as Web UI
    participant API as FastAPI
    participant Controller
    participant Agent as ReAct Agent
    participant Tools
    participant DB as MongoDB
    participant External as External APIs
    
    User->>UI: Select Product & Start Generation
    UI->>API: GET /api/generate/stream?product_id=xxx
    API->>Controller: Initialize with product context
    Controller->>Agent: Create with system prompt
    
    loop ReAct Loop (max 5 iterations)
        Agent->>Agent: Thought (reasoning)
        Agent->>Tools: Action (tool selection)
        Tools->>External: API Calls (search/scrape/LLM)
        External-->>Tools: Results
        Tools-->>Agent: Observation
        
        alt Lead Found & Qualified
            Agent->>Tools: save_lead_tool(domain, emails, score, product_id)
            Tools->>DB: Insert lead document
            DB-->>Tools: Success + lead_id
            Tools-->>Agent: Confirmation
            Agent->>API: Stream lead event
            API->>UI: SSE: lead data
        end
        
        Agent->>API: Stream step events
        API->>UI: SSE: thought/action/observation
        UI->>User: Live activity log update
        
        alt Task Complete
            Agent->>Tools: complete_task(quality_saved, total_found)
            Tools-->>Agent: Task completion signal
            Agent->>API: Stream complete event
            API->>UI: SSE: completion message
            UI->>User: Show success + lead count
        end
    end
    
    API->>UI: Close SSE stream
```

---

## 🗂️ Component Breakdown

### 1. **FastAPI Server** (`api/main.py`)
```mermaid
graph LR
    A[Request Handler] --> B[Product Endpoints]
    A --> C[Lead Generation]
    A --> D[Lead Retrieval]
    
    B --> B1[/api/products]
    B --> B2[/api/products/id]
    
    C --> C1[/api/generate/stream<br/>SSE Endpoint]
    
    D --> D1[/api/mongodb/leads]
    D --> D2[/api/leads/products]
    
    C1 --> E[LeadResearchController]
    
    style A fill:#667eea,color:#fff
    style C1 fill:#f093fb,color:#fff
    style E fill:#764ba2,color:#fff
```

**Key Features:**
- Server-Sent Events (SSE) for real-time streaming
- Product management CRUD operations
- Lead filtering by product, score, persona
- MongoDB integration via motor (async)

---

### 2. **ReAct Agent** (`agent/react_agent.py`)
```mermaid
stateDiagram-v2
    [*] --> Thought
    Thought --> Action: Reason about next step
    Action --> ToolExecution: Select tool
    ToolExecution --> Observation: Get results
    Observation --> Thought: Analyze results
    
    Thought --> Complete: Task finished
    Complete --> [*]
    
    note right of Thought
        LLM generates reasoning
        "I need to search for companies..."
    end note
    
    note right of Action
        LLM selects tool + inputs
        "searxng_search(query='...')"
    end note
    
    note right of Observation
        Tool returns results
        "Found 10 companies..."
    end note
```

**ReAct Pattern:**
1. **Thought**: LLM reasons about current state
2. **Action**: LLM chooses tool and parameters
3. **Observation**: Tool execution results
4. Repeat until `complete_task` called

---

### 3. **Tool Ecosystem**

```mermaid
mindmap
    root((Agent Tools))
        Discovery
            searxng_search
                Meta-search queries
                Company discovery
                Industry filtering
        Enrichment
            firecrawl_enrich
                Homepage scraping
                Contact extraction
                Email generation
                DNS/SMTP validation
        Qualification
            score_company
                LLM-based scoring
                ICP matching
                Fit labeling
        Storage
            save_lead_tool
                MongoDB insertion
                Deduplication
                Product linking
        Control
            complete_task
                Termination signal
                Summary generation
                Quality metrics
```

---

### 4. **Email Validation Pipeline**

```mermaid
flowchart TD
    A[Scraped Text] --> B{Emails Found?}
    B -->|Yes| C[Extract Emails]
    B -->|No| D[Generate Patterns]
    
    C --> E[Email List]
    D --> E
    
    E --> F[DNS MX Lookup]
    F --> G{MX Records?}
    
    G -->|Yes| H[Mark: has_mx = true]
    G -->|No| I[Mark: has_mx = false<br/>confidence = 0%]
    
    H --> J{SMTP Verify?}
    J -->|Enabled| K[SMTP Mailbox Check]
    J -->|Disabled| L[Skip SMTP]
    
    K --> M{Mailbox Exists?}
    M -->|Yes| N[confidence = 95%<br/>status = verified]
    M -->|No/Error| O[confidence = 70%<br/>status = likely]
    
    L --> P{Common Pattern?}
    P -->|Yes| Q[confidence = 70%<br/>status = likely]
    P -->|No| R[confidence = 60%<br/>status = likely]
    
    N --> S[email_details]
    O --> S
    Q --> S
    R --> S
    I --> S
    
    style A fill:#667eea,color:#fff
    style E fill:#764ba2,color:#fff
    style S fill:#4bc0c0,color:#fff
    style N fill:#10b981,color:#fff
```

**Confidence Scoring:**
- **95%**: SMTP verified (mailbox confirmed)
- **70%**: DNS valid + common pattern (sales@, info@, contact@)
- **60%**: DNS valid only
- **0%**: No MX records (invalid domain)

---

## 💾 MongoDB Schema

```mermaid
erDiagram
    PRODUCTS ||--o{ LEADS : generates
    
    PRODUCTS {
        ObjectId _id PK
        string name
        string description
        array target_personas
        array industries
        array regions
        string company_name
        string website_url
        datetime created_at
    }
    
    LEADS {
        ObjectId _id PK
        string domain UK
        string name
        string description
        string url
        array emails
        array email_details
        string email_source
        object qualification
        string product_id FK
        string product_name
        datetime created_at
        datetime updated_at
    }
    
    LEADS ||--o| EMAIL_DETAILS : contains
    LEADS ||--|| QUALIFICATION : has
    
    EMAIL_DETAILS {
        string email
        int confidence
        string status
        bool has_mx
        bool smtp_valid
        bool scraped
    }
    
    QUALIFICATION {
        int score
        string reasoning
        string fit
        datetime qualified_at
    }
```

---

## 🌐 External Dependencies

```mermaid
graph TB
    subgraph "LeadGenAgent System"
        Agent[ReAct Agent]
    end
    
    subgraph "Search Infrastructure"
        SearXNG[SearXNG<br/>Self-Hosted<br/>Port 8080]
        Google[Google]
        Bing[Bing]
        DDG[DuckDuckGo]
        
        SearXNG --> Google
        SearXNG --> Bing
        SearXNG --> DDG
    end
    
    subgraph "Web Scraping"
        Firecrawl[Firecrawl API<br/>firecrawl.dev<br/>v2 API]
    end
    
    subgraph "AI/LLM"
        OpenAI[OpenAI API<br/>GPT-4<br/>or Compatible Endpoint]
    end
    
    subgraph "Database"
        MongoDB[MongoDB Atlas<br/>or Local Instance]
    end
    
    Agent -->|Company Search| SearXNG
    Agent -->|Homepage Scraping| Firecrawl
    Agent -->|Reasoning & Scoring| OpenAI
    Agent -->|Data Persistence| MongoDB
    
    style Agent fill:#f093fb,color:#fff
    style SearXNG fill:#667eea,color:#fff
    style Firecrawl fill:#764ba2,color:#fff
    style OpenAI fill:#ff6384,color:#fff
    style MongoDB fill:#4bc0c0,color:#fff
```

---

## 🔧 Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | HTML5, CSS3, JavaScript | UI, SSE client, real-time updates |
| **Backend** | FastAPI (Python 3.13) | REST API, SSE streaming |
| **Agent Framework** | LangChain Core | Tool abstraction, LLM integration |
| **LLM** | OpenAI GPT-4 | Reasoning, decision-making, scoring |
| **Search** | SearXNG (Meta-search) | Company discovery |
| **Scraping** | Firecrawl API v2 | Homepage data extraction |
| **Email Validation** | dnspython, smtplib | DNS MX lookup, SMTP verification |
| **Database** | MongoDB (motor, pymongo) | Lead & product storage |
| **Server** | Uvicorn (ASGI) | Production server with auto-reload |

---

## 🚀 Deployment Architecture

```mermaid
graph TB
    subgraph "Production Environment"
        LB[Load Balancer]
        
        subgraph "Application Servers"
            API1[LeadGenAgent Instance 1<br/>Port 8001]
            API2[LeadGenAgent Instance 2<br/>Port 8002]
        end
        
        subgraph "Data & Services"
            MongoDB[(MongoDB Cluster<br/>Replica Set)]
            Redis[(Redis Cache<br/>Optional)]
        end
        
        subgraph "External Services"
            SearXNG[SearXNG Instance<br/>Self-Hosted]
            Firecrawl[Firecrawl API<br/>SaaS]
            OpenAI[OpenAI API<br/>SaaS]
        end
    end
    
    LB --> API1
    LB --> API2
    
    API1 --> MongoDB
    API2 --> MongoDB
    
    API1 --> Redis
    API2 --> Redis
    
    API1 --> SearXNG
    API2 --> SearXNG
    
    API1 --> Firecrawl
    API2 --> Firecrawl
    
    API1 --> OpenAI
    API2 --> OpenAI
    
    style LB fill:#667eea,color:#fff
    style MongoDB fill:#4bc0c0,color:#fff
    style Redis fill:#ff6384,color:#fff
```

---

## 📊 Performance Characteristics

- **Concurrent Users**: Supports multiple simultaneous lead generation sessions via SSE
- **Iteration Limit**: Max 5 ReAct iterations per generation (configurable)
- **Target Count**: 30 leads per run (configurable)
- **Streaming**: Real-time step-by-step progress via Server-Sent Events
- **Deduplication**: MongoDB unique index on `domain` field prevents duplicates
- **Email Validation**: ~100ms per email (DNS), ~2-5s (SMTP) - currently DNS-only for speed

---

## 🔒 Security Considerations

1. **API Keys**: Stored in `.env`, never committed
2. **CORS**: Configured for localhost during development
3. **Rate Limiting**: External API rate limits respected
4. **Input Validation**: Pydantic models validate all API inputs
5. **MongoDB**: Connection string with authentication
6. **SMTP Validation**: Respectful timeout limits to avoid abuse detection
