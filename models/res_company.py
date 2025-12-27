from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    ngsign_qr_position_type = fields.Selection([
        ('custom', 'Custom Coordinates'),
        ('builtin', 'Builtin Position')
    ], string='QR Code Position Type', compute='_compute_ngsign_qr_temp', inverse='_inverse_ngsign_qr_temp', store=False)

    def _compute_ngsign_qr_temp(self):
        for record in self:
            record.ngsign_qr_position_type = 'custom'

    def _inverse_ngsign_qr_temp(self):
        pass

    ngsign_qr_position_x = fields.Integer(string='TTN QR Position X (mm)', default=10)
    ngsign_qr_position_y = fields.Integer(string='TTN QR Position Y (mm)', default=10)
    ngsign_qr_size = fields.Integer(string='TTN QR Size (mm)', default=30)
    
    ngsign_label_position_x = fields.Integer(string='TTN Label Position X (mm)', default=150)
    ngsign_label_position_y = fields.Integer(string='TTN Label Position Y (mm)', default=10)
    ngsign_label_width = fields.Integer(string='TTN Label Width (mm)', default=50)
    ngsign_label_text = fields.Char(string='TTN Label Text', default='')
    ngsign_label_font_size = fields.Integer(string='TTN Label Font Size (pt)', default=10)
