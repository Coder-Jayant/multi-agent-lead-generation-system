"""
MongoDB Data Models and Schemas
Defines the structure of Products, Leads, and Config documents
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, GetCoreSchemaHandler, GetJsonSchemaHandler
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import core_schema
from bson import ObjectId


class PyObjectId(str):
    """Custom type for Pydantic v2 to handle MongoDB ObjectId"""
    
    @classmethod
    def __get_pydantic_core_schema__(
        cls,
        _source_type: Any,
        _handler: GetCoreSchemaHandler,
    ) -> core_schema.CoreSchema:
        """Define the core schema for validation"""
        return core_schema.union_schema([
            core_schema.is_instance_schema(ObjectId),
            core_schema.chain_schema([
                core_schema.str_schema(),
                core_schema.no_info_plain_validator_function(cls.validate),
            ])
        ],
        serialization=core_schema.plain_serializer_function_ser_schema(
            lambda x: str(x)
        ))
    
    @classmethod
    def validate(cls, v):
        """Validate and convert to ObjectId"""
        if isinstance(v, ObjectId):
            return v
        if isinstance(v, str) and ObjectId.is_valid(v):
            return ObjectId(v)
        raise ValueError(f"Invalid ObjectId: {v}")
    
    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: GetJsonSchemaHandler
    ) -> JsonSchemaValue:
        """Define JSON schema for OpenAPI"""
        return {"type": "string", "format": "objectid"}


class EmailDetail(BaseModel):
    """Email with validation and persona information"""
    email: str
    confidence: int  # 0-100
    status: str  # 'verified', 'likely', 'uncertain'
    persona: Optional[str] = None  # 'C-Level', 'VP/Director', etc.
    validated_at: datetime = Field(default_factory=datetime.utcnow)


class LeadQualification(BaseModel):
    """LLM-based lead qualification"""
    score: int  # 0-100
    reasoning: str
    fit: str  # 'high', 'medium', 'low'
    qualified_at: datetime = Field(default_factory=datetime.utcnow)


class Lead(BaseModel):
    """Lead document schema"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    product_id: PyObjectId
    domain: str
    name: str
    description: str
    url: str
    emails: List[EmailDetail] = []
    qualification: Optional[LeadQualification] = None
    email_source: str  # 'scraped' or 'inferred'
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class ProductMetadata(BaseModel):
    """Product targeting metadata"""
    target_personas: List[str] = []
    industries: List[str] = []
    regions: List[str] = []
    company_size: Optional[str] = None
    budget_range: Optional[str] = None


class Product(BaseModel):
    """Product document schema"""
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    name: str
    description: str
    metadata: ProductMetadata = Field(default_factory=ProductMetadata)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    lead_count: int = 0  # Cached count, updated on lead save
    
    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class MongoDBConfig(BaseModel):
    """MongoDB configuration document"""
    id: str = Field(alias="_id", default="mongodb_config")
    mongo_uri: str
    database_name: str
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        populate_by_name = True


# Helper functions for common operations

def product_to_dict(product: Product) -> Dict[str, Any]:
    """Convert Product model to MongoDB document"""
    doc = product.dict(by_alias=True, exclude_none=True)
    if 'id' in doc and doc['id'] is None:
        del doc['id']
    return doc


def lead_to_dict(lead: Lead) -> Dict[str, Any]:
    """Convert Lead model to MongoDB document"""
    doc = lead.dict(by_alias=True, exclude_none=True)
    if 'id' in doc and doc['id'] is None:
        del doc['id']
    # Convert EmailDetail and LeadQualification to dicts
    if 'emails' in doc:
        doc['emails'] = [email.dict() if isinstance(email, EmailDetail) else email for email in doc['emails']]
    if 'qualification' in doc and doc['qualification']:
        doc['qualification'] = doc['qualification'].dict() if isinstance(doc['qualification'], LeadQualification) else doc['qualification']
    return doc


def dict_to_product(doc: Dict[str, Any]) -> Product:
    """Convert MongoDB document to Product model"""
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    return Product(**doc)


def dict_to_lead(doc: Dict[str, Any]) -> Lead:
    """Convert MongoDB document to Lead model"""
    if '_id' in doc:
        doc['_id'] = str(doc['_id'])
    if 'product_id' in doc:
        doc['product_id'] = str(doc['product_id'])
    return Lead(**doc)


# MongoDB indexes for performance
LEAD_INDEXES = [
    [("product_id", 1)],  # Query leads by product
    [("domain", 1), ("product_id", 1)],  # Duplicate checking
    [("qualification.score", -1)],  # Sort by score
    [("created_at", -1)],  # Sort by date
]

PRODUCT_INDEXES = [
    [("created_at", -1)],  # Sort by date
    [("name", 1)],  # Search by name
]
