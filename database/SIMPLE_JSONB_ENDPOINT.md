# Simple JSONB Search Endpoint

## Overview

A clean, simple endpoint `/search/jsonb` that searches **only** the newly ingested component-system tables using JSONB fields.

## Endpoints

### `/search/normalized` (Original - Unchanged)
- Searches the old `valve_specs` table
- No changes - works exactly as before
- Use this for existing workflows

### `/search/jsonb` (New - Simple)
- Searches **only** the new component-system tables (JSONB format)
- Clean and simple - no complexity
- Use this for new searches with crawled data

## Usage

### Request
```json
POST http://localhost:16000/search/jsonb
{
  "normalizedSpecs": {
    "size": "6",
    "valveType": "Butterfly Valve",
    "material": "Stainless Steel",
    "seatMaterial": "EPDM",
    "pressureRating": "150",
    "endConnection": "Lug"
  },
  "maxResults": 10
}
```

### Response
```json
{
  "success": true,
  "matches": [
    {
      "id": 123,
      "sourceUrl": "https://...",
      "componentType": "Butterfly Valve",
      "item": "Lugged Butterfly Valve",
      "price": 54.99,
      "score": 0.95,
      "tier": 1,
      "techSpecs": {...},
      "metadata": {...}
    }
  ],
  "bestMatch": {...},
  "count": 5
}
```

## Features

- ✅ Synonym normalization (SS → stainless_steel)
- ✅ Tiered relaxation (relaxes constraints if no matches)
- ✅ JSONB search (tech_specs and metadata columns)
- ✅ Simple and clean - no complexity

## Update n8n

Change your n8n workflow to use the new endpoint:

**Old:**
```
POST http://localhost:16000/search/normalized
```

**New:**
```
POST http://localhost:16000/search/jsonb
```

## Testing

```bash
curl -X POST http://localhost:16000/search/jsonb \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "size": "6",
      "valveType": "Butterfly Valve",
      "seatMaterial": "EPDM"
    }
  }'
```

## Summary

- `/search/normalized` - Original endpoint, unchanged
- `/search/jsonb` - New endpoint, simple and clean
- Update n8n to use `/search/jsonb` for new searches

