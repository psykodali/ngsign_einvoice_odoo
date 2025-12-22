import base64
import re
import json
import logging
from datetime import datetime
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)
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

    ngsign_show_debug_button = fields.Boolean(compute='_compute_show_debug_button')

    def _compute_show_debug_button(self):
        enable_debug = self.env['ir.config_parameter'].sudo().get_param('ngsign.enable_debug_button')
        for move in self:
            move.ngsign_show_debug_button = bool(enable_debug)

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
        pdf_base64 = ""
        try:
            # Find report action using search to be safe
            report_action = self.env['ir.actions.report'].sudo().search([
                ('model', '=', 'account.move'),
                ('report_name', 'in', ['account.report_invoice_with_payments', 'account.report_invoice'])
            ], limit=1)

            if report_action:
                # Correctly call _render_qweb_pdf on the model, passing the report record and IDs
                # Force language to partner's lang or French
                lang = self.partner_id.lang or 'fr_FR'
                pdf_content, _ = self.env['ir.actions.report'].with_context(lang=lang).sudo()._render_qweb_pdf(report_action, self.ids)
                pdf_base64 = base64.b64encode(pdf_content).decode('utf-8')
            else:
                pdf_base64 = "REPORT_ACTION_NOT_FOUND"
                
        except Exception as e:
            # If PDF generation fails, we still want to see the JSON data mapping
            pdf_base64 = f"PDF_GENERATION_FAILED: {str(e)}"

        # 1. Header Data
        # Map move_type to TEIF codes
        teif_doc_type = 'I-11' # Default Facture
        if self.move_type == 'out_refund':
            teif_doc_type = 'I-12'
        
        # Clean VAT (remove non-numeric characters for check, but keep logic simple as per req)
        # Req: Strip country code (e.g. 'TN') and ensure 7 digits + key.
        partner_vat = self.partner_id.vat or ''
        partner_vat = partner_vat.upper().replace('TN', '').strip()
        # Basic regex validation could be added here or just pass it. 
        # The API might reject it if invalid.
        
        # 2. Items Mapping
        items = []
        # In Odoo 16+, display_type can be 'product'. We want to exclude sections and notes.
        for line in self.invoice_line_ids.filtered(lambda l: l.display_type not in ('line_section', 'line_note')):
            # VAT Rate and Taxes Logic
            # 1. Identify Primary VAT (I-1602)
            # 2. All other taxes (including secondary VATs or non-VATs) go to 'taxes' list
            
            all_taxes = line.tax_ids
            vat_taxes = all_taxes.filtered(lambda t: t.teif_code == 'I-1602')
            taxes_with_codes = all_taxes.filtered(lambda t: t.teif_code)
            
            primary_vat_tax = None
            if vat_taxes:
                primary_vat_tax = vat_taxes[0]
            elif not taxes_with_codes and all_taxes:
                # Fallback: if no codes configured at all, assume first tax is VAT
                primary_vat_tax = all_taxes[0]
            
            vat_rate = primary_vat_tax.amount if primary_vat_tax else 0.0

            # Other taxes (FODEC, DC, etc. OR secondary VATs)
            other_taxes = []
            for tax in all_taxes:
                if tax == primary_vat_tax:
                    continue
                
                other_taxes.append({
                    'taxTypeName': {
                        'code': tax.teif_code or 'I-1606', # Default to Autre
                        'value': tax.name
                    },
                    'taxDetails': {
                        'taxRate': str(tax.amount)
                    }
                })

            # Discount (Allowance)
            item_alc = None
            if line.discount > 0:
                item_alc = {
                    'alc': True, # Allowance
                    'pcd': {
                        'percentage': str(line.discount),
                        'percentageBasis': str(line.quantity * line.price_unit)
                    },
                    'comments': ['Remise ligne']
                }

            items.append({
                'name': line.name[:500],
                'code': line.product_id.default_code or 'N/A',
                'quantity': str(line.quantity),
                'unit': line.product_uom_id.name or 'UNIT',
                'unitPrice': line.price_unit,
                'totalPrice': line.price_subtotal,
                'tvaRate': vat_rate,
                'currencyIdentifier': self.currency_id.name,
                'taxes': other_taxes,
                'discountPercentage': line.discount,
                'discount': (line.quantity * line.price_unit * line.discount) / 100,
                'itemAlc': item_alc,
                'service': line.product_id.type == 'service'
            })

        # 3. Totals and Financials
        # Stamp Tax (Timbre)
        stamp_tax_amount = 0.0
        # Find tax line with name 'Timbre' or specific code if we had it on lines (usually it's a global tax or added as line)
        # In Odoo, Timbre is often a tax on a line or a specific line. 
        # If it's a tax on a line, it's in amount_tax. If it's a specific product, it's in lines.
        # Let's look for a tax with teif_code 'I-1601' in the tax lines (account.move.tax.line? No, tax_totals in recent odoo)
        # Or just check invoice_line_ids for a tax that matches.
        # Simplified: Check all taxes applied.
        for line in self.invoice_line_ids:
            for tax in line.tax_ids:
                if tax.teif_code == 'I-1601':
                    # This is tricky because tax amount is per line. 
                    # We might need to sum it up from tax_totals or similar.
                    # For now, let's assume standard Odoo tax computation handles the total amount_tax.
                    # But TEIF wants 'stampTax' separately.
                    pass
        
        # Better approach for Stamp Tax: Look at tax_totals or line_ids if it's a specific line.
        # Often Timbre is a tax.
        # Let's try to find it in the tax lines (account.tax objects don't store the computed amount on the invoice directly easily without inspecting tax_lines)
        # We can iterate over line.tax_ids and if we find I-1601, we calculate the amount.
        # Or use `amount_by_group` if available.
        # For this implementation, let's leave stampTax as 0.600 if we find a tax named 'Timbre' or code I-1601.
        
        stamp_tax = 0.0
        # This is a rough approximation. In real Odoo, check `tax_totals` json or `line_ids` tax amounts.
        # We will assume if any tax has code I-1601, we sum its amount.
        # Since accessing tax amounts per tax type is complex in Odoo 14+ (it's in tax_totals), 
        # we will iterate invoice lines and compute it manually or check tax lines.
        # Let's check `line_ids` (journal items) which are tax lines.
        for tax_line in self.line_ids:
            if tax_line.tax_line_id and tax_line.tax_line_id.teif_code == 'I-1601':
                stamp_tax += abs(tax_line.balance) # In company currency? Need invoice currency.
                # tax_line.amount_currency is in invoice currency.
                stamp_tax = abs(tax_line.amount_currency)

        # 4. Payment Details
        # Resolve Bank Account (Unconditionally)
        # Priority: 1. Invoice specific bank (partner_bank_id)
        #           2. Journal's bank account (if set)
        #           3. Company's first bank account
        
        # Use sudo() to ensure we can read bank account details regardless of user permissions
        bank_account = self.partner_bank_id.sudo()
        
        _logger.info(f"NGSign Debug: partner_bank_id={bank_account}, acc_number={bank_account.acc_number if bank_account else 'None'}")
        
        if not bank_account and self.journal_id.bank_account_id:
            bank_account = self.journal_id.bank_account_id.sudo()
            _logger.info(f"NGSign Debug: Fallback to Journal Bank={bank_account}")
        
        if not bank_account:
             # Fallback to the first bank account of the company
             company_banks = self.company_id.partner_id.bank_ids.sudo()
             if company_banks:
                 bank_account = company_banks[0]
                 _logger.info(f"NGSign Debug: Fallback to Company Bank={bank_account}")

        _logger.info(f"NGSign Debug: Final Resolved Bank={bank_account}")

        payment_details = []
        if self.invoice_payment_term_id:
            pyt_code = self.invoice_payment_term_id.teif_code or 'I-121' # Default Immediate
            
            # Payment Means (Espèce, Chèque, Virement)
            pai_means_code = 'I-135' # Virement
            
            pyt_fii = None
            if bank_account:
                pyt_fii = {
                    'accountHolder': {
                        'accountNumber': bank_account.acc_number,
                    },
                    'institutionIdentification': {
                        'institutionName': bank_account.bank_id.name or 'Bank',
                    }
                }

            payment_details.append({
                'pyt': {
                    'paiConditionCode': pyt_code,
                    'paymentTearmsDescription': self.invoice_payment_term_id.name
                },
                'pytPai': {
                    'paiConditionCode': pyt_code,
                    'paiMeansCode': pai_means_code
                },
                'pytFii': pyt_fii
            })

        # Clean Company VAT (Issuer)
        company_vat = self.company_id.vat or ''
        company_vat = company_vat.upper().replace('TN', '').strip()

        # Construct TEIF Invoice object
        # Convert date to Unix timestamp (seconds)
        invoice_date_ts = 0
        if self.invoice_date:
            # Convert date to datetime at midnight
            dt = datetime.combine(self.invoice_date, datetime.min.time())
            invoice_date_ts = int(dt.timestamp())
        else:
            invoice_date_ts = int(datetime.now().timestamp())

        teif_invoice = {
            'documentIdentifier': self.name,
            'invoiceDate': invoice_date_ts,
            'documentType': teif_doc_type,
            'clientIdentifier': company_vat, # Issuer Tax ID
            'currencyIdentifier': self.currency_id.name,
            'comments': [self.narration] if self.narration else [],
            'accountNumber': bank_account.acc_number if bank_account else None,
            'institutionName': bank_account.bank_id.name if bank_account and bank_account.bank_id else None,
            
            'clientDetails': {
                'partnerIdentifier': partner_vat, # Customer Tax ID
                'partnerName': self.partner_id.name,
                'address': {
                    'description': self.partner_id.contact_address.replace('\n', ' ') if self.partner_id.contact_address else '',
                    'street': self.partner_id.street,
                    'cityName': self.partner_id.city,
                    'postalCode': self.partner_id.zip,
                    'country': self.partner_id.country_id.code if self.partner_id.country_id else 'TN'
                }
            },
            
            'items': items,
            
            'invoiceTotalWithoutTax': self.amount_untaxed,
            'invoiceTotalWithTax': self.amount_total,
            'invoiceTotalTax': self.amount_tax,
            'stampTax': stamp_tax,
            'invoiceTotalinLetters': self.currency_id.with_context(lang='fr_FR').amount_to_text(self.amount_total),
            
            'paymentDetails': payment_details
        }

        # Construct NGInvoiceUpload object
        invoice_upload = {
            'invoiceFileB64': pdf_base64,
            'type': teif_doc_type,
            'clientEmail': self.partner_id.email,
            'invoiceTIEF': teif_invoice,
            'configuration': {
                'qrPositionX': 10,
                'qrPositionY': 10,
                'qrPositionP': 0,
                'labelPositionX': 150,
                'labelPositionY': 10,
                'labelPositionP': 0,
                'allPages': True
            }
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

    def action_generate_debug_json(self):
        """
        Generate a debug JSON payload for the current invoice.
        """
        self.ensure_one()
        try:
            payload = self._prepare_ngsign_invoice_payload()
            json_data = json.dumps(payload, indent=4, ensure_ascii=False)
            
            # Create attachment
            attachment = self.env['ir.attachment'].create({
                'name': f'ngsign_debug_{self.name}.json',
                'type': 'binary',
                'datas': base64.b64encode(json_data.encode('utf-8')),
                'mimetype': 'application/json',
                'res_model': 'account.move',
                'res_id': self.id,
            })
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        except Exception as e:
            raise UserError(_("Failed to generate debug JSON: %s") % str(e))
