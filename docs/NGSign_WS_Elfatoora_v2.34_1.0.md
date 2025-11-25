# NGSign — Elfatoora Web Services Specifications (Markdown Extract)

> Source: `NGSIGN-WS-INV` • Product Version **NGSign 2.34** • Document Version **1.0**  
> Audience: Internal / Clients (API Only)

---

## 0. Document Metadata

- **Identifier:** NGSIGN-WS-INV
- **Product Version:** NGSign 2.34
- **Document Version:** 1.0
- **Description:** NGSign Web Services documentation for e-invoicing (TTN-compliant).

---

## 1. Change History (excerpt)

- **2.17 (2021-05-08):** Added invoice signing API.
- **2.17 — 1.1 (2021-05-19):** Fixed typos in WS call.
- **2.31 (2025-06-13):** Add WS for invoices, MobileID, native CEV.
- **2.32 (2025-06-25):** Add v2 WS for invoices; support pre-generated TEIF; payment details; separate TEIF API.
- **2.32 — 1.4 (2025-07-27):** Improvements and JSON tables fixes.
- **2.34 — 1.0 (2025-08-08):** Item‑level tax updates; e‑invoice process description; webhook docs.

---

## 2. Introduction

NGSign is a platform to generate and digitally sign invoices that comply with **TEIF (Tunisian Electronic Invoice Format)** and the **TTN (Tunisie TradeNet)** requirements. It supports:

- TEIF XML generation from structured inputs (JSON or XML).
- Digital signatures via:
  - Local token (USB) — PDF provided by caller.
  - Remote token (DigiGo / IDTrust) — PDF provided by caller.
  - **SEAL** (automated organizational certificate) — PDF optional.
- Submission to TTN; retrieval of results; enrichment of PDF with **TTN unique reference** and **QR code**.
- Web dashboard module "Invoice" when Organization option is enabled.

**Principle:** Only **signed XML** is transmitted to TTN. PDF is retained client-side for distribution/archiving.

---

## 3. E‑Invoicing Process (summary)

1. **Generate TEIF XML**
   - Either produced client-side, or NGSign generates it from structured data (JSON/XML).

2. **Sign the TEIF XML**
   - Local token (manual), Remote token (manual), or **SEAL** (automated).

3. **Submit to TTN**
   - TTN verifies signature/certificate, issuer authorization, data consistency; stores invoice; assigns a **unique reference**; applies a visible **electronic seal**; and signs the final document.

4. **Retrieve TTN Result (asynchronous)**
   - NGSign schedules a background job to fetch status/results and triggers post‑processing.

5. **Post‑Processing (config‑dependent)**
   - Update PDF with **TTN reference + QR code** (if PDF was sent to NGSign).
   - Send **webhook** with signed XML (and PDF if enabled).
   - Send email notifications (if enabled).

> If PDF is **not provided** to NGSign, the **caller must add TTN reference + QR** to the PDF to satisfy regulations.

---

## 4. Common Web Services

### 4.1 Design
- **REST** API with predictable URLs and standard HTTP status codes.
- **JSON** inputs/outputs.

### 4.2 Responses
- **200**: success — JSON payload
  - `object`: primary payload
  - `errorCode`: error code (0 if none)
  - `message`: informational message
- **400**: client/server error — contains `errorCode` and `message`

### 4.3 Authentication
- **JWT** (Bearer) generated via NGSign Web App after login.
- Header: `Authorization: Bearer <token>`
- Token persists until regenerated (regeneration invalidates prior tokens).
- Authorizes access to `/protected/*` endpoints per user roles.

---

## 5. Regular Invoices Web Services

> Use these when sending invoice **data** (not pre-built TEIF XML).

### 5.1 Create Transaction (V1)
- **Path:** `POST /protected/invoice/transaction/`
- **Input:** `NGInvoiceUpload[]`
- **Output:** String — **signing URL** (for a transaction covering all invoices)
- **Flow:** validate → generate TEIF → return URL → user signs (DigiGo/IDTrust) → NGSign forwards to TTN
- **Since:** 2.31

### 5.2 Create Transaction (V2)
- **Path:** `POST /protected/invoice/v2/transaction/`
- **Input:** `NGInvoiceUpload[]`
- **Output:** `NGInvoiceTransaction` (includes **transaction UUID**, invoice statuses, details); signing URL derivable as `[server]/.../{uuid}`
- **Since:** 2.32

### 5.3 Create **Advanced** Transaction (delegate signer)
- **Path:** `POST /protected/invoice/transaction/advanced/`
- **Input:** `NGAdvancedInvoiceUpload` (incl. `signerEmail`)
- **Output:** String — signing URL
- **Since:** 2.32

