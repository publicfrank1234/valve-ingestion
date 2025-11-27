#!/bin/bash
# Setup script for valve-spec-ingestion

echo "Setting up Valve Spec Ingestion System..."
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check for .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "Please copy .env.example to .env and fill in your database credentials:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env with your Supabase/PostgreSQL credentials"
    exit 1
fi

# Load environment variables
export $(cat .env | grep -v '^#' | xargs)

# Setup database schema
echo ""
echo "Setting up database schema..."
python database/setup.py

echo ""
echo "✓ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Extract product URLs: python extraction/sitemap_extractor.py"
echo "  2. Start crawling: python extraction/batch_processor.py product_urls.json"
echo "  3. Or use: ./scripts/start_crawl.sh"

