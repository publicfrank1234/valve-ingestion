# API Server Management Guide

## Quick Start

### Start the server
```bash
cd valve-spec-ingestion/database
./start_api_server.sh start
```

### Check status
```bash
./start_api_server.sh status
```

### Stop the server
```bash
./start_api_server.sh stop
```

### Restart the server
```bash
./start_api_server.sh restart
```

### View logs
```bash
./start_api_server.sh logs
```

## Keep Server Always Running

### Option 1: Keep-Alive Script (Simple)

Run the keep-alive monitor in the background:

```bash
cd valve-spec-ingestion/database
nohup ./keep_alive.sh > keep_alive.log 2>&1 &
```

This will:
- Check every 30 seconds if the server is running
- Automatically restart it if it crashes
- Log activity to `keep_alive.log`

To stop the keep-alive monitor:
```bash
pkill -f keep_alive.sh
```

### Option 2: Systemd Service (Linux - Production)

Create a systemd service file:

```bash
sudo nano /etc/systemd/system/valve-api.service
```

Add this content:

```ini
[Unit]
Description=Valve Spec API Server
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/valve-spec-ingestion/database
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 database_api.py
Restart=always
RestartSec=10
StandardOutput=append:/path/to/valve-spec-ingestion/database/api_server.log
StandardError=append:/path/to/valve-spec-ingestion/database/api_server.log

[Install]
WantedBy=multi-user.target
```

Then:
```bash
sudo systemctl daemon-reload
sudo systemctl enable valve-api
sudo systemctl start valve-api
sudo systemctl status valve-api
```

### Option 3: Launchd (macOS - Production)

Create a launchd plist file:

```bash
nano ~/Library/LaunchAgents/com.valve.api.plist
```

Add this content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.valve.api</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/valve-spec-ingestion/database/database_api.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/valve-spec-ingestion/database</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/path/to/valve-spec-ingestion/database/api_server.log</string>
    <key>StandardErrorPath</key>
    <string>/path/to/valve-spec-ingestion/database/api_server.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/bin:/usr/local/bin</string>
    </dict>
</dict>
</plist>
```

Then:
```bash
launchctl load ~/Library/LaunchAgents/com.valve.api.plist
launchctl start com.valve.api
launchctl list | grep valve
```

### Option 4: Screen/Tmux (Development)

Using screen:
```bash
screen -S valve-api
cd valve-spec-ingestion/database
./start_api_server.sh start
# Press Ctrl+A then D to detach
# Reattach with: screen -r valve-api
```

Using tmux:
```bash
tmux new -s valve-api
cd valve-spec-ingestion/database
./start_api_server.sh start
# Press Ctrl+B then D to detach
# Reattach with: tmux attach -t valve-api
```

## Troubleshooting

### Server won't start
1. Check if port 6000 is already in use:
   ```bash
   lsof -i :6000
   ```
2. Check the log file:
   ```bash
   tail -f api_server.log
   ```
3. Verify .env file exists and has correct credentials:
   ```bash
   cat .env
   ```

### Server keeps crashing
1. Check logs for errors:
   ```bash
   tail -50 api_server.log
   ```
2. Test database connection:
   ```bash
   python3 test_connection.py
   ```
3. Verify Python dependencies:
   ```bash
   pip3 list | grep -E "flask|psycopg2|dotenv"
   ```

### Check if server is responding
```bash
curl http://localhost:6000/health
```

### Test search endpoint
```bash
curl -X POST http://localhost:6000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "Gate Valve",
      "size": "1/2"
    },
    "maxResults": 5
  }'
```

## Files Created

- `api_server.log` - Server output and errors
- `api_server.pid` - Process ID file
- `keep_alive.log` - Keep-alive monitor log (if using keep_alive.sh)

## Environment Variables

The server reads from `.env` file:
- `DB_POOLER_HOST` - Database pooler hostname
- `DB_POOLER_PORT` - Database pooler port (default: 5432)
- `DB_POOLER_USER` - Database user
- `DB_PASSWORD` - Database password
- `PORT` - API server port (default: 6000)






