# Handling Multiple Domains in py-air-sviva-api

Based on analysis of the Postman collection and HAR files, the API uses different subdomains:

## Observed Patterns:
1. **Authentication Endpoints**: 
   - `air-api.sviva.gov.il/Account/GetApiToken` (Postman)
   - Likely also uses `air.sviva.gov.il` for some auth flows

2. **Envista API Endpoints**:
   - `air-papi.sviva.gov.il/v1/envista/` (HAR files and current implementation)
   - `air-api.sviva.gov.il/v1/envista/` (Postman collection)

## Recommended Implementation Approach:

### Option 1: Domain Mapping by Endpoint Group
Modify `air_sviva_api/const.py` to define domain mappings:

```python
# Domain mappings
AUTH_DOMAIN = "https://air-api.sviva.gov.il"  # or air.sviva.gov.il
ENVISTA_DOMAIN = "https://air-papi.sviva.gov.il"
MAIN_DOMAIN = "https://air.sviva.gov.il"

# Then define endpoints with their appropriate domain
GET_API_TOKEN_URL = f"{AUTH_DOMAIN}/Account/GetApiToken"
GENERATE_TOKEN_URL = f"{ENVISTA_DOMAIN}/v1/GenerateToken"
GET_REGIONS_URL = f"{ENVISTA_DOMAIN}/v1/envista/regions"
# etc.
```

### Option 2: Dynamic Domain Selection
Modify the `_build_url` function in `air_sviva_api/data.py` to select domain based on endpoint:

```python
DOMAIN_MAP = {
    'auth': 'https://air-api.sviva.gov.il',
    'envista': 'https://air-papi.sviva.gov.il',
    'main': 'https://air.sviva.gov.il'
}

ENDPOINT_DOMAINS = {
    'GetApiToken': 'auth',
    'GenerateToken': 'envista',
    'regions': 'envista',
    # ... map all endpoints to their domain
}

def _build_url(endpoint: str) -> str:
    """Build a full URL from an endpoint path with appropriate domain."""
    domain_key = ENDPOINT_DOMAINS.get(endpoint.split('/')[0], 'envista')  # default to envista
    base_url = DOMAIN_MAP[domain_key]
    return base_url + endpoint
```

### Option 3: Fallback Mechanism
Implement retry logic that tries alternative domains on specific errors (like 404 or DNS failures).

## Current Status:
The implementation now includes a fallback mechanism (Option 3) that automatically tries alternative domains when requests fail with specific error codes. This provides transparent handling of domain variability without requiring changes to endpoint configurations.

The authentication flow has been fixed to use the correct domains as observed in the Postman collection, and all API requests now benefit from automatic fallback between `air-papi.sviva.gov.il` and `air-api.sviva.gov.il` when encountering retryable errors (404, 500, 502, 503, 504).

This approach maintains backward compatibility while providing resilience against domain-specific issues.