# MongoDB Quick Setup Script for Windows

Write-Host "🚀 Starting MongoDB with Docker Compose..." -ForegroundColor Green

# Start MongoDB and Mongo Express
docker-compose -f docker-compose.mongodb.yml up -d

Write-Host ""
Write-Host "✅ MongoDB is starting up!" -ForegroundColor Green
Write-Host ""
Write-Host "📊 Services:" -ForegroundColor Cyan
Write-Host "   - MongoDB: mongodb://localhost:27017"
Write-Host "   - Mongo Express UI: http://localhost:8081"
Write-Host ""
Write-Host "🔐 Credentials:" -ForegroundColor Cyan
Write-Host "   - Username: admin"
Write-Host "   - Password: admin123"
Write-Host ""
Write-Host "⏳ Waiting for MongoDB to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Test connection
Write-Host ""
Write-Host "🧪 Testing MongoDB connection..." -ForegroundColor Yellow
$testResult = docker exec leadgen_mongodb mongosh --eval "db.adminCommand('ping')" 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ MongoDB is healthy and ready!" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎯 Connection string for app:" -ForegroundColor Cyan
    Write-Host "   MONGODB_URI=mongodb://admin:admin123@localhost:27017"
    Write-Host "   MONGODB_DATABASE=leadgen"
} else {
    Write-Host "⚠️ MongoDB might still be starting up. Please wait a moment." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "📝 Commands:" -ForegroundColor Cyan
Write-Host "   Stop: docker-compose -f docker-compose.mongodb.yml down"
Write-Host "   Logs: docker-compose -f docker-compose.mongodb.yml logs -f"
Write-Host "   Open Mongo Express: start http://localhost:8081"
