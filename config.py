"""
Configuration settings for valve specification ingestion.
"""

import os

# Batch processing settings
BATCH_SIZE = 10  # Process in batches of N URLs
DELAY_BETWEEN_REQUESTS = 1  # Seconds to wait between requests (be respectful)
DELAY_BETWEEN_BATCHES = 5  # Seconds to wait between batches

# Retry settings
RETRY_FAILED_URLS = False  # Set to True to retry previously failed URLs (many failures are non-valve products)

# File paths
PROGRESS_FILE = 'extraction_progress.json'
ERROR_LOG_FILE = 'extraction_errors.json'
PRODUCT_URLS_FILE = 'product_urls.json'

# Database settings (can be overridden by environment variables)
DB_CONFIG = {
    'host': os.getenv('DB_HOST', ''),
    'port': os.getenv('DB_PORT', '5432'),
    'database': os.getenv('DB_NAME', 'postgres'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', ''),
    'sslmode': os.getenv('DB_SSLMODE', 'require')
}

# Extraction settings
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
REQUEST_TIMEOUT = 10  # Seconds

