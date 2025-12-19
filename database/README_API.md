# Database API Server - Quick Start

## Local Testing (Before Deployment)

### 1. Install Dependencies
```bash
cd valve-spec-ingestion/database
pip3 install flask flask-cors psycopg2-binary
```

### 2. Set Database Credentials
```bash
export DATABASE_URL="postgresql://postgres:password@db.deaohsesihodomvhqlxe.supabase.co:5432/postgres"
# OR set individual DB_* variables
```

### 3. Test Search Function
```bash
python3 test_search.py
```

This tests:
- Database connection
- Search functionality
- Compatibility mappings

### 4. Start API Server
```bash
python3 database_api.py
```

Server runs on `http://localhost:5000`

### 5. Test API
```bash
# Health check
curl http://localhost:5000/health

# Test search
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

## Deploy to Cloud

Once local testing works:

1. **Copy to server**: `scp -r database/ user@52.10.49.140:/path/to/`
2. **SSH into server**: `ssh user@52.10.49.140`
3. **Install deps**: `pip3 install flask flask-cors psycopg2-binary`
4. **Set credentials**: Export DATABASE_URL or DB_* variables
5. **Start server**: `python3 database_api.py` (or use screen/nohup/systemd)
6. **Update n8n**: n8n workflow already configured to use `http://localhost:5000/search/normalized`

## Why Use Python API?

- ✅ Uses compatibility mappings (finds all variations)
- ✅ Uses IN clauses (fast, uses indexes)
- ✅ Handles abbreviations automatically
- ✅ Better matching than direct Supabase queries






