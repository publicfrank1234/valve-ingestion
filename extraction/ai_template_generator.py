#!/usr/bin/env python3
"""
AI Agent for generating new extraction templates.

When a product page doesn't match any existing template, this agent:
1. Analyzes the HTML structure
2. Identifies component type and category
3. Determines which spec fields are present
4. Creates extraction rules for each field
5. Generates a complete template JSON structure
"""

import json
import re
from typing import Dict, Optional, List
from bs4 import BeautifulSoup
import openai  # or anthropic, etc.


class AITemplateGenerator:
    """Generates extraction templates using AI analysis."""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize AI Template Generator.
        
        Args:
            api_key: API key for LLM service
            model: Model name to use
        """
        self.api_key = api_key
        self.model = model
        if api_key:
            openai.api_key = api_key
    
    def generate_template(
        self,
        url: str,
        html_content: str,
        page_title: Optional[str] = None
    ) -> Dict:
        """
        Generate a new extraction template for a product page.
        
        Args:
            url: Product page URL
            html_content: HTML content of the page
            page_title: Optional page title
            
        Returns:
            Generated template dictionary
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        if not page_title:
            page_title = self._extract_page_title(soup)
        
        # Analyze page structure
        page_analysis = self._analyze_page_structure(soup, html_content)
        
        # Call AI to generate template
        template_json = self._call_ai_for_template(
            url,
            page_title,
            page_analysis,
            html_content[:5000]  # Limit HTML for token efficiency
        )
        
        return template_json
    
    def _analyze_page_structure(
        self,
        soup: BeautifulSoup,
        html_content: str
    ) -> Dict:
        """
        Analyze HTML structure to help AI understand the page.
        
        Args:
            soup: BeautifulSoup parsed HTML
            html_content: Raw HTML content
            
        Returns:
            Analysis dictionary
        """
        analysis = {
            'has_spec_table': False,
            'has_spec_section': False,
            'spec_keywords_found': [],
            'table_count': len(soup.find_all('table')),
            'list_count': len(soup.find_all(['ul', 'ol', 'dl'])),
            'heading_structure': []
        }
        
        # Check for specification tables
        tables = soup.find_all('table')
        for table in tables:
            table_text = table.get_text().lower()
            spec_keywords = ['specification', 'spec', 'item', 'size', 'material', 'pressure', 'temperature', 'rating']
            if any(keyword in table_text for keyword in spec_keywords):
                analysis['has_spec_table'] = True
                analysis['spec_keywords_found'].extend([
                    kw for kw in spec_keywords if kw in table_text
                ])
        
        # Check for specification sections
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        for heading in headings:
            heading_text = heading.get_text().lower()
            if any(keyword in heading_text for keyword in ['specification', 'spec', 'technical', 'details']):
                analysis['has_spec_section'] = True
                analysis['heading_structure'].append({
                    'level': heading.name,
                    'text': heading.get_text().strip()
                })
        
        # Extract sample spec fields from tables
        sample_fields = []
        for table in tables[:3]:  # Check first 3 tables
            rows = table.find_all('tr')[:10]  # First 10 rows
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text().strip()
                    value = cells[1].get_text().strip()
                    if key and value and len(key) < 50:
                        sample_fields.append({
                            'key': key,
                            'value': value[:100]  # Limit value length
                        })
        
        analysis['sample_fields'] = sample_fields[:20]  # Limit to 20 samples
        
        return analysis
    
    def _call_ai_for_template(
        self,
        url: str,
        page_title: str,
        page_analysis: Dict,
        html_snippet: str
    ) -> Dict:
        """
        Call AI to generate template JSON.
        
        Args:
            url: Product page URL
            page_title: Page title
            page_analysis: Page structure analysis
            html_snippet: HTML snippet for context
            
        Returns:
            Generated template dictionary
        """
        prompt = self._build_template_generation_prompt(
            url,
            page_title,
            page_analysis,
            html_snippet
        )
        
        # Call OpenAI API (or other LLM)
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing product pages and creating extraction templates for web scraping. You understand HTML structure and can identify component types and their specifications."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            response_text = response.choices[0].message.content
            
            # Parse JSON from response
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                template_json = json.loads(json_match.group(1))
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    template_json = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not parse JSON from AI response")
            
            return template_json
            
        except Exception as e:
            print(f"Error calling AI for template generation: {e}")
            # Return a basic template as fallback
            return self._create_fallback_template(page_title, page_analysis)
    
    def _build_template_generation_prompt(
        self,
        url: str,
        page_title: str,
        page_analysis: Dict,
        html_snippet: str
    ) -> str:
        """Build prompt for AI template generation."""
        return f"""Analyze this product page and create an extraction template for it.

URL: {url}
Page Title: {page_title}

Page Structure Analysis:
- Has spec table: {page_analysis.get('has_spec_table', False)}
- Has spec section: {page_analysis.get('has_spec_section', False)}
- Tables found: {page_analysis.get('table_count', 0)}
- Spec keywords: {', '.join(set(page_analysis.get('spec_keywords_found', [])))}

Sample Fields Found:
{json.dumps(page_analysis.get('sample_fields', [])[:10], indent=2)}

HTML Snippet (first 5000 chars):
{html_snippet[:5000]}

Based on this analysis, create a complete extraction template JSON with:

1. **templateId**: A unique identifier (e.g., "gate_valve_v1", "resistor_0805_v1")
2. **componentType**: The type of component (e.g., "Gate Valve", "Resistor", "Capacitor")
3. **category**: Component category (e.g., "valve", "resistor", "capacitor", "actuator")
4. **pagePatterns**: Patterns to identify this component type:
   - titleKeywords: Keywords in page title
   - urlPatterns: URL path patterns
   - htmlMarkers: HTML markers/headings
5. **specFields**: Array of specification fields with:
   - name: Field name (e.g., "valveType", "size", "pressureRating")
   - required: Whether this field is required
   - extractionRules: Array of extraction rules (regex, css_selector, table_lookup, etc.)
   - normalization: How to normalize the extracted value

Example template structure:
{{
  "templateId": "gate_valve_v1",
  "componentType": "Gate Valve",
  "category": "valve",
  "version": "1.0",
  "pagePatterns": {{
    "titleKeywords": ["gate valve", "gate"],
    "urlPatterns": ["/gate-valve", "/gate"],
    "htmlMarkers": ["<h1>Gate Valve", "Technical Specifications"]
  }},
  "specFields": [
    {{
      "name": "valveType",
      "required": true,
      "extractionRules": [
        {{
          "type": "regex",
          "pattern": "Item[:\\s]+([^\\n]+)",
          "fallback": "extract_from_title"
        }}
      ],
      "normalization": {{
        "type": "enum",
        "values": ["Gate Valve", "Ball Valve", "Butterfly Valve"]
      }}
    }}
  ],
  "validation": {{
    "requiredFields": ["valveType", "size", "pressureRating"]
  }}
}}

Generate the complete template JSON now:"""
    
    def _create_fallback_template(
        self,
        page_title: str,
        page_analysis: Dict
    ) -> Dict:
        """Create a basic fallback template when AI fails."""
        # Extract component type from title
        component_type = page_title.split('-')[0].strip() if '-' in page_title else page_title[:50]
        
        return {
            "templateId": f"{component_type.lower().replace(' ', '_')}_v1",
            "componentType": component_type,
            "category": "unknown",
            "version": "1.0",
            "pagePatterns": {
                "titleKeywords": [component_type.lower()],
                "urlPatterns": [],
                "htmlMarkers": []
            },
            "specFields": [
                {
                    "name": "item",
                    "required": False,
                    "extractionRules": [
                        {
                            "type": "regex",
                            "pattern": "Item[:\\s]+([^\\n]+)"
                        }
                    ],
                    "normalization": {
                        "type": "string"
                    }
                }
            ],
            "validation": {
                "requiredFields": []
            }
        }
    
    def _extract_page_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from HTML."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "Unknown Product"

