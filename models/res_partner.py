from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    ngsign_notify_owner = fields.Boolean(string='Notify Owner (NGSign)', default=True, help="If checked, the owner will be notified when an invoice is signed via NGSign.")
