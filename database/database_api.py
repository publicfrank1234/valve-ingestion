#!/usr/bin/env python3
"""
Simple HTTP API for database search.
Can be used as an n8n HTTP tool.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    # Try loading from current directory first, then parent directory
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
    else:
        # Try parent directory
        parent_env = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        if os.path.exists(parent_env):
            load_dotenv(parent_env)
except ImportError:
    # python-dotenv not installed, skip
    pass

# Add current directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import from same directory (works as both module and script)
try:
    # Try absolute import first (when run as script)
    from search_specs import search_specs, search_specs_by_normalized_specs
except ImportError:
    # Fallback for relative import (when used as module)
    try:
        from .search_specs import search_specs, search_specs_by_normalized_specs
    except ImportError:
        # Last resort: import directly
        import importlib.util
        spec = importlib.util.spec_from_file_location("search_specs", os.path.join(current_dir, "search_specs.py"))
        search_specs_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(search_specs_module)
        search_specs = search_specs_module.search_specs
        search_specs_by_normalized_specs = search_specs_module.search_specs_by_normalized_specs

app = Flask(__name__)
CORS(app)  # Enable CORS for n8n


@app.route('/search', methods=['POST'])
def search():
    """Search valve specs by criteria."""
    try:
        data = request.get_json() or {}
        
        # Extract search parameters
        results = search_specs(
            valve_type=data.get('valveType') or data.get('valve_type'),
            size_nominal=data.get('size') or data.get('size_nominal'),
            body_material=data.get('material') or data.get('body_material'),
            pressure_class=data.get('pressureRating') or data.get('pressure_class'),
            end_connection=data.get('endConnection') or data.get('end_connection'),
            max_results=data.get('maxResults', 10)
        )
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.get("id"),
                "sourceUrl": result.get("source_url"),
                "specSheetUrl": result.get("spec_sheet_url"),
                "sku": result.get("sku"),
                "valveType": result.get("valve_type"),
                "size": result.get("size_nominal"),
                "material": result.get("body_material"),
                "pressureClass": result.get("pressure_class"),
                "endConnection": result.get("end_connection_inlet") or result.get("end_connection_outlet"),
                "price": float(result.get("starting_price")) if result.get("starting_price") else None,
                "msrp": float(result.get("msrp")) if result.get("msrp") else None,
                "spec": result.get("spec"),
                "priceInfo": result.get("price_info")
            }
            formatted_results.append(formatted_result)
        
        return jsonify({
            "success": True,
            "count": len(formatted_results),
            "results": formatted_results
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/search/normalized', methods=['POST'])
def search_normalized():
    """Search using normalized specs object."""
    try:
        data = request.get_json() or {}
        normalized_specs = data.get('normalizedSpecs', {})
        max_results = data.get('maxResults', 10)
        
        results = search_specs_by_normalized_specs(normalized_specs, max_results)
        
        # Format results
        formatted_results = []
        for result in results:
            formatted_result = {
                "id": result.get("id"),
                "sourceUrl": result.get("source_url"),
                "specSheetUrl": result.get("spec_sheet_url"),
                "sku": result.get("sku"),
                "valveType": result.get("valve_type"),
                "size": result.get("size_nominal"),
                "material": result.get("body_material"),
                "pressureClass": result.get("pressure_class"),
                "endConnection": result.get("end_connection_inlet") or result.get("end_connection_outlet"),
                "price": float(result.get("starting_price")) if result.get("starting_price") else None,
                "msrp": float(result.get("msrp")) if result.get("msrp") else None,
                "spec": result.get("spec"),
                "priceInfo": result.get("price_info")
            }
            formatted_results.append(formatted_result)
        
        return jsonify({
            "success": True,
            "count": len(formatted_results),
            "results": formatted_results
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    port = int(os.getenv('PORT', 6000))
    app.run(host='0.0.0.0', port=port, debug=True)

