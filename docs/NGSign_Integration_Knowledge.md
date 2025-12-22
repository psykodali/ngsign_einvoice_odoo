# NGSign API Integration Knowledge

This document provides a technical overview of the NGSign e-invoice integration implemented in Odoo.

## 1. Architecture Overview

The integration connects Odoo with the NGSign API to perform the following operations:
1.  **Authentication**: Obtains a JWT token for secure communication.
2.  **Transaction Creation (SEAL)**: Sends invoice data (TEIF) and PDF to NGSign for electronic sealing and TTN submission.
3.  **Status Polling**: Checks the status of the transaction.
4.  **Document Retrieval**: Downloads the final signed PDF enriched with the TTN QR code.

## 2. Authentication

-   **Method**: JWT (JSON Web Token) Bearer Token.
-   **Endpoint**: `POST /login` (Configurable base URL).
-   **Header**: `Authorization: Bearer <token>` is added to all subsequent requests.

## 3. Key API Endpoints

### 3.1 Create SEAL Transaction
Creates a new signing transaction using the organization's server stamp (SEAL).

-   **Endpoint**: `POST /protected/invoice/transaction/seal`
-   **Payload**:
    ```json
    {
      "invoices": [
        {
          "invoiceFileB64": "<base64_pdf>",
          "invoiceTIEF": { ...TEIF_JSON_Structure... }
        }
      ],
      "passphrase": "<seal_passphrase>"
    }
    ```
-   **Response**: Returns a transaction object containing the `uuid`.

### 3.2 Get Transaction Details (Status Check)
Retrieves the current status of the transaction and its invoices.

-   **Endpoint**: `GET /any/invoice/{transaction_uuid}`
-   **Response**:
    ```json
    {
      "uuid": "{transaction_uuid}",
      "status": "...",
      "invoices": [
        {
          "uuid": "{invoice_uuid}",
          "status": "TTN_SIGNED", 
          ...
        }
      ]
    }
    ```
-   **Key Statuses**:
    -   `TTN_SIGNED`: Successfully processed and signed by TTN.
    -   `TTN_REJECTED`: Rejected by TTN.
    -   `CANCELED`: Canceled transaction.

### 3.3 Download Signed PDF
Downloads the final PDF file which includes the TTN QR code (2D-Doc) and reference.

-   **Endpoint**: `GET /protected/invoice/pdf/{invoice_uuid}`
-   **Response**: Binary PDF content.