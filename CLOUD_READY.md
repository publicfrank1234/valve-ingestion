# Cloud Deployment Checklist ✅

## Status: READY FOR CLOUD DEPLOYMENT

All systems are ready for deployment to a cloud instance.

## What's Included

✅ **Complete ingestion system** - All files organized in `valve-spec-ingestion/` folder
✅ **Database schema** - PostgreSQL/Supabase ready
✅ **Progress tracking** - Resume capability via `extraction_progress.json`
✅ **Error handling** - Failed URLs logged (non-valve products skipped)
✅ **Configuration** - Easy to adjust via `config.py`

## Pre-Deployment Checklist

### 1. Files to Commit to Git

```bash
cd valve-spec-ingestion

# Make sure these are committed:
git add README.md
git add DEPLOYMENT.md
git add config.py
git add requirements.txt
git add setup.sh
git add .gitignore
git add extraction/
git add database/
git add scripts/
git add docs/

# Commit progress file (if you want to resume from current state)
# First, edit .gitignore to allow extraction_progress.json:
# Comment out: # extraction_progress.json
git add extraction_progress.json  # Optional - only if you want to resume from current progress
git add product_urls.json         # Optional - the 27k URLs

git commit -m "Initial valve spec ingestion system"
git push
```

### 2. Environment Setup on Cloud

```bash
# On cloud instance:
git clone <your-repo-url> valve-spec-ingestion
cd valve-spec-ingestion

# Run setup
chmod +x setup.sh
./setup.sh

# Configure database
cp .env.example .env
nano .env  # Add your Supabase credentials
```

### 3. Database Credentials

Make sure your `.env` file has:
```bash
DB_HOST=db.your-project.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_SSLMODE=require
```

### 4. Start Crawling

```bash
# If you have product_urls.json, use it:
python extraction/batch_processor.py product_urls.json --yes

# Or extract URLs first:
python extraction/sitemap_extractor.py
python extraction/batch_processor.py product_urls.json --yes
```

## Current Configuration

- **Retry Failed URLs**: `False` (non-valve products will be skipped)
- **Batch Size**: 10 URLs per batch
- **Rate Limiting**: 1 second between requests
- **Progress File**: `extraction_progress.json` (committed to git for resume)

## What Happens on Cloud

1. **Loads progress file** from git (if committed)
2. **Skips already processed URLs** (from progress file)
3. **Skips failed URLs** (non-valve products like gauges, transmitters)
4. **Continues from last index** or finds first unprocessed URL
5. **Saves progress** every 10 URLs
6. **Can resume** if interrupted

## Monitoring Commands

```bash
# Check progress
python scripts/check_progress.py

# Check database count
python database/query.py count

# View recent entries
python database/query.py 10

# View logs (if running in background)
tail -f crawl.log
```

## Estimated Runtime

- **27,152 URLs** total
- **~1,200 already processed** (if you commit progress file)
- **~25,952 remaining**
- **~22 hours** at 0.33 URLs/sec

## Notes

- Failed URLs are **not retried** by default (many are non-valve products)
- Progress is saved every 10 URLs (can resume anytime)
- All specs are stored in Supabase database
- Progress file can be committed to git for cross-machine resume

## Ready to Deploy! 🚀






