# 📋 LeadGenAgent - Complete Project Reference

**Last Updated**: 2026-02-11

---

## 🔗 Git Repository Information

**GitHub Repository**: https://github.com/coder-jayant/multi-agent-lead-generation-system

**Git Configuration**:
- **Username**: coder-jayant
- **Email**: jayantverma12@me.com
- **Branch**: main
- **Initial Commit**: `8149251` - "Initial commit: AI-powered B2B Lead Generation Agent with ReAct pattern, email validation, and real-time streaming"

**Remote URL**:
```bash
https://github.com/coder-jayant/multi-agent-lead-generation-system.git
```

**Local Repository Path**:
```
c:\Users\JayantVerma\AA\SSH_AGENT\SOLO_AGENTS\SalesAgent\v19-backup\v19\LeadGenAgent
```

**Git Commands Quick Reference**:
```bash
# Navigate to project
cd c:\Users\JayantVerma\AA\SSH_AGENT\SOLO_AGENTS\SalesAgent\v19-backup\v19\LeadGenAgent

# Check status
git status

# Add changes
git add .

# Commit
git commit -m "Your commit message"

# Push to GitHub
git push origin main

# Pull latest
git pull origin main
```

---

## 📁 Project Structure

```
LeadGenAgent/
├── agent/
│   ├── __init__.py
│   ├── controller.py          # LeadResearchController - orchestrates agent execution
│   ├── react_agent.py         # ReAct pattern implementation
│   ├── prompts.py             # System prompts for agent
│   └── tools/
│       ├── __init__.py
│       ├── database_tools.py  # save_lead_tool - MongoDB operations
│       ├── firecrawl_tool.py  # firecrawl_enrich - web scraping
│       ├── searxng_tool.py    # searxng_search - company discovery
│       ├── email_tools.py     # email_validation - DNS/SMTP verification
│       ├── llm_helpers.py     # score_company - ICP matching
│       ├── normalize_tool.py  # Domain normalization
│       └── complete_task_tool.py  # Task completion signal
├── api/
│   ├── __init__.py
│   ├── main.py                # FastAPI application - main entry point
│   ├── static/
│   │   └── index.html         # Web UI - single-page application
│   └── mongodb_client.py      # MongoDB async connection manager
├── .env                       # Environment variables (NOT in git)
├── .gitignore                 # Git ignore rules
├── README.md                  # Project documentation
└── requirements.txt           # Python dependencies
```

---

## 🔧 Environment Configuration

**Environment File Location**: `c:\Users\JayantVerma\AA\SSH_AGENT\SOLO_AGENTS\SalesAgent\v19-backup\v19\LeadGenAgent\.env`

**Required Environment Variables**:

```env
# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=leadgen

# OpenAI Configuration (or compatible endpoint)
OPENAI_API_KEY=your_api_key_here
OPENAI_BASE_URL=http://49.50.117.66:8000/v1
OPENAI_MODEL=gpt-4

# External Services
SEARXNG_BASE_URL=http://localhost:8080
FIRECRAWL_API_KEY=your_firecrawl_key
FIRECRAWL_BASE_URL=https://api.firecrawl.dev

# Optional Settings
SMTP_VALIDATE=false            # Enable/disable SMTP email validation
SMTP_TEST_TIMEOUT=10           # Timeout for SMTP checks (seconds)
```

**Important Notes**:
- `.env` file is git-ignored for security
- Never commit API keys or credentials
- OpenAI base URL points to self-hosted LLM endpoint

---

## 🚀 Running the Application

### Development Server

**Command**:
```bash
cd c:\Users\JayantVerma\AA\SSH_AGENT\SOLO_AGENTS\SalesAgent\v19-backup\v19\LeadGenAgent
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

**Access Points**:
- **Web UI**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs
- **OpenAPI JSON**: http://localhost:8001/openapi.json

**Auto-Reload**: Enabled with `--reload` flag - server restarts on code changes

### Terminal Processes

**Currently Running**:
1. Process ID `23476` - Running for 27+ hours
2. Process ID (backup) - Running for 20+ hours

---

## 🗄️ Database Information

**MongoDB Configuration**:
- **Connection**: `mongodb://localhost:27017`
- **Database Name**: `leadgen`
- **Collections**: `products`, `leads`

### Collections Schema

#### `products` Collection
```javascript
{
  _id: ObjectId,                    // Unique product ID
  name: String,                     // Product name
  description: String,              // Product description
  target_personas: Array[String],   // ["CTO", "VP Engineering", ...]
  industries: Array[String],        // ["Technology", "SaaS", ...]
  regions: Array[String],           // ["North America", "Europe", ...]
  company_name: String,             // Seller company name
  website_url: String,              // Seller website
  value_proposition: String,        // Product value prop
  created_at: DateTime,             // Creation timestamp
  updated_at: DateTime              // Last update timestamp
}
```

