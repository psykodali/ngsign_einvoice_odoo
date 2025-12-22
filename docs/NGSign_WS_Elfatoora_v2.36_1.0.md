# NGSign Web Services (Fatoora) Integration Documentation

This documentation provides the technical specifications for integrating with the **NGSign Web Service (Fatoora)**. It is designed to handle the generation, digital signing, and submission of invoices in compliance with the **Tunisian Electronic Invoice Format (TEIF)** and **Tunisie TradeNet (TTN)**.

---

## 1. General Information
*   **Product Version:** NGSign 2.36
*   **Protocol:** REST API
*   **Data Format:** JSON (Input/Output)
*   **Base URL Context:** `/protected/invoice/`

---

## 2. Authentication
All endpoints require a **JSON Web Token (JWT)** obtained from the NGSign Web Application.
*   **Mechanism:** Bearer Authentication
*   **Header:** `Authorization: Bearer <your_token>`
*   **Note:** Tokens do not expire unless regenerated. Generating a new token invalidates the previous one.

---

## 3. Standard Response Structure
All successful responses (HTTP 200) follow this JSON structure:
```json
{
  "object": { ... }, // The actual payload
  "errorCode": null,  // Error code if applicable
  "message": "..."    // Status message
}
```
*   **HTTP 200:** Success.
*   **HTTP 400:** Request error or server error (includes a detailed error message).

---

## 4. Key Workflows

### A. Manual Signing (User Intervention)
1.  **Submit Invoice:** Call `create/transaction` to send invoice data.
2.  **Get Signing URL:** The API returns a URL.
3.  **User Signs:** The user visits the URL to sign using a USB token or DigiGo.
4.  **TTN Submission:** NGSign automatically forwards the signed XML to TTN.

### B. Automated Signing (SEAL)
1.  **Submit Invoice:** Call `transaction/seal` with the `passphrase` for the electronic seal.
2.  **Automatic Processing:** NGSign signs the invoice server-side and submits it to TTN immediately.

---

## 5. API Endpoints

### 5.1 Transaction Creation
| Endpoint | Method | Input Object | Description |
| :--- | :--- | :--- | :--- |
| `transaction/` | POST | `[]` (List of Invoices) | Basic transaction for current user to sign. |
| `v2/transaction/` | POST/GET | `NGInvoiceUpload` | V2 transaction with richer response metadata. |
| `transaction/advanced/` | POST | `NGAdvancedInvoiceUpload` | Delegate signature to a specific email. |
| `v2/transaction/advanced/` | POST | `NGAdvancedInvoiceUpload` | V2 Delegate signature with full visibility. |
| `transaction/seal/` | POST | `NGAdvancedInvoiceUpload` | Fully automated server-side sealing. |

### 5.2 Transaction Management
| Endpoint | Method | Input | Description |
| :--- | :--- | :--- | :--- |
| `transaction/cancel/{uuid}` | POST | Transaction UUID | Cancels a batch of invoices (if not yet signed). |
| `cancel/{uuid}` | POST | Invoice UUID | Cancels a specific single invoice. |
| `check/{uuid}` | POST | Invoice UUID | Forces a status check with the TTN server. |
| `pdf/{uuid}` | GET | Invoice UUID | Returns the Base64 encoding of the signed PDF. |
| `{uuid}` | GET | Transaction UUID | Returns full metadata and status for a transaction. |

---

## 6. Data Models (JSON Objects)

### 6.1 `NGInvoiceUpload`
| Field | Type | Required | Description |
| :--- | :--- | :--- | :--- |
| `invoiceFileB64` | String | Yes (V1) | Base64 PDF file. Optional in V2. |
| `type` | String | Yes | Invoice type (e.g., `I-11` for Facture). |
| `clientEmail` | String | No | Email to receive the final signed PDF. |
| `configuration` | Object | Yes | `InvoiceConfiguration` (Positioning of QR/Label). |
| `invoiceTIEF` | Object | Yes | `TEIFInvoice` (The structured invoice data). |

