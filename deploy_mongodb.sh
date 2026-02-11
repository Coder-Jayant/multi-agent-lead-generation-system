#!/bin/bash
# MongoDB Docker Deployment Script for Server
# Run this on your server: 49.50.117.66

echo "🚀 Deploying MongoDB with Docker..."
echo ""

# Configuration
CONTAINER_NAME="leadgen_mongodb"
MONGO_USER="leadgen_admin"
MONGO_PASS="LeadGen@2026Secure"
MONGO_DB="leadgen"
MONGO_PORT="27017"

# Check if container already exists
if docker ps -a | grep -q $CONTAINER_NAME; then
    echo "⚠️  Container $CONTAINER_NAME already exists."
    echo "   Removing old container..."
    docker stop $CONTAINER_NAME 2>/dev/null
    docker rm $CONTAINER_NAME 2>/dev/null
fi

# Start MongoDB
echo "📦 Starting MongoDB container..."
docker run -d \
  --name $CONTAINER_NAME \
  --restart unless-stopped \
  -p $MONGO_PORT:27017 \
  -v mongodb_data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=$MONGO_USER \
  -e MONGO_INITDB_ROOT_PASSWORD=$MONGO_PASS \
  -e MONGO_INITDB_DATABASE=$MONGO_DB \
  mongo:7.0

if [ $? -eq 0 ]; then
    echo "✅ MongoDB container started successfully!"
else
    echo "❌ Failed to start MongoDB container"
    exit 1
fi

# Wait for MongoDB to be ready
echo ""
echo "⏳ Waiting for MongoDB to be ready..."
sleep 5

# Test connection
echo ""
echo "🧪 Testing MongoDB connection..."
docker exec $CONTAINER_NAME mongosh \
  -u $MONGO_USER \
  -p $MONGO_PASS \
  --eval "db.adminCommand('ping')" \
  --quiet > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo "✅ MongoDB is healthy and ready!"
else
    echo "⚠️  MongoDB might still be starting up..."
fi

# Display info
echo ""
echo "=" * 60
echo "🎉 MongoDB Deployment Complete!"
echo "=" * 60
echo ""
echo "📊 Connection Details:"
echo "   Host: $(hostname -I | awk '{print $1}'):$MONGO_PORT"
echo "   Username: $MONGO_USER"
echo "   Password: $MONGO_PASS"
echo "   Database: $MONGO_DB"
echo ""
echo "🔗 Connection String:"
echo "   mongodb://$MONGO_USER:$MONGO_PASS@$(hostname -I | awk '{print $1}'):$MONGO_PORT/"
echo ""
echo "📝 Add to LeadGenAgent/.env:"
echo "   MONGODB_URI=mongodb://$MONGO_USER:$MONGO_PASS@$(hostname -I | awk '{print $1}'):$MONGO_PORT/"
echo "   MONGODB_DATABASE=$MONGO_DB"
echo ""
echo "🛠️  Management:"
echo "   View logs: docker logs $CONTAINER_NAME"
echo "   Stop: docker stop $CONTAINER_NAME"
echo "   Start: docker start $CONTAINER_NAME"
echo ""
