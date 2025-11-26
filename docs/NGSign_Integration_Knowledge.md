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
-   **Credentials**: Uses `Login` and `Password` stored in Odoo System Parameters.
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

## 4. Data Mapping (TEIF)

The integration maps Odoo `account.move` fields to the **Tunisian Electronic Invoice Format (TEIF)** JSON structure.

| Odoo Field | TEIF Field | Description |
| :--- | :--- | :--- |
| `name` | `documentIdentifier` | Invoice Number |
| `invoice_date` | `invoiceDate` | Date of issuance |
| `partner_id.name` | `clientDetails.partnerName` | Client Name |
| `partner_id.vat` | `clientDetails.partnerIdentifier` | Client Tax ID (Matricule Fiscal) |
| `amount_untaxed` | `invoiceTotalWithoutTax` | Total amount excluding tax |
| `amount_tax` | `invoiceTotalTax` | Total tax amount |
| `amount_total` | `invoiceTotalWithTax` | Total amount including tax |

**Invoice Lines (`items`):**
-   `name` -> `name`
-   `product_id.default_code` -> `code`
-   `quantity` -> `quantity`
-   `price_unit` -> `unitPrice`
-   `price_subtotal` -> `totalPrice`
-   `tax_ids` -> `tvaRate` (Simplified mapping)

## 5. Configuration Parameters

The following parameters are stored in `ir.config_parameter`:

-   `ngsign.api_url`: Base URL of the API (e.g., `https://api.ng-sign.com`).
-   `ngsign.login`: API Username.
-   `ngsign.password`: API Password.
-   `ngsign.passphrase`: Passphrase for the SEAL certificate (required for `/seal` endpoint).
-   `ngsign.signer_email`: (Optional) Email for delegated signing flows.
