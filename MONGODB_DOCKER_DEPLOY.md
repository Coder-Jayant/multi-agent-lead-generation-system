# MongoDB Docker Deployment Guide

## Quick Start on Server (49.50.117.66)

### Option 1: Single Command (Recommended)

```bash
# On your server (49.50.117.66)
docker run -d \
  --name leadgen_mongodb \
  --restart unless-stopped \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=leadgen_admin \
  -e MONGO_INITDB_ROOT_PASSWORD=LeadGen@2026Secure \
  -e MONGO_INITDB_DATABASE=leadgen \
  mongo:7.0
```

**That's it!** MongoDB is now running at `49.50.117.66:27017`

---

### Option 2: With Mongo Express Web UI

```bash
# 1. Create network
docker network create leadgen_network

# 2. Start MongoDB
docker run -d \
  --name leadgen_mongodb \
  --network leadgen_network \
  --restart unless-stopped \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=leadgen_admin \
  -e MONGO_INITDB_ROOT_PASSWORD=LeadGen@2026Secure \
  -e MONGO_INITDB_DATABASE=leadgen \
  mongo:7.0

# 3. Start Mongo Express (Web UI)
docker run -d \
  --name mongo_express \
  --network leadgen_network \
  --restart unless-stopped \
  -p 8083:8081 \
  -e ME_CONFIG_MONGODB_URL=mongodb://leadgen_admin:LeadGen@2026Secure@leadgen_mongodb:27017/ \
  -e ME_CONFIG_BASICAUTH=false \
  mongo-express:latest
```

**Access:**
- MongoDB: `49.50.117.66:27017`
- Web UI: `http://49.50.117.66:8083`

---

## Connection String for App

Add to `LeadGenAgent/.env`:

```bash
# MongoDB on your server
MONGODB_URI=mongodb://leadgen_admin:LeadGen@2026Secure@49.50.117.66:27017/
MONGODB_DATABASE=leadgen
```

---

## Verify Installation

### 1. Check Container Status
```bash
docker ps | grep mongo
```

Should show:
```
leadgen_mongodb   mongo:7.0   Up X minutes   27017/tcp
```

### 2. Test Connection
```bash
docker exec -it leadgen_mongodb mongosh \
  -u leadgen_admin \
  -p LeadGen@2026Secure \
  --authenticationDatabase admin
```

Should open MongoDB shell. Try:
```javascript
show dbs
use leadgen
db.test.insertOne({test: "Hello LeadGen!"})
db.test.find()
```

### 3. From Python (on your dev machine)
```bash
cd LeadGenAgent
python test_connection.py
```

Should output: `🎉 All tests passed!`

---

## Management Commands

```bash
# View logs
docker logs leadgen_mongodb

# Follow logs
docker logs -f leadgen_mongodb

# Stop MongoDB
docker stop leadgen_mongodb

# Start MongoDB
docker start leadgen_mongodb

# Restart MongoDB
docker restart leadgen_mongodb

# Remove MongoDB (DANGER: Deletes data if no volume)
docker stop leadgen_mongodb
docker rm leadgen_mongodb
```

---

## Backup & Restore

### Create Backup
```bash
# Backup all databases
docker exec leadgen_mongodb mongodump \
  -u leadgen_admin \
  -p LeadGen@2026Secure \
  --authenticationDatabase admin \
  --archive=/data/backup.archive

# Copy to host
docker cp leadgen_mongodb:/data/backup.archive ./mongodb_backup_$(date +%Y%m%d).archive
```

### Restore Backup
```bash
# Copy backup to container
docker cp ./mongodb_backup.archive leadgen_mongodb:/data/restore.archive

# Restore
docker exec leadgen_mongodb mongorestore \
  -u leadgen_admin \
  -p LeadGen@2026Secure \
  --authenticationDatabase admin \
  --archive=/data/restore.archive
```

---

## Production Best Practices

### 1. Use Strong Password
```bash
# Generate secure password
openssl rand -base64 32

# Use it in docker run command
-e MONGO_INITDB_ROOT_PASSWORD=<your-secure-password>
```

### 2. Enable Persistence (Already included with `-v mongodb_data:/data/db`)

### 3. Configure Memory Limits
```bash
docker run -d \
  --name leadgen_mongodb \
  --restart unless-stopped \
  --memory="2g" \
  --memory-swap="2g" \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=leadgen_admin \
  -e MONGO_INITDB_ROOT_PASSWORD=LeadGen@2026Secure \
  mongo:7.0
```

### 4. Bind to Specific IP (More secure)
```bash
# Only listen on server's private IP
docker run -d \
  --name leadgen_mongodb \
  --restart unless-stopped \
  -p 127.0.0.1:27017:27017 \  # Only localhost
  -v mongodb_data:/data/db \
  -e MONGO_INITDB_ROOT_USERNAME=leadgen_admin \
  -e MONGO_INITDB_ROOT_PASSWORD=LeadGen@2026Secure \
  mongo:7.0
```

Then use SSH tunnel:
```bash
# From dev machine
ssh -L 27017:localhost:27017 user@49.50.117.66
```

---

## Troubleshooting

### Can't Connect
```bash
# Check if MongoDB is running
docker ps | grep mongo

# Check logs
docker logs leadgen_mongodb

# Check port is open
netstat -tlnp | grep 27017

# Test from server itself
docker exec -it leadgen_mongodb mongosh -u leadgen_admin -p LeadGen@2026Secure
```

### Permission Denied
```bash
# Fix volume permissions
docker exec -it leadgen_mongodb chown -R mongodb:mongodb /data/db
```

### Out of Disk Space
```bash
# Check disk usage
docker system df

# Clean up unused images
docker system prune -a
```

---

## Quick Reference

| Component | URL |
|-----------|-----|
| MongoDB | `49.50.117.66:27017` |
| Mongo Express | `http://49.50.117.66:8083` |
| Username | `leadgen_admin` |
| Password | `LeadGen@2026Secure` |
| Database | `leadgen` |

**Connection String:**
```
mongodb://leadgen_admin:LeadGen@2026Secure@49.50.117.66:27017/
```

---

## Next Steps

1. ✅ Run Docker command on server
2. ✅ Update `.env` with connection string
3. ✅ Test connection: `python test_connection.py`
4. ✅ Run tests: `pytest tests/test_mongodb.py -v`
5. ✅ Continue with Phase 2 implementation
