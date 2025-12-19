# Template-Based Extraction System - Usage Guide

## Overview

The template-based extraction system allows you to extract specifications from product pages using component-type-specific templates. Each component type (valve, resistor, capacitor, etc.) has its own specialized extraction template.

## Quick Start

### 1. Setup Database

```bash
# Set your database connection string
export DATABASE_URL='postgresql://user:password@localhost/valve_specs'

# Run setup script
python extraction/setup_templates.py
```

This will:

- Create the template database tables
- Load example templates (Gate Valve, Ball Valve, Resistor)
- Verify the setup

### 2. Basic Usage

```python
from extraction.template_based_extractor import TemplateBasedExtractor
import os

# Initialize extractor
db_conn_string = os.getenv("DATABASE_URL")
ai_api_key = os.getenv("OPENAI_API_KEY")  # Optional, for AI template generation

extractor = TemplateBasedExtractor(db_conn_string, ai_api_key)

# Extract from URL
result = extractor.extract_from_url(
    "https://valveman.com/products/1-2-SVF-Flow-Control-500F-Gate-Valve",
    component_type_hint="Gate Valve"  # Optional hint
)

print(result)
```

### 3. Result Structure

```python
{
    'success': True,
    'template_id': 'gate_valve_v1',
    'match_score': 0.95,
    'extracted_specs': {
        'valveType': 'Gate Valve',
        'size': '1/2',
        'pressureRating': {'value': 1975, 'unit': 'psi'},
        'bodyMaterial': 'Carbon Steel',
        'endConnection': 'Socket Welded'
    },
    'missing_required_fields': [],
    'extraction_time_ms': 45
}
```

## How It Works

### Template Matching Process

1. **Fetch Page**: Downloads HTML from product page
2. **Extract Indicators**: Analyzes page title, URL, HTML structure
3. **Match Templates**: Compares indicators against existing templates
4. **Extract Specs**: Uses matched template's extraction rules
5. **Validate**: Checks if all required fields were extracted

### When No Template Matches

If no template matches (score < 0.7):

1. **AI Agent Called**: Analyzes the page structure
2. **Template Generated**: Creates new template with:
   - Component type identification
   - Spec field definitions
   - Extraction rules
   - Page patterns for future matching
3. **Template Stored**: Saved to database for future use
4. **Extraction Retried**: Uses new template to extract specs

## Template Structure

Each template defines:

```json
{
  "templateId": "gate_valve_v1",
  "componentType": "Gate Valve",
  "category": "valve",
  "pagePatterns": {
    "titleKeywords": ["gate valve"],
    "urlPatterns": ["/gate-valve"],
    "htmlMarkers": ["Technical Specifications"]
  },
  "specFields": [
    {
      "name": "valveType",
      "required": true,
      "extractionRules": [
        {
          "type": "regex",
          "pattern": "Item[:\\s]+([^\\n]+)"
        }
      ],
      "normalization": {
        "type": "enum",
        "values": ["Gate Valve", "Ball Valve"]
      }
    }
  ],
  "validation": {
    "requiredFields": ["valveType", "size", "pressureRating"]
  }
}
```

## Managing Templates

### List All Templates

```python
from extraction.template_manager import TemplateManager

tm = TemplateManager(db_conn_string)
templates = tm.list_templates()

for template in templates:
    print(f"{template['template_id']}: {template['component_type']}")
    print(f"  Usage: {template['usage_count']} times")
    print(f"  Success rate: {template['success_rate']:.2%}")
```

### Get Template Statistics

```python
stats = tm.get_template_statistics("gate_valve_v1")
print(f"Successful extractions: {stats['successful_extractions']}")
print(f"Failed extractions: {stats['failed_extractions']}")
print(f"Average extraction time: {stats['avg_extraction_time_ms']}ms")
```

### Create Custom Template

```python
custom_template = {
    "templateId": "custom_valve_v1",
    "componentType": "Custom Valve",
    "category": "valve",
    "version": "1.0",
    "pagePatterns": {
        "titleKeywords": ["custom valve"],
        "urlPatterns": ["/custom"],
        "htmlMarkers": []
    },
    "specFields": [
        {
            "name": "valveType",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Type[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {"type": "string"}
        }
    ],
    "validation": {
        "requiredFields": ["valveType"]
    }
}

tm.create_template(
    template_id="custom_valve_v1",
    component_type="Custom Valve",
    category="valve",
    template_data=custom_template,
    created_by="manual"
)
```

## Extraction Rules

### Regex Rule

```json
{
  "type": "regex",
  "pattern": "Size[:\\s]+([^\\n]+)",
  "fallback": "extract_from_table"
}
```

### CSS Selector Rule

```json
{
  "type": "css_selector",
  "selector": ".product-specs .size",
  "attribute": "text"
}
```

### Table Lookup Rule

```json
{
  "type": "table_lookup",
  "tableSelector": "table.specs",
  "keyColumn": 0,
  "valueColumn": 1,
  "keyText": "Size"
}
```

## Normalization Types

### Enum Normalization

```json
{
  "type": "enum",
  "values": ["Gate Valve", "Ball Valve", "Butterfly Valve"]
}
```

### Size Normalization

```json
{
  "type": "size",
  "format": "fractional_inches"
}
```

### Pressure Normalization

```json
{
  "type": "pressure",
  "unit": "psi"
}
```

### Temperature Normalization

```json
{
  "type": "temperature"
}
```

## AI Template Generation

To enable AI template generation:

1. Set `OPENAI_API_KEY` environment variable
2. Pass API key to `TemplateBasedExtractor`

```python
extractor = TemplateBasedExtractor(
    db_conn_string,
    ai_api_key=os.getenv("OPENAI_API_KEY"),
    ai_model="gpt-4"
)
```

When a page doesn't match any template, the AI agent will:

- Analyze the HTML structure
- Identify component type
- Determine spec fields
- Generate extraction rules
- Create complete template

## Best Practices

1. **Start with Example Templates**: Use the provided example templates as starting points
2. **Test Templates**: Test templates on multiple pages before marking as production-ready
3. **Monitor Success Rates**: Check template statistics regularly
4. **Refine Templates**: Update templates based on extraction results
5. **Use AI for New Types**: Let AI generate templates for new component types
6. **Version Templates**: Use version numbers to track template changes

## Troubleshooting

### No Template Matches

- Check if component type is in database
- Verify page patterns in template
- Consider lowering match threshold (currently 0.7)
- Use `component_type_hint` parameter

### Low Extraction Success Rate

- Review extraction rules
- Check if HTML structure changed
- Update template with better rules
- Add more extraction rule fallbacks

### AI Template Generation Fails

- Verify API key is set correctly
- Check API quota/limits
- Review HTML content quality
- Try different AI model

## Next Steps

1. **Expand Templates**: Add more component types (capacitors, actuators, etc.)
2. **Improve Matching**: Enhance template matching algorithm
3. **Template Versioning**: Implement template version management
4. **Performance**: Optimize extraction speed
5. **Monitoring**: Add dashboard for template performance

