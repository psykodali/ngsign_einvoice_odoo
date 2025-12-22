This document details the data mapping required to integrate **Odoo 18** with the **NGSign/Fatoora** e-invoicing API.

The mapping combines the **JSON Schema** from the NGSign API documentation (PDF 1) with the functional definitions and code lists from the **TEIF (Tunisian Electronic Invoice Format)** specifications (PDF 2).

---

## 1. High-Level Integration Workflow

1.  **Odoo Action:** User clicks "Confirm" on an Invoice (`account.move`).
2.  **Odoo Process:**
    *   Generate the standard PDF invoice.
    *   Extract data from `account.move` to build the `TEIFInvoice` JSON object.
    *   Authenticate with NGSign (JWT).
    *   Call `POST /api/invoice/v2/transaction/`.
3.  **Response:** Store the returned `uuid` and `ttnReference` in Odoo.

---

## 2. Main Request Object: `NGInvoiceUpload`

This is the wrapper object sent to the API.

| JSON Field | Type | Odoo 18 Mapping / Logic | TEIF Ref |
| :--- | :--- | :--- | :--- |
| `invoiceFileB64` | String | **Report Engine:** Render the invoice PDF to bytes and base64 encode it.<br>`base64.b64encode(pdf_content)` | N/A |
| `type` | String | **`account.move.move_type`** (Mapped)<br>• `out_invoice` $\rightarrow$ `"I-11"` (Facture)<br>• `out_refund` $\rightarrow$ `"I-12"` (Avoir)<br>• *See Enum 6.1* | I-1 |
| `clientEmail` | String | `account.move.partner_id.email` | N/A |
| `configuration` | Object | **Hardcoded Configuration**<br>Define where the QR code (2D-Doc) appears on your PDF layout (e.g., `qrPositionX: 100`, `qrPositionY: 100`). | N/A |
| `invoiceTIEF` | Object | See **Section 3** below. | TEIF |

---

## 3. Core Invoice Data: `TEIFInvoice`

This object represents the structured data validated by the Tunisian Tax Authority (TTN).

### A. Header & Totals

| JSON Field | Type | Odoo 18 Mapping | Constraints (PDF 2) |
| :--- | :--- | :--- | :--- |
| `documentIdentifier` | String | `account.move.name` (e.g., INV/2025/001) | Max 70 chars. |
| `invoiceDate` | Date | `account.move.invoice_date` | YYYY-MM-DD |
| `documentType` | String | Same logic as `NGInvoiceUpload.type` (e.g., "I-11"). | Ref I-1 |
| `clientIdentifier` | String | `account.move.partner_id.vat`<br>*Note: Must strip country code 'TN' if present.* | Regex: `[0-9]{7}[A-Z]...` (Matricule Fiscal) |
| `clientDetails` | Object | See **Section 3.C (PartnerDetails)** | |
| `invoiceTotalWithoutTax`| Decimal| `account.move.amount_untaxed` | |
| `invoiceTotalWithTax` | Decimal| `account.move.amount_total` | |
| `invoiceTotalTax` | Decimal| `account.move.amount_tax` | |
| `stampTax` | Decimal| **Custom Logic:**<br>In Tunisia, this is the "Timbre Fiscal" (0.600 or 1.000).<br>Map to a specific tax line where `tax_id.name` contains "Timbre". | |
| `invoiceTotalinLetters` | String | `account.move.amount_total_words` (Odoo standard computation). | Max 500 chars. |
| `currencyIdentifier` | String | `account.move.currency_id.name` (Default "TND"). | ISO 4217 |

### B. Payment Details (`paymentDetails` Array)

Mapped from Odoo Payment Terms and Journals.

| JSON Field | Type | Odoo 18 Mapping | Ref |
| :--- | :--- | :--- | :--- |
| `pyt.paiConditionCode` | String | **`account.move.invoice_payment_term_id`**<br>Map Odoo terms to codes:<br>• Immediate $\rightarrow$ `I-121`<br>• Specific Date $\rightarrow$ `I-124` | I-12 |
| `pytPai.paiMeansCode` | String | **Custom Field on Invoice:** `payment_method_code`<br>• Cash $\rightarrow$ `I-131`<br>• Check $\rightarrow$ `I-132`<br>• Bank Transfer $\rightarrow$ `I-135` | I-13 |
| `pytFii.accountHolder` | Object | **Bank Account:** `account.move.partner_bank_id`<br>• `accountNumber`: `partner_bank_id.acc_number`<br>• `institutionName`: `partner_bank_id.bank_id.name` | I-14 |