### 5.4 Create **Advanced** Transaction (V2)
- **Path:** `POST /protected/invoice/v2/transaction/advanced/`
- **Input:** `NGAdvancedInvoiceUpload`
- **Output:** `NGInvoiceTransaction` (adds UUID, per‑invoice details, signer email, status/errors)
- **Since:** 2.32

### 5.5 Create & Sign (SEAL) — automated
- **Path:** `POST /protected/invoice/transaction/seal`
- **Input:** same schema as transaction endpoints
- **Output:** transaction object
- **Since:** 2.31

### 5.6 Create & Sign (SEAL) — **V2**
- **Path:** `POST /protected/invoice/v2/transaction/seal`
- **Key:** **No** QR/label coordinates needed; NGSign does **not** render/modify PDF — caller enriches PDF with 2D‑Doc/labels.
- **Input/Output:** same structural family as V1; optimized for automation.
- **Since:** 2.32

### 5.7 Cancel Transaction
- **Path:** `POST /protected/invoice/transaction/cancel/{uuid}`
- **Effect:** aborts invoices in **non‑terminal** states. **No effect** on `TTN_SIGNED` or `TTN_TRANSFERRED`.
- **Since:** 2.31

### 5.8 Send Single Invoice to NGSign (manual sign in UI)
- **Path:** `POST /protected/invoice`
- **Input:** `NGInvoiceUpload`
- **Output:** `NGInvoice`
- **Note:** User must sign in NGSign UI; for automation prefer **transaction** endpoints.
- **Since:** 2.17

### 5.9 Cancel Single Invoice
- **Path:** `POST /protected/invoice/cancel/{uuid}`
- **Input:** invoice UUID
- **Output:** updated `NGInvoice`
- **Since:** 2.17

### 5.10 Check Invoice Status
- **Path:** `POST /protected/invoice/check/{uuid}`
- **Output:** `NGInvoice`
- **Behavior:** queries TTN if not terminal; updates local status.
- **Since:** 2.17

### 5.11 Download Signed Invoice (PDF)
- **Path:** `GET /protected/invoice/pdf/{uuid}`
- **Output:** PDF (base64 or bytes depending on client)
- **Since:** 2.17

### 5.12 Get Transaction Details
- **Path:** `GET /any/invoice/{uuid}`
- **Output:** transaction details (metadata + per‑invoice info)
- **Since:** 2.17

### 5.13 Webhook (callback)
- **Path:** `POST <configured client URL>`
- **Input:** `WebhookPayload`
- **Retries:** up to 3 attempts (10 min backoff between retries); no auth embedded by NGSign (client endpoint must manage auth).
- **Since:** 2.34

---

## 6. TEIF API (when **you** already generate TEIF XML)

> Use these when you submit **pre‑built TEIF XML** (NGSign validates, signs, and submits to TTN).

### 6.1 Create Transaction (XML)
- **Path:** `POST /protected/invoice/xml/transaction/`
- **Input:** `NGXMLInvoiceUpload[]` (raw TEIF XMLs)
- **Output:** signing URL (batch) — user signs (DigiGo/IDTrust)
- **Since:** 2.31

### 6.2 Create Transaction (XML, V2)
- **Path:** `POST /protected/invoice/xml/v2/transaction/`
- **Input:** `NGXMLInvoiceUpload[]`
- **Output:** `NGXMLInvoiceTransaction` (incl. UUID); signing URL derivable as `[server]/.../{uuid}`
- **Since:** 2.32

### 6.3 Create **Advanced** Transaction (XML, delegate signer)
- **Path:** `POST /protected/invoice/transaction/xml/advanced/`
- **Since:** 2.31

### 6.4 Create **Advanced** Transaction (XML, V2)
- **Path:** `POST /protected/invoice/xml/transaction/advanced/`
- **Since:** 2.32

### 6.5 Create & Sign (SEAL) (XML, V1)
- **Path:** `POST /protected/invoice/xml/transaction/seal`
- **Since:** 2.32

### 6.6 Create & Sign (SEAL) (XML, **V2**)
- **Path:** `POST /protected/invoice/xml/v2/transaction/seal`
- **Note:** caller handles PDF enrichment; optimized for automated flows.
- **Since:** 2.32

### 6.7 Download Signed Invoice (XML)
- **Path:** `GET /protected/invoice/xml/{uuid}`
- **Output:** TEIF XML (base64 or bytes)
- **Since:** 2.31

---

## 7. JSON Objects (selected)

