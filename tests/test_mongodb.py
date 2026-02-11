"""
Test suite for MongoDB integration
Run with: pytest tests/test_mongodb.py -v
"""

import pytest
import asyncio
from datetime import datetime
from bson import ObjectId

from db.mongodb import MongoDBManager, get_db_manager
from db.models import (
    Product, Lead, EmailDetail, LeadQualification,
    ProductMetadata, product_to_dict, lead_to_dict
)


@pytest.fixture
async def db_manager():
    """Setup MongoDB manager for testing"""
    manager = get_db_manager()
    
    # Configure with test database
    result = await manager.configure(
        mongo_uri="mongodb://localhost:27017",
        database_name="leadgen_test"
    )
    
    assert result['status'] == 'success', f"Failed to configure MongoDB: {result.get('message')}"
    
    yield manager
    
    # Cleanup: Drop test database
    if manager.get_database():
        await manager.get_database().client.drop_database("leadgen_test")
    
    await manager.close()


@pytest.mark.asyncio
async def test_mongodb_configuration(db_manager):
    """Test MongoDB configuration"""
    assert db_manager.is_configured()
    
    health = await db_manager.health_check()
    assert health['status'] == 'healthy'
    assert health['database'] == 'leadgen_test'


@pytest.mark.asyncio
async def test_product_creation(db_manager):
    """Test creating a product"""
    db = db_manager.get_database()
    products_collection = db.products
    
    # Create product
    product = Product(
        name="AI Voicebot",
        description="Agentic voicebot for customer support",
        metadata=ProductMetadata(
            target_personas=["C-Level", "VP/Director"],
            industries=["Technology", "Healthcare"],
            regions=["North America"]
        )
    )
    
    # Insert to database
    product_dict = product_to_dict(product)
    result = await products_collection.insert_one(product_dict)
    
    assert result.inserted_id is not None
    product_id = result.inserted_id
    
    # Retrieve and verify
    saved_product = await products_collection.find_one({"_id": product_id})
    assert saved_product is not None
    assert saved_product['name'] == "AI Voicebot"
    assert "C-Level" in saved_product['metadata']['target_personas']


@pytest.mark.asyncio
async def test_lead_creation_with_qualification(db_manager):
    """Test creating a lead with emails and qualification"""
    db = db_manager.get_database()
    leads_collection = db.leads
    products_collection = db.products
    
    # First create a product
    product = Product(
        name="Test Product",
        description="Test product for leads"
    )
    product_result = await products_collection.insert_one(product_to_dict(product))
    product_id = product_result.inserted_id
    
    # Create lead with emails and qualification
    lead = Lead(
        product_id=product_id,
        domain="acme.com",
        name="Acme Corp",
        description="Leading tech company",
        url="https://acme.com",
        emails=[
            EmailDetail(
                email="ceo@acme.com",
                confidence=95,
                status="verified",
                persona="C-Level"
            ),
            EmailDetail(
                email="vp@acme.com",
                confidence=90,
                status="verified",
                persona="VP/Director"
            )
        ],
        qualification=LeadQualification(
            score=85,
            reasoning="Perfect fit for AI automation, large enterprise",
            fit="high"
        ),
        email_source="scraped"
    )
    
    # Insert to database
    lead_dict = lead_to_dict(lead)
    result = await leads_collection.insert_one(lead_dict)
    
    assert result.inserted_id is not None
    lead_id = result.inserted_id
    
    # Retrieve and verify
    saved_lead = await leads_collection.find_one({"_id": lead_id})
    assert saved_lead is not None
    assert saved_lead['domain'] == "acme.com"
    assert len(saved_lead['emails']) == 2
    assert saved_lead['emails'][0]['email'] == "ceo@acme.com"
    assert saved_lead['emails'][0]['persona'] == "C-Level"
    assert saved_lead['qualification']['score'] == 85
    assert saved_lead['qualification']['fit'] == "high"


