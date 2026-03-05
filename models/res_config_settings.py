import json
import base64
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ngsign_api_einvoice_url = fields.Char(string='NGSign API URL', config_parameter='ngsign.api_einvoice_url', default='https://ngsign.app')
    ngsign_enable_debug_button = fields.Boolean(string='Developer options', config_parameter='ngsign.enable_debug_button', help='Show "Generate Debug JSON" button on invoices')
    ngsign_bearer_token = fields.Char(string='Bearer Token', config_parameter='ngsign.bearer_token')
    
    # Certificate Type Configuration
    ngsign_ttn_mode = fields.Selection([
        ('test', 'TEST'),
        ('prod', 'PROD')
    ], string='TTN MODE', config_parameter='ngsign.ttn_mode', default='test', required=True,
       help='Select the mode for NGSign TTN integration:\n'
            '- TEST: Invoices are signed in test mode and can be reset.\n'
            '- PROD: Production mode, transactions are final.')

    ngsign_certificate_type = fields.Selection([
        ('seal', 'SEAL (Automatic Signing)'),
        ('digigo', 'DigiGO (User Signature)'),
        ('sscd', 'SSCD (USB Token)')
    ], string='Certificate Type', config_parameter='ngsign.certificate_type', default='seal',
       help='Select the type of certificate to use for signing invoices:\n'
            '- SEAL: Automatic server-side signing with passphrase\n'
            '- DigiGO: Personal digital certificate requiring user authentication\n'
            '- SSCD: Secure Signature Creation Device (USB token)')
    
    ngsign_passphrase = fields.Char(string='SEAL Passphrase', config_parameter='ngsign.passphrase', 
                                     help='Passphrase for the SEAL certificate (required only for SEAL type)')
    ngsign_signer_email = fields.Char(string='Signer Email', config_parameter='ngsign.signer_email', 
                                       help='Email of the delegated signer (optional)')
    ngsign_notify_owner_default = fields.Boolean(string='Notify Owner Default', config_parameter='ngsign.notify_owner_default', default=True, 
                                                  help='Default value for "Notify Owner" on invoices')
    ngsign_use_v2_endpoint = fields.Boolean(string='Use V2 Seal Endpoint', config_parameter='ngsign.use_v2_endpoint', 
                                             help='Use V2 endpoint (no PDF upload, local stamping) - Only for SEAL certificates')
    ngsign_pds_base_url = fields.Char(string='PDS Base URL', config_parameter='ngsign.pds_base_url', 
                                       default='https://sandbox.ng-sign.com/pdsv2/#/invoice/',
                                       help='Base URL for the Page de Signature (PDS) - Used for DigiGO and SSCD certificates')
    
    ngsign_email_template_id = fields.Many2one('mail.template', string='Signature Email Template',
                                               help='Template used when sending signature requests via email (DigiGO / SSCD)')
    ngsign_authorized_users = fields.Many2many('res.users', 'ngsign_auth_users_rel', 'config_id', 'user_id', string='Authorized Signers',
                                               help='Users authorized to sign invoices with DigiGO / SSCD. If empty, everyone can sign.')

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        
        # Explicitly save to ensure it works and log it
        param.set_param('ngsign.api_einvoice_url', self.ngsign_api_einvoice_url or '')
        param.set_param('ngsign.bearer_token', self.ngsign_bearer_token or '')
        param.set_param('ngsign.certificate_type', self.ngsign_certificate_type or 'seal')
        param.set_param('ngsign.passphrase', self.ngsign_passphrase or '')
        param.set_param('ngsign.signer_email', self.ngsign_signer_email or '')
        param.set_param('ngsign.notify_owner_default', str(self.ngsign_notify_owner_default))
        param.set_param('ngsign.use_v2_endpoint', str(self.ngsign_use_v2_endpoint))
        param.set_param('ngsign.pds_base_url', self.ngsign_pds_base_url or 'https://sandbox.ng-sign.com/pdsv2/#/invoice/')
        param.set_param('ngsign.email_template_id', self.ngsign_email_template_id.id or '')
        param.set_param('ngsign.authorized_users', ','.join(map(str, self.ngsign_authorized_users.ids)) if self.ngsign_authorized_users else '')
        
        # Log what we are saving
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info(f"NGSign Settings Saved: URL={self.ngsign_api_einvoice_url}, Mode={self.ngsign_ttn_mode}, CertType={self.ngsign_certificate_type}, TokenLen={len(self.ngsign_bearer_token) if self.ngsign_bearer_token else 0}")

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        param = self.env['ir.config_parameter'].sudo()
        
        res.update(
            ngsign_api_einvoice_url=param.get_param('ngsign.api_einvoice_url', default='https://ngsign.app'),
            ngsign_bearer_token=param.get_param('ngsign.bearer_token'),
            ngsign_ttn_mode=param.get_param('ngsign.ttn_mode', default='test'),
            ngsign_certificate_type=param.get_param('ngsign.certificate_type', default='seal'),
            ngsign_passphrase=param.get_param('ngsign.passphrase'),
            ngsign_signer_email=param.get_param('ngsign.signer_email'),
            ngsign_notify_owner_default=param.get_param('ngsign.notify_owner_default', 'True') == 'True',
            ngsign_use_v2_endpoint=param.get_param('ngsign.use_v2_endpoint', 'False') == 'True',
            ngsign_pds_base_url=param.get_param('ngsign.pds_base_url', default='https://sandbox.ng-sign.com/pdsv2/#/invoice/'),
        )
        
        template_id = param.get_param('ngsign.email_template_id', '')
        if template_id:
            res.update(ngsign_email_template_id=int(template_id))
            
        auth_users = param.get_param('ngsign.authorized_users', '')
        if auth_users:
            res.update(ngsign_authorized_users=[(6, 0, [int(u) for u in auth_users.split(',')])])
            
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
    
    def action_open_ttn_layout_settings(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'TTN Layout Configuration',
            'res_model': 'ngsign.ttn.layout.settings',
            'view_mode': 'form',
            'target': 'new',
        }