> Below are key payloads. Types are indicative; omit images/binaries unless needed.

### 7.1 `NGInvoiceUpload` (V1/V2)
- `invoiceFileB64: string` — PDF (base64). **Required in V1**, **optional in V2**.
- `clientEmail: string?`
- `configuration: InvoiceConfiguration`
- `invoiceTIEF: TEIFInvoice` (raw business data)
- `callbackUrl: NGRedirectionUrl` (final-status callbacks)

### 7.2 `NGXMLInvoiceUpload` (TEIF XML)
- `invoiceFileB64: string` — PDF (base64). **Required in V1**, **optional in V2**.
- `clientEmail: string?`
- `configuration: InvoiceConfiguration`
- `invoiceTIEF: string` — **TEIF XML** (raw)
- `callbackUrl: NGRedirectionUrl`
- `documentIdentifier: string` — used to fetch TTN assets (QR, ref)

### 7.3 `NGAdvancedInvoiceUpload`
- `invoices: NGInvoiceUpload[]`
- `signerEmail: string?` — delegated signer
- `passphrase: string` — **mandatory** for SEAL endpoints (to decrypt SEAL PIN)
- `notifyOwner: boolean?` — email the creator
- `ccEmail: string?`

### 7.4 `NGInvoiceTransaction`
- `uuid: string`
- `invoices: NGInvoice[]`
- `creationDate: date`
- `status: string`
- `signingTime: date?`

### 7.5 `NGXMLInvoiceTransaction`
- `uuid: string`
- `invoices: NGXMLInvoice[]`
- `creationDate: date`
- `status: string`
- `signingTime: date?`

### 7.6 `InvoiceConfiguration` (for V1 APIs requiring PDF positions)
- `qrPositionX|Y|P: number` — coordinates/page for **2D-Doc** (TTN QR)  
- `labelPositionX|Y|P: number` — coordinates/page for TTN label  
- `qrRatio: number (default 0.5)`  
- `textPositionX|Y|Page: number?` — optional text “Copie de la facture…”

> **Note:** V2 endpoints (incl. `/v2/transaction/*`) **do not require** QR/label coordinates; caller enriches PDF.

### 7.7 `TEIFInvoice` (business data extract)
- Supplier:
  - `supplierIdentifier: string` (pattern per TEIF rules)
  - `supplierDetails: PartnerDetails`
- Client:
  - `clientIdentifier: string` (pattern per TEIF rules)
  - `clientDetails: PartnerDetails`
- Document:
  - `documentIdentifier: string`
  - `invoiceDate: date`
  - `items: InvoiceItem[]`
- Totals:
  - `invoiceTotalWithoutTax: number`
  - `invoiceTotalTax: number`
  - `invoiceTotalWithTax: number`
  - `invoiceTotalinLetters: string`
  - `stampTax: number`
  - `tvaRate: number`
  - `tvaTax: number`
  - `totalDiscount: number`
- Payments & allowances:
  - `paymentDetails: PytSeg[]?`
  - `alcDetails: AlcDetails[]?`

### 7.8 `PartnerDetails`
- `partnerIdentifier: string (<=35)`
- `partnerName: string (<=200)`
- `address: InvoiceAddress?`
- `partnerReference: string? (<=200)`

### 7.9 `InvoiceItem`
- `name: string (<=200)`
- `code: string (<=35)`
- `quantity: string`
- `tvaRate: number`
- `currencyIdentifier: string = "TND"`
- `taxes: Tax[]?`
- `itemAlc: ItemAlcDetail?`
- `discountPercentage: number?`
- `unitPrice: number`
- `totalPrice: number`

### 7.10 `NGInvoice`
- `uuid: string`
- `status: InvoiceStatus`
- `clientEmail: string?`
- `clientId: string?`
- `ttnReference: number`
- `invoiceNumber: string`
- `invoiceDate: date`
- `amount: number`

### 7.11 `NGXMLInvoice`
- `uuid: string`
- `status: InvoiceStatus`
- `clientEmail: string?`
- `ttnReference: number`
- `invoiceNumber: string`
- `invoiceDate: date`
- `withPDF: boolean` (true if PDF was included; for SEAL V2 can be false)
- `twoDocImage: binary` (TTN 2D-Doc image)

### 7.12 `InvoiceAddress`
- `description: string (<=500)`
- `street: string? (<=35)`
- `cityName: string? (<=35)`
- `postalCode: string? (<=17)`
- `country: string? (<=6, ISO‑3166‑1)`

