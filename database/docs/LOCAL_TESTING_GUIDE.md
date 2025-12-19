# Local Testing Guide

## Test the Python API Server Locally Before Deploying

### Step 1: Install Dependencies

```bash
cd valve-spec-ingestion/database
pip3 install flask flask-cors psycopg2-binary
```

### Step 2: Set Database Credentials

Create a `.env` file in `valve-spec-ingestion/` directory or export environment variables:

```bash
# Option 1: Use DATABASE_URL (recommended)
export DATABASE_URL="postgresql://postgres:your-password@db.deaohsesihodomvhqlxe.supabase.co:5432/postgres"

# Option 2: Use individual variables
export DB_HOST=db.deaohsesihodomvhqlxe.supabase.co
export DB_PORT=5432
export DB_NAME=postgres
export DB_USER=postgres
export DB_PASSWORD=your-password
export DB_SSLMODE=require
```

### Step 3: Test Database Connection

```bash
cd valve-spec-ingestion/database
python3 -c "from search_specs import get_db_connection; conn = get_db_connection(); print('✅ Connected!'); conn.close()"
```

### Step 4: Test Search Function

```bash
python3 -c "
from search_specs import search_specs
results = search_specs(
    valve_type='Gate Valve',
    size_nominal='1/2',
    body_material='Carbon Steel',
    max_results=5
)
print(f'Found {len(results)} results')
for r in results[:3]:
    print(f\"  - {r.get('valve_type')} {r.get('size_nominal')} {r.get('body_material')}\")
"
```

### Step 5: Start API Server

```bash
cd valve-spec-ingestion/database
python3 database_api.py
```

Server will start on `http://localhost:5000`

### Step 6: Test API Endpoints

**Health Check:**
```bash
curl http://localhost:5000/health
```

**Test Search (Normalized):**
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
    },
    "maxResults": 10
  }'
```

**Test Search (Individual Parameters):**
```bash
curl -X POST http://localhost:5000/search \
  -H "Content-Type: application/json" \
  -d '{
    "valveType": "Gate Valve",
    "size": "1/2",
    "material": "Carbon Steel",
    "pressureRating": "800",
    "endConnection": "Socket-weld",
    "maxResults": 10
  }'
```

### Step 7: Test Compatibility Mappings

Test that abbreviations work:

```bash
# Test "GT" abbreviation
curl -X POST http://localhost:5000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "GT",
      "size": "1/2",
      "material": "CS"
    }
  }'
```

Should find results even though database has "Gate Valve" and "Carbon Steel".

### Quick Test Script

Run the automated test script:

```bash
cd valve-spec-ingestion/database
./test_api_local.sh
```

This will:
1. Check dependencies
2. Test database connection
3. Test search function
4. Test compatibility mappings
5. Start the API server

## Expected Results

✅ **Database Connection**: Should connect successfully
✅ **Search Function**: Should return results (or empty array if no matches)
✅ **Compatibility Mappings**: "GT" should match "Gate Valve", "CS" should match "Carbon Steel"
✅ **API Server**: Should start on port 5000
✅ **API Endpoints**: Should return JSON responses

## Troubleshooting

### Database Connection Error
- Check your `.env` file or environment variables
- Verify Supabase credentials are correct
- Test connection: `python3 -c "from search_specs import get_db_connection; get_db_connection()"`

### Import Errors
- Make sure you're in the `database/` directory
- Check that `search_specs.py` and `comprehensive_compatibility_mapping.py` are in the same directory

### No Results
- Check if records exist in database with those specs
- Try a simpler search (just valve_type)
- Check database directly: `SELECT * FROM valve_specs WHERE valve_type LIKE '%Gate Valve%' LIMIT 5;`

## Next Steps After Local Testing

Once local testing works:
1. Deploy to the same server as n8n (`52.10.49.140`)
2. Update n8n workflow URL to point to the deployed API
3. Test end-to-end with n8n workflow






