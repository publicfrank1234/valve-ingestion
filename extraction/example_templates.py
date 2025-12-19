#!/usr/bin/env python3
"""
Example templates for different component types.

These templates can be loaded into the database as initial templates.
"""

# Gate Valve Template
GATE_VALVE_TEMPLATE = {
    "templateId": "gate_valve_v1",
    "componentType": "Gate Valve",
    "category": "valve",
    "version": "1.0",
    "pagePatterns": {
        "titleKeywords": ["gate valve", "gate"],
        "urlPatterns": ["/gate-valve", "/gate"],
        "htmlMarkers": ["Gate Valve", "Technical Specifications"]
    },
    "specFields": [
        {
            "name": "valveType",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Item[:\\s]+([^\\n]+)",
                    "fallback": "extract_from_title"
                },
                {
                    "type": "table_lookup",
                    "tableSelector": "table",
                    "keyColumn": 0,
                    "valueColumn": 1,
                    "keyText": "Item"
                }
            ],
            "normalization": {
                "type": "enum",
                "values": ["Gate Valve", "Ball Valve", "Butterfly Valve", "Check Valve", "Globe Valve"]
            }
        },
        {
            "name": "size",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Size[:\\s]+([^\\n]+)",
                    "fallback": "extract_from_table"
                },
                {
                    "type": "table_lookup",
                    "tableSelector": "table",
                    "keyColumn": 0,
                    "valueColumn": 1,
                    "keyText": "Size"
                }
            ],
            "normalization": {
                "type": "size",
                "format": "fractional_inches"
            }
        },
        {
            "name": "pressureRating",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Maximum\\s+Pressure[:\\s]+([^\\n]+)",
                    "fallback": "extract_from_table"
                },
                {
                    "type": "table_lookup",
                    "tableSelector": "table",
                    "keyColumn": 0,
                    "valueColumn": 1,
                    "keyText": "Maximum Pressure"
                }
            ],
            "normalization": {
                "type": "pressure",
                "unit": "psi"
            }
        },
        {
            "name": "temperatureRating",
            "required": False,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Maximum\\s+Temperature[:\\s]+([^\\n]+)",
                    "fallback": "extract_from_table"
                },
                {
                    "type": "table_lookup",
                    "tableSelector": "table",
                    "keyColumn": 0,
                    "valueColumn": 1,
                    "keyText": "Maximum Temperature"
                }
            ],
            "normalization": {
                "type": "temperature"
            }
        },
        {
            "name": "bodyMaterial",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Body\\s+Material[:\\s]+([^\\n]+)",
                    "fallback": "extract_from_table"
                },
                {
                    "type": "table_lookup",
                    "tableSelector": "table",
                    "keyColumn": 0,
                    "valueColumn": 1,
                    "keyText": "Body Material"
                }
            ],
            "normalization": {
                "type": "enum",
                "values": ["Carbon Steel", "Stainless Steel", "Brass", "Bronze", "Cast Iron", "Ductile Iron"]
            }
        },
        {
            "name": "endConnection",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "End\\s+Connection[:\\s]+([^\\n]+)",
                    "fallback": "extract_from_table"
                },
                {
                    "type": "table_lookup",
                    "tableSelector": "table",
                    "keyColumn": 0,
                    "valueColumn": 1,
                    "keyText": "End Connection"
                }
            ],
            "normalization": {
                "type": "enum",
                "values": ["Socket Welded", "Screwed/Threaded", "Flanged", "Butt Welded", "NPT"]
            }
        },
        {
            "name": "actuationMethod",
            "required": False,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Actuation[:\\s]+([^\\n]+)",
                    "fallback": "extract_from_table"
                }
            ],
            "normalization": {
                "type": "enum",
                "values": ["Manual", "Pneumatic", "Electric", "Hydraulic"]
            }
        }
    ],
    "validation": {
        "requiredFields": ["valveType", "size", "pressureRating", "bodyMaterial", "endConnection"]
    }
}

