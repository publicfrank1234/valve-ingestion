#!/usr/bin/env python3
"""
Test script to extract valve specifications from ValveMan product pages.
Tests locally before building the full n8n workflow.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from typing import Dict, Optional

def fetch_page(url: str) -> Optional[str]:
    """Fetch HTML content from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_specs_section(html: str) -> Optional[str]:
    """Extract the Technical Specifications section from HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for the Technical Specifications section
    spec_section = None
    
    # Try to find by heading - look for h2, h3, h4 with "Technical Spec"
    headings = soup.find_all(['h2', 'h3', 'h4'])
    for heading in headings:
        heading_text = heading.get_text().strip()
        if re.search(r'Technical\s+Spec', heading_text, re.I):
            # Find the parent container
            parent = heading.find_parent(['div', 'section', 'article'])
            if parent:
                spec_section = str(parent)
                break
    
    # Alternative: Look for tables with spec-like content
    if not spec_section:
        tables = soup.find_all('table')
        for table in tables:
            # Check if table contains spec keywords
            table_text = table.get_text().lower()
            if any(keyword in table_text for keyword in ['item', 'size', 'body material', 'maximum pressure', 'maximum temperature']):
                spec_section = str(table.find_parent(['div', 'section'])) or str(table)
                break
    
    # Try finding by specific div structure (common in modern sites)
    if not spec_section:
        # Look for divs containing both "Item" and "Size" text
        all_divs = soup.find_all('div')
        for div in all_divs:
            div_text = div.get_text().lower()
            if 'item' in div_text and 'size' in div_text and 'body material' in div_text:
                spec_section = str(div)
                break
    
    return spec_section

def parse_specs_table(html_section: str) -> Dict:
    """Parse the specs table into structured data."""
    soup = BeautifulSoup(html_section, 'html.parser')
    specs = {}
    
    # Pattern 1: Table with <tr><td>Key</td><td>Value</td></tr>
    rows = soup.find_all('tr')
    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            key = cells[0].get_text().strip()
            value = cells[1].get_text().strip()
            if key and value and key.lower() not in ['item', 'value']:  # Skip header rows
                specs[key] = value
    
    # Pattern 2: Div-based key-value pairs (common in modern sites)
    # Look for patterns like: <div>Item</div><div>Gate Valve</div>
    if not specs or len(specs) < 3:
        # Try to find pairs of divs or spans
        all_elements = soup.find_all(['div', 'span', 'p', 'dt', 'dd'])
        current_key = None
        
        for elem in all_elements:
            text = elem.get_text().strip()
            if not text:
                continue
            
            # Check if this looks like a key (common spec field names)
            if text.lower() in ['item', 'size', 'body material', 'design', 'maximum pressure', 
                              'maximum temperature', 'end connection', 'standard', 'pressure', 
                              'temperature', 'material']:
                current_key = text
            elif current_key and text and len(text) > 1:
                # This might be the value for the previous key
                if current_key not in specs or not specs[current_key]:
                    specs[current_key] = text
                current_key = None
    
    # Pattern 3: Look for specific text patterns in the HTML
    if not specs or len(specs) < 3:
        # Try regex-based extraction from the raw HTML
        html_text = soup.get_text()
        
        # Pattern: "Item\nGate Valve" or "Item: Gate Valve"
        patterns = [
            (r'Item[:\s]+([^\n]+)', 'Item'),
            (r'Size[:\s]+([^\n]+)', 'Size'),
            (r'Body\s+Material[:\s]+([^\n]+)', 'Body Material'),
            (r'Design[:\s]+([^\n]+)', 'Design'),
            (r'Maximum\s+Pressure[:\s]+([^\n]+)', 'Maximum Pressure'),
            (r'Maximum\s+Temperature[:\s]+([^\n]+)', 'Maximum Temperature'),
            (r'End\s+Connection[:\s]+([^\n]+)', 'End Connection'),
            (r'Standard[:\s]+([^\n]+)', 'Standard'),
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, html_text, re.I | re.MULTILINE)
            if match and key not in specs:
                value = match.group(1).strip()
                if value:
                    specs[key] = value
    
    # Pattern 4: Definition lists
    if not specs or len(specs) < 3:
        dts = soup.find_all('dt')
        for dt in dts:
            key = dt.get_text().strip()
            dd = dt.find_next_sibling('dd')
            if dd:
                value = dd.get_text().strip()
                if key and value:
                    specs[key] = value
    
    return specs

def extract_spec_sheet_link(html: str) -> Optional[str]:
    """Extract the specification sheet link from the page."""
    soup = BeautifulSoup(html, 'html.parser')
    
    # Look for links containing "specification sheet" or "spec sheet"
    links = soup.find_all('a', href=True)
    for link in links:
        link_text = link.get_text().lower()
        href = link.get('href', '')
        
        if any(keyword in link_text for keyword in ['specification sheet', 'spec sheet', 'view valve specification']):
            # Make absolute URL if relative
            if href.startswith('/'):
                return f"https://valveman.com{href}"
            elif href.startswith('http'):
                return href
            else:
                return f"https://valveman.com/{href}"
    
    return None

def extract_price_info(html: str) -> Dict:
    """Extract price information from the page."""
    soup = BeautifulSoup(html, 'html.parser')
    price_info = {}
    
    # Look for price patterns in the HTML text
    page_text = soup.get_text()
    
    # Extract SKU
    sku_match = re.search(r'SKU[:\s]+([A-Z0-9\-]+)', page_text, re.I)
    if sku_match:
        price_info['sku'] = sku_match.group(1).strip()
    
    # Extract starting price (e.g., "Starting At: $55.99")
    starting_price_match = re.search(r'Starting\s+At[:\s]+\$?([\d,]+\.?\d*)', page_text, re.I)
    if starting_price_match:
        price_info['startingPrice'] = float(starting_price_match.group(1).replace(',', ''))
    
    # Extract MSRP (e.g., "MSRP: $66.86")
    msrp_match = re.search(r'MSRP[:\s]+\$?([\d,]+\.?\d*)', page_text, re.I)
    if msrp_match:
        price_info['msrp'] = float(msrp_match.group(1).replace(',', ''))
    
    # Extract savings (e.g., "You save $10.87")
    savings_match = re.search(r'(?:You\s+save|save)[:\s]+\$?([\d,]+\.?\d*)', page_text, re.I)
    if savings_match:
        price_info['savings'] = float(savings_match.group(1).replace(',', ''))
    
    # Also try to find price in structured data (JSON-LD, meta tags)
    # Look for price in script tags with JSON-LD
    scripts = soup.find_all('script', type='application/ld+json')
    for script in scripts:
        try:
            data = json.loads(script.string)
            if isinstance(data, dict):
                if 'offers' in data:
                    offers = data['offers']
                    if isinstance(offers, dict):
                        if 'price' in offers:
                            price_info['structuredPrice'] = float(offers['price'])
                    elif isinstance(offers, list) and offers:
                        if 'price' in offers[0]:
                            price_info['structuredPrice'] = float(offers[0]['price'])
        except:
            pass
    
    return price_info

def normalize_specs(raw_specs: Dict) -> Dict:
    """Normalize extracted specs to match valve-spec-schema.json structure."""
    normalized = {
        "sourceUrl": "",
        "extractedAt": "",
        "specSheetUrl": None,
        "priceInfo": {},
        "spec": {}
    }
    
    # Map common field names to schema fields
    field_mapping = {
        'item': 'valveType',
        'size': 'size',
        'body material': 'materials',
        'material': 'materials',
        'maximum pressure': 'pressureRating',
        'max pressure': 'pressureRating',
        'pressure': 'pressureRating',
        'maximum temperature': 'temperatureRating',
        'max temperature': 'temperatureRating',
        'temperature': 'temperatureRating',
        'end connection': 'endConnections',
        'standard': 'standards',
        'design': 'design'
    }
    
    # Extract valve type
    item = raw_specs.get('Item', raw_specs.get('item', ''))
    if item:
        normalized['spec']['valveType'] = item
    
    # Extract size
    size = raw_specs.get('Size', raw_specs.get('size', ''))
    if size:
        normalized['spec']['size'] = {
            'nominalSize': size.replace('"', '').strip()
        }
    
    # Extract material
    material = raw_specs.get('Body Material', raw_specs.get('body material', raw_specs.get('Material', '')))
    if material:
        # Determine material type
        material_lower = material.lower()
        if 'carbon steel' in material_lower or 'forged carbon' in material_lower:
            body_material = 'Carbon Steel'
        elif 'stainless' in material_lower:
            body_material = 'Stainless Steel'
        elif 'forged' in material_lower:
            body_material = 'Forged Steel'
        else:
            body_material = material
        
        normalized['spec']['materials'] = {
            'bodyMaterial': body_material,
            'specificGrade': material
        }
    
    # Extract pressure
    pressure_str = raw_specs.get('Maximum Pressure', raw_specs.get('maximum pressure', raw_specs.get('Pressure', '')))
    if pressure_str:
        # Extract number and unit
        match = re.search(r'(\d+(?:\.\d+)?)\s*(psi|bar|kPa|MPa)', pressure_str, re.I)
        if match:
            value = float(match.group(1))
            unit = match.group(2).lower()
            normalized['spec']['pressureRating'] = {
                'maxOperatingPressure': value,
                'pressureUnit': unit
            }
        
        # Extract class if mentioned
        class_match = re.search(r'Class\s+(\d+)', pressure_str, re.I)
        if class_match:
            if 'pressureRating' not in normalized['spec']:
                normalized['spec']['pressureRating'] = {}
            normalized['spec']['pressureRating']['pressureClass'] = class_match.group(1)
    
    # Extract temperature
    temp_str = raw_specs.get('Maximum Temperature', raw_specs.get('maximum temperature', raw_specs.get('Temperature', '')))
    if temp_str:
        match = re.search(r'(\d+(?:\.\d+)?)\s*[°]?([FC])', temp_str, re.I)
        if match:
            value = float(match.group(1))
            unit = '°F' if match.group(2).upper() == 'F' else '°C'
            normalized['spec']['temperatureRating'] = {
                'maxTemperature': value,
                'temperatureUnit': unit
            }
    
    # Extract end connection
    end_conn = raw_specs.get('End Connection', raw_specs.get('end connection', ''))
    if end_conn:
        end_conn_lower = end_conn.lower()
        if 'socket' in end_conn_lower and 'weld' in end_conn_lower:
            conn_type = 'Socket Welded'
        elif 'threaded' in end_conn_lower or 'screwed' in end_conn_lower:
            conn_type = 'Screwed/Threaded'
        elif 'flanged' in end_conn_lower:
            conn_type = 'Flanged'
        elif 'butt' in end_conn_lower and 'weld' in end_conn_lower:
            conn_type = 'Butt Welded'
        else:
            conn_type = end_conn
        
        normalized['spec']['endConnections'] = {
            'inlet': conn_type,
            'outlet': conn_type
        }
    
    # Extract standards
    standards_str = raw_specs.get('Standard', raw_specs.get('standard', ''))
    if standards_str:
        # Split by comma and clean
        standards = [s.strip() for s in standards_str.split(',')]
        normalized['spec']['standards'] = standards
    
    # Store raw specs for reference
    normalized['rawSpecs'] = raw_specs
    
    return normalized

def test_extraction(url: str):
    """Test extraction from a single URL."""
    print(f"\n{'='*60}")
    print(f"Testing extraction from: {url}")
    print(f"{'='*60}\n")
    
    # Fetch page
    print("1. Fetching page...")
    html = fetch_page(url)
    if not html:
        print("❌ Failed to fetch page")
        return
    
    print(f"   ✓ Fetched {len(html)} characters")
    
    # Extract specs section
    print("\n2. Extracting Technical Specifications section...")
    spec_section = extract_specs_section(html)
    if not spec_section:
        print("   ⚠️  Could not find specs section, using full page")
        spec_section = html
    else:
        print(f"   ✓ Found specs section ({len(spec_section)} characters)")
        # Save for debugging
        with open('debug_spec_section.html', 'w') as f:
            f.write(spec_section)
        print("   💾 Saved to debug_spec_section.html for inspection")
    
    # Parse specs
    print("\n3. Parsing specifications...")
    raw_specs = parse_specs_table(spec_section)
    print(f"   ✓ Extracted {len(raw_specs)} fields:")
    for key, value in raw_specs.items():
        print(f"     - {key}: {value}")
    
    # Extract spec sheet link
    print("\n4. Extracting specification sheet link...")
    spec_sheet_url = extract_spec_sheet_link(html)
    if spec_sheet_url:
        print(f"   ✓ Found spec sheet: {spec_sheet_url}")
    else:
        print("   ⚠️  No spec sheet link found")
    
    # Extract price information
    print("\n5. Extracting price information...")
    price_info = extract_price_info(html)
    if price_info:
        print(f"   ✓ Found price info:")
        for key, value in price_info.items():
            if isinstance(value, float):
                print(f"     - {key}: ${value:.2f}")
            else:
                print(f"     - {key}: {value}")
    else:
        print("   ⚠️  No price information found")
    
    # Normalize specs
    print("\n6. Normalizing to schema format...")
    normalized = normalize_specs(raw_specs)
    normalized['sourceUrl'] = url
    normalized['specSheetUrl'] = spec_sheet_url
    normalized['priceInfo'] = price_info
    from datetime import datetime, timezone
    normalized['extractedAt'] = datetime.now(timezone.utc).isoformat()
    
    print("\n5. Normalized output:")
    print(json.dumps(normalized, indent=2))
    
    return normalized

def batch_extract(urls: list, output_file: str = 'extracted_specs.json'):
    """Extract specs from multiple URLs."""
    results = []
    total = len(urls)
    
    print(f"\n{'='*60}")
    print(f"Batch extraction: {total} URLs")
    print(f"{'='*60}\n")
    
    for i, url in enumerate(urls, 1):
        print(f"\n[{i}/{total}] Processing: {url}")
        try:
            result = test_extraction(url)
            if result:
                results.append(result)
                print(f"✓ Success")
            else:
                print(f"✗ Failed")
        except Exception as e:
            print(f"✗ Error: {e}")
            continue
    
    # Save all results
    if results:
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n{'='*60}")
        print(f"✓ Extracted {len(results)}/{total} specs")
        print(f"✓ Saved to {output_file}")
    else:
        print(f"\n✗ No specs extracted")

if __name__ == "__main__":
    import sys
    
    # Check if URLs file provided
    if len(sys.argv) > 1 and sys.argv[1] == '--urls':
        urls_file = sys.argv[2] if len(sys.argv) > 2 else 'product_urls.json'
        try:
            with open(urls_file, 'r') as f:
                urls = json.load(f)
            batch_extract(urls)
        except FileNotFoundError:
            print(f"Error: {urls_file} not found")
            sys.exit(1)
    else:
        # Test with the example URL
        test_url = "https://valveman.com/products/1-2-SVF-Flow-Control-500F-Gate-Valve-Forged-Carbon-Steel-Body-Socket-Weld-Ends"
        
        result = test_extraction(test_url)
        
        # Save to file
        if result:
            with open('test_extracted_spec.json', 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n✓ Saved to test_extracted_spec.json")