### 6.2 `InvoiceConfiguration`
Used to position the TTN 2D-Doc/QR code on the PDF.
*   **qrPositionX / qrPositionY:** (int) Coordinates for the QR stamp.
*   **qrPositionP:** (int) Page number (0 for the first page).
*   **allPages:** (boolean) Add QR to all pages.

### 6.3 `TEIFInvoice` (Core Data)
This is the structured content required by TTN.
| Field | Type | Description |
| :--- | :--- | :--- |
| `clientIdentifier` | String | Tunisian Fiscal ID (Pattern matching required). |
| `documentIdentifier` | String | Your internal invoice reference. |
| `invoiceDate` | Date | Issuance date. |
| `items` | List | Array of `InvoiceItem` objects. |
| `invoiceTotalWithTax` | BigDecimal | Total amount including taxes. |
| `paymentDetails` | List | Array of `PytSeg` (Payment information). |

---

## 7. Important Enumerations

### 7.1 Invoice Statuses
*   `CREATED`: Stored in NGSign, not yet signed.
*   `SIGNED`: Signed by supplier, pending TTN transfer.
*   `TTN_TRANSFERED`: Sent to TTN.
*   `TTN_SIGNED`: Process complete, final invoice available for download.
*   `TTN_REJECTED`: Rejected by the TTN platform.

### 7.2 Common Type Codes
*   **Invoice Types:** `I-11` (Facture), `I-12` (Avoir), `I-15` (Export).
*   **Payment Means:** `I-131` (Cash), `I-132` (Check), `I-135` (Transfer).
*   **Allowance Types:** `I-151` (Discount), `I-153` (Rebate).

---

## 8. Error Codes

| Code | Label | Description |
| :--- | :--- | :--- |
| 101 | `MISSING_PDF_ERROR` | PDF file must be provided for this call. |
| 105 | `TRANSACTION_SIGNED_ERROR` | Action failed because transaction is already signed. |
| 113 | `INVALID_CONFIGURATION` | QR/Label positioning is invalid. |
| 255 | `PDF_BAD_ENCODING` | The provided Base64 string is not a valid PDF. |
| 50001| `INVALID_XML_ENCODING` | The generated TEIF XML failed validation. |

---

## 9. Implementation Notes for AI
1.  **Coordinates:** When positioning the QR code (`qrPositionX/Y`), `0,0` usually refers to the bottom-left of the PDF page.
2.  **V1 vs V2:** Always prefer **V2** endpoints if the client version supports it, as V2 returns the `NGXMLInvoiceTransaction.uuid` directly for easier tracking.
3.  **Base64:** Ensure PDF files are properly sanitized before Base64 encoding to avoid upload errors.

