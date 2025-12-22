from odoo import models, fields, api

class NGSignTemplateSettings(models.TransientModel):
    _name = 'ngsign.template.settings'
    _description = 'NGSign eInvoice Template Settings'

    qr_position_x = fields.Integer(string='QR Position X', default=10)
    qr_position_y = fields.Integer(string='QR Position Y', default=10)
    qr_position_p = fields.Integer(string='QR Position P', default=0)
    qr_ratio = fields.Float(string='QR Ratio', default=0.5)
    
    text_position_x = fields.Integer(string='Text Position X', default=40)
    text_position_y = fields.Integer(string='Text Position Y', default=40)
    text_page = fields.Integer(string='Text Page', default=0)
    
    label_position_x = fields.Integer(string='Label Position X', default=150)
    label_position_y = fields.Integer(string='Label Position Y', default=10)
    label_position_p = fields.Integer(string='Label Position P', default=0)
    
    all_pages = fields.Boolean(string='All Pages', default=False)

    @api.model
    def default_get(self, fields_list):
        res = super(NGSignTemplateSettings, self).default_get(fields_list)
        params = self.env['ir.config_parameter'].sudo()
        
        res.update({
            'qr_position_x': int(params.get_param('ngsign.qr_position_x', 10)),
            'qr_position_y': int(params.get_param('ngsign.qr_position_y', 10)),
            'qr_position_p': int(params.get_param('ngsign.qr_position_p', 0)),
            'qr_ratio': float(params.get_param('ngsign.qr_ratio', 0.5)),
            'text_position_x': int(params.get_param('ngsign.text_position_x', 40)),
            'text_position_y': int(params.get_param('ngsign.text_position_y', 40)),
            'text_page': int(params.get_param('ngsign.text_page', 0)),
            'label_position_x': int(params.get_param('ngsign.label_position_x', 150)),
            'label_position_y': int(params.get_param('ngsign.label_position_y', 10)),
            'label_position_p': int(params.get_param('ngsign.label_position_p', 0)),
            'all_pages': params.get_param('ngsign.all_pages', 'False') == 'True',
        })
        return res

    def action_save(self):
        params = self.env['ir.config_parameter'].sudo()
        params.set_param('ngsign.qr_position_x', self.qr_position_x)
        params.set_param('ngsign.qr_position_y', self.qr_position_y)
        params.set_param('ngsign.qr_position_p', self.qr_position_p)
        params.set_param('ngsign.qr_ratio', self.qr_ratio)
        params.set_param('ngsign.text_position_x', self.text_position_x)
        params.set_param('ngsign.text_position_y', self.text_position_y)
        params.set_param('ngsign.text_page', self.text_page)
        params.set_param('ngsign.label_position_x', self.label_position_x)
        params.set_param('ngsign.label_position_y', self.label_position_y)
        params.set_param('ngsign.label_position_p', self.label_position_p)
        params.set_param('ngsign.all_pages', self.all_pages)
        
        return {'type': 'ir.actions.act_window_close'}
