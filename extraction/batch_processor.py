#!/usr/bin/env python3
"""
Batch extract valve specs from all product URLs and insert into database.
Handles errors, shows progress, and can resume from where it left off.
"""

import json
import time
import os
import sys
from datetime import datetime
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from extraction.spec_extractor import (
    fetch_page, extract_specs_section, parse_specs_table, 
    normalize_specs, extract_spec_sheet_link, extract_price_info
)
from datetime import timezone
from database.insert import get_db_connection, insert_spec
import config

# Configuration (from config.py)
BATCH_SIZE = config.BATCH_SIZE
DELAY_BETWEEN_REQUESTS = config.DELAY_BETWEEN_REQUESTS
DELAY_BETWEEN_BATCHES = config.DELAY_BETWEEN_BATCHES
PROGRESS_FILE = config.PROGRESS_FILE
ERROR_LOG_FILE = config.ERROR_LOG_FILE

def load_progress():
    """Load progress from previous run."""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {
        'processed': [],
        'failed': [],
        'last_index': 0,
        'start_time': None,
        'total_urls': 0
    }

# Removed database check - using progress file only for simplicity

def save_progress(progress):
    """Save progress to file."""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def log_error(url, error, error_log):
    """Log error to file."""
    error_log.append({
        'url': url,
        'error': str(error),
        'timestamp': datetime.now().isoformat()
    })
    with open(ERROR_LOG_FILE, 'w') as f:
        json.dump(error_log, f, indent=2)

def batch_process(urls, start_index=0, db_conn=None):
    """Process URLs in batches and insert into database."""
    
    # Load progress
    progress = load_progress()
    error_log = []
    if os.path.exists(ERROR_LOG_FILE):
        with open(ERROR_LOG_FILE, 'r') as f:
            error_log = json.load(f)
    
    # Connect to database
    if db_conn is None:
        db_conn = get_db_connection()
        print("✓ Connected to database")
    
    total = len(urls)
    processed_count = len(progress.get('processed', []))
    failed_count = len(progress.get('failed', []))
    
    # Use progress file as source of truth
    all_processed = set(progress.get('processed', []))
    
    # Start from where we left off
    current_index = progress.get('last_index', start_index)
    
    # If progress file says we're done, check if we should continue
    if current_index >= total:
        # Find first unprocessed URL
        for i, url in enumerate(urls):
            if url not in all_processed:
                current_index = i
                print(f"📍 Found first unprocessed URL at index {i}")
                break
        else:
            # All URLs are processed according to progress file
            print("✓ All URLs have already been processed!")
            return
    
    print(f"\n{'='*80}")
    print(f"Batch Processing Valve Specs")
    print(f"{'='*80}")
    print(f"Total URLs: {total}")
    print(f"Already processed: {processed_count} (from progress file)")
    print(f"Failed: {failed_count}")
    remaining = total - processed_count
    print(f"Remaining: {remaining}")
    print(f"Starting from index: {current_index}")
    if progress.get('start_time'):
        print(f"Resuming from previous run...")
    print(f"{'='*80}\n")
    
    if progress.get('start_time'):
        print(f"Resuming from previous run...\n")
    else:
        progress['start_time'] = datetime.now().isoformat()
        progress['total_urls'] = total
    
    start_time = time.time()
    
    try:
        for i in range(current_index, total):
            url = urls[i]
            
            # Skip if already processed successfully (check both progress file and database)
            if url in all_processed:
                if i % 100 == 0:  # Only print every 100th skip to reduce noise
                    print(f"[{i+1}/{total}] ⏭️  Skipping (already in database): {url[:60]}...")
                continue
            
            # Handle previously failed URLs
            if url in progress['failed']:
                if config.RETRY_FAILED_URLS:
                    print(f"[{i+1}/{total}] 🔄 Retrying (previously failed): {url[:60]}...")
                    # Remove from failed list to retry
                    progress['failed'].remove(url)
                    # Continue processing (don't skip)
                else:
                    # Skip failed URLs
                    if i % 100 == 0:
                        print(f"[{i+1}/{total}] ⚠️  Skipping (previously failed): {url[:60]}...")
                    continue
            
            print(f"\n[{i+1}/{total}] Processing: {url}")
            print(f"{'─'*80}")
            
            try:
                # Extract spec (silent mode for batch processing)
                html = fetch_page(url)
                if not html:
                    raise Exception("Failed to fetch page")
                
                spec_section = extract_specs_section(html)
                if not spec_section:
                    spec_section = html
                
                raw_specs = parse_specs_table(spec_section)
                spec_sheet_url = extract_spec_sheet_link(html)
                price_info = extract_price_info(html)
                
                normalized = normalize_specs(raw_specs)
                normalized['sourceUrl'] = url
                normalized['specSheetUrl'] = spec_sheet_url
                normalized['priceInfo'] = price_info
                normalized['extractedAt'] = datetime.now(timezone.utc).isoformat()
                
                result = normalized
                
                if result and result.get('spec'):
                    # Insert into database
                    spec_id = insert_spec(db_conn, result)
                    
                    if spec_id:
                        progress['processed'].append(url)
                        spec_fields = len([k for k in result.get('spec', {}).keys() if result['spec'][k]])
                        print(f"✓ Success - Inserted (ID: {spec_id}) - {spec_fields} spec fields")
                    else:
                        progress['failed'].append(url)
                        error_msg = "Database insert failed"
                        log_error(url, error_msg, error_log)
                        print(f"✗ Failed - {error_msg}")
                else:
                    progress['failed'].append(url)
                    error_msg = "No specs extracted"
                    log_error(url, error_msg, error_log)
                    print(f"⚠️  No specs extracted")
                
            except Exception as e:
                progress['failed'].append(url)
                log_error(url, e, error_log)
                print(f"✗ Error: {e}")
            
            # Update progress
            progress['last_index'] = i + 1
            save_progress(progress)
            
            # Rate limiting - wait between requests
            if i < total - 1:  # Don't wait after last item
                time.sleep(DELAY_BETWEEN_REQUESTS)
            
            # Batch commit and progress update
            if (i + 1) % BATCH_SIZE == 0:
                db_conn.commit()
                elapsed = time.time() - start_time
                rate = (i + 1 - current_index) / elapsed if elapsed > 0 else 0
                remaining = total - (i + 1)
                eta_seconds = remaining / rate if rate > 0 else 0
                eta_minutes = eta_seconds / 60
                
                print(f"\n{'='*80}")
                print(f"Batch Progress: {i+1}/{total} ({((i+1)/total*100):.1f}%)")
                print(f"Processed: {len(progress['processed'])}")
                print(f"Failed: {len(progress['failed'])}")
                print(f"Rate: {rate:.2f} URLs/sec")
                print(f"ETA: {eta_minutes:.1f} minutes")
                print(f"{'='*80}\n")
                
                # Wait between batches
                time.sleep(DELAY_BETWEEN_BATCHES)
        
        # Final commit
        db_conn.commit()
        
        # Final summary
        elapsed_total = time.time() - start_time
        print(f"\n{'='*80}")
        print(f"Batch Processing Complete!")
        print(f"{'='*80}")
        print(f"Total URLs: {total}")
        print(f"Successfully processed: {len(progress['processed'])}")
        print(f"Failed: {len(progress['failed'])}")
        print(f"Total time: {elapsed_total/60:.1f} minutes")
        print(f"Average rate: {total/elapsed_total:.2f} URLs/sec")
        print(f"{'='*80}\n")
        
    except KeyboardInterrupt:
        print(f"\n\n⚠️  Interrupted by user at index {i+1}")
        print(f"Progress saved. Resume by running the script again.")
        db_conn.commit()
    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        db_conn.rollback()
    finally:
        db_conn.close()

