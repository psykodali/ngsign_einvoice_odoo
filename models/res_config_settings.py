from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ngsign_api_url = fields.Char(string='NGSign API URL', config_parameter='ngsign.api_url', default='https://api.ng-sign.com')
    ngsign_login = fields.Char(string='Login', config_parameter='ngsign.login')
    ngsign_password = fields.Char(string='Password', config_parameter='ngsign.password')
    ngsign_passphrase = fields.Char(string='SEAL Passphrase', config_parameter='ngsign.passphrase', help='Passphrase for the SEAL certificate')
    ngsign_signer_email = fields.Char(string='Signer Email', config_parameter='ngsign.signer_email', help='Email of the delegated signer (optional)')
