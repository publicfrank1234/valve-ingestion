# Compatibility Mapping Guide

## Purpose

This guide helps ensure we don't miss any value variations when searching. We need to map all possible input variations to the actual database values.

## How to Use This Guide

1. **Run the SQL analysis**: Execute `analyze_distinct_values.sql` in your database
2. **Review distinct values**: For each column, review all distinct values
3. **Group similar values**: Identify variations that should map to the same value
4. **Update compatibility mappings**: Add mappings to `search_specs.py`

## Current Compatibility Mappings

### Material Compatibility

Currently in `search_specs.py`:
```python
MATERIAL_COMPATIBILITY = {
    'carbon steel': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS'],
    'cs': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS'],
    'forged steel': ['Forged Steel', 'Forged Carbon Steel', 'Carbon Steel'],
    'stainless steel': ['Stainless Steel', 'SS', '316SS', '304SS'],
    'ss': ['Stainless Steel', 'SS', '316SS', '304SS'],
}
```

**What to check:**
- Are there other abbreviations? (e.g., "C.S.", "S.S.", "316", "304")
- Are there other variations? (e.g., "Carbon Steel ASTM", "Stainless Steel 316")
- Are there other materials? (e.g., Brass, Bronze, Cast Iron, Ductile Iron)

### Valve Type Compatibility

**Current approach**: Uses prefix match (`ILIKE 'Gate Valve%'`)

**What to check:**
- Abbreviations: "GT" → "Gate Valve", "GL" → "Globe Valve", "BV" → "Ball Valve"
- Variations: "Gate" vs "Gate Valve", "Ball" vs "Ball Valve"
- Compound types: "2-Way Normally Closed" vs "2-Way NC" vs "2WNC"

### End Connection Compatibility

**Current approach**: Exact match on inlet or outlet

**What to check:**
- Socket-weld variations: "Socket-weld", "SW", "SWE", "Socket Weld", "Socket-Weld"
- Threaded variations: "Threaded", "NPT", "Thread", "Screwed", "THR"
- Flanged variations: "Flanged", "FLG", "Flange", "RF" (Raised Face), "FF" (Flat Face)
- Butt-weld variations: "Butt-weld", "BWE", "Butt Weld", "BW"
- Other: "Grooved", "Compression", "Barbed", etc.

### Pressure Class Compatibility

**Current approach**: Exact match with NULL handling

**What to check:**
- Format variations: "800" vs "Class 800" vs "800#"
- Equivalent classes: "150" vs "PN16", "300" vs "PN50"
- Range handling: Should "800" match "800" and "900"?

### Size Compatibility

**Current approach**: Exact match

**What to check:**
- Fraction variations: "1/2" vs "0.5" vs "½"
- Mixed formats: "1-1/2" vs "1.5" vs "1 1/2"
- Unit variations: "1/2" vs "1/2\"" vs "1/2 inch"
- Metric conversions: "15mm" vs "1/2" (if applicable)

## Recommended Process

1. **Run SQL analysis** to get all distinct values
2. **For each column**, create a mapping table:
   ```
   Input Variation → [Database Values]
   ```
3. **Test mappings** with sample searches
4. **Update `search_specs.py`** with comprehensive mappings
5. **Document** any edge cases or special handling needed

## Example: Comprehensive Material Mapping

```python
MATERIAL_COMPATIBILITY = {
    # Carbon Steel variations
    'carbon steel': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.', 'Carbon Steel ASTM'],
    'cs': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.'],
    'c.s.': ['Carbon Steel', 'Forged Steel', 'Forged Carbon Steel', 'CS', 'C.S.'],
    'forged steel': ['Forged Steel', 'Forged Carbon Steel', 'Carbon Steel'],
    'forged carbon steel': ['Forged Carbon Steel', 'Forged Steel', 'Carbon Steel'],
    
    # Stainless Steel variations
    'stainless steel': ['Stainless Steel', 'SS', 'S.S.', '316SS', '304SS', '316 Stainless Steel', '304 Stainless Steel'],
    'ss': ['Stainless Steel', 'SS', 'S.S.', '316SS', '304SS'],
    's.s.': ['Stainless Steel', 'SS', 'S.S.', '316SS', '304SS'],
    '316': ['316 Stainless Steel', '316SS', 'Stainless Steel'],
    '304': ['304 Stainless Steel', '304SS', 'Stainless Steel'],
    '316ss': ['316 Stainless Steel', '316SS', 'Stainless Steel'],
    '304ss': ['304 Stainless Steel', '304SS', 'Stainless Steel'],
    
    # Add other materials as found in database
    # 'brass': ['Brass', 'BR'],
    # 'bronze': ['Bronze', 'BRZ'],
    # etc.
}
```

## Next Steps

1. Execute `analyze_distinct_values.sql` in your database
2. Review the output for each column
3. Create comprehensive compatibility mappings
4. Update `search_specs.py` with the mappings
5. Test with various input variations






