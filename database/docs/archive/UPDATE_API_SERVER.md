# Update Existing API Server

## What We Did

Integrated the new JSONB search into your existing `database_api.py` server.

## Changes Made

1. **Added JSONB search import** - Tries to load new search functions
2. **Updated `/search/normalized` endpoint** - Tries JSONB search first, falls back to old search
3. **Backward compatible** - Old search still works if JSONB search fails

## How It Works

**Request comes in:**
```json
{
  "normalizedSpecs": {
    "size": "6",
    "valveType": "Butterfly Valve",
    "seatMaterial": "EPDM"
  }
}
```

**API tries:**
1. ✅ JSONB search (new component-system tables) - if available
2. ⬇️ Falls back to old search (valve_specs table) - if JSONB fails or no results

**Response format is the same** - n8n workflow doesn't need changes!

## Restart the Server

**Yes, you need to restart** after adding the new code:

```bash
# Stop the current server (Ctrl+C if running in terminal)

# Restart it
cd valve-spec-ingestion/database
python3 database_api.py
```

Or if using a process manager:
```bash
# Restart the service
systemctl restart database-api
# or
pm2 restart database-api
```

## Testing

### Test 1: Check if JSONB search loads
When you start the server, you should see:
```
✅ JSONB search and synonym normalizer loaded
```

If you see:
```
⚠️ JSONB search not available: ...
```
That's OK - it will use old search only.

### Test 2: Test the endpoint
```bash
curl -X POST http://localhost:16000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "size": "6",
      "valveType": "Butterfly Valve",
      "seatMaterial": "EPDM"
    }
  }'
```

**Check response:**
- `"searchStrategy": "tiered_jsonb"` = Using new JSONB search ✅
- `"searchStrategy": "valve_specs_table"` = Using old search (fallback)

## Configuration

### Force JSONB Search Only
```json
{
  "normalizedSpecs": {...},
  "useJsonb": true  // Default: true
}
```

### Force Old Search Only
```json
{
  "normalizedSpecs": {...},
  "useJsonb": false  // Skip JSONB, use old search
}
```

## What Happens

### Scenario 1: JSONB Search Available
1. Normalizes synonyms (SS → stainless_steel)
2. Searches component-system tables (tech_specs JSONB)
3. Returns results with `searchStrategy: "tiered_jsonb"`

### Scenario 2: JSONB Search Not Available
1. Falls back to old search (valve_specs table)
2. Returns results with `searchStrategy: "valve_specs_table"`

### Scenario 3: JSONB Search Returns No Results
1. Tries JSONB search first
2. If no results, tries old search
3. Returns whichever has results

## No n8n Changes Needed!

The response format is the same:
```json
{
  "success": true,
  "matches": [...],
  "bestMatch": {...},
  "count": 5
}
```

Your n8n workflow will work as-is!

## Troubleshooting

### Import Error
**Problem:** `ModuleNotFoundError: No module named 'jsonb_search'`

**Solution:**
1. Check if `component-system/database/synonym_normalizer.py` exists
2. Check if `component-system/api/jsonb_search.py` exists
3. Server will fall back to old search (this is OK)

### No Results from JSONB Search
**Problem:** JSONB search returns empty results

**Possible causes:**
1. No products in component-system tables yet
2. Field names don't match

**Solution:**
- API automatically falls back to old search
- Check `searchStrategy` in response to see which was used

## Summary

✅ **Integrated** - New code added to existing API
✅ **Backward compatible** - Old search still works
✅ **Auto-fallback** - Uses best available search
✅ **No n8n changes** - Response format is same
✅ **Restart needed** - Yes, restart server after code changes

