# Deploy API Server with Redis Support

## Quick Deployment Steps

### 1. Install Dependencies (including Redis)

```bash
cd valve-spec-ingestion/database
./install_dependencies.sh
```

This installs:
- flask, flask-cors, psycopg2-binary, python-dotenv
- **redis** (newly added)

### 2. Start the Server

```bash
./start_api_server.sh start
```

This will:
- Use `nohup` to run in background
- Save PID to `api_server.pid`
- Log to `api_server.log`
- Auto-load `.env` file if present

### 3. Check Status

```bash
./start_api_server.sh status
```

Should show:
- ✅ API server is running
- Health check (should show Redis connected)

### 4. View Logs

```bash
./start_api_server.sh logs
```

Look for:
- `✅ Connected to Redis: redis-14604.c85.us-east-1-2.ec2.cloud.redislabs.com:14604`

### 5. Restart After Code Changes

```bash
./start_api_server.sh restart
```

This stops and starts the server with new code.

## Available Commands

```bash
# Start server
./start_api_server.sh start

# Start (force restart if running)
./start_api_server.sh start --force

# Stop server
./start_api_server.sh stop

# Restart server
./start_api_server.sh restart

# Check status
./start_api_server.sh status

# View logs (follow)
./start_api_server.sh logs
```

## Verify Redis Connection

After starting, test:

```bash
# Health check (should show Redis connected)
curl http://localhost:6000/health

# Expected response:
# {"status": "ok", "redis": "connected"}
```

## Environment Variables

The script automatically loads `.env` file if it exists. You can also set:

```bash
export REDIS_URL=redis://default:NPTICUxXh921HLMvIhNvAXrUY9YyAR9f@redis-14604.c85.us-east-1-2.ec2.cloud.redislabs.com:14604
export PORT=6000
```

## Files Created

- `api_server.log` - Server output and errors
- `api_server.pid` - Process ID (used by script to manage server)

## Troubleshooting

### Server won't start
```bash
# Check logs
tail -50 api_server.log

# Check if port is in use
lsof -i :6000
```

### Redis not connecting
- Check logs for Redis connection errors
- Verify Redis URL is correct
- Script will auto-try SSL (`rediss://`) if `redis://` fails

### Restart after code changes
```bash
./start_api_server.sh restart
```






