import json
import base64
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ngsign_api_einvoice_url = fields.Char(string='NGSign API URL', config_parameter='ngsign.api_einvoice_url', default='https://ngsign.app')
    ngsign_enable_debug_button = fields.Boolean(string='Developer options', config_parameter='ngsign.enable_debug_button', help='Show "Generate Debug JSON" button on invoices')
    ngsign_bearer_token = fields.Char(string='Bearer Token', config_parameter='ngsign.bearer_token')
    ngsign_passphrase = fields.Char(string='SEAL Passphrase', config_parameter='ngsign.passphrase', help='Passphrase for the SEAL certificate')
    ngsign_signer_email = fields.Char(string='Signer Email', config_parameter='ngsign.signer_email', help='Email of the delegated signer (optional)')
    ngsign_notify_owner_default = fields.Boolean(string='Notify Owner Default', config_parameter='ngsign.notify_owner_default', default=True, help='Default value for "Notify Owner" on invoices')
    ngsign_use_v2_endpoint = fields.Boolean(string='Use V2 Seal Endpoint', config_parameter='ngsign.use_v2_endpoint', help='Use V2 endpoint (no PDF upload, local stamping)')
    
    # TTN Layout settings (company-specific)
    ngsign_qr_position_x = fields.Integer(related='company_id.ngsign_qr_position_x', readonly=False, string='TTN QR Position X (mm)')
    ngsign_qr_position_y = fields.Integer(related='company_id.ngsign_qr_position_y', readonly=False, string='TTN QR Position Y (mm)')
    ngsign_label_position_x = fields.Integer(related='company_id.ngsign_label_position_x', readonly=False, string='TTN Label Position X (mm)')
    ngsign_label_position_y = fields.Integer(related='company_id.ngsign_label_position_y', readonly=False, string='TTN Label Position Y (mm)')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        
        # Explicitly save to ensure it works and log it
        param.set_param('ngsign.api_einvoice_url', self.ngsign_api_einvoice_url or '')
        param.set_param('ngsign.bearer_token', self.ngsign_bearer_token or '')
        param.set_param('ngsign.passphrase', self.ngsign_passphrase or '')
        param.set_param('ngsign.signer_email', self.ngsign_signer_email or '')
        param.set_param('ngsign.notify_owner_default', str(self.ngsign_notify_owner_default))
        param.set_param('ngsign.use_v2_endpoint', str(self.ngsign_use_v2_endpoint))
        
        # Log what we are saving
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"NGSign Settings Saved: URL={self.ngsign_api_einvoice_url}, TokenLen={len(self.ngsign_bearer_token) if self.ngsign_bearer_token else 0}")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        
        res.update(
            ngsign_api_einvoice_url=param.get_param('ngsign.api_einvoice_url', default='https://ngsign.app'),
            ngsign_bearer_token=param.get_param('ngsign.bearer_token'),
            ngsign_passphrase=param.get_param('ngsign.passphrase'),
            ngsign_signer_email=param.get_param('ngsign.signer_email'),
            ngsign_notify_owner_default=param.get_param('ngsign.notify_owner_default', 'True') == 'True',
            ngsign_use_v2_endpoint=param.get_param('ngsign.use_v2_endpoint', 'False') == 'True',
        )
        return res

    def action_open_template_settings(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'eInvoice Template Settings',
            'res_model': 'ngsign.template.settings',
            'view_mode': 'form',
            'target': 'new',
        }

    def action_open_developer_settings(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Developer Options',
            'res_model': 'ngsign.developer.settings',
            'view_mode': 'form',
            'target': 'new',
        }