#### `leads` Collection
```javascript
{
  _id: ObjectId,                    // Unique lead ID
  domain: String (unique index),    // Company domain (unique)
  name: String,                     // Company name
  description: String,              // Company description
  url: String,                      // Company website URL
  emails: Array[String],            // ["sales@...", "info@...", ...]
  email_details: Array[{            // Email validation details
    email: String,
    confidence: Number,             // 0-100 confidence score
    status: String,                 // "verified", "likely", "unknown"
    has_mx: Boolean,                // DNS MX record exists
    smtp_valid: Boolean,            // SMTP mailbox verified
    scraped: Boolean                // Scraped vs generated
  }],
  email_source: String,             // "scraped" or "inferred"
  qualification: {                  // ICP matching results
    score: Number,                  // 0-100 relevance score
    reasoning: String,              // LLM explanation
    fit: String,                    // "high", "medium", "low"
    qualified_at: DateTime
  },
  product_id: String,               // Associated product ID
  product_name: String,             // Product name for filtering
  created_at: DateTime,
  updated_at: DateTime
}
```

**MongoDB Indexes**:
- `leads.domain`: Unique index (prevents duplicate companies)

---

## 🌐 API Endpoints Reference

### Product Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/products` | List all products |
| POST | `/api/products` | Create new product |
| GET | `/api/products/{id}` | Get product by ID |
| PUT | `/api/products/{id}` | Update product |
| DELETE | `/api/products/{id}` | Delete product |

### Lead Generation

| Method | Endpoint | Parameters | Description |
|--------|----------|------------|-------------|
| GET | `/api/generate/stream` | `product_description`, `target_count`, `product_id`, `product_name`, `max_iterations` | SSE stream for real-time lead generation |

**SSE Event Types**:
- `step` - Agent thought/action/observation
- `lead` - New lead discovered and saved
- `complete` - Generation finished
- `error` - Execution error

### Lead Retrieval

| Method | Endpoint | Query Params | Description |
|--------|----------|--------------|-------------|
| GET | `/api/mongodb/leads` | `limit`, `skip`, `min_score`, `product_filter`, `persona_filter` | Get leads with filters |
| GET | `/api/leads/products` | - | Get all products with lead counts |

---

## 🔗 External Services & Dependencies

### SearXNG (Meta-Search Engine)
- **URL**: http://localhost:8080
- **Purpose**: Company discovery via aggregated search
- **Used By**: `searxng_search` tool
- **Status**: Self-hosted, must be running

### Firecrawl API
- **URL**: https://api.firecrawl.dev
- **Purpose**: Homepage scraping and data extraction
- **API Key Required**: Yes
- **Used By**: `firecrawl_enrich` tool
- **Version**: v2 API

### OpenAI Compatible LLM
- **URL**: http://49.50.117.66:8000/v1
- **Model**: gpt-4
- **Purpose**: ReAct agent reasoning, company scoring
- **Used By**: ReAct agent, `score_company` tool
- **Note**: Custom self-hosted endpoint

### MongoDB
- **URL**: mongodb://localhost:27017
- **Purpose**: Lead and product storage
- **Used By**: `save_lead_tool`, API endpoints
- **Status**: Must be running locally or via Atlas

---

## 🛠️ Tech Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| **Backend** | FastAPI | Latest |
| **Python** | Python | 3.13 |
| **Agent Framework** | LangChain Core | Latest |
| **LLM** | GPT-4 Compatible | - |
| **Database** | MongoDB | Latest |
| **Search** | SearXNG | Self-hosted |
| **Scraping** | Firecrawl API | v2 |
| **Server** | Uvicorn | ASGI |
| **Frontend** | HTML/CSS/JS | Vanilla |
| **Streaming** | Server-Sent Events | SSE |

---

## 📝 Recent Important Updates

### Product Context Wiring (2026-02-11)
**Issue**: Leads were being saved without product association, causing product filter dropdown to show 0 leads.

**Root Cause**: `save_lead_tool` had `product_id` and `product_name` parameters but wasn't actually saving them to MongoDB.

**Fix Applied**:
1. Added `product_id` and `product_name` to lead document before MongoDB insertion
2. Updated controller to pass product context to agent via system prompt
3. Modified `/api/generate/stream` to accept product parameters from UI
4. Updated frontend to send product context in EventSource URL

**Files Changed**:
- `agent/tools/database_tools.py` - Added product fields to lead_doc
- `agent/controller.py` - Accepts and stores product_id/product_name
- `api/main.py` - Added product params to stream endpoint
- `api/static/index.html` - Pass product selection to backend

**Impact**: New leads will be saved with product association. Legacy leads have `product_id: "default"` or null.

### Email Validation Backward Compatibility (2026-02-10)
**Issue**: Agent was passing `emails` as `List[str]` but tool expected `List[Dict]`.

**Fix**: Updated `save_lead_tool` to accept `Union[List[str], List[Dict[str, Any]]]`.

**File**: `agent/tools/database_tools.py`

### Lead Counter Fix (2026-02-10)
**Issue**: UI was hardcoded to show "0 leads generated" on completion.

**Fix**: Updated SSE complete event listener to use `data.total_leads` from backend.

