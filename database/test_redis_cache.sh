#!/bin/bash
# Test Redis cache endpoints

API_URL="${API_URL:-http://localhost:6000}"

echo "🧪 Testing Redis Cache Endpoints"
echo "API URL: $API_URL"
echo ""

# Test 1: Health check
echo "1️⃣ Testing health endpoint..."
HEALTH=$(curl -s "$API_URL/health")
echo "Response: $HEALTH"
echo ""

# Test 2: Set cache
echo "2️⃣ Testing SET cache..."
SET_RESPONSE=$(curl -s -X POST "$API_URL/cache/test_key_123" \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "matches": [{"url": "https://example.com", "price": 99.99}],
      "bestMatch": {"url": "https://example.com", "price": 99.99},
      "timestamp": "2025-01-01T00:00:00Z"
    },
    "ttl": 3600
  }')
echo "Response: $SET_RESPONSE"
echo ""

# Test 3: Get cache
echo "3️⃣ Testing GET cache..."
GET_RESPONSE=$(curl -s "$API_URL/cache/test_key_123")
echo "Response: $GET_RESPONSE"
echo ""

# Test 4: List cache keys
echo "4️⃣ Testing LIST cache keys..."
LIST_RESPONSE=$(curl -s "$API_URL/cache?prefix=cache_")
echo "Response: $LIST_RESPONSE"
echo ""

# Test 5: Delete cache
echo "5️⃣ Testing DELETE cache..."
DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/cache/test_key_123")
echo "Response: $DELETE_RESPONSE"
echo ""

echo "✅ Test complete!"






