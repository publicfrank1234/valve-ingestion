#!/bin/bash
# Test the Python API server locally before deploying

cd "$(dirname "$0")"

echo "🧪 Testing Python API Server Locally"
echo "======================================"
echo ""

# Check if Flask is installed
echo "1. Checking dependencies..."
if ! python3 -c "import flask" 2>/dev/null; then
    echo "   ⚠️  Flask not installed. Installing..."
    pip3 install flask flask-cors
else
    echo "   ✅ Flask installed"
fi

if ! python3 -c "import psycopg2" 2>/dev/null; then
    echo "   ⚠️  psycopg2 not installed. Installing..."
    pip3 install psycopg2-binary
else
    echo "   ✅ psycopg2 installed"
fi

echo ""
echo "2. Testing database connection..."
python3 -c "
from search_specs import get_db_connection
try:
    conn = get_db_connection()
    print('   ✅ Database connection successful!')
    conn.close()
except Exception as e:
    print(f'   ❌ Database connection failed: {e}')
    print('   Make sure DATABASE_URL or DB_* environment variables are set')
    exit(1)
"

echo ""
echo "3. Testing search function..."
python3 -c "
from search_specs import search_specs
try:
    results = search_specs(
        valve_type='Gate Valve',
        size_nominal='1/2',
        body_material='Carbon Steel',
        max_results=3
    )
    print(f'   ✅ Search successful! Found {len(results)} results')
    if len(results) > 0:
        print(f'   Sample result: {results[0].get(\"valve_type\")} - {results[0].get(\"size_nominal\")} - {results[0].get(\"body_material\")}')
    else:
        print('   ⚠️  No results found (this might be OK if no matching records exist)')
except Exception as e:
    print(f'   ❌ Search failed: {e}')
    import traceback
    traceback.print_exc()
    exit(1)
"

echo ""
echo "4. Testing compatibility mappings..."
python3 -c "
from search_specs import search_specs
# Test with abbreviation
results_gt = search_specs(valve_type='GT', max_results=1)
results_gate = search_specs(valve_type='Gate Valve', max_results=1)
print(f'   ✅ Compatibility mapping test:')
print(f'      \"GT\" search: {len(results_gt)} results')
print(f'      \"Gate Valve\" search: {len(results_gate)} results')
"

echo ""
echo "5. Starting API server on port 5000..."
echo "   Press Ctrl+C to stop"
echo "   Then test with: curl -X POST http://localhost:5000/search/normalized -H 'Content-Type: application/json' -d '{\"normalizedSpecs\": {\"valveType\": \"Gate Valve\", \"size\": \"1/2\", \"material\": \"Carbon Steel\"}}'"
echo ""

python3 database_api.py