# Ball Valve Template
BALL_VALVE_TEMPLATE = {
    "templateId": "ball_valve_v1",
    "componentType": "Ball Valve",
    "category": "valve",
    "version": "1.0",
    "pagePatterns": {
        "titleKeywords": ["ball valve", "ball"],
        "urlPatterns": ["/ball-valve", "/ball"],
        "htmlMarkers": ["Ball Valve", "Technical Specifications"]
    },
    "specFields": [
        {
            "name": "valveType",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Item[:\\s]+([^\\n]+)",
                    "fallback": "extract_from_title"
                }
            ],
            "normalization": {
                "type": "enum",
                "values": ["Ball Valve", "Gate Valve", "Butterfly Valve"]
            }
        },
        {
            "name": "size",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Size[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {
                "type": "size",
                "format": "fractional_inches"
            }
        },
        {
            "name": "pressureRating",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Maximum\\s+Pressure[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {
                "type": "pressure",
                "unit": "psi"
            }
        },
        {
            "name": "bodyMaterial",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Body\\s+Material[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {
                "type": "enum",
                "values": ["Carbon Steel", "Stainless Steel", "Brass", "Bronze"]
            }
        },
        {
            "name": "endConnection",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "End\\s+Connection[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {
                "type": "enum",
                "values": ["Socket Welded", "Screwed/Threaded", "Flanged", "NPT"]
            }
        }
    ],
    "validation": {
        "requiredFields": ["valveType", "size", "pressureRating", "bodyMaterial", "endConnection"]
    }
}

# Example: Resistor Template (for future expansion)
RESISTOR_TEMPLATE = {
    "templateId": "resistor_v1",
    "componentType": "Resistor",
    "category": "resistor",
    "version": "1.0",
    "pagePatterns": {
        "titleKeywords": ["resistor", "resistance"],
        "urlPatterns": ["/resistor", "/resistance"],
        "htmlMarkers": ["Resistor", "Specifications"]
    },
    "specFields": [
        {
            "name": "resistance",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Resistance[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {
                "type": "resistance",
                "unit": "ohm"
            }
        },
        {
            "name": "tolerance",
            "required": False,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Tolerance[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {
                "type": "percentage"
            }
        },
        {
            "name": "powerRating",
            "required": True,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Power\\s+Rating[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {
                "type": "power",
                "unit": "watt"
            }
        },
        {
            "name": "packageType",
            "required": False,
            "extractionRules": [
                {
                    "type": "regex",
                    "pattern": "Package[:\\s]+([^\\n]+)"
                }
            ],
            "normalization": {
                "type": "enum",
                "values": ["0805", "1206", "2010", "2512", "Through Hole"]
            }
        }
    ],
    "validation": {
        "requiredFields": ["resistance", "powerRating"]
    }
}

# All example templates
EXAMPLE_TEMPLATES = [
    GATE_VALVE_TEMPLATE,
    BALL_VALVE_TEMPLATE,
    RESISTOR_TEMPLATE
]


def load_example_templates(template_manager):
    """
    Load example templates into the database.
    
    Args:
        template_manager: TemplateManager instance
    """
    for template in EXAMPLE_TEMPLATES:
        success = template_manager.create_template(
            template_id=template["templateId"],
            component_type=template["componentType"],
            category=template["category"],
            template_data=template,
            version=template.get("version", "1.0"),
            created_by="manual",
            notes="Example template loaded from example_templates.py"
        )
        if success:
            print(f"✓ Loaded template: {template['templateId']}")
        else:
            print(f"✗ Failed to load template: {template['templateId']}")


if __name__ == "__main__":
    # Example usage
    import os
    from template_manager import TemplateManager
    
    db_conn_string = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/valve_specs")
    tm = TemplateManager(db_conn_string)
    
    load_example_templates(tm)
    print("\n✓ All example templates loaded!")

