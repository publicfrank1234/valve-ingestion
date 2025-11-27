#!/usr/bin/env python3
"""
Setup database schema for valve specs.
"""

import psycopg2
import os
import sys

def setup_database():
    """Create database schema."""
    import sys
    import os
    
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # dotenv not installed, skip
    
    # Get connection details from environment variables (required)
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT', '5432')
    db_name = os.getenv('DB_NAME', 'postgres')
    db_user = os.getenv('DB_USER', 'postgres')
    db_password = os.getenv('DB_PASSWORD')
    
    if not db_host or not db_password:
        print("✗ Error: Database credentials not found!")
        print("\nPlease create a .env file with your database credentials:")
        print("  DB_HOST=db.your-project.supabase.co")
        print("  DB_PASSWORD=your-password")
        print("  DB_USER=postgres")
        print("  DB_NAME=postgres")
        print("  DB_PORT=5432")
        print("  DB_SSLMODE=require")
        sys.exit(1)
    
    # Build connection string (URL encode password if needed)
    from urllib.parse import quote_plus
    encoded_password = quote_plus(db_password)
    conn_string = f"postgresql://{db_user}:{encoded_password}@{db_host}:{db_port}/{db_name}"
    
    print("Connecting to Supabase database...")
    print(f"Host: {db_host}")
    print(f"Database: {db_name}")
    print(f"User: {db_user}\n")
    
    try:
        # Connect to database
        conn = psycopg2.connect(conn_string)
        print("✓ Connected successfully!")
        
        # Read and execute schema
        schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
        
        cursor = conn.cursor()
        
        # Execute schema (split by semicolons for multiple statements)
        print("\nCreating database schema...")
        cursor.execute(schema_sql)
        conn.commit()
        
        print("✓ Schema created successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'valve_specs'
        """)
        
        if cursor.fetchone():
            print("✓ valve_specs table exists")
        
        # Check row count
        cursor.execute("SELECT COUNT(*) FROM valve_specs")
        count = cursor.fetchone()[0]
        print(f"✓ Current records in valve_specs: {count}")
        
        cursor.close()
        conn.close()
        
        print("\n" + "="*60)
        print("Database setup complete!")
        print("="*60)
        print("\nYou can now insert specs using:")
        print("  python database/insert_spec.py test_extracted_spec.json")
        
    except psycopg2.Error as e:
        print(f"✗ Database error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    setup_database()

