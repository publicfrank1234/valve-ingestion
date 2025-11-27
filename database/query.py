#!/usr/bin/env python3
"""
Query valve specs from the database.
"""

import psycopg2
import os
import sys
import json

def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    import sys
    import os
    
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed, skip
    
    # Try DATABASE_URL first (full connection string)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    
    # Get from environment variables
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    db_sslmode = os.getenv('DB_SSLMODE', 'require')
    
    if not db_host or not db_password:
        raise ValueError("Database credentials not found! Please set DB_HOST and DB_PASSWORD in .env file")
    
    # Build connection string (same as local)
    from urllib.parse import quote_plus
    encoded_password = quote_plus(db_password)
    conn_string = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
    
    return psycopg2.connect(conn_string)

def query_specs(limit=10):
    """Query specs from database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT 
            id, source_url, spec_sheet_url, sku,
            valve_type, size_nominal, body_material,
            max_pressure, pressure_class,
            starting_price, msrp,
            extracted_at
        FROM valve_specs
        ORDER BY extracted_at DESC
        LIMIT %s
    """
    
    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    
    print(f"\n{'='*80}")
    print(f"Found {len(results)} specs:")
    print(f"{'='*80}\n")
    
    for row in results:
        print(f"ID: {row[0]}")
        print(f"URL: {row[1]}")
        print(f"Spec Sheet: {row[2] or 'N/A'}")
        print(f"SKU: {row[3] or 'N/A'}")
        print(f"Type: {row[4] or 'N/A'}")
        print(f"Size: {row[5] or 'N/A'}")
        print(f"Material: {row[6] or 'N/A'}")
        print(f"Pressure: {row[7] or 'N/A'} {row[8] or ''}")
        print(f"Price: ${row[9] or 'N/A'}")
        print(f"MSRP: ${row[10] or 'N/A'}")
        print(f"Extracted: {row[11]}")
        print(f"{'-'*80}\n")
    
    cursor.close()
    conn.close()

def count_specs():
    """Count total specs in database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM valve_specs")
    count = cursor.fetchone()[0]
    
    print(f"Total specs in database: {count}")
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == 'count':
        count_specs()
    else:
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        query_specs(limit)

