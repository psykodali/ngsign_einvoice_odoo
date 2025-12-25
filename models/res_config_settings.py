import json
import base64
from odoo import fields, models, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ngsign_api_einvoice_url = fields.Char(string='NGSign API URL', config_parameter='ngsign.api_einvoice_url', default='https://ngsign.app')
    ngsign_enable_debug_button = fields.Boolean(string='Enable Debug Button', config_parameter='ngsign.enable_debug_button', help='Show "Generate Debug JSON" button on invoices')
    ngsign_bearer_token = fields.Char(string='Bearer Token', config_parameter='ngsign.bearer_token')
    ngsign_passphrase = fields.Char(string='SEAL Passphrase', config_parameter='ngsign.passphrase', help='Passphrase for the SEAL certificate')
    ngsign_signer_email = fields.Char(string='Signer Email', config_parameter='ngsign.signer_email', help='Email of the delegated signer (optional)')
    ngsign_notify_owner_default = fields.Boolean(string='Notify Owner Default', config_parameter='ngsign.notify_owner_default', default=True, help='Default value for "Notify Owner" on invoices')

    def action_open_template_settings(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'eInvoice Template Settings',
            'res_model': 'ngsign.template.settings',
            'view_mode': 'form',
            'target': 'new',
        }