### C. Partner Details (`PartnerDetails`)

Mapped from `res.partner`.

| JSON Field | Type | Odoo 18 Mapping | Notes |
| :--- | :--- | :--- | :--- |
| `partnerIdentifier` | String | `res.partner.vat` | Max 35 chars. |
| `partnerName` | String | `res.partner.name` | Max 200 chars. |
| `address.description` | String | Computed field combining: `street` + `street2` + `city` + `zip`. | Max 500 chars. |
| `address.street` | String | `res.partner.street` | |
| `address.cityName` | String | `res.partner.city` | |
| `address.postalCode` | String | `res.partner.zip` | |
| `address.country` | String | `res.partner.country_id.code` | ISO 3166-1 (e.g., "TN") |

---

## 4. Line Items: `InvoiceItem`

Each line in `invoiceTIEF.items` corresponds to an `account.move.line` (excluding section/note lines).

| JSON Field | Type | Odoo 18 Mapping | Ref |
| :--- | :--- | :--- | :--- |
| `name` | String | `account.move.line.name` (Description) | |
| `code` | String | `account.move.line.product_id.default_code` | |
| `quantity` | Decimal| `account.move.line.quantity` | |
| `unitPrice` | Decimal| `account.move.line.price_unit` | |
| `discount` | Decimal| **Calculation:**<br>`(quantity * price_unit * discount) / 100` | Odoo stores %, API wants amount. |
| `tvaRate` | Float | `account.move.line.tax_ids` (Filter for VAT type taxes).<br>e.g., 19.0, 7.0. | |
| `totalPrice` | Decimal| `account.move.line.price_subtotal` | Amount excluding tax. |
| `unit` | String | `account.move.line.product_uom_id.name` | Default "UNIT" |
| `service` | Boolean| `account.move.line.product_id.type == 'service'` | |
| `taxes` | Array | **Other Taxes (FODEC, etc.):**<br>Iterate `tax_ids`. If tax is NOT VAT, map here.<br>See **Section 4.1**. | |

### 4.1 Other Taxes (`taxes` Array inside Item)

This is specific for Tunisian taxes like **FODEC** (1%) or **DC** (Droit de Consommation).

| JSON Field | Type | Odoo Mapping | Ref |
| :--- | :--- | :--- | :--- |
| `taxTypeName.code` | String | **`account.tax.tax_group_id`** or **Custom Field**.<br>• FODEC $\rightarrow$ `I-162`<br>• DC $\rightarrow$ `I-161` | I-16 |
| `taxTypeName.value` | String | `account.tax.name` | |
| `taxDetails.taxRate` | String | `account.tax.amount` (e.g., "1") | |

---

## 5. Odoo Model Extensions Required

To fully support TEIF, you need to add specific fields or python logic to Odoo 18.

### 5.1 On `res.partner`
*   **Validation Method:** Ensure `vat` (Matricule Fiscal) strictly follows the format: `1234567/A/A/M/000` (7 digits, Key char, VAT code, Category code, Establishment number).

### 5.2 On `account.move` (Invoice)
*   **`ttn_reference`** (Char): To store the UUID returned by NGSign.
*   **`ngsign_status`** (Selection): To track status (`CREATED`, `SIGNED`, `TTN_SIGNED`).
*   **`payment_method_code`** (Selection): To map to TEIF codes `I-131` (Espèce), `I-132` (Chèque), etc.

### 5.3 On `account.tax`
*   **`teif_tax_type`** (Selection): Add a field to map Odoo taxes to TEIF codes (I-161, I-162, I-1604, etc.).

---

## 6. Enumerations Mapping (Reference)

Use these tables to create "Selection" fields in Odoo.

### 6.1 Invoice Type (`I-1`)
*   `I-11`: Facture (Standard)
*   `I-12`: Avoir (Credit Note)
*   `I-15`: Facture Export

### 6.2 Payment Means (`I-13`)
*   `I-131`: Espèce
*   `I-132`: Chèque
*   `I-135`: Virement bancaire

### 6.3 Tax Types (`I-16`)
*   `I-161`: Droit de consommation
*   `I-162`: FODEC
*   `I-1601`: Droit de timbre
*   `I-1602`: TVA
*   `I-1604`: Retenu à la source