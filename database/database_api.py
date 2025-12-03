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
    """Add or update a result in the job's accumulated results."""
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
        
        # Get new result from request
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
            else:
                # Append new result
                existing_results.append(new_result)
        else:
            # No rowIndex, just append
            existing_results.append(new_result)
        
        # Sort by rowIndex to maintain order
        existing_results.sort(key=lambda r: r.get('rowIndex', 999999))
        
        # Get TTL from request (optional, default 24 hours for job results)
        ttl = data.get('ttl', 86400)  # Default: 24 hours
        
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
            "message": "Result merged successfully"
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
    port = int(os.getenv('PORT', 6000))
    app.run(host='0.0.0.0', port=port, debug=True)

