#!/usr/bin/env python3
"""
Main template-based extractor that orchestrates the extraction process.

This is the entry point for template-based extraction:
1. Tries to match page to existing template
2. If match found, extracts using template
3. If no match, calls AI agent to generate new template
4. Stores new template and extracts using it
"""

import requests
from typing import Dict, Optional
from template_manager import TemplateManager
from template_extractor import TemplateExtractor
from ai_template_generator import AITemplateGenerator


class TemplateBasedExtractor:
    """Main orchestrator for template-based extraction."""
    
    def __init__(
        self,
        db_connection_string: str,
        ai_api_key: Optional[str] = None,
        ai_model: str = "gpt-4"
    ):
        """
        Initialize TemplateBasedExtractor.
        
        Args:
            db_connection_string: PostgreSQL connection string
            ai_api_key: Optional API key for AI template generation
            ai_model: AI model to use for template generation
        """
        self.template_manager = TemplateManager(db_connection_string)
        self.template_extractor = TemplateExtractor(self.template_manager)
        self.ai_generator = AITemplateGenerator(ai_api_key, ai_model) if ai_api_key else None
    
    def extract_from_url(self, url: str, component_type_hint: Optional[str] = None) -> Dict:
        """
        Extract specifications from a product page URL.
        
        Args:
            url: Product page URL
            component_type_hint: Optional hint about component type
            
        Returns:
            Extraction result dictionary
        """
        # Fetch page
        print(f"Fetching page: {url}")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            html_content = response.text
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to fetch page: {e}",
                'url': url
            }
        
        # Extract using template system
        result = self.template_extractor.extract_from_page(
            url,
            html_content,
            component_type_hint
        )
        
        # If no template found and AI is available, generate new template
        if not result.get('success') and result.get('needs_ai_template') and self.ai_generator:
            print("🤖 Generating new template using AI agent...")
            
            try:
                # Generate template
                new_template = self.ai_generator.generate_template(
                    url,
                    html_content,
                    result.get('page_title')
                )
                
                # Store template
                template_id = new_template.get('templateId')
                if template_id:
                    success = self.template_manager.create_template(
                        template_id=template_id,
                        component_type=new_template.get('componentType', 'Unknown'),
                        category=new_template.get('category', 'unknown'),
                        template_data=new_template,
                        version=new_template.get('version', '1.0'),
                        created_by='ai_agent',
                        notes=f"Auto-generated from {url}"
                    )
                    
                    if success:
                        print(f"✓ Generated and stored new template: {template_id}")
                        
                        # Now extract using the new template
                        result = self.template_extractor.extract_from_page(
                            url,
                            html_content,
                            component_type_hint
                        )
                        result['new_template_generated'] = True
                        result['new_template_id'] = template_id
                    else:
                        result['error'] = "Failed to store generated template"
                else:
                    result['error'] = "AI generated template missing templateId"
                    
            except Exception as e:
                result['error'] = f"AI template generation failed: {e}"
                print(f"✗ AI template generation error: {e}")
        
        return result
    
    def extract_from_html(self, url: str, html_content: str, component_type_hint: Optional[str] = None) -> Dict:
        """
        Extract specifications from HTML content.
        
        Args:
            url: Source URL
            html_content: HTML content
            component_type_hint: Optional hint about component type
            
        Returns:
            Extraction result dictionary
        """
        return self.template_extractor.extract_from_page(
            url,
            html_content,
            component_type_hint
        )


if __name__ == "__main__":
    # Example usage
    import os
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python template_based_extractor.py <url> [component_type_hint]")
        sys.exit(1)
    
    url = sys.argv[1]
    component_type_hint = sys.argv[2] if len(sys.argv) > 2 else None
    
    db_conn_string = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/valve_specs")
    ai_api_key = os.getenv("OPENAI_API_KEY")
    
    extractor = TemplateBasedExtractor(db_conn_string, ai_api_key)
    result = extractor.extract_from_url(url, component_type_hint)
    
    import json
    print("\n" + "="*60)
    print("Extraction Result:")
    print("="*60)
    print(json.dumps(result, indent=2))

