# NGSign API Usage in Odoo Module

This document outlines the NGSign e-Invoice API endpoints integrated into this Odoo module.

## Base URL
The base URL is configured in Odoo Settings.
- Sandbox: `https://sandbox.ng-sign.com/server`
- Production: `https://ngsign.app/server` (or similar)

## Authentication
Most endpoints require a Bearer Token, configured in Odoo Settings.
- Header: `Authorization: Bearer <TOKEN>`

## Endpoints

### 1. Create & Sign Transaction (SEAL)
**Method:** `POST`
**Endpoint:** `/protected/invoice/transaction/seal`
**Purpose:** Uploads one or more invoices to be signed using the server-side SEAL certificate.
**Used In:** `account_move.py` -> `action_sign_ngsign`

**Payload Structure:**
```json
{
    "invoices": [
        {
            "invoiceFileB64": "<Base64 Encoded PDF>",
            "clientEmail": "client@example.com",
            "invoiceTIEF": { ... TEIF JSON Object ... },
            "configuration": { ... QR/Text Position Config ... }
        }
    ],
    "passphrase": "<SEAL Passphrase>",
    "notifyOwner": true,
    "ccEmail": "optional@example.com"
}
```

**Response:**
Returns a transaction object containing a Transaction UUID and a list of Invoice UUIDs.

### 2. Check Transaction Status (Public)
**Method:** `GET`
**Endpoint:** `/any/invoice/{transaction_uuid}`
**Purpose:** Checks the status of all invoices within a transaction without requiring authentication.
**Used In:** `account_move.py` -> `action_check_ngsign_status`

**Response:**
Returns a JSON object containing the status of the transaction and a list of invoices with their individual statuses (`SIGNED`, `CANCELLED`, `TTN_SIGNED`, etc.) and TTN references.

### 3. Download Signed PDF
**Method:** `GET`
**Endpoint:** `/protected/invoice/pdf/{invoice_uuid}`
**Purpose:** Downloads the final signed PDF for a specific invoice.
**Used In:** `account_move.py` -> `action_check_ngsign_status`

**Response:**
Returns a JSON object containing the Base64 encoded PDF.
```json
{
    "object": "<Base64 Encoded PDF Content>",
    "message": null,
    "errorCode": 0
}
```

### 4. Check Invoice Status (Protected - Legacy)
**Method:** `POST`
**Endpoint:** `/protected/invoice/check/{invoice_uuid}`
**Purpose:** Checks the status of a specific invoice using its UUID. Requires authentication.
**Used In:** `ngsign_client.py` (Method `check_status`, currently fallback/legacy use).

### 5. Get Transaction Details (Legacy)
**Method:** `GET`
**Endpoint:** `/any/invoice/{invoice_uuid}`
**Purpose:** Retrieves details of a transaction/invoice.
**Used In:** `ngsign_client.py` (Method `get_transaction_details`, currently unused/helper).
