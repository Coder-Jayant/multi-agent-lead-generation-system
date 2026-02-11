#!/bin/bash
# MongoDB Quick Setup Script

echo "🚀 Starting MongoDB with Docker Compose..."

# Start MongoDB and Mongo Express
docker-compose -f docker-compose.mongodb.yml up -d

echo ""
echo "✅ MongoDB is starting up!"
echo ""
echo "📊 Services:"
echo "   - MongoDB: mongodb://localhost:27017"
echo "   - Mongo Express UI: http://localhost:8081"
echo ""
echo "🔐 Credentials:"
echo "   - Username: admin"
echo "   - Password: admin123"
echo ""
echo "⏳ Waiting for MongoDB to be ready..."
sleep 5

# Test connection
echo ""
echo "🧪 Testing MongoDB connection..."
docker exec leadgen_mongodb mongosh --eval "db.adminCommand('ping')" > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ MongoDB is healthy and ready!"
    echo ""
    echo "🎯 Connection string for app:"
    echo "   MONGODB_URI=mongodb://admin:admin123@localhost:27017"
    echo "   MONGODB_DATABASE=leadgen"
else
    echo "⚠️ MongoDB might still be starting up. Please wait a moment."
fi

echo ""
echo "📝 To stop MongoDB: docker-compose -f docker-compose.mongodb.yml down"
echo "📝 To view logs: docker-compose -f docker-compose.mongodb.yml logs -f"
