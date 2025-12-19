#!/usr/bin/env python3
"""
Simple synonym normalization for valve specifications.

Self-contained - no external dependencies.
Maps different ways of expressing the same thing to canonical forms.
Example: "SS", "Stainless Steel", "316SS" → "stainless_steel"
"""

import json
import os
from typing import Dict, Optional, Any


class SynonymNormalizer:
    """Normalize synonyms to canonical forms."""
    
    def __init__(self, knowledge_base_path: Optional[str] = None):
        """Initialize with built-in synonyms."""
        self._load_builtin_synonyms()
        
        # Try to load learned synonyms from knowledge base (optional)
        if knowledge_base_path is None:
            knowledge_base_path = os.path.join(
                os.path.dirname(__file__),
                'knowledge_base.json'
            )
        
        self.field_priorities = {}
        if os.path.exists(knowledge_base_path):
            try:
                with open(knowledge_base_path, 'r') as f:
                    kb = json.load(f)
                    learned_synonyms = kb.get('synonyms', {})
                    self.synonym_map.update(learned_synonyms)
                    self.field_priorities = kb.get('field_priorities', {})
            except Exception as e:
                print(f"Warning: Could not load knowledge_base.json: {e}")
    
    def _load_builtin_synonyms(self):
        """Load built-in synonym mappings (domain knowledge)."""
        self.synonym_map = {
            # Materials
            'stainless steel': {'canonical': 'stainless_steel', 'category': 'material'},
            'stainless': {'canonical': 'stainless_steel', 'category': 'material'},
            'ss': {'canonical': 'stainless_steel', 'category': 'material'},
            's.s.': {'canonical': 'stainless_steel', 'category': 'material'},
            '316ss': {'canonical': 'stainless_steel', 'category': 'material'},
            '304ss': {'canonical': 'stainless_steel', 'category': 'material'},
            '316': {'canonical': 'stainless_steel', 'category': 'material'},
            '304': {'canonical': 'stainless_steel', 'category': 'material'},
            
            'carbon steel': {'canonical': 'carbon_steel', 'category': 'material'},
            'carbon': {'canonical': 'carbon_steel', 'category': 'material'},
            'cs': {'canonical': 'carbon_steel', 'category': 'material'},
            'c.s.': {'canonical': 'carbon_steel', 'category': 'material'},
            
            'brass': {'canonical': 'brass', 'category': 'material'},
            'br': {'canonical': 'brass', 'category': 'material'},
            
            # Seat materials
            'epdm': {'canonical': 'epdm', 'category': 'seat_material'},
            'viton': {'canonical': 'viton', 'category': 'seat_material'},
            'fkm': {'canonical': 'viton', 'category': 'seat_material'},
            'nbr': {'canonical': 'nbr', 'category': 'seat_material'},
            'nitrile': {'canonical': 'nbr', 'category': 'seat_material'},
            'ptfe': {'canonical': 'ptfe', 'category': 'seat_material'},
            'teflon': {'canonical': 'ptfe', 'category': 'seat_material'},
            
            # Connections
            'socket-weld': {'canonical': 'socket_weld', 'category': 'connection'},
            'socket weld': {'canonical': 'socket_weld', 'category': 'connection'},
            'socket': {'canonical': 'socket_weld', 'category': 'connection'},
            'sw': {'canonical': 'socket_weld', 'category': 'connection'},
            
            'threaded': {'canonical': 'threaded', 'category': 'connection'},
            'thread': {'canonical': 'threaded', 'category': 'connection'},
            'npt': {'canonical': 'threaded', 'category': 'connection'},
            'fnpt': {'canonical': 'threaded', 'category': 'connection'},
            'mnpt': {'canonical': 'threaded', 'category': 'connection'},
            
            'flanged': {'canonical': 'flanged', 'category': 'connection'},
            'flange': {'canonical': 'flanged', 'category': 'connection'},
            'flg': {'canonical': 'flanged', 'category': 'connection'},
            
            'lug': {'canonical': 'lug', 'category': 'connection'},
            'lugged': {'canonical': 'lug', 'category': 'connection'},
            
            'wafer': {'canonical': 'wafer', 'category': 'connection'},
        }
    
    def normalize_specs(self, specs: Dict, component_type: Optional[str] = None) -> Dict:
        """
        Normalize all specs in a dictionary.
        
        Args:
            specs: Dictionary of specs like {"material": "SS", "seatMaterial": "EPDM"}
            component_type: Optional component type for context
        
        Returns:
            Normalized specs with canonical values
        """
        normalized = {}
        
        # Fields that should be normalized with synonyms
        synonym_fields = ['material', 'bodyMaterial', 'body_material', 
                         'seatMaterial', 'seat_material', 'seat',
                         'endConnection', 'connection', 'end_connection',
                         'valveType', 'valve_type', 'type',
                         'pressureRating', 'pressure', 'pressure_rating']
        
        for key, value in specs.items():
            if value is None:
                continue
            
            # Only apply synonym normalization to specific fields
            should_normalize = any(key.lower() == sf.lower() for sf in synonym_fields)
            
            if should_normalize:
                value_lower = str(value).lower().strip()
                
                # Check synonym map
                if value_lower in self.synonym_map:
                    mapping = self.synonym_map[value_lower]
                    canonical = mapping['canonical']
                else:
                    # Try partial matching
                    found = False
                    for synonym, mapping in self.synonym_map.items():
                        if synonym in value_lower or value_lower in synonym:
                            canonical = mapping['canonical']
                            found = True
                            break
                    
                    if not found:
                        # Keep original, just normalize format
                        canonical = value_lower.replace(' ', '_')
                
                # Map to correct field name
                if key in ['material', 'bodyMaterial', 'body_material']:
                    normalized['material'] = canonical
                elif key in ['seatMaterial', 'seat_material', 'seat']:
                    normalized['seatMaterial'] = canonical
                elif key in ['endConnection', 'connection', 'end_connection']:
                    normalized['endConnection'] = canonical
                elif key in ['valveType', 'valve_type', 'type']:
                    normalized['valveType'] = canonical
                elif key in ['pressureRating', 'pressure', 'pressure_rating']:
                    normalized['pressureRating'] = canonical
                else:
                    # Keep original key with normalized value
                    normalized[key] = canonical
            else:
                # For non-synonym fields (like size), keep original value
                normalized[key] = value
        
        return normalized

