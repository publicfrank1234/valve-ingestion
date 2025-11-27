#!/usr/bin/env python3
"""
Check progress of the batch extraction process.
"""

import json
import os
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.query import count_specs

def check_progress():
    """Check extraction progress."""
    print("\n" + "="*80)
    print("Extraction Progress")
    print("="*80)
    
    # Check database count
    try:
        from database.insert import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM valve_specs")
        db_count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        print(f"✓ Database records: {db_count}")
    except Exception as e:
        print(f"✗ Database error: {e}")
        db_count = 0
    
    # Check progress file
    if os.path.exists('extraction_progress.json'):
        with open('extraction_progress.json', 'r') as f:
            progress = json.load(f)
        
        processed = len(progress.get('processed', []))
        failed = len(progress.get('failed', []))
        last_index = progress.get('last_index', 0)
        total = progress.get('total_urls', 0)
        
        print(f"✓ Processed URLs: {processed}")
        print(f"✗ Failed URLs: {failed}")
        print(f"📍 Last index: {last_index}/{total}")
        
        if total > 0:
            percentage = (last_index / total) * 100
            print(f"📊 Progress: {percentage:.1f}%")
            remaining = total - last_index
            print(f"⏳ Remaining: {remaining} URLs")
    else:
        print("⚠️  No progress file found (process may not have started)")
    
    # Check error log
    if os.path.exists('extraction_errors.json'):
        with open('extraction_errors.json', 'r') as f:
            errors = json.load(f)
        print(f"⚠️  Total errors logged: {len(errors)}")
        if errors:
            print("\nRecent errors:")
            for error in errors[-5:]:
                print(f"  - {error.get('url', 'Unknown')[:60]}...")
                print(f"    {error.get('error', 'Unknown error')[:60]}")
    
    print("="*80 + "\n")

if __name__ == "__main__":
    check_progress()

