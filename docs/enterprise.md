# Enterprise services

Core mail works without a license. Paid capabilities (hosted spam filtering) require activation at `/ops/enterprise/`.

## Data flow

Hosted filtering sends MIME bytes and envelope fields to the vendor API. The portal never sends Resend API keys, passwords, or other users' mail.

## Mock vendor

`python -m mock_vendor` runs a local stub. It is **not** production spam detection.

## Remaining for paid launch

Billing, license issuance, production classifier, key rotation, SLA, DPA, abuse handling, vendor rate limits, monitoring.
