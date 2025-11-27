# Valve Specification Ingestion System

Automated system to extract valve specifications from ValveMan.com product pages and store them in a PostgreSQL database.

## Overview

This system:
1. Extracts product URLs from ValveMan sitemap
2. Scrapes each product page
3. Extracts technical specifications, prices, and spec sheet links
4. Stores everything in a PostgreSQL database (Supabase)

## Project Structure

```
valve-spec-ingestion/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── config.py                # Configuration settings
│
├── extraction/              # Extraction scripts
│   ├── sitemap_extractor.py
│   ├── spec_extractor.py
│   └── batch_processor.py
│
├── database/                # Database scripts
│   ├── schema.sql
│   ├── setup.py
│   ├── insert.py
│   └── query.py
│
├── scripts/                 # Utility scripts
│   ├── start_crawl.sh
│   └── check_progress.py
│
└── docs/                    # Documentation
    └── INGESTION_PLAN.md
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Database

Create a Supabase project (or use any PostgreSQL database) and set environment variables:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 3. Initialize Database Schema

```bash
python database/setup.py
```

### 4. Extract Product URLs (First Time Only)

```bash
python extraction/sitemap_extractor.py
# This creates product_urls.json
```

### 5. Start Batch Extraction

```bash
# Option 1: Run in foreground
python extraction/batch_processor.py product_urls.json

# Option 2: Run in background
./scripts/start_crawl.sh
```

## Configuration

Edit `config.py` to adjust:
- Batch size
- Rate limiting (delay between requests)
- Database connection settings

## Monitoring

Check progress:
```bash
python scripts/check_progress.py
python database/query.py count
```

View recent entries:
```bash
python database/query.py 10
```

## Database Schema

The database stores:
- Technical specifications (normalized to valve-spec-schema.json format)
- Price information (SKU, starting price, MSRP, savings)
- Specification sheet PDF links
- Source URLs and extraction timestamps

## Files Generated

- `product_urls.json` - All product URLs from sitemap
- `extraction_progress.json` - Progress tracking (allows resume)
- `extraction_errors.json` - Error log
- `crawl.log` - Full extraction log (if running in background)

## Resume After Interruption

The system automatically saves progress. To resume:
```bash
python extraction/batch_processor.py product_urls.json
# It will automatically continue from where it left off
```

## Requirements

- Python 3.8+
- PostgreSQL database (Supabase recommended)
- Internet connection for scraping

## License

MIT

# valve-ingestion