def main():
    """Main function."""
    if len(sys.argv) < 2:
        print("Usage: python batch_extract_and_insert.py <urls_json_file>")
        print("Example: python batch_extract_and_insert.py product_urls.json")
        print("\nIf product_urls.json doesn't exist, extract URLs first:")
        print("  python extraction/sitemap_extractor.py")
        sys.exit(1)
    
    urls_file = sys.argv[1]
    
    # Check if file exists
    if not os.path.exists(urls_file):
        print(f"✗ Error: {urls_file} not found!")
        print(f"\nTo extract product URLs from sitemap, run:")
        print(f"  python extraction/sitemap_extractor.py")
        print(f"\nThis will create {urls_file} with all product URLs.")
        sys.exit(1)
    
    # Load URLs
    print(f"Loading URLs from {urls_file}...")
    with open(urls_file, 'r') as f:
        urls = json.load(f)
    
    print(f"✓ Loaded {len(urls)} URLs\n")
    
    # Ask for confirmation (skip if --yes flag provided)
    skip_confirm = '--yes' in sys.argv or '-y' in sys.argv
    
    if not skip_confirm:
        print(f"This will process {len(urls)} URLs.")
        print(f"Estimated time: ~{len(urls) * (DELAY_BETWEEN_REQUESTS + 2) / 60:.0f} minutes")
        print(f"Rate: ~{1/(DELAY_BETWEEN_REQUESTS + 2):.2f} URLs/sec")
        try:
            response = input("\nContinue? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("Cancelled.")
                sys.exit(0)
        except EOFError:
            # Non-interactive mode, proceed
            print("\nNon-interactive mode, proceeding...")
    
    # Start processing
    batch_process(urls)

if __name__ == "__main__":
    main()

