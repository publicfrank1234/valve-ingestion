#!/usr/bin/env python3
"""
Simple HTTP API for database search.
Can be used as an n8n HTTP tool.
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json
import redis
from urllib.parse import unquote

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

# Import JSONB search functions from local module
try:
    from jsonb_search import search_jsonb_tiered
    from synonym_normalizer import SynonymNormalizer
    jsonb_search_available = True
    normalizer = SynonymNormalizer()
    print("✅ JSONB search and synonym normalizer loaded")
except ImportError as e:
    print(f"⚠️ JSONB search not available: {e}")
    jsonb_search_available = False
    normalizer = None
except Exception as e:
    print(f"⚠️ JSONB search initialization failed: {e}")
    jsonb_search_available = False
    normalizer = None

app = Flask(__name__)
CORS(app)  # Enable CORS for n8n

# Initialize Redis connection
redis_client = None
try:
    # Default to Redis Labs connection if REDIS_URL not set
    # Note: Redis Labs typically requires SSL, but try both redis:// and rediss://
    default_redis_url = 'redis://default:NPTICUxXh921HLMvIhNvAXrUY9YyAR9f@redis-14604.c85.us-east-1-2.ec2.cloud.redislabs.com:14604'
    redis_url = os.getenv('REDIS_URL', default_redis_url)
    
    # Configure SSL for Redis Labs (if using rediss:// or if connection fails)
    ssl_config = {}
    if redis_url.startswith('rediss://'):
        ssl_config = {
            'ssl_cert_reqs': None,  # Don't verify SSL certificate
            'ssl_ca_certs': None
        }
    
    # Try connection
    redis_client = redis.from_url(redis_url, decode_responses=True, **ssl_config)
    redis_client.ping()
    
    # Hide password in log
    display_url = redis_url.split('@')[1] if '@' in redis_url else redis_url
    print(f"✅ Connected to Redis: {display_url}")
except Exception as e:
    # If connection failed with redis://, try rediss:// (SSL)
    if redis_url.startswith('redis://') and not redis_url.startswith('rediss://'):
        try:
            ssl_url = redis_url.replace('redis://', 'rediss://')
            print(f"⚠️ First attempt failed, trying SSL connection...")
            redis_client = redis.from_url(ssl_url, decode_responses=True, 
                                        ssl_cert_reqs=None, ssl_ca_certs=None)
            redis_client.ping()
            redis_url = ssl_url
            display_url = redis_url.split('@')[1] if '@' in redis_url else redis_url
            print(f"✅ Connected to Redis (SSL): {display_url}")
        except Exception as e2:
            print(f"⚠️ Redis not available: {e}")
            print(f"⚠️ SSL attempt also failed: {e2}")
            print("⚠️ Cache endpoints will not work without Redis")
            redis_client = None
    else:
        print(f"⚠️ Redis not available: {e}")
        print("⚠️ Cache endpoints will not work without Redis")
        redis_client = None


@app.route('/search', methods=['POST'])
def search():
    """Search valve specs by criteria."""
    try:
        data = request.get_json() or {}
        
        # Extract search parameters
        # make_material_optional defaults to True - allows material mismatch when size and type match
        results = search_specs(
            valve_type=data.get('valveType') or data.get('valve_type'),
            size_nominal=data.get('size') or data.get('size_nominal'),
            body_material=data.get('material') or data.get('body_material'),
            pressure_class=data.get('pressureRating') or data.get('pressure_class'),
            end_connection=data.get('endConnection') or data.get('end_connection'),
            max_results=data.get('maxResults', 100),
            make_material_optional=data.get('makeMaterialOptional', True)  # Default: relaxed material matching
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
                "maxPressure": float(result.get("max_pressure")) if result.get("max_pressure") else None,
                "pressureUnit": result.get("pressure_unit"),
                "maxTemperature": float(result.get("max_temperature")) if result.get("max_temperature") else None,
                "temperatureUnit": result.get("temperature_unit"),
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
    """Search using normalized specs object (old valve_specs table)."""
    try:
        data = request.get_json() or {}
        normalized_specs = data.get('normalizedSpecs', {})
        max_results = data.get('maxResults', 10)
        make_material_optional = data.get('makeMaterialOptional', True)
        
        print(f"🔍 API /search/normalized called:")
        print(f"   - normalizedSpecs: {normalized_specs}")
        print(f"   - maxResults: {max_results}")
        
        results = search_specs_by_normalized_specs(normalized_specs, max_results, make_material_optional)
        
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
                "maxPressure": float(result.get("max_pressure")) if result.get("max_pressure") else None,
                "pressureUnit": result.get("pressure_unit"),
                "maxTemperature": float(result.get("max_temperature")) if result.get("max_temperature") else None,
                "temperatureUnit": result.get("temperature_unit"),
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


@app.route('/search/jsonb', methods=['POST'])
def search_jsonb():
    """
    Search component-system tables using JSONB fields.
    
    This endpoint searches the newly ingested component-system tables (JSONB format).
    Use this for searching the new crawled data.
    
    Request:
    {
        "normalizedSpecs": {
            "size": "6",
            "valveType": "Butterfly Valve",
            "material": "Stainless Steel",
            "seatMaterial": "EPDM",
            "pressureRating": "150",
            "endConnection": "Lug"
        },
        "maxResults": 10
    }
    """
    try:
        if not jsonb_search_available:
            return jsonify({
                "success": False,
                "error": "JSONB search not available. Make sure jsonb_search.py and synonym_normalizer.py are in the database directory."
            }), 503
        
        data = request.get_json() or {}
        normalized_specs = data.get('normalizedSpecs', {})
        max_results = data.get('maxResults', 10)
        
        if not normalized_specs:
            return jsonify({
                "success": False,
                "error": "normalizedSpecs is required"
            }), 400
        
        print(f"🔍 API /search/jsonb called:")
        print(f"   - normalizedSpecs: {normalized_specs}")
        print(f"   - maxResults: {max_results}")
        
        # Extract valve type
        component_type = normalized_specs.get('valveType') or normalized_specs.get('componentType')
        
        # Normalize synonyms first
        if normalizer:
            normalized_specs = normalizer.normalize_specs(normalized_specs, component_type)
            print(f"   - Normalized specs: {normalized_specs}")
        
        # Search JSONB tables - exact match only (no relaxation)
        # If no results, LLM at application level should modify query and retry
        jsonb_results = search_jsonb_tiered(
            normalized_specs,
            component_type=component_type,
            max_results=max_results,
            relax_constraints=False  # Strict matching - let LLM handle relaxation
        )
        
        if not jsonb_results:
            return jsonify({
                "success": True,
                "matches": [],
                "bestMatch": None,
                "count": 0
            })
        
        # Format results for n8n compatibility
        formatted_matches = []
        for result in jsonb_results:
            metadata = result.get('metadata', {})
            if isinstance(metadata, str):
                try:
                    metadata = json.loads(metadata)
                except:
                    metadata = {}
            
            tech_specs = result.get('tech_specs', {})
            if isinstance(tech_specs, str):
                try:
                    tech_specs = json.loads(tech_specs)
                except:
                    tech_specs = {}
            
            formatted_matches.append({
                "id": result.get('id'),
                "sourceUrl": result.get('source_url'),
                "source_url": result.get('source_url'),
                "componentType": result.get('component_type'),
                "item": result.get('item'),
                "price": metadata.get('price') if isinstance(metadata, dict) else None,
                "starting_price": metadata.get('price') if isinstance(metadata, dict) else None,
                "description": metadata.get('title') if isinstance(metadata, dict) else None,
                "sku": metadata.get('sku') if isinstance(metadata, dict) else None,
                "score": result.get('score', 0),
                "tier": result.get('tier', 4),
                "techSpecs": tech_specs,
                "metadata": metadata
            })
        
        best_match = formatted_matches[0] if formatted_matches else None
        
        return jsonify({
            "success": True,
            "matches": formatted_matches,
            "bestMatch": best_match,
            "count": len(formatted_matches)
        })
    
    except Exception as e:
        print(f"❌ Error in /search/jsonb: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/valve/by-urls', methods=['POST'])
def get_valves_by_urls():
    """Fetch full valve specs by URLs. Takes array of sourceUrls and returns full details."""
    try:
        data = request.get_json() or {}
        source_urls = data.get('sourceUrls') or data.get('source_urls') or []
        
        if not source_urls or not isinstance(source_urls, list):
            return jsonify({
                "success": False,
                "error": "sourceUrls array is required"
            }), 400
        
        # Fetch specs for each URL
        from search_specs import get_specs_by_identifiers
        all_results = []
        for url in source_urls:
            if url:  # Skip empty URLs
                results = get_specs_by_identifiers(source_url=url)
                all_results.extend(results)
        
        # Deduplicate by id (in case same URL appears multiple times)
        seen_ids = set()
        unique_results = []
        for result in all_results:
            result_id = result.get('id')
            if result_id and result_id not in seen_ids:
                seen_ids.add(result_id)
                unique_results.append(result)
        
        # Format results (same format as /search/normalized)
        formatted_results = []
        for result in unique_results:
            formatted_result = {
                "id": result.get("id"),
                "sourceUrl": result.get("source_url"),
                "specSheetUrl": result.get("spec_sheet_url"),
                "sku": result.get("sku"),
                "valveType": result.get("valve_type"),
                "size": result.get("size_nominal"),
                "material": result.get("body_material"),
                "pressureClass": result.get("pressure_class"),
                "maxPressure": float(result.get("max_pressure")) if result.get("max_pressure") else None,
                "pressureUnit": result.get("pressure_unit"),
                "maxTemperature": float(result.get("max_temperature")) if result.get("max_temperature") else None,
                "temperatureUnit": result.get("temperature_unit"),
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
    redis_status = "connected" if redis_client and redis_client.ping() else "disconnected"
    return jsonify({
        "status": "ok",
        "redis": redis_status
    })


# ============================================================================
# Redis Cache Endpoints
# ============================================================================

@app.route('/cache/<path:key>', methods=['GET'])
def get_cache(key):
    """Get cache entry by key."""
    if not redis_client:
        return jsonify({
            "success": False,
            "error": "Redis not available"
        }), 503
    
    try:
        # Decode URL-encoded key
        decoded_key = unquote(key)
        value = redis_client.get(decoded_key)
        
        if value is None:
            return jsonify({
                "success": True,
                "found": False,
                "key": decoded_key
            })
        
        # Parse JSON value
        try:
            data = json.loads(value)
            return jsonify({
                "success": True,
                "found": True,
                "key": decoded_key,
                "data": data
            })
        except json.JSONDecodeError:
            # If not JSON, return as string
            return jsonify({
                "success": True,
                "found": True,
                "key": decoded_key,
                "data": value
            })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/cache/<path:key>', methods=['POST', 'PUT'])
def set_cache(key):
    """Set cache entry by key."""
    if not redis_client:
        return jsonify({
            "success": False,
            "error": "Redis not available"
        }), 503
    
    try:
        data = request.get_json() or {}
        
        # Decode URL-encoded key
        decoded_key = unquote(key)
        
        # Get TTL from request (optional, in seconds)
        ttl = data.get('ttl', 3600)  # Default: 1 hour
        cache_data = data.get('data', data)  # Support both {data: {...}} and direct {...}
        
        # Store as JSON string
        value = json.dumps(cache_data)
        redis_client.setex(decoded_key, ttl, value)
        
        return jsonify({
            "success": True,
            "key": decoded_key,
            "ttl": ttl,
            "message": "Cache entry stored"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/cache/<path:key>', methods=['DELETE'])
def delete_cache(key):
    """Delete cache entry by key."""
    if not redis_client:
        return jsonify({
            "success": False,
            "error": "Redis not available"
        }), 503
    
    try:
        # Decode URL-encoded key
        decoded_key = unquote(key)
        deleted = redis_client.delete(decoded_key)
        
        return jsonify({
            "success": True,
            "key": decoded_key,
            "deleted": deleted > 0
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/cache', methods=['GET'])
def list_cache():
    """List all cache keys (for a specific jobId prefix)."""
    if not redis_client:
        return jsonify({
            "success": False,
            "error": "Redis not available"
        }), 503
    
    try:
        # Get prefix from query parameter (e.g., ?prefix=cache_job_123)
        prefix = request.args.get('prefix', 'cache_')
        
        # Get all keys matching prefix
        keys = redis_client.keys(f"{prefix}*")
        
        return jsonify({
            "success": True,
            "prefix": prefix,
            "count": len(keys),
            "keys": keys
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================================
# Job-Specific Results Endpoints (for incremental streaming)
# ============================================================================

@app.route('/job/<path:job_id>/results', methods=['GET'])
def get_job_results(job_id):
    """Get accumulated results for a specific job."""
    if not redis_client:
        return jsonify({
            "success": False,
            "error": "Redis not available"
        }), 503
    
    try:
        # Decode URL-encoded job_id
        decoded_job_id = unquote(job_id)
        redis_key = f"job_{decoded_job_id}_results"
        
        # Get results from Redis
        value = redis_client.get(redis_key)
        
        if value is None:
            return jsonify({
                "success": True,
                "found": False,
                "jobId": decoded_job_id,
                "results": []
            })
        
        # Parse JSON value
        try:
            data = json.loads(value)
            # Ensure it's an array
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict) and 'results' in data:
                results = data['results']
            else:
                results = [data]
            
            return jsonify({
                "success": True,
                "found": True,
                "jobId": decoded_job_id,
                "results": results,
                "count": len(results)
            })
        except json.JSONDecodeError:
            return jsonify({
                "success": False,
                "error": "Invalid JSON in cache"
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/job/<path:job_id>/results', methods=['POST', 'PUT'])
def merge_job_result(job_id):
    """Add or update results in the job's accumulated results.
    
    Supports two modes:
    1. POST with 'results' (array): Replace entire results array
    2. POST with 'result' (object): Merge single result into existing array
    """
    if not redis_client:
        return jsonify({
            "success": False,
            "error": "Redis not available"
        }), 503
    
    try:
        data = request.get_json() or {}
        
        # Decode URL-encoded job_id
        decoded_job_id = unquote(job_id)
        redis_key = f"job_{decoded_job_id}_results"
        
        # Get TTL from request (optional, default 24 hours for job results)
        ttl = data.get('ttl', 86400)  # Default: 24 hours
        
        # Check if we're replacing the entire array or merging a single result
        if 'results' in data and isinstance(data['results'], list):
            # MODE 1: Replace entire results array (n8n sends merged array)
            existing_results = data['results']
            print(f"📦 Replacing entire results array with {len(existing_results)} items")
        else:
            # MODE 2: Merge single result (backward compatibility)
            new_result = data.get('result', data)  # Support both {result: {...}} and direct {...}
            
            if not isinstance(new_result, dict):
                return jsonify({
                    "success": False,
                    "error": "Result must be an object"
                }), 400
            
            # Get existing results from Redis
            existing_results = []
            value = redis_client.get(redis_key)
            if value:
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        existing_results = parsed
                    elif isinstance(parsed, dict) and 'results' in parsed:
                        existing_results = parsed['results']
                    else:
                        existing_results = [parsed]
                except json.JSONDecodeError:
                    existing_results = []
            
            # Merge logic: update if rowIndex exists, append if new
            new_row_index = new_result.get('rowIndex')
            if new_row_index is not None:
                # Find existing result with same rowIndex
                existing_index = -1
                for i, result in enumerate(existing_results):
                    if result.get('rowIndex') == new_row_index:
                        existing_index = i
                        break
                
                if existing_index >= 0:
                    # Update existing result
                    existing_results[existing_index] = new_result
                    print(f"🔄 Updated existing result at index {existing_index} (rowIndex: {new_row_index})")
                else:
                    # Append new result
                    existing_results.append(new_result)
                    print(f"➕ Added new result (rowIndex: {new_row_index}, total: {len(existing_results)})")
            else:
                # No rowIndex, just append
                existing_results.append(new_result)
                print(f"➕ Added new result (no rowIndex, total: {len(existing_results)})")
        
        # Sort by rowIndex to maintain order
        existing_results.sort(key=lambda r: r.get('rowIndex', 999999))
        
        # Store merged results back to Redis
        value = json.dumps(existing_results)
        redis_client.setex(redis_key, ttl, value)
        
        # Calculate summary
        matched_count = sum(1 for r in existing_results if r.get('bestMatch') or r.get('ValveMan_URL'))
        unmatched_count = len(existing_results) - matched_count
        
        return jsonify({
            "success": True,
            "jobId": decoded_job_id,
            "results": existing_results,
            "count": len(existing_results),
            "summary": {
                "totalRows": len(existing_results),
                "matchedRows": matched_count,
                "unmatchedRows": unmatched_count
            },
            "ttl": ttl,
            "message": "Results stored successfully"
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/job/<path:job_id>/results', methods=['DELETE'])
def clear_job_results(job_id):
    """Clear all results for a specific job."""
    if not redis_client:
        return jsonify({
            "success": False,
            "error": "Redis not available"
        }), 503
    
    try:
        # Decode URL-encoded job_id
        decoded_job_id = unquote(job_id)
        redis_key = f"job_{decoded_job_id}_results"
        
        deleted = redis_client.delete(redis_key)
        
        return jsonify({
            "success": True,
            "jobId": decoded_job_id,
            "deleted": deleted > 0
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 16000))
    app.run(host='0.0.0.0', port=port, debug=True)

