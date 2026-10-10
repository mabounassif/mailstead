# Enterprise API v1 (contract)

Versioned HTTPS API between Mailstead and the vendor.

## POST /v1/activate

Request: `{license_key, installation_id, domains, client_version}`

Response: `{service_credential, entitlement_token}`

## POST /v1/entitlements/refresh

Bearer: service credential

Response: `{entitlement_token}`

## POST /v1/spam/classify

Bearer: service credential

Request: `{message_id, mime_b64 | mime_sha256+mime_b64, envelope{from,to}, auth_results}`

Response: `{verdict, score, reasons[], service, engine_version, model_version}`

## POST /v1/spam/feedback

Request: `{message_id, label}`

## Errors

401 invalid credential, 402 not entitled, 403 scope, 429 limits, 503 unavailable.