@pytest.mark.asyncio
async def test_duplicate_detection(db_manager):
    """Test duplicate lead detection by domain"""
    db = db_manager.get_database()
    leads_collection = db.leads
    products_collection = db.products
    
    # Create product
    product_result = await products_collection.insert_one(
        product_to_dict(Product(name="Test", description="Test"))
    )
    product_id = product_result.inserted_id
    
    # Create first lead
    lead1 = Lead(
        product_id=product_id,
        domain="duplicate.com",
        name="Duplicate Co",
        description="Test",
        url="https://duplicate.com",
        email_source="scraped"
    )
    await leads_collection.insert_one(lead_to_dict(lead1))
    
    # Check for duplicate
    existing = await leads_collection.find_one({
        'product_id': product_id,
        'domain': "duplicate.com"
    })
    
    assert existing is not None
    assert existing['domain'] == "duplicate.com"
    
    # Verify we can detect it
    is_duplicate = existing is not None
    assert is_duplicate == True


@pytest.mark.asyncio
async def test_get_leads_by_product(db_manager):
    """Test retrieving leads for a specific product"""
    db = db_manager.get_database()
    leads_collection = db.leads
    products_collection = db.products
    
    # Create two products
    product1_result = await products_collection.insert_one(
        product_to_dict(Product(name="Product 1", description="First"))
    )
    product2_result = await products_collection.insert_one(
        product_to_dict(Product(name="Product 2", description="Second"))
    )
    
    product1_id = product1_result.inserted_id
    product2_id = product2_result.inserted_id
    
    # Create leads for product 1
    for i in range(3):
        lead = Lead(
            product_id=product1_id,
            domain=f"company{i}.com",
            name=f"Company {i}",
            description="Test",
            url=f"https://company{i}.com",
            email_source="scraped"
        )
        await leads_collection.insert_one(lead_to_dict(lead))
    
    # Create leads for product 2
    for i in range(2):
        lead = Lead(
            product_id=product2_id,
            domain=f"other{i}.com",
            name=f"Other {i}",
            description="Test",
            url=f"https://other{i}.com",
            email_source="scraped"
        )
        await leads_collection.insert_one(lead_to_dict(lead))
    
    # Query leads for product 1
    product1_leads = []
    async for lead in leads_collection.find({'product_id': product1_id}):
        product1_leads.append(lead)
    
    assert len(product1_leads) == 3
    
    # Query leads for product 2
    product2_leads = []
    async for lead in leads_collection.find({'product_id': product2_id}):
        product2_leads.append(lead)
    
    assert len(product2_leads) == 2


@pytest.mark.asyncio
async def test_filter_leads_by_score(db_manager):
    """Test filtering leads by qualification score"""
    db = db_manager.get_database()
    leads_collection = db.leads
    products_collection = db.products
    
    # Create product
    product_result = await products_collection.insert_one(
        product_to_dict(Product(name="Test", description="Test"))
    )
    product_id = product_result.inserted_id
    
    # Create leads with different scores
    scores = [95, 75, 85, 55, 65]
    for i, score in enumerate(scores):
        lead = Lead(
            product_id=product_id,
            domain=f"company{i}.com",
            name=f"Company {i}",
            description="Test",
            url=f"https://company{i}.com",
            qualification=LeadQualification(
                score=score,
                reasoning="Test",
                fit="high" if score >= 80 else "medium" if score >= 60 else "low"
            ),
            email_source="scraped"
        )
        await leads_collection.insert_one(lead_to_dict(lead))
    
    # Filter leads with score >= 80
    high_score_leads = []
    async for lead in leads_collection.find({
        'product_id': product_id,
        'qualification.score': {'$gte': 80}
    }).sort('qualification.score', -1):
        high_score_leads.append(lead)
    
    assert len(high_score_leads) == 3  # 95, 85, (75 excluded, 55, 65 excluded)
    assert high_score_leads[0]['qualification']['score'] == 95
    assert high_score_leads[1]['qualification']['score'] == 85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
