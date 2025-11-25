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
2.  Update your Odoo app list.
3.  Install the **NGSign e-invoice** module.

## Configuration

1.  Go to **Settings > Invoicing**.
2.  Scroll down to the **NGSign e-invoice** section.
3.  Enter your NGSign credentials:
    -   **NGSign API URL**: The base URL for the NGSign API (default: `https://api.ng-sign.com`).
    -   **Login**: Your NGSign username.
    -   **Password**: Your NGSign password.
    -   **SEAL Passphrase**: The passphrase for your SEAL certificate.
    -   **Signer Email**: (Optional) Email of the delegated signer.

## Usage

1.  **Create an Invoice**: Create and post a Customer Invoice as usual.
2.  **Sign**: Click the **"Sign with NGSign"** button in the invoice header. The status will change to "Pending".
3.  **Check Status**: Click the **"Check NGSign Status"** button to poll for updates.
    -   Once processed by TTN, the status will change to **"Signed"**.
    -   The signed PDF (containing the TTN QR code) will be automatically downloaded and attached to the invoice.

## Author

**NGSIGN**
