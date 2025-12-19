#!/usr/bin/env python3
"""
Quick diagnostic to check database connection and table discovery.
"""

import psycopg2
import os
from dotenv import load_dotenv
from urllib.parse import quote_plus

load_dotenv()

def get_db_connection():
    """Get database connection using same logic as jsonb_search.py."""
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url, sslmode='require')
    
    password = os.getenv('DB_PASSWORD', 'valve@123')
    encoded_password = quote_plus(password)
    
    pooler_host = os.getenv('DB_POOLER_HOST')
    if pooler_host:
        pooler_user = os.getenv('DB_POOLER_USER', 'postgres.deaohsesihodomvhqlxe')
        pooler_port = os.getenv('DB_POOLER_PORT', '6543')
        conn_string = f"postgresql://{pooler_user}:{encoded_password}@{pooler_host}:{pooler_port}/postgres?sslmode=require"
        try:
            return psycopg2.connect(conn_string)
        except Exception as e:
            print(f"⚠️  Pooler connection failed: {e}")
            print("Trying direct connection...")
    
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'db.deaohsesihodomvhqlxe.supabase.co'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres'),
        password=password,
        sslmode='require'
    )

conn = get_db_connection()
cursor = conn.cursor()

# Check database info
cursor.execute("SELECT current_database(), current_user")
db_info = cursor.fetchone()
print(f"✅ Connected to database: {db_info[0]}, user: {db_info[1]}\n")

# Check all tables with 'valve' in name
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%valve%'
    ORDER BY table_name
""")
tables = [row[0] for row in cursor.fetchall()]
print(f"Tables with 'valve' in name ({len(tables)}):")
for t in tables[:15]:
    print(f"  - {t}")

# Check all tables ending in _specs
cursor.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name LIKE '%_specs'
    ORDER BY table_name
""")
spec_tables = [row[0] for row in cursor.fetchall()]
print(f"\nTables ending in '_specs' ({len(spec_tables)}):")
for t in spec_tables[:15]:
    print(f"  - {t}")

# Check if butterfly_valve_specs exists
if 'butterfly_valve_specs' in spec_tables:
    cursor.execute('SELECT COUNT(*) FROM butterfly_valve_specs')
    count = cursor.fetchone()[0]
    print(f"\n✅ butterfly_valve_specs exists with {count} rows")
    
    # Check sample data
    cursor.execute("""
        SELECT 
            tech_specs->>'size' as size, 
            tech_specs->>'seatMaterial' as seat_material,
            tech_specs->>'seat_material' as seat_material_alt
        FROM butterfly_valve_specs 
        WHERE tech_specs IS NOT NULL
        LIMIT 5
    """)
    samples = cursor.fetchall()
    print(f"\nSample data (size, seatMaterial, seat_material):")
    for sample in samples:
        print(f"  {sample}")
    
    # Test search query
    cursor.execute("""
        SELECT COUNT(*) 
        FROM butterfly_valve_specs
        WHERE (tech_specs->>'size' ILIKE '%6%' OR tech_specs->>'size' = '6')
          AND (tech_specs->>'seatMaterial' ILIKE '%epdm%' OR tech_specs->>'seat_material' ILIKE '%epdm%')
    """)
    match_count = cursor.fetchone()[0]
    print(f"\n🔍 Test query (size=6, seatMaterial=EPDM): Found {match_count} matches")
else:
    print("\n❌ butterfly_valve_specs NOT found in database")

conn.close()

