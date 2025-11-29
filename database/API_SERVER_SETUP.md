# Python API Server Setup

## Why Use Python API Instead of Direct Supabase Query?

The Python API (`database_api.py`) uses:

- ✅ **Compatibility mappings** - Expands abbreviations to all database variations
- ✅ **IN clauses** - Fast exact matches (10-50x faster than ILIKE)
- ✅ **Full index utilization** - Optimal query performance
- ✅ **Handles all variations** - "GT" matches all Gate Valve types, "CS" matches all Carbon Steel variations

Direct Supabase queries via n8n:

- ❌ Only use ILIKE (slower, limited index usage)
- ❌ Don't use compatibility mappings
- ❌ May miss variations

## Quick Start

### 1. Start the API Server

```bash
cd valve-spec-ingestion/database
./start_api_server.sh
```

Or manually:

```bash
cd valve-spec-ingestion/database
python3 database_api.py
```

The server will start on `http://localhost:5000`

### 2. Test the API

```bash
# Health check
curl http://localhost:6000/health

# Test search
curl -X POST http://localhost:6000/search/normalized \
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

### 3. Update n8n Workflow

The n8n workflow has been updated to call:

- **URL**: `http://localhost:5000/search/normalized`
- **Method**: POST
- **Body**: JSON with `normalizedSpecs` object

## API Endpoints

### POST `/search/normalized`

Search using normalized specs object.

**Request:**

```json
{
  "normalizedSpecs": {
    "valveType": "Gate Valve",
    "size": "1/2",
    "material": "Carbon Steel",
    "pressureRating": "800",
    "endConnection": "Socket-weld"
  },
  "maxResults": 10
}
```

**Response:**

```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 123,
      "sourceUrl": "https://...",
      "valveType": "Gate Valve",
      "size": "1/2",
      "material": "Carbon Steel",
      "price": 54.99,
      ...
    }
  ]
}
```

### POST `/search`

Search using individual parameters.

**Request:**

```json
{
  "valveType": "Gate Valve",
  "size": "1/2",
  "material": "Carbon Steel",
  "pressureRating": "800",
  "endConnection": "Socket-weld",
  "maxResults": 10
}
```

### GET `/health`

Health check endpoint.

## Deployment Options

### Option 1: Local Development

```bash
cd valve-spec-ingestion/database
python3 database_api.py
```

### Option 2: Production (with gunicorn)

```bash
pip install gunicorn
cd valve-spec-ingestion/database
gunicorn -w 4 -b 0.0.0.0:5000 database_api:app
```

### Option 3: Docker

```dockerfile
FROM python:3.9
WORKDIR /app
COPY database/ .
RUN pip install flask flask-cors psycopg2-binary
ENV PORT=5000
CMD ["python", "database_api.py"]
```

### Option 4: Same Server as n8n

If n8n is running on `52.10.49.140:25678`, you can run the Python API on the same server:

```bash
# On the server
cd /path/to/valve-spec-ingestion/database
python3 database_api.py --port 5000
```

Then update n8n workflow URL to: `http://localhost:5000/search/normalized` (if on same server) or `http://52.10.49.140:5000/search/normalized` (if accessible)

## Environment Variables

The API uses the same database connection as other scripts:

- `DATABASE_URL` (preferred)
- Or `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE`

## Benefits

1. **Uses compatibility mappings** - All abbreviations and variations handled
2. **Fast searches** - IN clauses with exact matches
3. **Better matching** - Finds all variations (e.g., "Gate Valve" matches all Gate Valve types)
4. **Consistent** - Same logic as Python `search_specs.py`

## Troubleshooting

### Import Error

If you get import errors, make sure you're running from the `database/` directory:

```bash
cd valve-spec-ingestion/database
python3 database_api.py
```

### Database Connection Error

Check your `.env` file or environment variables for database credentials.

### Port Already in Use

Change the port:

```bash
PORT=5001 python3 database_api.py
```

Then update n8n workflow URL to use port 5001.