**File**: `api/static/index.html`

### Product Dropdown Fix (2026-02-10)
**Issue**: Product filter dropdown showed "Unnamed Product" and had routing conflicts.

**Fixes**:
1. Renamed `/api/products/list` to `/api/leads/products` to avoid route conflict
2. Updated frontend to call new endpoint
3. Improved display logic for null/default product names

**Files**: `api/main.py`, `api/static/index.html`

---

## 🎯 Quality Lead Criteria

Leads are qualified based on:

1. **Relevance Score** >= 65/100
2. **Fit Label** == "high"
3. **Valid Emails** with confidence >= 60%
4. **Email Confidence Levels**:
   - 95%: SMTP verified (mailbox confirmed)
   - 70%: DNS valid + common pattern (sales@, info@, contact@)
   - 60%: DNS valid only
   - 0%: No MX records (invalid)

---

## 🔍 Troubleshooting Guide

### Server Won't Start
- Check if port 8001 is already in use
- Verify MongoDB is running: `mongosh`
- Check `.env` file exists and has all required variables
- Verify Python virtual environment is activated

### Agent Not Finding Leads
- Verify SearXNG is running: `curl http://localhost:8080`
- Check Firecrawl API key and quota
- Review agent logs in terminal for errors
- Check LLM endpoint is accessible

### Product Dropdown Shows 0 Leads
- This is expected for products created before 2026-02-11
- Generate new leads with product selected
- Legacy leads have `product_id: "default"` and won't show in per-product counts

### Database Connection Errors
- Verify MongoDB is running
- Check MONGODB_URI in `.env`
- Test connection: `mongosh "mongodb://localhost:27017/leadgen"`

### Import Errors
- Ensure virtual environment is activated
- Reinstall dependencies: `pip install -r requirements.txt`

---

## 📚 Documentation Files

**Architecture Diagrams**:
- Located in: `C:\Users\JayantVerma\.gemini\antigravity\brain\468b4914-ac54-476d-9028-8400d9bab274\`
- `architecture_diagram.md` - 10+ Mermaid diagrams covering system architecture
- `agent_flow_diagram.md` - 15+ Mermaid diagrams covering agent execution flow

**Other Artifacts**:
- `task.md` - Task checklist
- `implementation_plan.md` - Implementation planning
- `walkthrough.md` - Session walkthrough
- `poc_vs_main_comparison.md` - POC comparison

---

## 🔐 Security & Credentials

**Git Token** (Classic with full permissions):
- DO NOT commit to repository
- Stored separately for push operations
- Expires: Check GitHub settings

**API Keys to Never Commit**:
- `OPENAI_API_KEY`
- `FIRECRAWL_API_KEY`
- `MONGODB_URI` (if contains credentials)

**Protected by .gitignore**:
- `.env` files
- Virtual environments (`venv/`, `env/`)
- `__pycache__/`
- `.log` files

---

## 🚦 Development Workflow

### Starting Development Session
1. Navigate to project: `cd c:\Users\JayantVerma\AA\SSH_AGENT\SOLO_AGENTS\SalesAgent\v19-backup\v19\LeadGenAgent`
2. Activate virtual environment (if using)
3. Start MongoDB (if not running)
4. Start SearXNG (if not running)
5. Run server: `uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload`
6. Access UI: http://localhost:8001

### Making Changes
1. Make code edits
2. Server auto-reloads (with `--reload` flag)
3. Test changes in UI
4. Check terminal logs for errors

### Committing Changes
```bash
git add .
git commit -m "Description of changes"
git push origin main
```

---

## 📊 Performance Notes

- **Concurrent Users**: FastAPI supports multiple simultaneous SSE streams
- **Iteration Limit**: Max 5 ReAct iterations per generation (configurable)
- **Target Count**: 30 leads per run (configurable)
- **Email Validation**: ~100ms per email (DNS only, SMTP disabled for speed)
- **Scraping Speed**: ~5s per company (Firecrawl API)
- **Scoring Speed**: ~2-3s per company (LLM API)

---

## 🎓 Key Concepts

### ReAct Pattern
The agent follows **Thought → Action → Observation** loop:
1. **Thought**: LLM reasons about current state
2. **Action**: LLM selects tool and parameters
3. **Observation**: Tool execution results
4. Repeat until `complete_task` called or max iterations reached

### Server-Sent Events (SSE)
Real-time streaming from server to client:
- One-way communication (server → client)
- Automatic reconnection
- Event-based messages
- No WebSocket overhead

### Tool Execution Flow
1. Agent decides which tool to call
2. Tool executes (search, scrape, validate, score, save)
3. Results returned as observation
4. Agent reasons about next action
5. Progress streamed to UI via SSE

---

## 📞 Support & Contact

**GitHub Issues**: https://github.com/coder-jayant/multi-agent-lead-generation-system/issues

**Developer**: Jayant Verma
**Email**: jayantverma12@me.com

---

**Last Sync**: 2026-02-11T14:10:00+05:30
**Version**: 1.0.0
