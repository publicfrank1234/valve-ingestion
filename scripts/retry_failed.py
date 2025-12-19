#!/usr/bin/env python3
"""
Retry all failed URLs from extraction_progress.json
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import config
from extraction.batch_processor import batch_process

def retry_failed():
    """Retry all failed URLs."""
    
    progress_file = config.PROGRESS_FILE
    
    if not os.path.exists(progress_file):
        print("No progress file found. Nothing to retry.")
        return
    
    # Load progress
    with open(progress_file, 'r') as f:
        progress = json.load(f)
    
    failed_urls = progress.get('failed', [])
    
    if not failed_urls:
        print("No failed URLs to retry!")
        return
    
    print(f"\n{'='*80}")
    print(f"Retrying Failed URLs")
    print(f"{'='*80}")
    print(f"Found {len(failed_urls)} failed URLs to retry")
    print(f"{'='*80}\n")
    
    # Clear failed list (they'll be added back if they fail again)
    progress['failed'] = []
    
    # Save updated progress
    with open(progress_file, 'w') as f:
        json.dump(progress, f, indent=2)
    
    # Process just the failed URLs
    batch_process(failed_urls, start_index=0)

if __name__ == "__main__":
    retry_failed()









