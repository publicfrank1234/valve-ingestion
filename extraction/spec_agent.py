#!/usr/bin/env python3
"""
Spec Extraction Agent

A simple agent that takes a URL, extracts specifications, and returns JSON
with both the extracted specs and location information (where each spec was found).

This can be used to:
1. Extract specs from any product page
2. Identify where specs are located (for template creation)
3. Provide guidance for other agents on where to find information
"""

import requests
import json
import re
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse


class SpecExtractionAgent:
    """Agent that extracts specs and provides location information."""
    
    def __init__(self):
        """Initialize the spec extraction agent."""
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def extract_from_url(self, url: str) -> Dict[str, Any]:
        """
        Extract specifications from a URL.
        
        Args:
            url: Product page URL
            
        Returns:
            Dictionary with extracted specs and location information
        """
        # Fetch page
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            html_content = response.text
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'url': url
            }
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract specs with location info
        result = {
            'success': True,
            'url': url,
            'page_title': self._extract_title(soup),
            'specs': {},
            'spec_locations': {},
            'extraction_methods': {},
            'recommendations': []
        }
        
        # Find Technical Specifications section
        spec_section = self._find_spec_section(soup)
        
        if spec_section:
            result['spec_section_found'] = True
            result['spec_section_location'] = self._get_element_location(spec_section)
            
            # Extract specs from section
            specs = self._extract_specs_from_section(spec_section, soup)
            result['specs'] = specs['specs']
            result['spec_locations'] = specs['locations']
            result['extraction_methods'] = specs['methods']
        else:
            result['spec_section_found'] = False
            result['recommendations'].append(
                "No Technical Specifications section found. Try extracting from full page."
            )
            # Try extracting from full page
            specs = self._extract_specs_from_full_page(soup)
            result['specs'] = specs['specs']
            result['spec_locations'] = specs['locations']
            result['extraction_methods'] = specs['methods']
        
        # Extract price information
        price_info = self._extract_price_info(soup, html_content)
        if price_info:
            result['price_info'] = price_info
        
        # Extract spec sheet link
        spec_sheet_url = self._extract_spec_sheet_link(soup, url)
        if spec_sheet_url:
            result['spec_sheet_url'] = spec_sheet_url
        
        # Generate recommendations
        result['recommendations'].extend(
            self._generate_recommendations(result, soup)
        )
        
        return result
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ""
    
    def _find_spec_section(self, soup: BeautifulSoup) -> Optional[Any]:
        """Find the Technical Specifications section."""
        # Look for headings with "Technical Spec" or "Specifications"
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        for heading in headings:
            heading_text = heading.get_text().strip()
            if re.search(r'Technical\s+Spec|Specification', heading_text, re.I):
                # Find the parent container
                parent = heading.find_parent(['div', 'section', 'article', 'table'])
                if parent:
                    return parent
        
        # Look for tables with spec-like content
        tables = soup.find_all('table')
        for table in tables:
            table_text = table.get_text().lower()
            spec_keywords = ['item', 'size', 'body material', 'pressure', 'temperature', 'connection']
            if sum(1 for kw in spec_keywords if kw in table_text) >= 3:
                return table
        
        return None
    
    def _get_element_location(self, element: Any) -> Dict[str, str]:
        """Get location information for an element."""
        location = {}
        
        # CSS selector
        if element.name:
            location['css_selector'] = self._generate_css_selector(element)
        
        # XPath (simplified)
        location['xpath'] = self._generate_xpath(element)
        
        # Tag info
        location['tag'] = element.name if hasattr(element, 'name') else 'unknown'
        location['classes'] = element.get('class', []) if hasattr(element, 'get') else []
        location['id'] = element.get('id', '') if hasattr(element, 'get') else ''
        
        return location
    
    def _generate_css_selector(self, element: Any) -> str:
        """Generate a CSS selector for an element."""
        if not hasattr(element, 'name'):
            return ""
        
        selector = element.name
        
        # Add ID if present
        if hasattr(element, 'get') and element.get('id'):
            selector += f"#{element.get('id')}"
            return selector
        
        # Add classes if present
        if hasattr(element, 'get') and element.get('class'):
            classes = ' '.join(element.get('class'))
            selector += f".{classes.replace(' ', '.')}"
        
        return selector
    
    def _generate_xpath(self, element: Any) -> str:
        """Generate a simplified XPath for an element."""
        if not hasattr(element, 'name'):
            return ""
        
        parts = []
        current = element
        
        while current and hasattr(current, 'name') and current.name:
            tag = current.name
            idx = 1
            sibling = current.find_previous_sibling(tag)
            while sibling:
                idx += 1
                sibling = sibling.find_previous_sibling(tag)
            
            parts.insert(0, f"{tag}[{idx}]")
            current = current.parent
        
        return "/" + "/".join(parts) if parts else ""
    
    def _extract_specs_from_section(self, section: Any, soup: BeautifulSoup) -> Dict:
        """Extract specs from a specific section."""
        specs = {}
        locations = {}
        methods = {}
        
        # Try table extraction first
        table = section.find('table') if hasattr(section, 'find') else None
        if table:
            table_specs = self._extract_from_table(table)
            specs.update(table_specs['specs'])
            locations.update(table_specs['locations'])
            methods.update(table_specs['methods'])
        
        # Try definition list
        if not specs:
            dl = section.find('dl') if hasattr(section, 'find') else None
            if dl:
                dl_specs = self._extract_from_dl(dl)
                specs.update(dl_specs['specs'])
                locations.update(dl_specs['locations'])
                methods.update(dl_specs['methods'])
        
        # Try div-based key-value pairs
        if not specs:
            div_specs = self._extract_from_divs(section)
            specs.update(div_specs['specs'])
            locations.update(div_specs['locations'])
            methods.update(div_specs['methods'])
        
        return {
            'specs': specs,
            'locations': locations,
            'methods': methods
        }
    
    def _extract_from_table(self, table: Any) -> Dict:
        """Extract specs from a table."""
        specs = {}
        locations = {}
        methods = {}
        
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                key_cell = cells[0]
                value_cell = cells[1]
                
                key = key_cell.get_text().strip()
                value = value_cell.get_text().strip()
                
                if key and value and key.lower() not in ['item', 'value', 'specification']:
                    # Normalize key name
                    normalized_key = self._normalize_key(key)
                    specs[normalized_key] = value
                    
                    # Store location
                    locations[normalized_key] = {
                        'type': 'table',
                        'row_index': rows.index(row),
                        'key_cell': self._get_element_location(key_cell),
                        'value_cell': self._get_element_location(value_cell),
                        'table_location': self._get_element_location(table)
                    }
                    
                    methods[normalized_key] = 'table_extraction'
        
        return {
            'specs': specs,
            'locations': locations,
            'methods': methods
        }
    
    def _extract_from_dl(self, dl: Any) -> Dict:
        """Extract specs from a definition list."""
        specs = {}
        locations = {}
        methods = {}
        
        dts = dl.find_all('dt')
        for dt in dts:
            key = dt.get_text().strip()
            dd = dt.find_next_sibling('dd')
            if dd:
                value = dd.get_text().strip()
                if key and value:
                    normalized_key = self._normalize_key(key)
                    specs[normalized_key] = value
                    
                    locations[normalized_key] = {
                        'type': 'definition_list',
                        'dt_location': self._get_element_location(dt),
                        'dd_location': self._get_element_location(dd)
                    }
                    
                    methods[normalized_key] = 'dl_extraction'
        
        return {
            'specs': specs,
            'locations': locations,
            'methods': methods
        }
    
    def _extract_from_divs(self, section: Any) -> Dict:
        """Extract specs from div-based structures."""
        specs = {}
        locations = {}
        methods = {}
        
        # Look for common patterns
        all_divs = section.find_all('div') if hasattr(section, 'find_all') else []
        
        # Pattern: <div class="spec-key">Key</div><div class="spec-value">Value</div>
        for i, div in enumerate(all_divs):
            div_text = div.get_text().strip().lower()
            div_classes = div.get('class', []) if hasattr(div, 'get') else []
            
            # Check if this looks like a spec key
            if any(keyword in div_text for keyword in ['item', 'size', 'material', 'pressure', 'temperature', 'connection']):
                # Look for next sibling or next div with value
                next_elem = div.find_next_sibling()
                if next_elem:
                    value = next_elem.get_text().strip()
                    if value and len(value) < 200:  # Reasonable value length
                        key = div.get_text().strip()
                        normalized_key = self._normalize_key(key)
                        specs[normalized_key] = value
                        
                        locations[normalized_key] = {
                            'type': 'div_pair',
                            'key_div': self._get_element_location(div),
                            'value_div': self._get_element_location(next_elem)
                        }
                        
                        methods[normalized_key] = 'div_extraction'
        
        return {
            'specs': specs,
            'locations': locations,
            'methods': methods
        }
    
    def _extract_specs_from_full_page(self, soup: BeautifulSoup) -> Dict:
        """Extract specs from full page using regex patterns."""
        specs = {}
        locations = {}
        methods = {}
        
        html_text = soup.get_text()
        
        # Common spec patterns
        patterns = [
            (r'Item[:\s]+([^\n]+)', 'item', 'Item'),
            (r'Size[:\s]+([^\n]+)', 'size', 'Size'),
            (r'Body\s+Material[:\s]+([^\n]+)', 'bodyMaterial', 'Body Material'),
            (r'Material[:\s]+([^\n]+)', 'material', 'Material'),
            (r'Pressure\s+Rating[:\s]+([^\n]+)', 'pressureRating', 'Pressure Rating'),
            (r'Maximum\s+Pressure[:\s]+([^\n]+)', 'maxPressure', 'Maximum Pressure'),
            (r'Temperature\s+Rating[:\s]+([^\n]+)', 'temperatureRating', 'Temperature Rating'),
            (r'Maximum\s+Temperature[:\s]+([^\n]+)', 'maxTemperature', 'Maximum Temperature'),
            (r'End\s+Connection[:\s]+([^\n]+)', 'endConnection', 'End Connection'),
            (r'Connection[:\s]+([^\n]+)', 'connection', 'Connection'),
            (r'Standard[:\s]+([^\n]+)', 'standard', 'Standard'),
            (r'Conforms\s+To[:\s]+([^\n]+)', 'conformsTo', 'Conforms To'),
        ]
        
        for pattern, key, label in patterns:
            match = re.search(pattern, html_text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                if value and key not in specs:
                    specs[key] = value
                    locations[key] = {
                        'type': 'regex',
                        'pattern': pattern,
                        'label': label,
                        'note': 'Found using regex pattern matching in page text'
                    }
                    methods[key] = 'regex_extraction'
        
        return {
            'specs': specs,
            'locations': locations,
            'methods': methods
        }
    
    def _normalize_key(self, key: str) -> str:
        """Normalize spec key names."""
        key_lower = key.lower().strip()
        
        # Common mappings
        mappings = {
            'item': 'valveType',
            'body material': 'bodyMaterial',
            'material': 'bodyMaterial',
            'pressure rating': 'pressureRating',
            'maximum pressure': 'maxPressure',
            'temperature rating': 'temperatureRating',
            'maximum temperature': 'maxTemperature',
            'end connection': 'endConnection',
            'connection': 'endConnection',
            'conforms to': 'conformsTo',
            'standard': 'standards'
        }
        
        return mappings.get(key_lower, key_lower.replace(' ', ''))
    
    def _extract_price_info(self, soup: BeautifulSoup, html_content: str) -> Dict:
        """Extract price information."""
        price_info = {}
        
        # Look for price patterns
        price_patterns = [
            (r'MSRP[:\s]+\$?([\d,]+\.?\d*)', 'msrp'),
            (r'Starting\s+At[:\s]+\$?([\d,]+\.?\d*)', 'startingPrice'),
            (r'Price[:\s]+\$?([\d,]+\.?\d*)', 'price'),
        ]
        
        for pattern, key in price_patterns:
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                try:
                    price_info[key] = float(match.group(1).replace(',', ''))
                except:
                    pass
        
        # Extract SKU
        sku_match = re.search(r'SKU[:\s]+([A-Z0-9\-]+)', html_content, re.I)
        if sku_match:
            price_info['sku'] = sku_match.group(1).strip()
        
        return price_info if price_info else None
    
    def _extract_spec_sheet_link(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Extract specification sheet link."""
        links = soup.find_all('a', href=True)
        for link in links:
            link_text = link.get_text().lower()
            href = link.get('href', '')
            
            if any(keyword in link_text for keyword in ['specification sheet', 'spec sheet', 'view valve specification']):
                # Make absolute URL
                if href.startswith('/'):
                    return urljoin(base_url, href)
                elif href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        
        return None
    
    def _generate_recommendations(self, result: Dict, soup: BeautifulSoup) -> List[str]:
        """Generate recommendations for extraction."""
        recommendations = []
        
        if not result.get('specs'):
            recommendations.append("No specs found. Consider checking the page structure or using different extraction methods.")
        
        if result.get('spec_section_found'):
            recommendations.append("Technical Specifications section found. Use table extraction for best results.")
        else:
            recommendations.append("No dedicated spec section found. Consider using regex patterns or full-page extraction.")
        
        # Check if table structure is consistent
        tables = soup.find_all('table')
        if tables:
            recommendations.append(f"Found {len(tables)} table(s). Table-based extraction recommended.")
        
        return recommendations


def main():
    """Main function for command-line usage."""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python spec_agent.py <url>")
        print("\nExample:")
        print("  python spec_agent.py https://valveman.com/products/1-1-2-milwaukee-valve-509")
        sys.exit(1)
    
    url = sys.argv[1]
    
    print(f"Extracting specs from: {url}\n")
    print("=" * 60)
    
    agent = SpecExtractionAgent()
    result = agent.extract_from_url(url)
    
    # Print results
    print(json.dumps(result, indent=2, default=str))
    
    # Save to file
    output_file = 'extracted_specs.json'
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2, default=str)
    
    print(f"\n✓ Results saved to {output_file}")


if __name__ == "__main__":
    main()