### 7.13 Allowances / Taxes (abbrev)
- `AlcDetails` → `alc: Alc`, `moa: Moa`, `comments?: string[]`, `taxAlc?: TaxDetails`
- `TaxDetails` → `tax: Tax`, `amountDetails: MoaDetails[]`
- `MoaDetails` → `moa: Moa`, `rffDtm?: RefGrp`
- `RefGrp` → `reference: Reference`, `referenceDate?: Dtm`
- `Reference` → `value: string (<=200)`, `refID: PartyName`, `date?: Dtm`
- `Moa` → `value: string (<=200)`, `currencyIdentifier: string="TND"`, `amountDescription?: string (<=200)`, `amountTypeCode: AmountType`
- `ItemAlcDetail` → `alc: Alc`, `pcd: Pcd`, `comments?: string[]`
- `Alc` → `allowanceIdentifier?: string (<=35)`, `specialServices?: string (<=200)`, `allowanceCode: AllowanceType (default I-151)`
- `Pcd` → `percentage: string (<=5)`, `percentageBasis: string (<=35)`
- `PytSeg` → `pyt?: Pyt`, `pytDtm?: string`, `amount?: number`, `amountType?: string`, `currencyIdentifier?: string`, `pytPai?: Pai`, `pytFii?: Fii`
- `Pyt` → `paymentTearmsTypeCode: PaymentConditions`, `paymentTearmsDescription?: string (<=500)`
- `Pai` → `paiConditionCode: PaymentConditions`, `paiMeansCode: PaymentMeans`
- `Tax` → `taxCategory?: string`, `code: "I-(160(1(2)?|3)?|16[0-9])"`, `taxRate: string`
- `Dtm` → `dateCode: Dates`, `date: string`
- `Fii` → `accountHolder?: AccountHolder`, `institutionIdentification?: InstitutionIdentification`, `country?: string`
- `InstitutionIdentification` → `branchIdentifier?: string (<=17)`, `institutionName?: string (<=70)`, `nameCode?: string`
- `AccountHolder` → `accountNumber: string (<=20)`, `ownerIdentifier?: string (<=70)`

### 7.14 `WebhookPayload`
- `ttnReference: string`
- `invoiceNumber: string`
- `uuid: string`
- `twoDocImage: string (base64)`
- `pdfBase64: string (base64)`
- `xmlBase64: string (base64)`

---

## 8. Enumerations (abbrev)

### 8.1 `InvoiceStatus`
- `CREATED`, `SIGNED`, `CANCELED`, `TTN_TRANSFERED`, `TTN_REJECTED`, `TTN_SIGNED`

### 8.2 `PaymentMeans` (I-131..I-137)
- Cash, Cheque, Certified Cheque, Direct Debit, Bank Transfer, Any Bank, Other

### 8.3 `PaymentConditions` (I-121..I-124)
- Direct Payment; Through a specific institution; Any bank; Other

### 8.4 `Dates` (I-31..I-38)
- Issue Date, Due Date, Confirmation Date, Expiration Date, Attachment Date, Billing Period, Reference Generation Date, Other

### 8.5 `AllowanceType` (I-151..I-155)
- Réduction, Ristourne, Rabais, Redevance Télécom, Autre

### 8.6 `AmountType` (I-171..I-188 excerpt)
- Item Total HT, Items Total HT, Paid Amount, Service HT, Services Total HT, Invoice Total HT, Tax Base, Tax Amount, Company Capital, Invoice Total TTC, Tax Total, Tax Base Total, Unit Item HT, Client Code, Exempted Total, Credit Amount, VAT Suspension Amount, Net Item Amount

---

## 9. Notes for Implementors

- Prefer **V2** endpoints for automation; do **not** send QR/label positions (you enrich the PDF yourself).
- When using **SEAL**, include the `passphrase` to decrypt the SEAL PIN.
- Strings in TEIF data **must avoid accents/special characters**; all strings are trimmed in final XML.
- Use **webhook** for immediate integration with back‑office once TTN finalizes processing.

---

## 10. Quick Pseudocode (Client Flow)

```text
1) Build NGInvoiceUpload[] (or NGXMLInvoiceUpload[] if you already have TEIF XMLs).
2) Call POST /protected/invoice/v2/transaction[/advanced|/seal].
3) If non-SEAL: follow returned signing URL (DigiGo/IDTrust) to sign.
4) Poll status or receive webhook after TTN finishes.
5) Download PDF (/protected/invoice/pdf/{uuid}) or XML (/protected/invoice/xml/{uuid}).
6) If V2: enrich your own PDF with TTN QR + reference.
```

---

*End of Markdown extract.*
