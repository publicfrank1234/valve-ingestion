# Deployment Steps: Local Testing → Cloud Deployment

## Phase 1: Local Testing ✅

### Step 1: Install Dependencies
```bash
cd valve-spec-ingestion/database
pip3 install flask flask-cors psycopg2-binary
```

### Step 2: Set Database Credentials
```bash
# Option 1: Use DATABASE_URL
export DATABASE_URL="postgresql://postgres:your-password@db.deaohsesihodomvhqlxe.supabase.co:5432/postgres"

# Option 2: Use individual variables
export DB_HOST=db.deaohsesihodomvhqlxe.supabase.co
export DB_PORT=5432
export DB_NAME=postgres
export DB_USER=postgres
export DB_PASSWORD=your-password
export DB_SSLMODE=require
```

### Step 3: Test Search Functionality
```bash
cd valve-spec-ingestion/database
python3 test_search.py
```

This will test:
- ✅ Database connection
- ✅ Basic search
- ✅ Compatibility mappings
- ✅ Full search with all parameters

### Step 4: Start API Server Locally
```bash
python3 database_api.py
```

Server starts on `http://localhost:5000`

### Step 5: Test API Endpoints

**Health Check:**
```bash
curl http://localhost:5000/health
```

**Test Search:**
```bash
curl -X POST http://localhost:5000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "Gate Valve",
      "size": "1/2",
      "material": "Carbon Steel",
      "pressureRating": "800",
      "endConnection": "Socket-weld"
    }
  }'
```

### Step 6: Test with Your Example

```bash
curl -X POST http://localhost:5000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "Gate Valve",
      "size": "1/2",
      "material": "Carbon Steel",
      "pressureRating": "800",
      "endConnection": "Socket-weld"
    }
  }'
```

Should return results if matching records exist in database.

## Phase 2: Deploy to Cloud Server

### On the Remote Server (52.10.49.140)

#### Step 1: Copy Files
```bash
# On your local machine
scp -r valve-spec-ingestion/database user@52.10.49.140:/path/to/rfq/valve-spec-ingestion/
```

#### Step 2: SSH into Server
```bash
ssh user@52.10.49.140
cd /path/to/rfq/valve-spec-ingestion/database
```

#### Step 3: Install Dependencies
```bash
pip3 install flask flask-cors psycopg2-binary
# OR if using virtual environment
python3 -m venv venv
source venv/bin/activate
pip install flask flask-cors psycopg2-binary
```

#### Step 4: Set Environment Variables
```bash
# Create .env file or export variables
export DATABASE_URL="postgresql://postgres:password@db.deaohsesihodomvhqlxe.supabase.co:5432/postgres"
# OR
export DB_HOST=db.deaohsesihodomvhqlxe.supabase.co
export DB_PASSWORD=your-password
# etc.
```

#### Step 5: Test on Server
```bash
python3 test_search.py
```

#### Step 6: Start API Server (Background)
```bash
# Using screen (recommended)
screen -S api-server
python3 database_api.py
# Press Ctrl+A, then D to detach

# OR using nohup
nohup python3 database_api.py > api.log 2>&1 &

# OR using systemd (see below)
```

#### Step 7: Update n8n Workflow URL

In n8n workflow, update the HTTP Request Tool URL to:
- `http://localhost:5000/search/normalized` (if on same server)
- OR `http://52.10.49.140:5000/search/normalized` (if accessible)

## Phase 3: Production Setup (Optional)

### Using systemd (Linux)

Create service file:
```bash
sudo nano /etc/systemd/system/valve-api.service
```

```ini
[Unit]
Description=Valve Specs Database API
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/valve-spec-ingestion/database
Environment="DATABASE_URL=postgresql://..."
ExecStart=/usr/bin/python3 /path/to/valve-spec-ingestion/database/database_api.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable valve-api
sudo systemctl start valve-api
sudo systemctl status valve-api
```

### Using gunicorn (Production)

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 database_api:app
```

## Verification

After deployment, test from n8n server:

```bash
curl http://localhost:5000/health
curl -X POST http://localhost:5000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{"normalizedSpecs": {"valveType": "Gate Valve", "size": "1/2"}}'
```

## Troubleshooting

### API Server Not Starting
- Check port 5000 is not in use: `lsof -i :5000`
- Check Python version: `python3 --version`
- Check dependencies: `pip3 list | grep flask`

### Database Connection Fails
- Verify credentials: `echo $DATABASE_URL`
- Test connection: `python3 test_search.py`
- Check Supabase dashboard for connection limits

### No Results from Search
- Test search directly: `python3 test_search.py`
- Check database: `SELECT COUNT(*) FROM valve_specs WHERE valve_type LIKE '%Gate Valve%';`
- Try simpler search (just valve_type)

### n8n Can't Reach API
- Check API is running: `curl http://localhost:5000/health`
- Check firewall/security groups allow port 5000
- If on different servers, use full URL: `http://52.10.49.140:5000/search/normalized`

