#!/usr/bin/env python3
"""
Extract product URLs from ValveMan sitemap.
"""

import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import json

def fetch_sitemap(sitemap_url: str) -> str:
    """Fetch sitemap content."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    response = requests.get(sitemap_url, headers=headers, timeout=10)
    response.raise_for_status()
    return response.text

def extract_sitemap_urls(sitemap_content: str) -> list:
    """Extract sitemap URLs from a sitemap index."""
    sitemap_urls = []
    
    try:
        root = ET.fromstring(sitemap_content)
        
        # Define namespace (common sitemap namespace)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Try with namespace first
        sitemaps = root.findall('.//ns:sitemap', namespace)
        if not sitemaps:
            # Try without namespace
            sitemaps = root.findall('.//sitemap')
        
        for sitemap in sitemaps:
            # Try with namespace
            loc = sitemap.find('ns:loc', namespace)
            if loc is None:
                # Try without namespace
                loc = sitemap.find('loc')
            
            if loc is not None and loc.text:
                sitemap_urls.append(loc.text.strip())
    
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
    
    return sitemap_urls

def extract_product_urls(sitemap_content: str) -> list:
    """Extract all product URLs from a sitemap page."""
    product_urls = []
    
    try:
        root = ET.fromstring(sitemap_content)
        
        # Define namespace
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        
        # Try with namespace first
        url_elems = root.findall('.//ns:url', namespace)
        if not url_elems:
            # Try without namespace
            url_elems = root.findall('.//url')
        
        for url_elem in url_elems:
            # Try with namespace
            loc = url_elem.find('ns:loc', namespace)
            if loc is None:
                # Try without namespace
                loc = url_elem.find('loc')
            
            if loc is not None and loc.text:
                url = loc.text.strip()
                # Filter for product URLs
                if '/products/' in url:
                    product_urls.append(url)
    
    except ET.ParseError as e:
        print(f"  XML parse error: {e}")
    
    return product_urls

def main():
    # Start with the main sitemap index
    main_sitemap_urls = [
        "https://valveman.com/sitemap.xml",
        "https://valveman.com/xmlsitemap.php",
        "https://valveman.com/sitemap_index.xml"
    ]
    
    # Step 1: Find the sitemap index
    print("Step 1: Finding sitemap index...")
    sitemap_index_url = None
    paginated_sitemaps = []
    
    for sitemap_url in main_sitemap_urls:
        try:
            print(f"  Trying: {sitemap_url}")
            content = fetch_sitemap(sitemap_url)
            sitemap_urls = extract_sitemap_urls(content)
            
            if sitemap_urls:
                print(f"  ✓ Found sitemap index with {len(sitemap_urls)} sub-sitemaps")
                # Filter for product sitemaps
                paginated_sitemaps = [url for url in sitemap_urls if 'products' in url.lower() or 'page=' in url]
                if paginated_sitemaps:
                    sitemap_index_url = sitemap_url
                    break
        except Exception as e:
            print(f"  ✗ Error: {e}")
            continue
    
    # If we found paginated sitemaps, fetch all of them
    if paginated_sitemaps:
        print(f"\nStep 2: Fetching {len(paginated_sitemaps)} product sitemap pages...")
        all_product_urls = []
        
        for i, sitemap_url in enumerate(paginated_sitemaps, 1):
            try:
                print(f"  [{i}/{len(paginated_sitemaps)}] Fetching: {sitemap_url}")
                content = fetch_sitemap(sitemap_url)
                product_urls = extract_product_urls(content)
                
                if product_urls:
                    all_product_urls.extend(product_urls)
                    print(f"    ✓ Found {len(product_urls)} product URLs")
                else:
                    print(f"    ⚠️  No product URLs found")
            except Exception as e:
                print(f"    ✗ Error: {e}")
                continue
        
        # Remove duplicates
        all_product_urls = list(set(all_product_urls))
        
        print(f"\n{'='*60}")
        print(f"Total unique product URLs: {len(all_product_urls)}")
        print(f"{'='*60}\n")
        
        # Show first 10
        if all_product_urls:
            print("First 10 URLs:")
            for i, url in enumerate(all_product_urls[:10], 1):
                print(f"  {i}. {url}")
            
            if len(all_product_urls) > 10:
                print(f"  ... and {len(all_product_urls) - 10} more")
            
            # Save to file
            with open('product_urls.json', 'w') as f:
                json.dump(all_product_urls, f, indent=2)
            
            print(f"\n✓ Saved {len(all_product_urls)} URLs to product_urls.json")
            print("\nTo test extraction on all URLs, run:")
            print("  python test_valve_spec_extraction.py --urls product_urls.json")
        else:
            print("⚠️  No product URLs extracted")
    else:
        print("\n⚠️  Could not find paginated sitemaps. Trying direct extraction...")
        # Fallback: try to extract directly from main sitemap
        for sitemap_url in main_sitemap_urls:
            try:
                content = fetch_sitemap(sitemap_url)
                product_urls = extract_product_urls(content)
                if product_urls:
                    print(f"✓ Found {len(product_urls)} product URLs directly")
                    with open('product_urls.json', 'w') as f:
                        json.dump(product_urls, f, indent=2)
                    print(f"✓ Saved to product_urls.json")
                    return
            except Exception as e:
                continue
        
        print("\n⚠️  No product URLs found. You may need to:")
        print("   1. Check the actual sitemap URL")
        print("   2. Manually provide a list of product URLs")

if __name__ == "__main__":
    main()

