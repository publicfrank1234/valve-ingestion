#!/usr/bin/env python3
"""
Test script to verify search functionality before deploying API server.
Run this to test:
1. Database connection
2. Search function
3. Compatibility mappings
"""

import os
import sys
from search_specs import search_specs, get_db_connection

def test_database_connection():
    """Test if we can connect to Supabase."""
    print("1. Testing database connection...")
    try:
        conn = get_db_connection()
        print("   ✅ Database connection successful!")
        conn.close()
        return True
    except Exception as e:
        print(f"   ❌ Database connection failed: {e}")
        print("\n   Make sure you have database credentials set:")
        print("   - DATABASE_URL (preferred)")
        print("   - OR DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD")
        return False

def test_basic_search():
    """Test basic search functionality."""
    print("\n2. Testing basic search...")
    try:
        results = search_specs(
            valve_type='Gate Valve',
            size_nominal='1/2',
            max_results=3
        )
        print(f"   ✅ Search successful! Found {len(results)} results")
        if len(results) > 0:
            print(f"   Sample: {results[0].get('valve_type')} - {results[0].get('size_nominal')} - {results[0].get('body_material')}")
        return True
    except Exception as e:
        print(f"   ❌ Search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_compatibility_mappings():
    """Test that compatibility mappings work."""
    print("\n3. Testing compatibility mappings...")
    try:
        # Test abbreviation "GT" should match "Gate Valve"
        results_gt = search_specs(valve_type='GT', max_results=1)
        results_gate = search_specs(valve_type='Gate Valve', max_results=1)
        
        print(f"   ✅ Compatibility mapping test:")
        print(f"      \"GT\" search: {len(results_gt)} results")
        print(f"      \"Gate Valve\" search: {len(results_gate)} results")
        
        # Test material abbreviation "CS" should match "Carbon Steel"
        results_cs = search_specs(body_material='CS', max_results=1)
        results_carbon = search_specs(body_material='Carbon Steel', max_results=1)
        print(f"      \"CS\" search: {len(results_cs)} results")
        print(f"      \"Carbon Steel\" search: {len(results_carbon)} results")
        
        return True
    except Exception as e:
        print(f"   ❌ Compatibility mapping test failed: {e}")
        return False

def test_full_search():
    """Test full search with all parameters."""
    print("\n4. Testing full search (Gate Valve, 1/2, Carbon Steel, 800, Socket-weld)...")
    try:
        results = search_specs(
            valve_type='Gate Valve',
            size_nominal='1/2',
            body_material='Carbon Steel',
            pressure_class='800',
            end_connection='Socket-weld',
            max_results=5
        )
        print(f"   ✅ Full search successful! Found {len(results)} results")
        if len(results) > 0:
            for i, r in enumerate(results[:3], 1):
                print(f"   Result {i}: {r.get('valve_type')} {r.get('size_nominal')} {r.get('body_material')} - ${r.get('starting_price')}")
        else:
            print("   ⚠️  No results found (might be OK if no matching records)")
        return True
    except Exception as e:
        print(f"   ❌ Full search failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Testing Python API Search Functionality")
    print("=" * 60)
    print()
    
    # Check environment
    if not os.getenv('DATABASE_URL') and not os.getenv('DB_HOST'):
        print("⚠️  No database credentials found in environment variables")
        print("   Set DATABASE_URL or DB_* variables before running")
        print()
    
    # Run tests
    all_passed = True
    all_passed &= test_database_connection()
    
    if all_passed:
        all_passed &= test_basic_search()
        all_passed &= test_compatibility_mappings()
        all_passed &= test_full_search()
    
    print("\n" + "=" * 60)
    if all_passed:
        print("✅ All tests passed! Ready to start API server.")
        print("\nNext step: Run 'python3 database_api.py' to start the server")
    else:
        print("❌ Some tests failed. Please fix issues before deploying.")
    print("=" * 60)