## 10.NGSign Fatoora Web Services API - Data Dictionary
{
  "__meta__": {
    "title": "NGSign Fatoora Web Services API - Data Dictionary",
    "version": "2.36",
    "description": "Unified definition of all objects. Values format: [Type] | [Requirement] | [Description]"
  },
  "API_INPUT_OBJECTS": {
    "NGInvoiceUpload": {
      "description": "Main object for uploading a single invoice (V1 and V2)",
      "fields": {
        "invoiceFileB64": "String | Required (V1), Optional (V2) | Base64 encoded PDF file. If omitted in V2, client must render PDF manually.",
        "type": "String | Optional | Invoice type code. Default: 'I-11' (Facture). See Enumerations.InvoiceType.",
        "clientEmail": "String | Optional | Email to receive the signed PDF.",
        "configuration": "InvoiceConfiguration | Required | Configuration for the visual security elements (QR/Label).",
        "invoiceTIEF": "TEIFInvoice | Required | The structured invoice data compliant with Tunisian regulations.",
        "callbackUrl": "NGCallbackUrl | Optional | URLs for asynchronous status updates (Success/Failure)."
      }
    },
    "NGAdvancedInvoiceUpload": {
      "description": "Object for batch transactions, delegated signing, or automated SEAL signing",
      "fields": {
        "invoices": "List<NGInvoiceUpload> | Required | Array of invoice objects to be processed.",
        "signerEmail": "String | Optional | Email of the specific user to whom signature is delegated.",
        "passphrase": "String | Conditional | Mandatory ONLY for 'transaction/seal' endpoint. Decrypts the SEAL certificate.",
        "notifyOwner": "Boolean | Optional | If true, the API caller receives the final email.",
        "ccEmail": "String | Optional | Email address to CC the final PDF."
      }
    },
    "TEIFInvoice": {
      "description": "The core structured data representing the Legal Electronic Invoice (TEIF)",
      "fields": {
        "clientIdentifier": "String | Required | Fiscal Identifier (Matricule Fiscale). Must match regex (Length 8 or 9).",
        "clientDetails": "PartnerDetails | Required | Detailed info about the client/buyer.",
        "documentIdentifier": "String | Required | Internal Invoice Number.",
        "documentReferences": "List<Reference> | Optional | List of related documents (orders, delivery notes).",
        "documentType": "String | Optional | Default: 'I-11'. See Enumerations.InvoiceType.",
        "invoiceDate": "Date | Required | Issuance date (YYYY-MM-DD).",
        "comments": "List<String> | Optional | Max 500 chars per line.",
        "accountNumber": "String | Optional | Bank account number. Max 20 chars. Highly recommended for public sector.",
        "institutionName": "String | Optional | Financial institution name. Max 70 chars.",
        "conditions": "List<String> | Optional | Special conditions. Max 200 chars.",
        "items": "List<InvoiceItem> | Required | List of products or services.",
        "invoiceTotalWithoutTax": "BigDecimal | Required | Total HT (Excluding Tax).",
        "invoiceTotalWithTax": "BigDecimal | Required | Total TTC (Including Tax).",
        "invoiceTotalTax": "BigDecimal | Required | Total Tax amount.",
        "amountServicesIncludingTax": "BigDecimal | Optional | Total of service items (TTC).",
        "amountServicesExcludingTax": "BigDecimal | Optional | Total of service items (HT).",
        "invoiceTotalinLetters": "String | Optional | Total amount in words. Max 500 chars.",
        "stampTax": "BigDecimal | Optional | Timbre Fiscal (usually 1.000 TND).",
        "totalDiscount": "BigDecimal | Optional | Total global discount.",
        "amountExempt": "AmountExempt | Optional | Details if tax exemption applies.",
        "currencyIdentifier": "String | Optional | Default: 'TND'.",
        "paymentDetails": "List<PytSeg> | Optional | Payment terms and segments.",
        "alcDetails": "List<AlcDetails> | Optional | Allowance or Charge details."
      }
    }
  },
  "SUB_OBJECT_DEFINITIONS": {
    "InvoiceConfiguration": {
      "description": "Coordinates for the TTN QR Code (2D-Doc) and Label on the PDF",
      "fields": {
        "qrPositionX": "Integer | Required | X coordinate for 2D-Doc (0 = left).",
        "qrPositionY": "Integer | Required | Y coordinate for 2D-Doc (0 = bottom).",
        "qrPositionP": "Integer | Required | Page number for 2D-Doc (0 = Page 1).",
        "labelPositionX": "Integer | Required | X coordinate for TTN Label.",
        "labelPositionY": "Integer | Required | Y coordinate for TTN Label.",
        "labelPositionP": "Integer | Required | Page number for TTN Label.",
        "qrRatio": "Float | Optional | Scaling ratio. Default: 0.5.",
        "textPositionX": "Integer | Optional | X pos for 'Copie de la facture...'.",
        "textPositionY": "Integer | Optional | Y pos for 'Copie de la facture...'.",
        "textPage": "Integer | Optional | Page for 'Copie de la facture...'.",
        "allPages": "Boolean | Optional | Default: false. If true, adds QR to all pages."
      }
    },
    "InvoiceItem": {
      "fields": {
        "name": "String | Required | Item name. Max 500 chars.",
        "code": "String | Required | Item code. Max 35 chars.",
        "unit": "String | Optional | Unit of measure. Default: 'UNIT'. Max 8 chars.",
        "quantity": "BigDecimal | Required | Quantity.",
        "tvaRate": "Float | Required | VAT Rate (e.g., 19.0).",
        "currencyIdentifier": "String | Optional | Default: 'TND'.",
        "taxes": "List<Tax> | Optional | Other taxes (Fodec, etc.).",
        "itemAlc": "ItemAlcDetail | Optional | Allowances specific to this item.",
        "discountPercentage": "Float | Optional | Discount %.",
        "discount": "BigDecimal | Optional | Discount amount.",
        "unitPrice": "BigDecimal | Required | Price per unit.",
        "totalPrice": "BigDecimal | Required | Total line price.",
        "service": "Boolean | Optional | True if item is a service."
      }
    },
    "PartnerDetails": {
      "fields": {
        "partnerIdentifier": "String | Required | Fiscal ID (Matricule). Max 35 chars.",
        "partnerName": "String | Required | Name/Reason Social. Max 200 chars.",
        "address": "InvoiceAddress | Required | Address object.",
        "partnerReference": "String | Optional | Internal reference. Max 200 chars."
      }
    },
    "InvoiceAddress": {
      "fields": {
        "description": "String | Required | Full address text. Max 500 chars.",
        "street": "String | Optional | Street name. Max 35 chars.",
        "cityName": "String | Optional | City. Max 35 chars.",
        "postalCode": "String | Optional | Zip code. Max 17 chars.",
        "country": "String | Optional | ISO 3166-1 Code (e.g., TN). Max 6 chars."
      }
    },
    "PytSeg": {
      "description": "Payment Segment",
      "fields": {
        "pyt": "Pyt | Optional | Payment Terms info.",
        "pytDtm": "Dtm | Optional | Date related to payment.",
        "amount": "BigDecimal | Optional | Payment amount.",
        "amountType": "String | Optional | Enum from AmountType.",
        "currencyIdentifier": "String | Optional | Default 'TND'.",
        "pytPai": "Pai | Optional | Payment Instructions.",
        "pytFii": "Fii | Optional | Financial Institution Info."
      }
    },
    "Pyt": {
      "fields": {
        "paiConditionCode": "String | Required | Enum. Max 6 chars.",
        "paymentTearmsDescription": "String | Optional | Max 500 chars."
      }
    },
    "Pai": {
      "fields": {
        "paiConditionCode": "String | Required | Enum (Payment Conditions). Max 6 chars.",
        "paiMeansCode": "String | Required | Enum (Payment Means). See Enumerations."
      }
    },
    "Fii": {
      "fields": {
        "accountHolder": "AccountHolder | Required | Account owner info.",
        "institutionIdentification": "InstitutionIdentification | Required | Bank info.",
        "country": "String | Optional | Country code.",
        "functionCode": "String | Required | Enum (FinancialInstitution). See Enumerations."
      }
    },
    "AccountHolder": {
      "fields": {
        "accountNumber": "String | Required | RIB/IBAN. Max 20 chars (Non-null).",
        "ownerIdentifier": "String | Optional | Max 70 chars."
      }
    },
    "InstitutionIdentification": {
      "fields": {
        "branchIdentifier": "String | Optional | Max 17 chars.",
        "institutionName": "String | Optional | Max 70 chars.",
        "nameCode": "String | Optional | Max 11 chars (Min 1)."
      }
    },
    "Tax": {
      "fields": {
        "taxTypeName": "TaxTypeName | Required | Tax type definition.",
        "taxCategory": "String | Optional | Category.",
        "taxDetails": "TaxRateDetail | Required | Rate details."
      }
    },
    "TaxTypeName": {
      "fields": {
        "code": "String | Required | Tax code.",
        "value": "String | Required | Tax name/value."
      }
    },
    "TaxRateDetail": {
      "fields": {
        "taxRate": "String | Required | The rate value.",
        "taxRateBasis": "String | Optional | Basis for tax. Max 35 chars."
      }
    },
    "AmountExempt": {
      "fields": {
        "totalExempt": "BigDecimal | Optional | Total amount exempted.",
        "totalExemptDesc": "String | Optional | Description. Max 200 chars."
      }
    },
    "Reference": {
      "fields": {
        "value": "String | Required | Reference value. Max 200 chars.",
        "refID": "String | Required | Regex: 'I-8[0-9]|I-81[1-7]'.",
        "date": "Date | Optional | Reference date."
      }
    },
    "NGCallbackUrl": {
      "fields": {
        "successUrl": "String | Optional | URL called on success.",
        "failureUrl": "String | Optional | URL called on failure/cancellation."
      }
    },
    "Dtm": {
      "fields": {
        "dateCode": "String | Required | See Dates Enumeration.",
        "date": "Date | Required | The date value."
      }
    },
    "AlcDetails": {
      "fields": {
        "alc": "Boolean | Required | Allowance (true) or Charge (false).",
        "moa": "MoaDetails | Required | Monetary amount.",
        "comments": "List<String> | Optional | Comments.",
        "taxAlc": "Boolean | Optional | Tax applicability."
      }
    },
    "ItemAlcDetail": {
      "fields": {
        "alc": "Boolean | Required | Allowance or Charge.",
        "pcd": "Pcd | Required | Percentage details.",
        "comments": "List<String> | Optional | Comments."
      }
    },
    "Pcd": {
      "fields": {
        "percentage": "String | Required | Max 5 chars.",
        "percentageBasis": "String | Required | Max 35 chars."
      }
    }
  },
  "API_RESPONSE_OBJECTS": {
    "NGInvoiceTransaction": {
      "description": "Returned by /transaction endpoints",
      "fields": {
        "uuid": "String | Output | Transaction Unique ID.",
        "invoices": "List<NGInvoice> | Output | List of processed invoices.",
        "creationDate": "Date | Output | Creation timestamp.",
        "status": "String | Output | See InvoiceStatus Enum.",
        "signingTime": "Date | Output | Time of signature."
      }
    },
    "NGInvoice": {
      "description": "Detailed invoice status object",
      "fields": {
        "uuid": "String | Output | Invoice Unique ID.",
        "status": "String | Output | Invoice status.",
        "ttnReference": "String | Output | The generated TTN reference (Legal Proof).",
        "invoiceNumber": "String | Output | Internal number.",
        "twoDocImage": "Byte[] | Output | QR Code raw data.",
        "withPDF": "Boolean | Output | Does NGSign have the PDF?"
      }
    }
  },
  "ENUMERATIONS": {
    "InvoiceStatus": {
      "CREATED": "Created in NGSign, not yet signed.",
      "SIGNED": "Signed by supplier, waiting for TTN transfer.",
      "CANCELLED": "Cancelled by user.",
      "TTN_TRANSFERED": "Sent to TTN.",
      "TTN_SIGNED": "Final Success. Signed by TTN.",
      "TTN_REJECTED": "Rejected by TTN."
    },
    "InvoiceType": {
      "I-11": "Facture (Invoice)",
      "I-12": "Facture d'avoir (Credit Note)",
      "I-13": "Note d'honoraire",
      "I-14": "Décompte (Public Market)",
      "I-15": "Facture Export",
      "I-16": "Bon de commande"
    },
    "PaymentMeans": {
      "I-131": "Espèce (Cash)",
      "I-132": "Chèque (Check)",
      "I-133": "Chèque certifié",
      "I-134": "Prélèvement bancaire (Direct Debit)",
      "I-135": "Virement bancaire (Bank Transfer)",
      "I-136": "Any bank",
      "I-137": "Other"
    },
    "AllowanceType": {
      "I-151": "Réduction",
      "I-152": "Ristourne",
      "I-153": "Rabais"
    },
    "FinancialInstitution": {
      "I-141": "Poste",
      "I-142": "Banque",
      "I-143": "Autre"
    },
    "Dates": {
      "I-31": "Date d'émission",
      "I-32": "Date limite de paiement",
      "I-34": "Date d'expiration"
    }
  }
}