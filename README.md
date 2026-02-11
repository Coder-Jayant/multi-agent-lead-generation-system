# 🤖 LeadGenAgent - AI-Powered B2B Lead Generation System

An intelligent ReAct agent that autonomously discovers, qualifies, and enriches B2B leads using LLM-powered decision making, real-time web scraping, and email validation.

## ✨ Features

- **🔍 Autonomous Lead Discovery**: ReAct agent searches for companies matching your ICP
- **📊 Intelligent Qualification**: LLM-based scoring against customizable criteria
- **📧 Email Validation**: DNS MX + SMTP verification with confidence scoring
- **🌐 Web Scraping**: Firecrawl integration for contact extraction
- **📱 Real-Time Streaming**: Server-Sent Events (SSE) for live progress updates
- **💾 Product Management**: Associate leads with products for organized tracking
- **🎯 Quality Filtering**: Score-based filtering (≥65) with fit labeling

## 🏗️ Architecture

```
Frontend (HTML/JS) → FastAPI (SSE) → LeadResearchController → ReAct Agent
                                            ↓
                      Tools: Search, Scrape, Email Validate, Score, Save
                                            ↓
                                        MongoDB
```

### Tech Stack
- **Backend**: FastAPI, Python 3.13
- **Agent**: LangChain Core, ReAct Pattern
- **LLM**: OpenAI GPT-4 (or compatible)
- **Search**: SearXNG (self-hosted meta-search)
- **Scraping**: Firecrawl API v2
- **Database**: MongoDB (async with motor)
- **Email**: dnspython, smtplib

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- MongoDB instance
- OpenAI API key (or compatible endpoint)
- SearXNG instance
- Firecrawl API key

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/YOUR_USERNAME/LeadGenAgent.git
cd LeadGenAgent
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

### Environment Variables

Create a `.env` file:

```env
# MongoDB
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=leadgen

# OpenAI (or compatible)
OPENAI_API_KEY=your_key_here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4

# External Services
SEARXNG_BASE_URL=http://localhost:8080
FIRECRAWL_API_KEY=your_firecrawl_key
FIRECRAWL_BASE_URL=https://api.firecrawl.dev
```

### Running the Application

```bash
cd api
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

Access the UI at: `http://localhost:8001`

## 📖 Usage

### 1. Create a Product
- Navigate to "Products" tab
- Fill in product details with optional advanced fields (industries, regions, personas)
- Click "Create Product"

### 2. Generate Leads
- Go to "Generate Leads" tab  
- Select a product from dropdown
- Set target count (default: 30)
- Add optional context
- Click "Start Generation"
- Watch real-time agent activity in the log

### 3. View Leads
- Switch to "View Leads" tab
- Filter by product, minimum score, or persona
- Export leads or manage via UI

## 🛠️ Agent Tools

The ReAct agent uses these tools:

| Tool | Purpose |
|------|---------|
| `searxng_search` | Discover companies via meta-search |
| `firecrawl_enrich` | Scrape homepage for emails & data |
| `email_validation` | Validate emails (DNS MX + SMTP) |
| `score_company` | LLM-based ICP matching (0-100) |
| `save_lead_tool` | Store qualified leads in MongoDB |
| `complete_task` | Signal completion & generate summary |

## 📊 Email Validation

**Confidence Scoring:**
- **95%**: SMTP verified (mailbox confirmed)
- **70%**: DNS valid + common pattern (sales@, info@, contact@)
- **60%**: DNS valid only
- **0%**: No MX records (invalid domain)

## 🗄️ MongoDB Schema

### Products Collection
```javascript
{
  _id: ObjectId,
  name: String,
  description: String,
  target_personas: Array,
  industries: Array,
  regions: Array,
  created_at: DateTime
}
```

### Leads Collection
```javascript
{
  _id: ObjectId,
  domain: String (unique),
  name: String,
  description: String,
  url: String,
  emails: Array[String],
  email_details: Array[{
    email: String,
    confidence: Number,
    status: String,
    has_mx: Boolean,
    smtp_valid: Boolean,
    scraped: Boolean
  }],
  email_source: String,
  qualification: {
    score: Number,
    reasoning: String,
    fit: String,
    qualified_at: DateTime
  },
  product_id: String,
  product_name: String,
  created_at: DateTime,
  updated_at: DateTime
}
```

## 🔧 API Endpoints

- `GET /` - Web UI
- `GET /api/products` - List all products
- `POST /api/products` - Create product
- `GET /api/generate/stream` - SSE lead generation
- `GET /api/mongodb/leads` - Get leads (with filters)
- `GET /api/leads/products` - Products with lead counts

## 📚 Documentation

- [Architecture Diagram](docs/architecture_diagram.md)
- [Agent Flow Diagram](docs/agent_flow_diagram.md)
- [Implementation Walkthrough](docs/walkthrough.md)

## 🐛 Troubleshooting

### Server won't start
- Check MongoDB connection
- Verify all environment variables are set
- Ensure port 8001 is available

### Agent not finding leads
- Verify SearXNG is running and accessible
- Check Firecrawl API key and quota
- Review agent logs for errors

### Email validation shows 0% confidence
- Check DNS resolver configuration
- Verify internet connectivity
- SMTP validation disabled by default (enable in config)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

MIT License - feel free to use this in your projects!

## 🙏 Credits

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [LangChain](https://python.langchain.com/)
- [Firecrawl](https://firecrawl.dev/)
- [SearXNG](https://github.com/searxng/searxng)

## 📧 Contact

For questions or support, open an issue on GitHub.

---

**⭐ If you find this useful, please star the repo!**
