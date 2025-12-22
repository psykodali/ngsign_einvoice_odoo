import json
import base64
from odoo import fields, models, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ngsign_api_einvoice_url = fields.Char(string='NGSign API URL', config_parameter='ngsign.api_einvoice_url', default='https://ngsign.app')
    ngsign_bearer_token = fields.Char(string='Bearer Token', config_parameter='ngsign.bearer_token')
    ngsign_passphrase = fields.Char(string='SEAL Passphrase', config_parameter='ngsign.passphrase', help='Passphrase for the SEAL certificate')
    ngsign_signer_email = fields.Char(string='Signer Email', config_parameter='ngsign.signer_email', help='Email of the delegated signer (optional)')

    def action_generate_debug_json(self):
        """
        Generate a debug JSON payload for the last invoice.
        """
        # Find the last invoice
        last_invoice = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ], order='id desc', limit=1)

        if not last_invoice:
            raise UserError(_("No posted customer invoice found to generate debug JSON."))

        try:
            payload = last_invoice._prepare_ngsign_invoice_payload()
            json_data = json.dumps(payload, indent=4, ensure_ascii=False)
            
            # Create attachment
            attachment = self.env['ir.attachment'].create({
                'name': f'ngsign_debug_{last_invoice.name}.json',
                'type': 'binary',
                'datas': base64.b64encode(json_data.encode('utf-8')),
                'mimetype': 'application/json',
                'res_model': 'res.config.settings',
                'res_id': self.id or 0, # Transient model might not have ID if not saved
            })
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'self',
            }
        except Exception as e:
            raise UserError(_("Failed to generate debug JSON: %s") % str(e))
