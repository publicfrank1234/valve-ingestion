# New JSONB Search Endpoint

## Overview

A new dedicated endpoint `/search/jsonb` that searches **only** the newly ingested component-system tables using JSONB fields with **valve-type-specific logic**.

## Why a Separate Endpoint?

1. **Clean separation** - Old search (`/search/normalized`) still works for `valve_specs` table
2. **Valve-type-specific logic** - Each valve type has different critical fields:
   - **Butterfly Valves**: `seat_material` and `end_type` (Wafer/Lug) are critical
   - **Ball Valves**: `port`, `seat_material`, `stem` are important
   - **Gate Valves**: `trim materials`, `end connection` are important
   - **Check Valves**: `flow_direction`, `cracking_pressure` are important
3. **No fallback confusion** - This endpoint ONLY searches JSONB tables, no fallback

## Endpoint

### POST `/search/jsonb`

**Request:**
```json
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

**Response:**
```json
{
  "success": true,
  "searchStrategy": "jsonb_valve_specific",
  "valveType": "Butterfly Valve",
  "matches": [
    {
      "id": 123,
      "sourceUrl": "https://...",
      "componentType": "Butterfly Valve",
      "item": "Lugged Butterfly Valve",
      "price": 54.99,
      "score": 0.95,
      "tier": 1,
      "matchedFields": ["size", "valveType", "seatMaterial", "endConnection"],
      "techSpecs": {...},
      "metadata": {...}
    }
  ],
  "bestMatch": {...},
  "count": 5
}
```

## Valve-Type-Specific Logic

### Butterfly Valves
- **Critical fields**: `seat_material`, `end_type` (Wafer/Lug)
- **Scoring boost**: +0.2 for seat_material match, +0.15 for end_type match
- **Why**: Butterfly valves are highly sensitive to seat material (EPDM for water, Viton for chemicals) and end type affects installation

### Ball Valves
- **Important fields**: `port` (Full Port vs Standard), `seat_material`, `stem`
- **Scoring boost**: +0.1 for port match, +0.1 for seat_material match
- **Why**: Port affects flow capacity, seat material affects chemical compatibility

### Gate Valves
- **Important fields**: `trim materials`, `end connection`
- **Why**: Trim materials affect chemical compatibility, end connection affects installation

### Check Valves
- **Critical fields**: `flow_direction`, `cracking_pressure`
- **Scoring boost**: +0.15 for flow_direction match
- **Why**: Flow direction is critical for check valves, wrong direction = valve won't work

## Usage in n8n

Update your n8n workflow to use the new endpoint:

**Old endpoint** (still works):
```
POST http://localhost:16000/search/normalized
```

**New endpoint** (JSONB only, valve-specific):
```
POST http://localhost:16000/search/jsonb
```

## Error Handling

If JSONB search is not available:
```json
{
  "success": false,
  "error": "JSONB search not available. Make sure component-system tables are set up.",
  "hint": "Check that component-system/api/jsonb_search.py and component-system/database/synonym_normalizer.py exist"
}
```

## Comparison

| Feature | `/search/normalized` | `/search/jsonb` |
|---------|---------------------|-----------------|
| Searches old tables | ✅ Yes (valve_specs) | ❌ No |
| Searches new tables | ✅ Yes (with fallback) | ✅ Yes (only) |
| Valve-specific logic | ❌ No | ✅ Yes |
| Fallback to old search | ✅ Yes | ❌ No |
| Synonym normalization | ✅ Yes | ✅ Yes |
| Tiered relaxation | ✅ Yes | ✅ Yes |

## Testing

```bash
# Test with butterfly valve
curl -X POST http://localhost:16000/search/jsonb \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "size": "6",
      "valveType": "Butterfly Valve",
      "seatMaterial": "EPDM",
      "endConnection": "Lug"
    }
  }'

# Test with ball valve
curl -X POST http://localhost:16000/search/jsonb \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "size": "1",
      "valveType": "Ball Valve",
      "port": "Full Port",
      "seatMaterial": "PTFE"
    }
  }'
```

## Next Steps

1. **Restart the API server** to load the new endpoint
2. **Update n8n workflow** to use `/search/jsonb` for new searches
3. **Test with real data** to verify valve-specific logic works
4. **Tune scoring** based on real-world results

