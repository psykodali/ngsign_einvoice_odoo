from odoo import models, fields, api

class NGSignDeveloperSettings(models.TransientModel):
    _name = 'ngsign.developer.settings'
    _description = 'NGSign Developer Settings'

    show_debug_json_button = fields.Boolean(string='Show "Generate Debug JSON" button')
    show_transaction_uuid = fields.Boolean(string='Show NGSign Transaction UUID')
    show_invoice_uuid = fields.Boolean(string='Show NGSign Invoice UUID')
    generate_pdf_debug = fields.Boolean(string='Generate PDF when debugging', help='Include base64 PDF in debug JSON')
    show_report_debug_info = fields.Boolean(string='Show Report Debug Info', help='Show yellow debug box with variable values on invoice report')
    use_v2_endpoint = fields.Boolean(string='Use V2 Seal Endpoint', help='Use V2 endpoint (no PDF upload, local stamping)')

    @api.model
    def default_get(self, fields_list):
        res = super(NGSignDeveloperSettings, self).default_get(fields_list)
        params = self.env['ir.config_parameter'].sudo()
        
        # Load existing values
        res.update({
            'show_debug_json_button': params.get_param('ngsign.show_debug_json_button', 'False') == 'True',
            'show_transaction_uuid': params.get_param('ngsign.show_transaction_uuid', 'False') == 'True',
            'show_invoice_uuid': params.get_param('ngsign.show_invoice_uuid', 'False') == 'True',
            'generate_pdf_debug': params.get_param('ngsign.debug_include_pdf', 'False') == 'True',
            'show_report_debug_info': params.get_param('ngsign.show_report_debug_info', 'False') == 'True',
            'use_v2_endpoint': params.get_param('ngsign.use_v2_endpoint', 'False') == 'True',
        })
        return res

    def action_save(self):
        params = self.env['ir.config_parameter'].sudo()
        
        params.set_param('ngsign.show_debug_json_button', str(self.show_debug_json_button))
        params.set_param('ngsign.show_transaction_uuid', str(self.show_transaction_uuid))
        params.set_param('ngsign.show_invoice_uuid', str(self.show_invoice_uuid))
        params.set_param('ngsign.debug_include_pdf', str(self.generate_pdf_debug))
        params.set_param('ngsign.show_report_debug_info', str(self.show_report_debug_info))
        params.set_param('ngsign.use_v2_endpoint', str(self.use_v2_endpoint))
        
        return {'type': 'ir.actions.act_window_close'}
