#!/usr/bin/env python3
"""
Template-based extractor that uses component-type-specific templates.

This module:
- Matches product pages to templates
- Extracts specs using template rules
- Validates extracted data
- Falls back to AI agent for new component types
"""

import json
import re
from typing import Dict, Optional, List, Tuple
from bs4 import BeautifulSoup
from template_manager import TemplateManager


class TemplateExtractor:
    """Extracts specifications using component-type-specific templates."""
    
    def __init__(self, template_manager: TemplateManager):
        """
        Initialize TemplateExtractor.
        
        Args:
            template_manager: TemplateManager instance
        """
        self.template_manager = template_manager
    
    def extract_from_page(
        self,
        url: str,
        html_content: str,
        component_type_hint: Optional[str] = None
    ) -> Dict:
        """
        Extract specifications from a product page.
        
        Args:
            url: Product page URL
            html_content: HTML content of the page
            component_type_hint: Optional hint about component type
            
        Returns:
            Dictionary with extraction results
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        page_title = self._extract_page_title(soup)
        
        # Try to find matching template
        match_result = self.template_manager.find_matching_template(
            page_title,
            url,
            html_content,
            component_type_hint
        )
        
        if match_result:
            template_id, template_data, match_score = match_result
            print(f"✓ Found matching template: {template_id} (score: {match_score:.2f})")
            
            # Extract using template
            extraction_result = self._extract_using_template(
                soup,
                html_content,
                template_data,
                url
            )
            
            # Log template usage
            self.template_manager.log_template_usage(
                template_id=template_id,
                source_url=url,
                extraction_success=extraction_result['success'],
                extracted_fields_count=len(extraction_result.get('extracted_specs', {})),
                missing_required_fields=extraction_result.get('missing_required_fields', []),
                extraction_time_ms=extraction_result.get('extraction_time_ms'),
                error_message=extraction_result.get('error_message')
            )
            
            extraction_result['template_id'] = template_id
            extraction_result['match_score'] = match_score
            return extraction_result
        else:
            print("⚠️  No matching template found - AI agent needed")
            return {
                'success': False,
                'template_id': None,
                'match_score': 0.0,
                'needs_ai_template': True,
                'page_title': page_title,
                'url': url,
                'message': 'No matching template found. AI agent needed to generate new template.'
            }
    
    def _extract_using_template(
        self,
        soup: BeautifulSoup,
        html_content: str,
        template_data: Dict,
        url: str
    ) -> Dict:
        """
        Extract specifications using a template.
        
        Args:
            soup: BeautifulSoup parsed HTML
            html_content: Raw HTML content
            template_data: Template data structure
            url: Source URL
            
        Returns:
            Extraction result dictionary
        """
        import time
        start_time = time.time()
        
        spec_fields = template_data.get('specFields', [])
        validation = template_data.get('validation', {})
        required_fields = validation.get('requiredFields', [])
        
        extracted_specs = {}
        missing_required = []
        
        # Extract each field according to template rules
        for field_def in spec_fields:
            field_name = field_def.get('name')
            if not field_name:
                continue
            
            field_value = self._extract_field(
                soup,
                html_content,
                field_def
            )
            
            if field_value:
                # Normalize the value
                normalized_value = self._normalize_field_value(
                    field_value,
                    field_def.get('normalization', {})
                )
                extracted_specs[field_name] = normalized_value
            else:
                if field_name in required_fields:
                    missing_required.append(field_name)
        
        extraction_time_ms = int((time.time() - start_time) * 1000)
        
        # Check if all required fields are present
        success = len(missing_required) == 0
        
        return {
            'success': success,
            'extracted_specs': extracted_specs,
            'missing_required_fields': missing_required,
            'extraction_time_ms': extraction_time_ms,
            'error_message': None if success else f"Missing required fields: {', '.join(missing_required)}"
        }
    
    def _extract_field(
        self,
        soup: BeautifulSoup,
        html_content: str,
        field_def: Dict
    ) -> Optional[str]:
        """
        Extract a single field using field definition rules.
        
        Args:
            soup: BeautifulSoup parsed HTML
            html_content: Raw HTML content
            field_def: Field definition from template
            
        Returns:
            Extracted field value or None
        """
        extraction_rules = field_def.get('extractionRules', [])
        
        for rule in extraction_rules:
            rule_type = rule.get('type')
            
            if rule_type == 'regex':
                pattern = rule.get('pattern')
                if pattern:
                    match = re.search(pattern, html_content, re.IGNORECASE | re.MULTILINE)
                    if match:
                        return match.group(1).strip() if match.groups() else match.group(0).strip()
            
            elif rule_type == 'css_selector':
                selector = rule.get('selector')
                attribute = rule.get('attribute', 'text')
                if selector:
                    element = soup.select_one(selector)
                    if element:
                        if attribute == 'text':
                            return element.get_text().strip()
                        else:
                            return element.get(attribute, '').strip()
            
            elif rule_type == 'table_lookup':
                table_selector = rule.get('tableSelector', 'table')
                key_column = rule.get('keyColumn', 0)
                value_column = rule.get('valueColumn', 1)
                key_text = rule.get('keyText', field_def.get('name', ''))
                
                table = soup.select_one(table_selector)
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cells = row.find_all(['td', 'th'])
                        if len(cells) > max(key_column, value_column):
                            key_cell = cells[key_column].get_text().strip()
                            if key_text.lower() in key_cell.lower():
                                return cells[value_column].get_text().strip()
            
            elif rule_type == 'extract_from_title':
                title = soup.find('title')
                if title:
                    return title.get_text().strip()
        
        # Try fallback if specified
        fallback = extraction_rules[0].get('fallback') if extraction_rules else None
        if fallback == 'extract_from_title':
            title = soup.find('title')
            if title:
                return title.get_text().strip()
        
        return None
    
    def _normalize_field_value(
        self,
        value: str,
        normalization: Dict
    ) -> any:
        """
        Normalize a field value according to normalization rules.
        
        Args:
            value: Raw extracted value
            normalization: Normalization rules from template
            
        Returns:
            Normalized value
        """
        norm_type = normalization.get('type')
        
        if norm_type == 'enum':
            # Check if value matches any enum value
            enum_values = normalization.get('values', [])
            value_lower = value.lower()
            for enum_val in enum_values:
                if enum_val.lower() == value_lower or enum_val.lower() in value_lower:
                    return enum_val
            return value
        
        elif norm_type == 'size':
            # Normalize size format
            format_type = normalization.get('format', 'fractional_inches')
            if format_type == 'fractional_inches':
                # Remove quotes, normalize fractions
                value = value.replace('"', '').strip()
                return value
        
        elif norm_type == 'pressure':
            # Extract numeric value and unit
            unit = normalization.get('unit', 'psi')
            match = re.search(r'(\d+(?:\.\d+)?)', value)
            if match:
                return {
                    'value': float(match.group(1)),
                    'unit': unit
                }
            return value
        
        elif norm_type == 'temperature':
            # Extract numeric value and unit
            match = re.search(r'(\d+(?:\.\d+)?)\s*[°]?([CF])', value, re.IGNORECASE)
            if match:
                return {
                    'value': float(match.group(1)),
                    'unit': '°F' if match.group(2).upper() == 'F' else '°C'
                }
            return value
        
        # Default: return as-is
        return value
    
    def _extract_page_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from HTML."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ""

