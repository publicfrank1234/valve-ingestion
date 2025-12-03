#!/usr/bin/env python3
"""
Test different database connection methods to find the working one.
"""
import os
import psycopg2
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv('.env')

password = os.getenv('DB_PASSWORD', 'valve@123')
encoded_password = quote_plus(password)

print("=" * 60)
print("Testing Database Connections")
print("=" * 60)

# Test 1: DATABASE_URL (if set)
database_url = os.getenv('DATABASE_URL')
if database_url:
    print("\n1. Testing DATABASE_URL...")
    try:
        conn = psycopg2.connect(database_url)
        print("   ✅ DATABASE_URL connection successful!")
        print(f"   Host: {conn.info.host}")
        conn.close()
    except Exception as e:
        print(f"   ❌ DATABASE_URL failed: {e}")

# Test 2: Pooler connection (current .env settings)
pooler_host = os.getenv('DB_POOLER_HOST')
if pooler_host:
    print(f"\n2. Testing Pooler connection ({pooler_host})...")
    pooler_user = os.getenv('DB_POOLER_USER', 'postgres.deaohsesihodomvhqlxe')
    pooler_port = os.getenv('DB_POOLER_PORT', '6543')
    conn_string = f"postgresql://{pooler_user}:{encoded_password}@{pooler_host}:{pooler_port}/postgres?sslmode=require"
    try:
        conn = psycopg2.connect(conn_string)
        print("   ✅ Pooler connection successful!")
        print(f"   Host: {conn.info.host}")
        conn.close()
    except Exception as e:
        print(f"   ❌ Pooler connection failed: {e}")
        print(f"   💡 Get the correct pooler hostname from Supabase Dashboard:")
        print(f"      Settings → Database → Connection Pooling → Session mode")

# Test 3: Direct connection (may not work if IPv6 is not available)
print("\n3. Testing Direct connection...")
db_host = os.getenv('DB_HOST', 'db.deaohsesihodomvhqlxe.supabase.co')
db_user = os.getenv('DB_USER', 'postgres')
try:
    conn = psycopg2.connect(
        host=db_host,
        port=os.getenv('DB_PORT', '5432'),
        database=os.getenv('DB_NAME', 'postgres'),
        user=db_user,
        password=password,
        sslmode=os.getenv('DB_SSLMODE', 'require')
    )
    print("   ✅ Direct connection successful!")
    print(f"   Host: {conn.info.host}")
    conn.close()
except Exception as e:
    print(f"   ❌ Direct connection failed: {e}")
    if "could not translate host name" in str(e):
        print(f"   💡 This is expected - use connection pooler instead")

print("\n" + "=" * 60)
print("Next Steps:")
print("=" * 60)
print("1. Go to https://supabase.com/dashboard")
print("2. Select your project")
print("3. Settings → Database → Connection Pooling")
print("4. Copy the 'Session mode' connection string")
print("5. Update .env file with the correct pooler hostname")
print("=" * 60)




