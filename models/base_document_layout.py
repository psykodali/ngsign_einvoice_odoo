from odoo import models, fields

class BaseDocumentLayout(models.TransientModel):
    _inherit = 'base.document.layout'

    ngsign_qr_position_type = fields.Selection(related='company_id.ngsign_qr_position_type', readonly=False)
    ngsign_qr_position_x = fields.Integer(related='company_id.ngsign_qr_position_x', readonly=False)
    ngsign_qr_position_y = fields.Integer(related='company_id.ngsign_qr_position_y', readonly=False)
    ngsign_label_position_x = fields.Integer(related='company_id.ngsign_label_position_x', readonly=False)
    ngsign_label_position_y = fields.Integer(related='company_id.ngsign_label_position_y', readonly=False)
