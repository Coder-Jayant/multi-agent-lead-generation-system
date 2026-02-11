"""
main.py
FastAPI backend for Lead Generator AI Agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import sys
from pathlib import Path
import logging
import json
import asyncio
from queue import Queue
import os
# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.controller import LeadResearchController
from agent.state import CompanyLead, load_leads, clear_all_leads

# MongoDB imports
from db.mongodb import get_db_manager
from db.models import Product, Lead, dict_to_product, dict_to_lead
from agent.tools.database_tools import create_product_tool

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global cancellation tracking for stop button
cancellation_flag = {"cancelled": False}
active_generation_id = None

app = FastAPI(
    title="Lead Generator AI Agent",
    description="""
    ## 🤖 MongoDB-Powered Lead Discovery & Management API
    
    ReAct-based AI agent for automated B2B lead generation, qualification, and management.
    
    ### Features
    - **Product Management**: Create and manage products/services for targeted lead generation
    - **AI Lead Discovery**: Automated web search and company discovery using ReAct agents
    - **Email Extraction**: Smart email extraction with persona classification (C-Level, VP/Director, etc.)
    - **LLM Qualification**: AI-powered lead scoring and qualification
    - **MongoDB Storage**: Persistent storage with duplicate detection
    - **Real-time Streaming**: Server-sent events for live progress updates
    
    ### MongoDB Endpoints
    - Configure MongoDB connection at runtime (no restart required)
    - Create products with targeting metadata
    - Generate and store leads per product
    - Filter and retrieve leads by product, score, persona
    
    ### External Services
    - **SearxNG**: Self-hosted web search
    - **Firecrawl**: Website content extraction
    - **OpenAI/LLM**: Lead qualification and analysis
    """,
    version="2.0.0",
    docs_url="/docs",  # Swagger UI
    redoc_url="/redoc",  # ReDoc alternative
    openapi_url="/openapi.json"
)

# Serve static files (UI)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Startup event: Auto-configure MongoDB from environment
@app.on_event("startup")
async def startup_event():
    """Auto-configure MongoDB on startup if .env has credentials"""
    mongo_uri = os.getenv("MONGODB_URI")
    mongo_db = os.getenv("MONGODB_DATABASE")
    
    if mongo_uri and mongo_db:
        try:
            await get_db_manager().configure(mongo_uri, mongo_db)
            logger.info(f"✅ MongoDB auto-configured: {mongo_db}")
        except Exception as e:
            logger.warning(f"⚠️ MongoDB auto-config failed: {e}")
    else:
        logger.info("ℹ️ MongoDB not in .env, configure via /api/config/mongodb")


# Root route - serve the UI
@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main UI page"""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return HTMLResponse(content="<h1>Lead Generation Agent API</h1><p>Visit <a href='/docs'>/docs</a> for API documentation</p>", status_code=200)

# Request/Response models
class LeadGenRequest(BaseModel):
    product_description: str = Field(..., min_length=20, description="Product/service description")
    
    # Product Details (from POC)
    product_name: Optional[str] = Field(default=None, description="Product name")
    company_name: Optional[str] = Field(default=None, description="Your company name")
    website_url: Optional[str] = Field(default=None, description="Your company website")
    
    # Optional additional fields for better targeting
    target_industries: Optional[str] = Field(default=None, description="Target industries (comma-separated)")
    target_regions: Optional[str] = Field(default=None, description="Target geographic regions (comma-separated)")
    company_size: Optional[str] = Field(default=None, description="Preferred company size (startup/SMB/mid-market/enterprise)")
    budget_range: Optional[str] = Field(default=None, description="Typical budget range")
    target_personas: Optional[List[str]] = Field(default=None, description="Target decision maker personas")
    
    # Seller info (optional)
    seller_company: Optional[str] = Field(default=None, description="Your company name")
    seller_value_prop: Optional[str] = Field(default=None, description="Your unique value proposition")
    
    # Search params
    target_count: int = Field(default=30, ge=5, le=100, description="Target number of quality leads")
    max_iterations: int = Field(default=5, ge=1, le=10, description="Max search iterations")
    
    class Config:
        # Allow empty strings to be converted to None
        json_schema_extra = {
            "example": {
                "product_description": "Cloud monitoring platform for DevOps teams",
                "target_industries": "Technology, E-commerce",
                "target_regions": "North America, Europe",
                "company_size": "mid-market",
                "budget_range": "$25K-100K",
                "seller_company": "MonitorCo",
                "seller_value_prop": "Real-time alerts with zero config",
                "target_count": 30,
                "max_iterations": 5
            }
        }

