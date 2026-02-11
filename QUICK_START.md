# 🚀 Lead Generator AI - Quick Start Guide

## ✅ Your Configuration

All services are configured and ready to use:

### Self-Hosted Services
- **SearxNG**: http://111.118.185.108:8080
- **Firecrawl**: http://111.118.185.108:3002
- **Scout LLM**: http://49.50.117.66:8000/v1

Configuration file: `.env` ✅ Already configured!

## 📦 Installation

### 1. Install Dependencies

```bash
cd LeadGenAgent
pip install -r requirements.txt
```

Expected packages:
- langgraph, langchain-core, langchain-openai
- fastapi, uvicorn
- requests, tldextract, python-dotenv

### 2. Verify Configuration

```bash
python -c "from config.settings import print_config; print_config()"
```

Should show:
```
===== Lead Generator Configuration =====
SEARXNG_BASE_URL: http://111.118.185.108:8080
FIRECRAWL_BASE_URL: http://111.118.185.108:3002
OPENAI_BASE_URL: http://49.50.117.66:8000/v1
OPENAI_MODEL: /model
MAX_SEARCH_ITERATIONS: 5
TARGET_LEAD_COUNT: 30
========================================
```

## 🎯 Run the Application

### Option 1: Quick Start Script (Recommended)

```bash
python start.py
```

### Option 2: Uvicorn Directly

```bash
cd api
uvicorn main:app --reload --port 8000
```

### Expected Output

```
🚀 Starting Lead Generator AI Agent...
📍 Access UI at: http://localhost:8000
📍 API docs at: http://localhost:8000/docs

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

## 🌐 Access the Application

**Web UI**: http://localhost:8000

**API Docs**: http://localhost:8000/docs (FastAPI Swagger)

**Health Check**: http://localhost:8000/health

## 🧪 Test the System

### 1. Test Services (From Browser/Curl)

```bash
# SearxNG
curl http://111.118.185.108:8080

# Firecrawl (if accessible)
curl http://111.118.185.108:3002/health

# Scout LLM
curl http://49.50.117.66:8000/v1/models
```

### 2. Test Lead Generation (Via UI)

1. Open http://localhost:8000
2. Enter product description:
   ```
   We provide cloud infrastructure services for enterprise clients. 
   Target customers: Mid-market to enterprise companies in India,
   specifically in technology, e-commerce, and financial services 
   sectors. Decision makers are CTOs, IT Directors, and DevOps leads.
   ```
3. Set target: 10 leads
4. Set max iterations: 3
5. Click "Generate Leads"
6. Wait 2-4 minutes for results

### 3. Test Via API

```bash
curl -X POST http://localhost:8000/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "product_description": "Cloud infrastructure for enterprises in India",
    "target_count": 10,
    "max_iterations": 3
  }'
```

## 📊 Monitor Logs

The ReAct controller logs all reasoning steps:

```
💭 Thought: I need to extract the ICP first...
⚙️ Action: extract_icp
📊 Observation: {"industries": ["Technology", "E-commerce"]...}

💭 Thought: Now I'll generate search queries...
⚙️ Action: generate_search_queries
📊 Observation: ["cloud hosting companies in India", ...]

💭 Thought: Searching for companies...
⚙️ Action: searxng_search
📊 Observation: [{"url": "https://...", "title": "..."}...]
```

## 📁 Data Storage

Leads are automatically saved to:
```
LeadGenAgent/data/leads.json
```

Structure:
```json
[
  {
    "company_name": "Example Corp",
    "domain": "example.com",
    "homepage_url": "https://example.com",
    "relevance_score": 85,
    "fit_label": "high",
    "extracted_emails": ["contact@example.com"],
    "discovered_at": "2026-02-04T10:30:00"
  }
]
```

## 🔧 Troubleshooting

### Issue: ImportError

**Fix**: Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "SEARXNG_BASE_URL not configured"

**Fix**: Check `.env` file exists in LeadGenAgent/ folder
```bash
# Verify
cat .env | grep SEARXNG
```

### Issue: LLM API errors

**Fix**: Test Scout LLM endpoint
```bash
curl http://49.50.117.66:8000/v1/models

# If timeout, check if accessible from your network
ping 49.50.117.66
```

### Issue: No search results

**Fix**: Test SearxNG directly
```bash
curl "http://111.118.185.108:8080/search?q=test&format=json"
```

### Issue: Firecrawl timeouts

**Solution**: Increase timeout in `.env`
```env
FIRECRAWL_TIMEOUT=60
```

## 📈 Expected Performance

**For 30 Leads:**
- Search iterations: 3-5
- Time: 3-5 minutes
- LLM calls: ~100-150 (ICP + queries + scoring)
- SearxNG searches: 15-25
- Firecrawl enrichments: 40-60

**Quality Metrics:**
- High fit (80-100): ~20-30%
- Medium fit (50-79): ~40-50%
- Low fit (<50): ~20-30% (filtered out)

## 🎨 Customization

### Adjust Search Strategy

Edit `agent/controller.py` - CONTROLLER_PROMPT:
```python
# Change default iterations
MAX_SEARCH_ITERATIONS=7  # More thorough

# Change quality threshold
# In controller.py, change score >= 50 to score >= 60
```

### Add Custom Tools

1. Create in `agent/tools/custom_tool.py`:
```python
from langchain_core.tools import tool

@tool
def linkedin_profile_scraper(company_domain: str) -> str:
    """Scrape LinkedIn company profile"""
    # Your logic
    return json.dumps(data)
```

2. Register in `agent/controller.py`:
```python
from agent.tools.custom_tool import linkedin_profile_scraper

ALL_TOOLS = [
    extract_icp,
    generate_search_queries,
    searxng_search,
    normalize_candidates,
    firecrawl_enrich,
    score_company,
    linkedin_profile_scraper  # Add here
]
```

## 🚧 Next Steps

1. **✅ Run the app** - Test with sample product
2. **📊 Review results** - Check `data/leads.json`
3. **🎯 Refine prompts** - Adjust ICP extraction and scoring
4. **📧 Add email tool** - Automate outreach
5. **🔗 CRM integration** - Push to Salesforce/HubSpot

## 📚 Documentation

- **Architecture Diagrams**: See `architecture_diagrams.md` artifact
- **Full README**: `README.md` in LeadGenAgent/
- **Implementation Walkthrough**: See `walkthrough.md` artifact

## 🎤 Presentation Demo Script

1. **Show Architecture** (architecture_diagrams.md)
   - Explain ReAct controller pattern
   - Highlight self-hosted services

2. **Run Live Demo**
   - Enter product description in UI
   - Show real-time logs with ReAct reasoning
   - Display scored leads

3. **Show Data**
   - Open `data/leads.json`
   - Explain deduplication
   - Show contact info extraction

4. **Discuss Extensions**
   - Email automation
   - CRM integration
   - Multi-product campaigns

## ✅ Ready to Generate Leads!

Your system is fully configured and ready to use. Start the app and begin generating quality B2B leads!

```bash
python start.py
```

Then visit: **http://localhost:8000**
