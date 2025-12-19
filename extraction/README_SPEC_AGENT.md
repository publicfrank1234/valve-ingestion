# Spec Extraction Agent

A simple agent that extracts specifications from product pages and provides location information.

## Quick Start

```bash
python extraction/spec_agent.py <url>
```

Example:

```bash
python extraction/spec_agent.py https://valveman.com/products/1-1-2-milwaukee-valve-509
```

## Output Format

The agent returns JSON with:

1. **Extracted Specs**: The actual specification values
2. **Spec Locations**: Where each spec was found (CSS selectors, XPath, etc.)
3. **Extraction Methods**: How each spec was extracted (table, regex, etc.)
4. **Recommendations**: Guidance for other agents on where to find information

## Example Output

```json
{
  "success": true,
  "url": "https://valveman.com/products/1-1-2-milwaukee-valve-509",
  "page_title": "1-1/4\" Milwaukee Valve 509 - Bronze, Horizontal Swing Check Valve",
  "spec_section_found": true,
  "specs": {
    "valveType": "Swing Check Valve",
    "size": "1-1/4\"",
    "bodyMaterial": "Bronze",
    "pressureRating": "125 SWP / 200 WOG",
    "endConnection": "Threaded Ends",
    "conformsTo": "MSS SP-80. Type 3, Type 4"
  },
  "spec_locations": {
    "valveType": {
      "type": "table",
      "row_index": 0,
      "key_cell": {
        "css_selector": "td",
        "xpath": "/table[1]/tr[1]/td[1]",
        "tag": "td"
      },
      "value_cell": {
        "css_selector": "td",
        "xpath": "/table[1]/tr[1]/td[2]",
        "tag": "td"
      }
    }
  },
  "extraction_methods": {
    "valveType": "table_extraction",
    "size": "table_extraction",
    "bodyMaterial": "table_extraction"
  },
  "recommendations": [
    "Technical Specifications section found. Use table extraction for best results.",
    "Found 1 table(s). Table-based extraction recommended."
  ]
}
```

## Usage as Python Module

```python
from extraction.spec_agent import SpecExtractionAgent

agent = SpecExtractionAgent()
result = agent.extract_from_url("https://valveman.com/products/...")

# Access extracted specs
specs = result['specs']
print(specs['valveType'])  # "Swing Check Valve"

# Access location information
locations = result['spec_locations']
print(locations['valveType']['css_selector'])  # Where to find it

# Access extraction methods
methods = result['extraction_methods']
print(methods['valveType'])  # "table_extraction"
```

## Use Cases

1. **Template Creation**: Use location info to create extraction templates
2. **Agent Guidance**: Tell other agents where to find specific specs
3. **Debugging**: Understand why extraction succeeded/failed
4. **Template Validation**: Verify template extraction rules

## Location Information

Each spec includes location information showing:

- **CSS Selector**: How to select the element with CSS
- **XPath**: XPath to the element
- **Tag/Classes/ID**: Element attributes
- **Row/Column Index**: For table-based extraction

This helps other agents or tools know exactly where to find each spec field.

