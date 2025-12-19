#!/usr/bin/env python3
"""
Sync progress file with database.
Useful when resuming on a different machine or after database changes.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.insert import get_db_connection
import json
import config

def sync_progress():
    """Sync extraction_progress.json with database."""
    
    print("Syncing progress with database...")
    
    # Connect to database
    try:
        conn = get_db_connection()
        print("✓ Connected to database")
    except Exception as e:
        print(f"✗ Database connection error: {e}")
        return
    
    # Load processed URLs from database
    cursor = conn.cursor()
    cursor.execute("SELECT source_url FROM valve_specs")
    db_urls = set(row[0] for row in cursor.fetchall())
    cursor.close()
    conn.close()
    
    print(f"✓ Found {len(db_urls)} URLs in database")
    
    # Load or create progress file
    progress_file = config.PROGRESS_FILE
    if os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            progress = json.load(f)
    else:
        progress = {
            'processed': [],
            'failed': [],
            'last_index': 0,
            'start_time': None,
            'total_urls': 0
        }
    
    # Update processed list with database URLs
    old_count = len(progress.get('processed', []))
    progress['processed'] = list(db_urls)
    new_count = len(progress['processed'])
    
    # Save updated progress
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)
    
    print(f"✓ Updated progress file")
    print(f"  Before: {old_count} processed URLs")
    print(f"  After: {new_count} processed URLs")
    print(f"  Added: {new_count - old_count} URLs from database")
    print(f"\nProgress file synced: {progress_file}")

if __name__ == "__main__":
    sync_progress()









