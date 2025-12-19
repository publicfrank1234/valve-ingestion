# How to Restart the API Server

## Quick Answer

**Yes, you need to restart the server** after adding new code.

## Steps

### 1. Stop the Current Server

**If running in terminal:**
- Press `Ctrl+C` to stop

**If running as a service:**
```bash
# Find the process
ps aux | grep database_api.py

# Kill it (replace PID with actual process ID)
kill <PID>
```

**If using systemd:**
```bash
sudo systemctl stop database-api
```

**If using PM2:**
```bash
pm2 stop database-api
```

### 2. Restart the Server

**Option A: Direct Python (for testing)**
```bash
cd valve-spec-ingestion/database
python3 database_api.py
```

**Option B: Using start script**
```bash
cd valve-spec-ingestion/database
./start_api_server.sh
```

**Option C: Background with nohup**
```bash
cd valve-spec-ingestion/database
nohup python3 database_api.py > api.log 2>&1 &
```

**Option D: Using systemd**
```bash
sudo systemctl start database-api
```

**Option E: Using PM2**
```bash
pm2 restart database-api
```

### 3. Verify It's Running

**Check logs for:**
```
✅ JSONB search and synonym normalizer loaded
```

**Or test the endpoint:**
```bash
curl http://localhost:16000/health
```

## What Changed

The server now:
1. ✅ Tries to load JSONB search functions
2. ✅ Uses new search if available
3. ✅ Falls back to old search if JSONB fails
4. ✅ Returns same response format (n8n compatible)

## Troubleshooting

### Server won't start
- Check Python version: `python3 --version` (needs 3.7+)
- Check dependencies: `pip3 install flask flask-cors psycopg2-binary`
- Check database connection: Set `DATABASE_URL` or `DB_*` env vars

### JSONB search not loading
- This is OK! Server will use old search
- Check that `component-system/api/jsonb_search.py` exists
- Check that `component-system/database/synonym_normalizer.py` exists

### Port already in use
```bash
# Find what's using the port
lsof -i :16000

# Kill it
kill <PID>
```

## Summary

1. **Stop** current server (Ctrl+C or kill process)
2. **Restart** with `python3 database_api.py` or start script
3. **Verify** it loaded JSONB search (check logs)
4. **Test** with curl or your n8n workflow

That's it! 🚀

