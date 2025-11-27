#!/bin/bash
# Start the batch extraction and insertion process

export DB_PASSWORD='valve@123'

echo "Starting batch extraction and insertion..."
echo "This will process all 27,152 product URLs"
echo "Estimated time: ~22 hours (at 0.33 URLs/sec)"
echo ""
echo "The process will:"
echo "  - Extract specs from each product page"
echo "  - Insert into Supabase database"
echo "  - Save progress to extraction_progress.json"
echo "  - Log errors to extraction_errors.json"
echo ""
echo "You can monitor progress with:"
echo "  python database/query_specs.py count"
echo "  cat extraction_progress.json | grep -c processed"
echo ""

# Run in background and log output
cd "$(dirname "$0")/.."
nohup python3 extraction/batch_processor.py product_urls.json --yes > crawl.log 2>&1 &

echo "Process started in background (PID: $!)"
echo "Logs are being written to crawl.log"
echo ""
echo "To check progress:"
echo "  tail -f crawl.log"
echo "  python scripts/check_progress.py"
echo "  python database/query.py count"

