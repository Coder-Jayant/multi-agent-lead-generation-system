"""
MongoDB Connection Manager
Singleton pattern for managing MongoDB connections with runtime configuration
"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError

logger = logging.getLogger(__name__)


class MongoDBManager:
    """
    Singleton MongoDB connection manager with dynamic configuration support
    """
    
    _instance: Optional['MongoDBManager'] = None
    _client: Optional[AsyncIOMotorClient] = None
    _db: Optional[AsyncIOMotorDatabase] = None
    _config: Dict[str, str] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize manager (singleton pattern ensures this runs once)"""
        pass
    
    async def configure(self, mongo_uri: str, database_name: str) -> Dict[str, Any]:
        """
        Configure MongoDB connection at runtime
        
        Args:
            mongo_uri: MongoDB connection URI
            database_name: Name of the database to use
            
        Returns:
            Dict with status and message
        """
        try:
            # Close existing connection if any
            if self._client:
                self._client.close()
                logger.info("[MongoDB] Closed previous connection")
            
            # Create new client
            self._client = AsyncIOMotorClient(
                mongo_uri,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                maxPoolSize=50,
                minPoolSize=10
            )
            
            # Test connection
            await self._client.admin.command('ping')
            
            # Set database
            self._db = self._client[database_name]
            
            # Store config
            self._config = {
                'mongo_uri': mongo_uri,
                'database_name': database_name,
                'configured_at': datetime.utcnow().isoformat()
            }
            
            # Save config to database for persistence
            await self._save_config()
            
            logger.info(f"[MongoDB] Successfully connected to database: {database_name}")
            
            return {
                'status': 'success',
                'message': f'Connected to MongoDB database: {database_name}',
                'database': database_name
            }
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"[MongoDB] Connection failed: {e}")
            return {
                'status': 'error',
                'message': f'Failed to connect to MongoDB: {str(e)}'
            }
        except Exception as e:
            logger.error(f"[MongoDB] Configuration error: {e}")
            return {
                'status': 'error',
                'message': f'Configuration error: {str(e)}'
            }
    
    async def _save_config(self):
        """Save configuration to database for persistence"""
        try:
            if self._db is not None:
                await self._db.config.update_one(
                    {'_id': 'mongodb_config'},
                    {'$set': {
                        'mongo_uri': self._config['mongo_uri'],
                        'database_name': self._config['database_name'],
                        'updated_at': datetime.utcnow()
                    }},
                    upsert=True
                )
        except Exception as e:
            logger.warning(f"[MongoDB] Could not save config: {e}")

    
    async def load_config_from_env(self, mongo_uri: str, database_name: str):
        """Load configuration from environment variables on startup"""
        if mongo_uri and database_name:
            logger.info("[MongoDB] Loading config from environment")
            await self.configure(mongo_uri, database_name)
    
    def get_database(self) -> Optional[AsyncIOMotorDatabase]:
        """Get the current database instance"""
        return self._db
    
    def get_collection(self, name: str):
        """
        Get a collection from the database
        
        Args:
            name: Collection name
            
        Returns:
            Collection instance or None if not configured
        """
        if not self._db:
            logger.warning(f"[MongoDB] Database not configured, cannot access collection: {name}")
            return None
        return self._db[name]
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check MongoDB connection health
        
        Returns:
            Dict with health status
        """
        if self._client is None or self._db is None:
            return {
                'status': 'not_configured',
                'message': 'MongoDB not configured'
            }
        
        try:
            # Ping server
            await self._client.admin.command('ping')
            
            # Get server info
            server_info = await self._client.server_info()
            
            return {
                'status': 'healthy',
                'message': 'MongoDB connection is healthy',
                'database': self._config.get('database_name'),
                'server_version': server_info.get('version'),
                'configured_at': self._config.get('configured_at')
            }
        except Exception as e:
            logger.error(f"[MongoDB] Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'message': f'Health check failed: {str(e)}'
            }
    
    def is_configured(self) -> bool:
        """Check if MongoDB is configured and connected"""
        return self._client is not None and self._db is not None
    
    async def close(self):
        """Close MongoDB connection"""
        if self._client:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("[MongoDB] Connection closed")


# Global instance
_db_manager: Optional[MongoDBManager] = None


def get_db_manager() -> MongoDBManager:
    """
    Get the global MongoDB manager instance
    
    Returns:
        MongoDBManager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = MongoDBManager()
    return _db_manager
