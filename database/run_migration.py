#!/usr/bin/env python3
"""
Run database migration to add performance indexes.
Uses the same connection logic as other database scripts.
"""

import psycopg2
import os
import sys
from urllib.parse import quote_plus

def get_db_connection():
    """Get PostgreSQL connection from environment variables."""
    # Try DATABASE_URL first (full connection string)
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg2.connect(database_url)
    
    # Otherwise use individual environment variables
    password = os.getenv('DB_PASSWORD', 'valve@123')
    
    # URL encode password if needed
    encoded_password = quote_plus(password)
    
    # Try connection pooler first (if pooler host is set)
    pooler_host = os.getenv('DB_POOLER_HOST')
    if pooler_host:
        pooler_user = os.getenv('DB_POOLER_USER', 'postgres.deaohsesihodomvhqlxe')
        pooler_port = os.getenv('DB_POOLER_PORT', '5432')
        conn_string = f"postgresql://{pooler_user}:{encoded_password}@{pooler_host}:{pooler_port}/postgres?sslmode=require"
        try:
            return psycopg2.connect(conn_string)
        except Exception as e:
            print(f"⚠️  Pooler connection failed: {e}")
            print("Trying direct connection...")
    
    # Fall back to direct connection
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'aws-1-us-east-2.pooler.supabase.com'),
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=os.getenv('DB_USER', 'postgres.deaohsesihodomvhqlxe'),
        password=password,
        sslmode=os.getenv('DB_SSLMODE', 'require')
    )

def run_migration():
    """Run the performance indexes migration."""
    print("🔧 Running database migration: Adding performance indexes...")
    print()
    
    # Read the migration SQL file
    migration_file = os.path.join(os.path.dirname(__file__), 'add_performance_indexes.sql')
    
    if not os.path.exists(migration_file):
        print(f"❌ Error: Migration file not found: {migration_file}")
        return False
    
    with open(migration_file, 'r') as f:
        migration_sql = f.read()
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print("✓ Connected to database")
        print(f"  Host: {conn.info.host}")
        print(f"  Database: {conn.info.dbname}")
        print()
        
        # Execute the migration
        print("📊 Creating indexes...")
        cursor.execute(migration_sql)
        conn.commit()
        
        print("✓ Migration completed successfully!")
        print()
        print("Created indexes:")
        print("  - idx_valve_size_material (valve_type, size_nominal, body_material)")
        print("  - idx_size_material_pressure (size_nominal, body_material, pressure_class)")
        print("  - idx_end_connection_inlet (end_connection_inlet)")
        print("  - idx_end_connection_outlet (end_connection_outlet)")
        print("  - idx_pressure_class_null (pressure_class)")
        print()
        print("🚀 Search queries should now be 10-50x faster!")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print()
        print("💡 Make sure your database credentials are set:")
        print("   Option 1: Set DATABASE_URL environment variable")
        print("   Option 2: Set DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        return False

if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

