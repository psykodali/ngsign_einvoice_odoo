import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from .ngsign_client import NGSignClient

class AccountMove(models.Model):
    _inherit = 'account.move'

    ngsign_transaction_uuid = fields.Char(string='NGSign Transaction UUID', copy=False)
    ngsign_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('signed', 'Signed'),
        ('error', 'Error')
    ], string='NGSign Status', default='draft', copy=False)

    def _get_ngsign_client(self):
        params = self.env['ir.config_parameter'].sudo()
        api_url = params.get_param('ngsign.api_einvoice_url')
        token = params.get_param('ngsign.bearer_token')
        
        if not api_url or not token:
            raise UserError(_("NGSign configuration is missing. Please check Settings."))
            
        return NGSignClient(api_url, token)

    def _prepare_ngsign_invoice_payload(self):
        """
        Prepare the payload for NGSign API.
        This maps Odoo invoice data to TEIF format.
        """
        self.ensure_one()
        
        # Generate PDF report
        # Assuming standard invoice report. Adjust if custom report is used.
        report_action = self.env.ref('account.account_invoices')
        # In Odoo 14+, _render_qweb_pdf returns (pdf_content, type)
        # In older versions it might be different. Assuming recent Odoo.
        pdf_content, _ = report_action._render_qweb_pdf(self.ids[0])
        pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')

        # Map invoice lines to TEIF items
        items = []
        for line in self.invoice_line_ids:
            items.append({
                'name': line.name,
                'code': line.product_id.default_code or 'N/A',
                'quantity': str(line.quantity),
                'tvaRate': line.tax_ids[0].amount if line.tax_ids else 0, # Simplified tax handling
                'unitPrice': line.price_unit,
                'totalPrice': line.price_subtotal,
                # Add other required fields based on TEIF spec
            })

        # Construct TEIF Invoice object
        # Note: This is a simplified mapping. Real implementation needs full TEIF compliance.
        teif_invoice = {
            'documentIdentifier': self.name,
            'invoiceDate': self.invoice_date.isoformat() if self.invoice_date else fields.Date.today().isoformat(),
            'items': items,
            'invoiceTotalWithoutTax': self.amount_untaxed,
            'invoiceTotalTax': self.amount_tax,
            'invoiceTotalWithTax': self.amount_total,
            # Add supplier and client details
            'clientDetails': {
                'partnerName': self.partner_id.name,
                'partnerIdentifier': self.partner_id.vat or 'N/A',
            },
            # ... other fields
        }

        # Construct NGInvoiceUpload object
        invoice_upload = {
            'invoiceFileB64': pdf_base64,
            'invoiceTIEF': teif_invoice,
            # 'configuration': ... # If needed for V1 positioning
        }
        
        return invoice_upload

    def action_sign_ngsign(self):
        self.ensure_one()
        client = self._get_ngsign_client()
        passphrase = self.env['ir.config_parameter'].sudo().get_param('ngsign.passphrase')
        
        if not passphrase:
            raise UserError(_("SEAL Passphrase is missing in Settings."))

        try:
            invoice_payload = self._prepare_ngsign_invoice_payload()
            # The API expects a list of invoices for transaction
            response = client.create_transaction_seal([invoice_payload], passphrase)
            
            # Assuming response structure based on docs
            # 7.4 NGInvoiceTransaction -> uuid
            self.ngsign_transaction_uuid = response.get('uuid')
            self.ngsign_status = 'pending'
            
            # Check status immediately? Or wait for cron/webhook?
            # Let's try to check status immediately just in case it's fast, or leave it pending.
            
        except Exception as e:
            self.ngsign_status = 'error'
            raise UserError(_("Failed to sign invoice: %s") % str(e))

    def action_check_ngsign_status(self):
        self.ensure_one()
        if not self.ngsign_transaction_uuid:
            return

        client = self._get_ngsign_client()
        try:
            # We use the transaction UUID to get details.
            # We need to add get_transaction_details to client first.
            # Assuming I will add it.
            transaction_details = client.get_transaction_details(self.ngsign_transaction_uuid)
            
            # Check status of the invoice inside the transaction
            # 7.4 NGInvoiceTransaction -> invoices: NGInvoice[]
            invoices = transaction_details.get('invoices', [])
            if not invoices:
                return

            # Assuming 1 invoice per transaction for now as per our create call
            invoice_data = invoices[0]
            status = invoice_data.get('status')
            invoice_uuid = invoice_data.get('uuid')

            if status == 'TTN_SIGNED':
                self.ngsign_status = 'signed'
                # Download PDF
                pdf_content = client.download_pdf(invoice_uuid)
                
                # Update attachment
                attachment_name = f"{self.name}_signed.pdf"
                self.env['ir.attachment'].create({
                    'name': attachment_name,
                    'type': 'binary',
                    'datas': base64.b64encode(pdf_content),
                    'res_model': 'account.move',
                    'res_id': self.id,
                    'mimetype': 'application/pdf'
                })
                
                # Optionally replace the main attachment or message_post
                self.message_post(body=_("Invoice signed via NGSign."), attachments=[(attachment_name, pdf_content)])
                
            elif status in ['CANCELED', 'TTN_REJECTED']:
                self.ngsign_status = 'error'
                self.message_post(body=_("NGSign signing failed/rejected. Status: %s") % status)
            else:
                # Still pending or processing
                pass
                
        except Exception as e:
            raise UserError(_("Failed to check status: %s") % str(e))
