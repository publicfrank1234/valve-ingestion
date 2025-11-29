# Compatibility Mapping Explanation

## How It Works

### The Problem

- **User Input**: Abbreviations like "GT", "CS", "SW" (what users type)
- **Database Values**: Full names like "Gate Valve", "Carbon Steel", "Socket-weld" (what's actually stored)
- **Challenge**: We need to match user abbreviations to database values

### The Solution: Compatibility Mappings

#### Structure

```python
COMPATIBILITY_MAPPING = {
    # KEY (abbreviation) → VALUE (list of what's in database)
    'gt': ['Gate Valve'],  # KEY: abbreviation, VALUE: actual database values
    'cs': ['Carbon Steel', 'Forged Steel', 'CS'],  # Multiple database variations
    'sw': ['Socket Welded', 'Socket-Weld', 'SW', 'SWE'],  # All variations
}
```

#### Search Process

1. **User Input**: "GT" (abbreviation)
2. **Normalize**: Convert to lowercase → "gt"
3. **Lookup KEY**: Find "gt" in mapping
4. **Get VALUES**: Retrieve `['Gate Valve']` (what's actually in database)
5. **Build Query**: Use VALUES in IN clause:
   ```sql
   WHERE valve_type IN ('Gate Valve')
   ```
6. **Result**: Matches database records with `valve_type = 'Gate Valve'`

### Why This Works

- **Keys (abbreviations)**: What users might type → "GT", "CS", "SW"
- **Values (database content)**: What's actually stored → "Gate Valve", "Carbon Steel", "Socket-weld"
- **IN Clause**: We search using VALUES (database content), not KEYS (abbreviations)

### Example Flow

```
User types: "GT" (abbreviation)
    ↓
Lookup: COMPATIBILITY['gt'] → ['Gate Valve']
    ↓
SQL Query: valve_type IN ('Gate Valve')
    ↓
Database Search: Finds records where valve_type = 'Gate Valve'
    ↓
Result: Matches found!
```

### Multiple Variations

For materials with multiple database variations:

```python
'cs': ['Carbon Steel', 'Forged Steel', 'CS', 'C.S.']
```

When user types "CS":

- Lookup returns: `['Carbon Steel', 'Forged Steel', 'CS', 'C.S.']`
- SQL Query: `body_material IN ('Carbon Steel', 'Forged Steel', 'CS', 'C.S.')`
- Matches: Any record with any of these values

### Case-Insensitive

All lookups are case-insensitive:

- "GT" → "gt" → lookup
- "gt" → "gt" → lookup
- "Gt" → "gt" → lookup

All three work the same way!

## Current Implementation

### Python (`search_specs.py`)

✅ **Uses compatibility mappings correctly**

- Looks up abbreviations in mapping
- Uses VALUES in IN clause
- Falls back to ILIKE if no mapping found

### n8n Workflow (Current Issue)

❌ **NOT using compatibility mappings**

- Queries Supabase directly with ILIKE
- Doesn't use IN clause with multiple values
- May miss matches for variations

### Solution

We need to either:

1. Call Python API endpoint (uses compatibility mappings)
2. Implement compatibility logic in n8n Code node
3. Have Agent 1 expand all abbreviations before search
