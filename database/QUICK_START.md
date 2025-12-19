# Quick Start: Python API Server

## The Problem
n8n workflow queries Supabase directly with ILIKE, which:
- Doesn't use compatibility mappings
- Is slower (can't use indexes efficiently)
- May miss variations

## The Solution
Use Python API server which:
- ✅ Uses compatibility mappings
- ✅ Uses IN clauses (fast, uses indexes)
- ✅ Handles all variations automatically

## Setup (2 Steps)

### Step 1: Start Python API Server

On the same server as n8n (or accessible from n8n):

```bash
cd valve-spec-ingestion/database

# Install dependencies (if needed)
pip install flask flask-cors psycopg2-binary

# Set database credentials (if not in .env)
export DATABASE_URL="postgresql://postgres:password@host:5432/postgres"
# OR
export DB_HOST=db.deaohsesihodomvhqlxe.supabase.co
export DB_PASSWORD=your-password
# etc.

# Start server
python3 database_api.py
```

Server will run on `http://localhost:5000` (or set `PORT` env var)

### Step 2: Update n8n Workflow URL

The n8n workflow is already updated to use:
- **URL**: `http://localhost:5000/search/normalized` (if on same server)
- **OR**: `http://52.10.49.140:5000/search/normalized` (if on different server)

You can also set environment variable in n8n:
- `DATABASE_API_URL=http://your-server:5000/search/normalized`

## Test It

```bash
# Test the API
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

## What Changed

**Before (Direct Supabase):**
- Query: `valve_type=ilike.*Gate Valve*` (slow, may miss variations)

**After (Python API):**
- Query: `valve_type IN ('Gate Valve', 'Gate Valve (Non-Rising Stem)', 'Gate Valve (Rising Stem)')` (fast, finds all variations)

## Benefits

1. **Faster**: IN clauses use indexes (10-50x faster)
2. **More accurate**: Finds all variations automatically
3. **Better matching**: "GT" matches all Gate Valve types, "CS" matches all Carbon Steel variations

## Running in Background

```bash
# Using screen
screen -S api-server
cd valve-spec-ingestion/database
python3 database_api.py
# Press Ctrl+A, then D to detach

# Using nohup
nohup python3 database_api.py > api.log 2>&1 &
```

## Next Steps

1. Start the Python API server
2. Test it with curl
3. The n8n workflow will automatically use it
4. You should now see matches!






