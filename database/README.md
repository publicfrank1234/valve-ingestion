# Valve Specs Database Setup

## Free PostgreSQL Options

### 1. **Supabase** (Recommended)
- **URL:** https://supabase.com
- **Free Tier:** 500MB database, 2GB bandwidth
- **Setup:**
  1. Sign up at supabase.com
  2. Create a new project
  3. Go to Settings → Database
  4. Copy connection string

### 2. **Neon**
- **URL:** https://neon.tech
- **Free Tier:** 3GB storage, serverless PostgreSQL
- **Setup:**
  1. Sign up at neon.tech
  2. Create a project
  3. Copy connection string from dashboard

### 3. **Railway**
- **URL:** https://railway.app
- **Free Tier:** $5 credit/month
- **Setup:**
  1. Sign up at railway.app
  2. Create PostgreSQL service
  3. Copy connection details

### 4. **Render**
- **URL:** https://render.com
- **Free Tier:** PostgreSQL (spins down after inactivity)
- **Setup:**
  1. Sign up at render.com
  2. Create PostgreSQL database
  3. Copy connection string

## Setup Instructions

### 1. Install Dependencies

```bash
pip install psycopg2-binary
```

### 2. Set Environment Variables

Create a `.env` file or export variables:

```bash
export DB_HOST=your-host.supabase.co
export DB_PORT=5432
export DB_NAME=postgres
export DB_USER=postgres
export DB_PASSWORD=your-password
export DB_SSLMODE=require
```

For Supabase, the connection string format is:
```
postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
```

### 3. Create Database Schema

```bash
psql $DATABASE_URL -f database/schema.sql
```

Or using Python:
```python
import psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
with open('database/schema.sql', 'r') as f:
    conn.cursor().execute(f.read())
conn.commit()
```

### 4. Insert Extracted Specs

```bash
# Single spec file
python database/insert_spec.py test_extracted_spec.json

# Batch insert from multiple specs
python database/insert_spec.py sample_extracted_specs.json
```

### 5. Query Examples

```sql
-- Find all gate valves
SELECT * FROM valve_specs_summary WHERE valve_type = 'Gate Valve';

-- Find valves by size and material
SELECT * FROM valve_specs_summary 
WHERE size_nominal = '1/2' AND body_material = 'Carbon Steel';

-- Find valves by pressure class
SELECT * FROM valve_specs_summary WHERE pressure_class = '800';

-- Search in JSONB spec field
SELECT * FROM valve_specs 
WHERE spec->>'valveType' = 'Gate Valve';

-- Find by price range
SELECT * FROM valve_specs_summary 
WHERE starting_price BETWEEN 50 AND 100;
```

## Database Schema

- **valve_specs** - Main table with all specs
- **valve_specs_summary** - View for easy querying
- Indexes on common fields (valve_type, size, material, etc.)
- JSONB fields for flexible querying

## Integration with Extraction Script

After extracting specs, insert them:

```python
from database.insert_spec import insert_spec, get_db_connection

# Extract spec
spec_data = test_extraction(url)

# Insert into database
conn = get_db_connection()
spec_id = insert_spec(conn, spec_data)
conn.close()
```