class LeadGenResponse(BaseModel):
    leads: List[CompanyLead]
    total_found: int
    quality_count: int
    status: str
    message: str

# MongoDB Configuration Models
class MongoDBConfigRequest(BaseModel):
    mongo_uri: str = Field(..., description="MongoDB connection URI")
    database_name: str = Field(default="leadgen", description="Database name")

class ProductCreateRequest(BaseModel):
    name: str = Field(..., min_length=3, description="Product name")
    description: str = Field(..., min_length=20, description="Product description")
    target_personas: Optional[List[str]] = Field(default=None, description="Target personas")
    industries: Optional[List[str]] = Field(default=None, description="Target industries")
    regions: Optional[List[str]] = Field(default=None, description="Target regions")

class ProductResponse(BaseModel):
    id: str
    name: str
    description: str
    lead_count: int
    created_at: str
    metadata: dict

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve main UI"""
    html_file = Path(__file__).parent / "static" / "index.html"
    if html_file.exists():
        return FileResponse(html_file)
    return HTMLResponse(content="<h1>Lead Generator AI</h1><p>UI not found</p>")

@app.post("/api/generate", response_model=LeadGenResponse)
async def generate_leads(request: LeadGenRequest):
    """
    Execute lead generation using ReAct controller.
    
    Process:
    1. Controller extracts ICP
    2. Generates search queries
    3. Searches via SearxNG
    4. Normalizes candidates
    5. Enriches via Firecrawl
    6. Scores companies
    7. Repeats until target reached or max iterations hit
    """
    try:
        logger.info(f"🚀 Lead generation request: target={request.target_count}, product='{request.product_description[:50]}...'")
        
        # Create and run controller
        controller = LeadResearchController(
            product_description=request.product_description,
            target_count=request.target_count,
            max_iterations=request.max_iterations
        )
        
        leads = controller.run()
        
        # Count quality leads
        quality_leads = [lead for lead in leads if lead.get('relevance_score', 0) >= 50]
        
        logger.info(f"✅ Generation complete: {len(quality_leads)} quality leads (total: {len(leads)})")
        
        return LeadGenResponse(
            leads=leads,
            total_found=len(leads),
            quality_count=len(quality_leads),
            status="complete",
            message=f"Generated {len(quality_leads)} quality leads out of {len(leads)} total"
        )
    
    except Exception as e:
        logger.exception("Lead generation failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/generate/stream")
async def generate_leads_stream(
    product_description: str,
    target_count: int = 30,
    max_iterations: int = 5,
    target_industries: str = None,
    target_regions: str = None,
    company_size: str = None,
    budget_range: str = None,
    seller_company: str = None,
    seller_value_prop: str = None,
    product_id: str = None,  # NEW
    product_name: str = None  # NEW
):
    """
    Stream lead generation progress in real-time using Server-Sent Events (SSE).
    Sends each agent step (thought, action, observation) as it happens.
    """
    async def event_generator():
        try:
            # Build enriched product description with additional context
            enriched_description = product_description
            
            # Add product details for better ICP extraction
            # Note: The original instruction snippet used 'request' object fields
            # which are not directly available as parameters in this function.
            # We are using the parameters that are available.
            
            if target_industries and target_industries.strip():
                enriched_description += f"\n\n**Target Industries**: {target_industries}"
            
            if target_regions and target_regions.strip():
                enriched_description += f"\n\n**Target Regions**: {target_regions}"
            
            # The instruction snippet had a partial line here, completing it based on context
            if company_size and company_size.strip():
                enriched_description += f"\n\n**Preferred Company Size**: {company_size}"
            if budget_range and budget_range.strip():
                enriched_description += f"\n\n**Typical Budget**: {budget_range}"
            if seller_company and seller_company.strip():
                enriched_description += f"\n\n**Seller**: {seller_company}"
            if seller_value_prop and seller_value_prop.strip():
                enriched_description += f"\nValue Proposition: {seller_value_prop}"
            
            # Send start event
            yield f"data: {json.dumps({'type': 'start', 'message': 'Starting lead research...'})}\n\n"
            
            # Reset cancellation flag
            global cancellation_flag, active_generation_id
            import uuid
            active_generation_id = str(uuid.uuid4())
            cancellation_flag = {"cancelled": False}
            
            # Create cancellation callback
            def check_cancellation():
                return cancellation_flag.get("cancelled", False)
            
            # Create controller
            controller = LeadResearchController(
                product_description=enriched_description,
                target_count=target_count,
                max_iterations=max_iterations,
                cancellation_callback=check_cancellation,
                product_id=product_id or "default",  # Pass product context
                product_name=product_name
            )
            
            # Set up step callback to stream progress
            step_count = 0
            
            def step_callback(step):
                nonlocal step_count
                step_count += 1
                
                event_data = {
                    'type': step.step_type,
                    'step_number': step_count,
                    'content': step.content,
                    'timestamp': step.timestamp if hasattr(step, 'timestamp') else None
                }
                
                if step.step_type == "action":
                    event_data['tool_name'] = step.tool_name
                    event_data['tool_input'] = step.tool_input if hasattr(step, 'tool_input') else None
                
                return f"data: {json.dumps(event_data)}\n\n"
            
            controller.set_step_callback(step_callback)
            
            # Run controller and stream steps
            # Note: We need to run this in a thread to avoid blocking
            import threading
            from queue import Queue
            
            message_queue = Queue()
            results = {}
            
            def run_controller():
                try:
                    # Override callback to push to queue
                    def queue_callback(step):
                        event_data = {
                            'step': step.step_type,
                            'message': step.content,
                            'observation': step.content if step.step_type == 'observation' else None
                        }
                        
                        if step.step_type == "action":
                            event_data['tool_name'] = getattr(step, 'tool_name', 'unknown')
                        
                        message_queue.put(event_data)
                    
                    controller.set_step_callback(queue_callback)
                    leads = controller.run()
                    
                    # Send each lead as separate event
                    for lead in leads:
                        message_queue.put({'event_type': 'lead', 'lead_data': lead})
                    
                    results['leads'] = leads
                    message_queue.put({'event_type': 'complete', 'total_leads': len(leads)})
                    
                except Exception as e:
                    logger.exception("Controller error")
                    message_queue.put({'event_type': 'error', 'message': str(e)})
            
            # Start controller in background thread
            thread = threading.Thread(target=run_controller)
            thread.start()
            
            # Stream messages from queue
            while True:
                # Check if cancelled
                if cancellation_flag.get("cancelled"):
                    yield f"event: error\ndata: {json.dumps({'message': 'Generation cancelled by user'})}\n\n"
                    break
                
                try:
                    # Non-blocking get with timeout
                    message = message_queue.get(timeout=0.1)
                    
                    # Check if it's a lead event
                    if message.get('event_type') == 'lead':
                        yield f"event: lead\ndata: {json.dumps(message['lead_data'])}\n\n"
                        continue
                    
                    # Check if it's a complete event
                    if message.get('event_type') == 'complete':
                        yield f"event: complete\ndata: {json.dumps({'total_leads': message.get('total_leads', 0)})}\n\n"
                        break
                    
                    # Check if it's an error
                    if message.get('event_type') == 'error':
                        yield f"event: error\ndata: {json.dumps({'message': message['message']})}\n\n"
                        break
                    
                    # Otherwise it's a step/observation from controller
                    if message.get('step') == 'thought':
                        yield f"event: step\ndata: {json.dumps({'step': 'thinking', 'message': message.get('message', '')})}\n\n"
                    elif message.get('step') == 'action':
                        yield f"event: step\ndata: {json.dumps({'step': 'action', 'message': message.get('message', ''), 'tool': message.get('tool_name', '')})}\n\n"
                    elif message.get('step') == 'observation' or message.get('observation'):
                        yield f"event: observation\ndata: {json.dumps({'observation': message.get('message', '') or message.get('observation', '')})}\n\n"
                
                except:
                    # Queue empty, check if thread still alive
                    if not thread.is_alive():
                        break
                    await asyncio.sleep(0.1)
            
            thread.join()
            
        except Exception as e:
            logger.exception("Streaming failed")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@app.post("/api/generate/cancel")
async def cancel_generation():
    """Cancel currently running lead generation"""
    global cancellation_flag, active_generation_id
    
    if active_generation_id is None:
        return {"status": "no_active_generation", "message": "No generation currently running"}
    
    cancellation_flag["cancelled"] = True
    gen_id = active_generation_id
    active_generation_id = None
    
    logger.info(f"🛑 Generation {gen_id} cancelled by user")
    
    return {
        "status": "cancelled",
        "message": "Lead generation cancelled successfully",
        "generation_id": gen_id
    }


@app.post("/api/generate/cancel")
async def cancel_generation():
    """Cancel currently running lead generation"""
    global cancellation_flag, active_generation_id
    
    if active_generation_id is None:
        return {"status": "no_active_generation", "message": "No generation currently running"}
    
    cancellation_flag["cancelled"] = True
    gen_id = active_generation_id
    active_generation_id = None
    
    logger.info(f"🛑 Generation {gen_id} cancelled by user")
    
    return {
        "status": "cancelled",
        "message": "Lead generation cancelled successfully",
        "generation_id": gen_id
    }

@app.get("/api/leads", response_model=List[CompanyLead])
async def get_all_leads():
    """Retrieve all persisted leads from JSON storage"""
    try:
        leads = load_leads()
        logger.info(f"Retrieved {len(leads)} persisted leads")
        return leads
    except Exception as e:
        logger.error(f"Failed to load leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/leads")
async def delete_all_leads():
    """Clear all persisted leads (for testing)"""
    try:
        clear_all_leads()
        logger.warning("All leads cleared")
        return {"status": "cleared", "message": "All leads have been deleted"}
    except Exception as e:
        logger.error(f"Failed to clear leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== MONGODB ENDPOINTS ====================

@app.post("/api/config/mongodb")
async def configure_mongodb(config: MongoDBConfigRequest):
    """
    Configure MongoDB connection at runtime
    No restart required - connection is established dynamically
    """
    try:
        manager = get_db_manager()
        result = await manager.configure(config.mongo_uri, config.database_name)
        
        if result['status'] == 'success':
            logger.info(f"✅ MongoDB configured: {config.database_name}")
            return result
        else:
            logger.error(f"❌ MongoDB configuration failed: {result['message']}")
            raise HTTPException(status_code=400, detail=result['message'])
    
    except Exception as e:
        logger.exception("MongoDB configuration error")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/config/mongodb/health")
async def mongodb_health():
    """Check MongoDB connection health"""
    try:
        manager = get_db_manager()
        health = await manager.health_check()
        return health
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

@app.post("/api/products")
async def create_product(product: ProductCreateRequest):
    """Create a new product for lead generation"""
    try:
        result = await create_product_tool(
            name=product.name,
            description=product.description,
            target_personas=product.target_personas,
            industries=product.industries,
            regions=product.regions
        )
        
        if result['status'] == 'success':
            logger.info(f"✅ Product created: {product.name}")
            return result
        else:
            raise HTTPException(status_code=400, detail=result['message'])
    
    except Exception as e:
        logger.exception("Product creation failed")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products")
async def list_products():
    """List all products"""
    try:
        manager = get_db_manager()
        if not manager.is_configured():
            raise HTTPException(status_code=503, detail="MongoDB not configured")
        
        db = manager.get_database()
        products_collection = db.products
        
        # Get all products, sorted by creation date
        products = []
        async for product_doc in products_collection.find().sort('created_at', -1):
            products.append({
                'id': str(product_doc['_id']),
                'name': product_doc['name'],
                'description': product_doc['description'],
                'lead_count': product_doc.get('lead_count', 0),
                'created_at': product_doc['created_at'].isoformat() if 'created_at' in product_doc else None,
                'metadata': product_doc.get('metadata', {})
            })
        
        logger.info(f"Retrieved {len(products)} products")
        return {'products': products, 'count': len(products)}
    
    except Exception as e:
        logger.exception("Failed to list products")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}")
async def get_product(product_id: str):
    """Get a single product by ID"""
    try:
        from bson import ObjectId
        manager = get_db_manager()
        if not manager.is_configured():
            raise HTTPException(status_code=503, detail="MongoDB not configured")
        
        db = manager.get_database()
        product_doc = await db.products.find_one({'_id': ObjectId(product_id)})
        
        if not product_doc:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return {
            'id': str(product_doc['_id']),
            'name': product_doc['name'],
            'description': product_doc['description'],
            'lead_count': product_doc.get('lead_count', 0),
            'created_at': product_doc['created_at'].isoformat() if 'created_at' in product_doc else None,
            'metadata': product_doc.get('metadata', {})
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get product")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/products/{product_id}/leads")
async def get_product_leads(product_id: str, min_score: Optional[int] = 0, limit: Optional[int] = 100):
    """Get all leads for a specific product"""
    try:
        from bson import ObjectId
        manager = get_db_manager()
        if not manager.is_configured():
            raise HTTPException(status_code=503, detail="MongoDB not configured")
        
        db = manager.get_database()
        leads_collection = db.leads
        
        # Build query
        query = {'product_id': ObjectId(product_id)}
        if min_score > 0:
            query['qualification.score'] = {'$gte': min_score}
        
        # Get leads
        leads = []
        async for lead_doc in leads_collection.find(query).sort('created_at', -1).limit(limit):
            leads.append({
                'id': str(lead_doc['_id']),
                'domain': lead_doc.get('domain'),
                'name': lead_doc.get('name'),
                'description': lead_doc.get('description'),
                'url': lead_doc.get('url'),
                'emails': lead_doc.get('emails', []),
                'qualification': lead_doc.get('qualification'),
                'created_at': lead_doc['created_at'].isoformat() if 'created_at' in lead_doc else None
            })
        
        logger.info(f"Retrieved {len(leads)} leads for product {product_id}")
        return {'leads': leads, 'count': len(leads)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get product leads")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/mongodb/leads")
async def create_mongodb_lead(lead_data: dict):
    """Create a new lead in MongoDB (called by agent save_lead tool)"""
    try:
        from bson import ObjectId
        from datetime import datetime
        
        manager = get_db_manager()
        if not manager.is_configured():
            raise HTTPException(status_code=503, detail="MongoDB not configured")
        
        db = manager.get_database()
        leads_collection = db.leads
        
        # Check for duplicate by domain
        existing = await leads_collection.find_one({'domain': lead_data.get('domain')})
        if existing:
            return {
                'status': 'duplicate',
                'message': f"Lead already exists: {lead_data.get('domain')}",
                'lead_id': str(existing['_id'])
            }
        
        # Create lead document
        lead_doc = {
            'domain': lead_data.get('domain'),
            'name': lead_data.get('name'),
            'description': lead_data.get('description', ''),
            'url': lead_data.get('url', ''),
            'emails': lead_data.get('emails', []),
            'phones': lead_data.get('phones', []),
            'linkedin_url': lead_data.get('linkedin_url'),
            'qualification': lead_data.get('qualification', {}),
            'product_context': lead_data.get('product_context', ''),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        }
        
        # Set qualification timestamp
        if 'qualification' in lead_doc and lead_doc['qualification']:
            lead_doc['qualification']['qualified_at'] = datetime.utcnow().isoformat()
        
        # Insert lead
        result = await leads_collection.insert_one(lead_doc)
        
        logger.info(f"✅ Created lead in MongoDB: {lead_data.get('name')} ({lead_data.get('domain')})")
        
        return {
            'status': 'success',
            'message': 'Lead created successfully',
            'lead_id': str(result.inserted_id)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to create lead")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/mongodb/leads")
async def get_all_mongodb_leads(
    min_score: int = 0, 
    limit: int = 100,
    product_id: Optional[str] = None,
    product_name: Optional[str] = None
):
    """Get all leads from MongoDB with optional filtering by score, product_id, or product_name"""
    try:
        manager = get_db_manager()
        if not manager.is_configured():
            raise HTTPException(status_code=503, detail="MongoDB not configured")
        
        db = manager.get_database()
        leads_collection = db.leads
        
        # Build query
        query = {}
        if min_score > 0:
            query['qualification.score'] = {'$gte': min_score}
        
        # Filter by product if specified
        if product_id:
            query['product_id'] = product_id
        elif product_name:
            query['product_name'] = product_name
        
        # Get leads
        leads = []
        async for lead_doc in leads_collection.find(query).sort('created_at', -1).limit(limit):
            leads.append({
                'id': str(lead_doc['_id']),
                'domain': lead_doc.get('domain'),
                'name': lead_doc.get('name'),
                'description': lead_doc.get('description'),
                'url': lead_doc.get('url'),
                'emails': lead_doc.get('emails', []),
                'email_details': lead_doc.get('email_details', []),  # Include validation details
                'email_source': lead_doc.get('email_source', 'unknown'),
                'phones': lead_doc.get('phones', []),
                'qualification': lead_doc.get('qualification'),
                'created_at': lead_doc['created_at'].isoformat() if 'created_at' in lead_doc else None
            })
        
        logger.info(f"Retrieved {len(leads)} leads from MongoDB")
        return {'leads': leads, 'count': len(leads)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to get leads")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leads/products")
async def list_products():
    """Get list of all products for filtering (from products collection, not leads aggregation)"""
    try:
        manager = get_db_manager()
        if not manager.is_configured():
            raise HTTPException(status_code=503, detail="MongoDB not configured")
        
        db = manager.get_database()
        products_collection = db.products
        leads_collection = db.leads
        
        # Get all products
        products = []
        async for product_doc in products_collection.find().sort('created_at', -1):
            product_id = str(product_doc['_id'])
            product_name = product_doc.get('name', 'Unnamed Product')
            
            # Count leads for this specific product only
            # Match by product_id OR product_name
            lead_count = await leads_collection.count_documents({
                '$or': [
                    {'product_id': product_id},
                    {'product_name': product_name}
                ]
            })
            
            products.append({
                'product_id': product_id,
                'product_name': product_name,
                'lead_count': lead_count
            })
        
        logger.info(f"Found {len(products)} products")
        return {'products': products, 'count': len(products)}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to list products")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/leads/filter")
async def filter_leads(
    product_id: Optional[str] = None,
    min_score: Optional[int] = 0,
    persona: Optional[str] = None,
    limit: Optional[int] = 100
):
    """Filter leads across all products or specific product"""
    try:
        from bson import ObjectId
        manager = get_db_manager()
        if not manager.is_configured():
            raise HTTPException(status_code=503, detail="MongoDB not configured")
        
        db = manager.get_database()
        leads_collection = db.leads
        
        # Build query
        query = {}
        if product_id:
            query['product_id'] = ObjectId(product_id)
        if min_score > 0:
            query['qualification.score'] = {'$gte': min_score}
        if persona:
            query['emails.persona'] = persona
        
        # Get leads
        leads = []
        async for lead_doc in leads_collection.find(query).sort('created_at', -1).limit(limit):
            leads.append({
                'id': str(lead_doc['_id']),
                'product_id': str(lead_doc['product_id']),
                'domain': lead_doc.get('domain'),
                'name': lead_doc.get('name'),
                'description': lead_doc.get('description'),
                'url': lead_doc.get('url'),
                'emails': lead_doc.get('emails', []),
                'qualification': lead_doc.get('qualification'),
                'created_at': lead_doc['created_at'].isoformat() if 'created_at' in lead_doc else None
            })
        
        logger.info(f"Filtered {len(leads)} leads (filters: product={product_id}, min_score={min_score}, persona={persona})")
        return {'leads': leads, 'count': len(leads), 'filters': {'product_id': product_id, 'min_score': min_score, 'persona': persona}}
    
    except Exception as e:
        logger.exception("Failed to filter leads")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    import os
    
    # Check required environment variables
    searxng_url = os.getenv("SEARXNG_BASE_URL", "")
    firecrawl_url = os.getenv("FIRECRAWL_BASE_URL", "")
    openai_key = os.getenv("OPENAI_API_KEY", "")
    
    status = {
        "status": "healthy",
        "searxng_configured": bool(searxng_url),
        "firecrawl_configured": bool(firecrawl_url),
        "llm_configured": bool(openai_key)
    }
    
    return status

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
