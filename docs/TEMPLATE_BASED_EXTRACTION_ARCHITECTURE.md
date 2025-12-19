# Template-Based Extraction Architecture

## Overview

This document outlines the new template-based extraction system where each component type (valve, resistor, capacitor, etc.) has its own specialized extraction template. This replaces the unified spec structure with component-specific templates that better capture the unique specifications of each component type.

## Core Concept

### Current System (Unified Spec)

- All components use the same extraction logic
- Same spec fields for all component types
- Limited flexibility for component-specific attributes

### New System (Template-Based)

- Each component type has its own extraction template
- Templates define which specs to extract and how
- AI agent generates new templates when encountering new component types
- Systematic building of template library

## Architecture

### 1. Template Structure

Each template defines:

- **Component Type**: e.g., "Gate Valve", "Ball Valve", "Resistor", "Capacitor"
- **Template Name**: Unique identifier for the template
- **Spec Fields**: List of expected spec fields for this component type
- **Extraction Rules**: How to extract each field from HTML
- **Page Patterns**: HTML patterns that identify this component type
- **Validation Rules**: How to validate extracted data

```json
{
  "templateId": "gate_valve_v1",
  "componentType": "Gate Valve",
  "category": "valve",
  "version": "1.0",
  "createdAt": "2024-01-15T10:00:00Z",
  "createdBy": "ai_agent",
  "pagePatterns": {
    "titleKeywords": ["gate valve", "gate"],
    "urlPatterns": ["/gate-valve", "/gate"],
    "htmlMarkers": ["<h1>Gate Valve", "Technical Specifications"]
  },
  "specFields": [
    {
      "name": "valveType",
      "required": true,
      "extractionRules": [
        {
          "type": "regex",
          "pattern": "Item[:\\s]+([^\\n]+)",
          "fallback": "extract_from_title"
        }
      ],
      "normalization": {
        "type": "enum",
        "values": ["Gate Valve", "Ball Valve", "Butterfly Valve"]
      }
    },
    {
      "name": "size",
      "required": true,
      "extractionRules": [
        {
          "type": "regex",
          "pattern": "Size[:\\s]+([^\\n]+)",
          "fallback": "extract_from_table"
        }
      ],
      "normalization": {
        "type": "size",
        "format": "fractional_inches"
      }
    },
    {
      "name": "pressureRating",
      "required": true,
      "extractionRules": [
        {
          "type": "regex",
          "pattern": "Maximum\\s+Pressure[:\\s]+([^\\n]+)",
          "fallback": "extract_from_table"
        }
      ],
      "normalization": {
        "type": "pressure",
        "unit": "psi"
      }
    }
  ],
  "validation": {
    "requiredFields": ["valveType", "size", "pressureRating"],
    "fieldDependencies": {
      "pressureRating": ["pressureUnit"]
    }
  }
}
```

### 2. Template Matching System

When crawling a new product page:

1. **Fetch Page HTML**
2. **Extract Component Type Indicators**:
   - Page title
   - URL patterns
   - HTML structure markers
   - Product category tags
3. **Match Against Existing Templates**:
   - Compare indicators with template `pagePatterns`
   - Score each template match (0-1)
   - Select best matching template (score > 0.7)
4. **If Match Found**:
   - Use template to extract specs
   - Validate extracted data against template rules
5. **If No Match Found**:
   - Call AI agent to analyze page
   - Generate new template
   - Store template in database
   - Use new template to extract specs

### 3. AI Agent for Template Generation

When no template matches:

**Input to AI Agent:**

- Full HTML of product page
- Page URL
- Page title
- Any detected component type hints

**AI Agent Tasks:**

1. Identify component type and category
2. Analyze HTML structure to find spec fields
3. Determine extraction rules for each field
4. Identify page patterns for future matching
5. Generate template JSON structure

**Output:**

- Complete template JSON
- Confidence score (0-1)
- Extracted sample data for validation

### 4. Template Storage

**Database Schema:**

```sql
CREATE TABLE extraction_templates (
    id SERIAL PRIMARY KEY,
    template_id TEXT UNIQUE NOT NULL,
    component_type TEXT NOT NULL,
    category TEXT NOT NULL,  -- 'valve', 'resistor', 'capacitor', etc.
    version TEXT NOT NULL,
    template_data JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by TEXT,  -- 'ai_agent', 'manual', 'user_id'
    usage_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5, 4),  -- 0.0000 to 1.0000
    last_used_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT true
);

CREATE INDEX idx_templates_component_type ON extraction_templates(component_type);
CREATE INDEX idx_templates_category ON extraction_templates(category);
CREATE INDEX idx_templates_active ON extraction_templates(is_active);
CREATE INDEX idx_templates_jsonb ON extraction_templates USING GIN(template_data);
```

### 5. Extraction Workflow

```
┌─────────────────┐
│  New Product    │
│     Page        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Fetch HTML     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Type    │
│ Indicators      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐      Yes      ┌──────────────┐
│ Template Match? ├──────────────►│ Use Template │
└────────┬────────┘               └──────┬───────┘
         │ No                              │
         ▼                                 ▼
┌─────────────────┐               ┌──────────────┐
│ Call AI Agent   │               │ Extract Specs│
│ to Generate     │               │ Using Rules  │
│ New Template    │               └──────┬───────┘
└────────┬────────┘                      │
         │                                ▼
         ▼                        ┌──────────────┐
┌─────────────────┐               │ Validate     │
│ Store Template  │               │ Extracted    │
│ in Database     │               │ Data        │
└────────┬────────┘               └──────┬───────┘
         │                                │
         └────────────┬───────────────────┘
                      ▼
              ┌──────────────┐
              │ Store Result │
              └──────────────┘
```

## Implementation Plan

### Phase 1: Database & Template Storage

1. Create `extraction_templates` table
2. Create template management functions
3. Migrate existing valve extraction logic to template format

### Phase 2: Template Matching

1. Build template matching algorithm
2. Implement page pattern detection
3. Create template scoring system

### Phase 3: AI Agent Integration

1. Design AI agent prompt for template generation
2. Integrate with LLM API (OpenAI, Anthropic, etc.)
3. Implement template validation and refinement

### Phase 4: Extraction Engine Update

1. Refactor extraction logic to use templates
2. Implement field extraction using template rules
3. Add validation using template rules

### Phase 5: Template Management

1. Build template review/approval system
2. Add template versioning
3. Implement template performance tracking

## Benefits

1. **Component-Specific Extraction**: Each component type has optimized extraction rules
2. **Systematic Growth**: Templates are built incrementally as new types are encountered
3. **Better Accuracy**: Specialized rules for each component type improve extraction quality
4. **Maintainability**: Easy to update templates for specific component types
5. **Scalability**: Can handle any component type, not just valves
6. **AI-Assisted**: Automatically generates templates for new component types

## Example: Gate Valve vs Resistor

### Gate Valve Template

```json
{
  "specFields": [
    "valveType",
    "size",
    "pressureRating",
    "temperatureRating",
    "bodyMaterial",
    "endConnection",
    "actuationMethod",
    "standards"
  ]
}
```

### Resistor Template

```json
{
  "specFields": [
    "resistance",
    "tolerance",
    "powerRating",
    "voltageRating",
    "temperatureCoefficient",
    "packageType",
    "mountingType"
  ]
}
```

These are completely different spec fields, which is why component-specific templates are essential.

## Next Steps

1. Review and approve this architecture
2. Implement Phase 1 (Database & Template Storage)
3. Create initial templates for existing component types
4. Test template matching system
5. Integrate AI agent for template generation

