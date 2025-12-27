from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    ngsign_qr_position_x = fields.Integer(string='TTN QR Position X (mm)', default=10)
    ngsign_qr_position_y = fields.Integer(string='TTN QR Position Y (mm)', default=10)
    ngsign_label_position_x = fields.Integer(string='TTN Label Position X (mm)', default=150)
    ngsign_label_position_y = fields.Integer(string='TTN Label Position Y (mm)', default=10)
