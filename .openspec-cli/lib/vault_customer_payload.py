#!/usr/bin/env python3
"""
vault_customer_payload.py — v3
Builds the JSON payload for POST /v1/customers
Usage: python3 vault_customer_payload.py [first_name] [last_name]

Cambios v3:
- Se quita el array "identifiers[]" -- Vault rechazaba
  "CUSTOMER_IDENTIFIER_TYPE_EXTERNAL" como valor invalido y no hay
  documentacion del enum exacto esperado. En su lugar se usa
  "external_customer_id" dentro de customer_details, que si aparece
  documentado en el schema de Core_Api.json y no requiere un enum.
"""
import sys
import json
import uuid

first_name = sys.argv[1] if len(sys.argv) > 1 else "OpenSpec"
last_name = sys.argv[2] if len(sys.argv) > 2 else "TestCustomer"
customer_id = str(uuid.uuid4())

payload = {
    "request_id": str(uuid.uuid4()),
    "customer": {
        "id": customer_id,
        "status": "CUSTOMER_STATUS_ACTIVE",
        "customer_details": {
            "title": "CUSTOMER_TITLE_UNKNOWN",
            "first_name": first_name,
            "last_name": last_name,
            "dob": "1990-01-01",
            "gender": "CUSTOMER_GENDER_UNKNOWN",
            "nationality": "GB",
            "email_address": f"{first_name.lower()}.{last_name.lower()}@openspec.test",
            "contact_method": "CUSTOMER_CONTACT_METHOD_EMAIL",
            "external_customer_id": f"openspec-{customer_id[:8]}",
        },
    },
}

print(json.dumps(payload, indent=2))
