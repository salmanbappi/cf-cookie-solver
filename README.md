# CF Cookie Solver
Cloudflare Turnstile solver using CloakBrowser (C++ source-level stealth Chromium).

## Endpoint
`POST /solve` with header `x-secret: <API_SECRET>`
```json
{"url": "https://example.com"}
```
Returns: `{"cf_clearance": "...", "user_agent": "..."}`
