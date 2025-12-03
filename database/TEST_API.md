# Testing the API Server

## Health Check

Test if the server is running:

```bash
curl http://localhost:6000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

## Test Search Endpoint

### Basic Search

```bash
curl -X POST http://localhost:6000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "Gate Valve",
      "size": "1/2",
      "material": "Carbon Steel",
      "pressureRating": "800",
      "endConnection": "Socket-weld"
    },
    "maxResults": 10
  }'
```

### Search Without End Connection

```bash
curl -X POST http://localhost:6000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "Gate Valve",
      "size": "1/2",
      "material": "Carbon Steel",
      "pressureRating": "800"
    },
    "maxResults": 5
  }'
```

### Search with Just Valve Type

```bash
curl -X POST http://localhost:6000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "Ball Valve"
    },
    "maxResults": 5
  }'
```

### Search with Abbreviations (to test compatibility mappings)

```bash
curl -X POST http://localhost:6000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "GT",
      "size": "1/2",
      "material": "CS",
      "endConnection": "SW"
    },
    "maxResults": 5
  }'
```

## Pretty Print JSON Output

Add `| python3 -m json.tool` or `| jq` to format the output:

```bash
curl -X POST http://localhost:6000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "Gate Valve",
      "size": "1/2"
    },
    "maxResults": 5
  }' | python3 -m json.tool
```

## Test on Remote Server

If testing on a remote server, replace `localhost` with the server IP:

```bash
curl http://52.10.49.140:6000/health
```

```bash
curl -X POST http://52.10.49.140:6000/search/normalized \
  -H "Content-Type: application/json" \
  -d '{
    "normalizedSpecs": {
      "valveType": "Gate Valve",
      "size": "1/2"
    },
    "maxResults": 5
  }'
```

## Expected Response Format

```json
{
  "success": true,
  "count": 5,
  "results": [
    {
      "id": 12345,
      "sourceUrl": "https://valveman.com/products/...",
      "specSheetUrl": "https://valveman.com/content/...",
      "sku": "ABC123",
      "valveType": "Gate Valve",
      "size": "1/2",
      "material": "Carbon Steel",
      "pressureClass": "800",
      "endConnection": "Socket Welded",
      "price": 55.99,
      "msrp": 66.86,
      "spec": {...},
      "priceInfo": {...}
    }
  ]
}
```

## Troubleshooting

### Connection Refused

```bash
# Check if server is running
./start_api_server.sh status

# Check if port is in use
lsof -i :6000
```

### Empty Results

- Check database connection: `python3 test_connection.py`
- Verify .env file has correct credentials
- Try a simpler search (just valveType)

### Timeout

- Check server logs: `tail -f api_server.log`
- Verify database connection is working
- Check firewall rules if testing remotely



