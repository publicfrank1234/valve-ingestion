# Deployment Guide

## Deploying to Cloud Instance

### Option 1: AWS EC2 / Google Cloud / Azure VM

1. **SSH into your instance:**
   ```bash
   ssh user@your-instance-ip
   ```

2. **Clone the repository:**
   ```bash
   git clone <your-repo-url> valve-spec-ingestion
   cd valve-spec-ingestion
   ```

3. **Run setup:**
   ```bash
   chmod +x setup.sh
   ./setup.sh
   ```

4. **Configure environment:**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your database credentials
   ```

5. **Start the crawl:**
   ```bash
   # Extract URLs first (if not already done)
   python extraction/sitemap_extractor.py
   
   # Start crawling in background
   ./scripts/start_crawl.sh
   ```

6. **Monitor progress:**
   ```bash
   # Check logs
   tail -f crawl.log
   
   # Check progress
   python scripts/check_progress.py
   ```

### Option 2: Using screen/tmux (Recommended)

Keep the process running even after disconnecting:

```bash
# Install screen
sudo apt-get install screen  # Ubuntu/Debian
# or
brew install screen  # macOS

# Start a screen session
screen -S valve-crawl

# Run the crawl
cd valve-spec-ingestion
source venv/bin/activate
export $(cat .env | grep -v '^#' | xargs)
python extraction/batch_processor.py product_urls.json --yes

# Detach: Press Ctrl+A, then D
# Reattach: screen -r valve-crawl
```

### Option 3: Using systemd (Linux)

Create a service file:

```bash
sudo nano /etc/systemd/system/valve-crawl.service
```

```ini
[Unit]
Description=Valve Spec Ingestion Crawler
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/valve-spec-ingestion
Environment="PATH=/path/to/valve-spec-ingestion/venv/bin"
ExecStart=/path/to/valve-spec-ingestion/venv/bin/python extraction/batch_processor.py product_urls.json --yes
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable valve-crawl
sudo systemctl start valve-crawl
sudo systemctl status valve-crawl
```

## Environment Variables

Set these in your `.env` file or export them:

```bash
DB_HOST=db.your-project.supabase.co
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your-password
DB_SSLMODE=require
```

## Monitoring

### Check if process is running:
```bash
ps aux | grep batch_processor
```

### View logs:
```bash
tail -f crawl.log
```

### Check database:
```bash
python database/query.py count
python database/query.py 10  # Show 10 latest
```

### Check progress:
```bash
python scripts/check_progress.py
```

## Troubleshooting

### Process stopped
- Check logs: `tail -100 crawl.log`
- Check errors: `cat extraction_errors.json`
- Resume: Just run the batch processor again (it auto-resumes)

### Database connection issues
- Verify credentials in `.env`
- Test connection: `python database/setup.py`
- Check Supabase dashboard for connection limits

### Rate limiting
- Adjust `DELAY_BETWEEN_REQUESTS` in `config.py`
- Be respectful of ValveMan.com's servers

## Estimated Runtime

- **27,152 URLs** at 0.33 URLs/sec = **~22 hours**
- Progress is saved, so you can stop/restart anytime
- The system will resume from where it left off






