# CF Cookie Solver
Cloudflare Turnstile solver — returns `cf_clearance` cookie via REST API.

## Endpoint
`POST /solve` with header `x-secret: <API_SECRET>`
```json
{"url": "https://example.com"}
```
Returns: `{"cf_clearance": "...", "user_agent": "..."}`
