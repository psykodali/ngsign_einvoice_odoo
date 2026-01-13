# NGSign e-invoice Odoo Module

This module integrates Odoo with the **NGSign** platform to enable electronic invoicing in compliance with Tunisian regulations (TEIF/TTN).

## Features

- **TEIF Compliance**: Generates e-invoices in the Tunisian Electronic Invoice Format (TEIF).
- **Electronic Seal (SEAL)**: Automatically signs invoices using NGSign's SEAL certificate.
- **TTN Integration**: Submits signed invoices to the Tunisie TradeNet (TTN) platform.
- **Automatic PDF Enrichment**: Updates the invoice PDF with the TTN unique reference and QR code (2D-Doc) upon successful signing.
- **Status Tracking**: Tracks the status of invoices (Pending, Signed, Rejected) directly within Odoo.

## Installation

1.  Clone this repository into your Odoo addons path.
2.  Restart Odoo.
3.  Update your Odoo app list.
4.  Install the **NGSign e-invoice** module.

## Configuration

### 1. General Settings
1.  Go to **Accounting > Configuration > Settings**.
2.  Scroll down to the **NGSign e-invoice** section.
3.  Enter your NGSign credentials:
    -   **NGSign API URL**: The base URL for the NGSign API (e.g., `https://api.ng-sign.com`).
    -   **Bearer Token**: Your NGSign API Bearer Token.
    -   **SEAL Passphrase**: The passphrase for your SEAL certificate.
    -   **QRCode and TTN UID PDF layout**: Set the QRCode and TTN UID coordinate under **NGSIGN (Seal V1) PDF Generation layout**.
    -   **BETA:Builtin (Seal V2) PDF layout**: Seal V2 must be activated under developer settings to enable this feature wich generate the PDF in Odoo.

### 2. Tax Configuration
1.  Go to **Accounting > Configuration > Taxes**.
2.  Open each tax used in invoices (e.g., VAT 19%, FODEC).
3.  Set the **TEIF Tax Code** field to the corresponding TEIF code (e.g., `I-1602` for VAT).

### 3. Payment Terms Configuration
1.  Go to **Accounting > Configuration > Payment Terms**.
2.  Open your payment terms (e.g., Immediate Payment).
3.  Set the **TEIF Condition Code** field (e.g., `I-121` for Immediate).

## Usage

### Signing Invoices
1.  **Create an Invoice**: Create and post a Customer Invoice as usual.
2.  **Sign**: Click the **"Sign with NGSign"** button in the invoice header. The status will change to "Pending".
3.  **Check Status**: Click the **"Check NGSign Status"** button to poll for updates.
    -   Once processed by TTN, the status will change to **"Signed"**.
    -   The signed PDF (containing the TTN QR code) will be automatically downloaded and attached to the invoice.

### Debugging
1.  **Enable Debug Mode**: Go to **Accounting > Configuration > Settings > NGSign e-invoice** and check **Enable Debug Button**.
2.  **Generate JSON**: Open any Customer Invoice. Click the **"Generate Debug JSON"** button in the header to download the payload.

## Author

**NGSIGN**
