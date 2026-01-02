from odoo import models, fields, api
from odoo.exceptions import UserError
import base64
import logging

_logger = logging.getLogger(__name__)

class NGSignTTNLayoutSettings(models.TransientModel):
    _name = 'ngsign.ttn.layout.settings'

    _description = 'TTN Layout Configuration'

    # Company-specific related fields
    # Company-specific related fields
    ngsign_qr_position_type = fields.Selection([
        ('custom', 'Custom Coordinates'),
        ('builtin', 'Builtin Position')
    ], string='Position Type', default='custom')

    ngsign_qr_position_x = fields.Integer(
        string='QR Position X (mm)',
        help='Horizontal position of the QR code from the left edge'
    )
    ngsign_qr_position_y = fields.Integer(
        string='QR Position Y (mm)',
        help='Vertical position of the QR code from the top edge'
    )
    ngsign_label_position_x = fields.Integer(
        string='Label Position X (mm)',
        help='Horizontal position of the TTN reference label from the left edge'
    )
    ngsign_label_position_y = fields.Integer(
        string='Label Position Y (mm)',
        help='Vertical position of the TTN reference label from the top edge'
    )
    
    ngsign_qr_size = fields.Integer(
        string='QR Code Size (mm)',
        default=30
    )
    
    ngsign_label_width = fields.Integer(
        string='Label Width (mm)',
        default=50
    )
    
    ngsign_label_text = fields.Char(
        string='Label Prefix Text',
        default=''
    )
    
    ngsign_label_font_size = fields.Integer(
        string='Label Font Size (pt)',
        default=10
    )
    
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # Company layout fields
    company_logo = fields.Binary(related='company_id.logo', string='Company Logo')
    company_name = fields.Char(related='company_id.name', string='Company Name')
    primary_color = fields.Char(related='company_id.primary_color', string='Primary Color')
    secondary_color = fields.Char(related='company_id.secondary_color', string='Secondary Color')
    font = fields.Selection(related='company_id.font', string='Font')
    layout_background = fields.Selection(related='company_id.layout_background', string='Layout Background')
    external_report_layout_id = fields.Many2one(related='company_id.external_report_layout_id', string='Document Layout')
    
    preview_image = fields.Binary(string="Custom Preview Image", attachment=True, help="Upload a screenshot or image (PNG/JPG) of your invoice to use as the background. PDF files are NOT supported.")
    preview_image_name = fields.Char(string="Image Name")
    
    @api.model
    def default_get(self, fields_list):
        defaults = super(NGSignTTNLayoutSettings, self).default_get(fields_list)
        company = self.env.company
        
        if 'company_id' in fields_list:
            defaults['company_id'] = company.id
            
        # Manually load values because TransientModel doesn't always autopopulate related fields on create
        if 'ngsign_qr_position_type' in fields_list:
            defaults['ngsign_qr_position_type'] = company.ngsign_qr_position_type
        if 'ngsign_qr_position_x' in fields_list:
            defaults['ngsign_qr_position_x'] = company.ngsign_qr_position_x
        if 'ngsign_qr_position_y' in fields_list:
            defaults['ngsign_qr_position_y'] = company.ngsign_qr_position_y
        if 'ngsign_qr_size' in fields_list:
            defaults['ngsign_qr_size'] = company.ngsign_qr_size
            
        if 'ngsign_label_position_x' in fields_list:
            defaults['ngsign_label_position_x'] = company.ngsign_label_position_x
        if 'ngsign_label_position_y' in fields_list:
            defaults['ngsign_label_position_y'] = company.ngsign_label_position_y
        if 'ngsign_label_width' in fields_list:
            defaults['ngsign_label_width'] = company.ngsign_label_width
        if 'ngsign_label_text' in fields_list:
            defaults['ngsign_label_text'] = company.ngsign_label_text
        if 'ngsign_label_font_size' in fields_list:
            defaults['ngsign_label_font_size'] = company.ngsign_label_font_size
            
        return defaults
    

    preview_html = fields.Html(string='Preview', compute='_compute_preview_html', store=True, sanitize=False)
    @api.depends('ngsign_qr_position_x', 'ngsign_qr_position_y', 'ngsign_qr_size', 
                 'ngsign_label_position_x', 'ngsign_label_position_y', 'ngsign_label_width', 'ngsign_label_text', 'ngsign_label_font_size',
                 'company_logo', 'company_name', 'primary_color', 'secondary_color', 'font', 'layout_background', 'preview_image')
    def _compute_preview_html(self):
        for record in self:
            # Try to get a recent invoice to use as preview (Posted first, then Draft)
            domain = [
                ('move_type', '=', 'out_invoice'),
                ('company_id', '=', record.company_id.id),
                ('state', '!=', 'cancel')
            ]
            # Prefer posted invoices
            sample_invoice = self.env['account.move'].search(domain + [('state', '=', 'posted')], limit=1, order='id desc')
            
            # Fallback to draft if no posted invoice found
            if not sample_invoice:
                sample_invoice = self.env['account.move'].search(domain, limit=1, order='id desc')
            
            if sample_invoice:
                pdf_base64_result = None
                error_message = None
                
                old_invoice_vals = {
                    'ngsign_status': sample_invoice.ngsign_status,
                    'ngsign_ttn_reference': sample_invoice.ngsign_ttn_reference,
                    'ngsign_ttn_qr_code': sample_invoice.ngsign_ttn_qr_code,
                }
                
                try:
                    # Prepare preview config dictionary to inject via context
                    # This avoids writing to company settings in DB
                    preview_config = {
                        'qr_position_type': record.ngsign_qr_position_type,
                        'qr_position_x': record.ngsign_qr_position_x,
                        'qr_position_y': record.ngsign_qr_position_y,
                        'qr_size': record.ngsign_qr_size,
                        'label_position_x': record.ngsign_label_position_x,
                        'label_position_y': record.ngsign_label_position_y,
                        'label_width': record.ngsign_label_width,
                        'label_text': record.ngsign_label_text,
                        'label_font_size': record.ngsign_label_font_size,
                        'use_v2_endpoint': True, # Force V2 for overlays
                        'show_debug_info': self.env['ir.config_parameter'].sudo().get_param('ngsign.show_report_debug_info', 'False') == 'True'
                    }

                    # Mock NGSign data on the invoice record
                    # Better Dummy QR (1x1 Black Pixel, scaled by style) to ensure visibility and valid data
                    dummy_qr = b'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII='
                    
                    sample_invoice.sudo().write({
                        'ngsign_status': 'TTN Signed',
                        'ngsign_ttn_reference': 'ABC123XYZ-PREVIEW',
                        'ngsign_ttn_qr_code': dummy_qr
                    })
                    
                    # Render the PDF with injected configuration
                    report_action = self.env.ref('account.account_invoices')
                    
                    ctx = dict(self.env.context)
                    ctx.update({
                        'force_report_rendering': True,
                        'ngsign_preview_config': preview_config
                    })
                    
                    pdf_content, _ = report_action.sudo().with_context(ctx)._render_qweb_pdf(report_action, sample_invoice.ids)
                    
                    # Capture result
                    pdf_base64_result = base64.b64encode(pdf_content).decode('utf-8')
                        
                except Exception as e:
                     _logger.error(f"Error rendering PDF preview: {str(e)}")
                     error_message = str(e)
                finally:
                    # Revert mock invoice data
                    try:
                        sample_invoice.sudo().write(old_invoice_vals)
                    except Exception as revert_e:
                        _logger.error(f"Failed to revert invoice preview changes: {revert_e}")
                
                # Assign field value
                if pdf_base64_result:
                    record.preview_html = f'<iframe src="data:application/pdf;base64,{pdf_base64_result}#toolbar=0&navpanes=0&scrollbar=0" width="100%" height="900px" style="border: none;"></iframe>'
                elif error_message:
                    record.preview_html = f'<div style="padding: 50px; text-align: center; color: #d9534f;"><h3>Preview Error</h3><p>{error_message}</p></div>'
                else:
                    record.preview_html = f'<div style="padding: 50px; text-align: center; color: #d9534f;"><h3>Preview Error</h3><p>Unknown error occurred during PDF generation.</p></div>'
            else:
                 record.preview_html = '''
                    <div style="padding: 50px; text-align: center; color: #666; background: #f9f9f9; border-radius: 8px;">
                        <h3 style="margin-top: 0;">No Invoice Available for Preview</h3>
                        <p>Please create and save at least one invoice (even as draft) to see the preview.</p>
                    </div>
                '''

    def action_save(self):
        """Save and close the wizard - save fields to company"""
        company = self.env.company
        company.sudo().write({
            'ngsign_qr_position_type': self.ngsign_qr_position_type,
            'ngsign_qr_position_x': self.ngsign_qr_position_x,
            'ngsign_qr_position_y': self.ngsign_qr_position_y,
            'ngsign_qr_size': self.ngsign_qr_size,
            'ngsign_label_position_x': self.ngsign_label_position_x,
            'ngsign_label_position_y': self.ngsign_label_position_y,
            'ngsign_label_width': self.ngsign_label_width,
            'ngsign_label_text': self.ngsign_label_text,
            'ngsign_label_font_size': self.ngsign_label_font_size,
        })
        return {'type': 'ir.actions.act_window_close'}
        
    def action_apply(self):
        """Update the preview with current form values without saving to company"""
        # Since fields are stored, saving the record (automatic) triggers compute of preview_html.
        
        # Re-open the same wizard to keep it open and show updated fields
        return {
            'type': 'ir.actions.act_window',
            'name': 'TTN Layout Configuration',
            'res_model': 'ngsign.ttn.layout.settings',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_reset(self):
        """Reset form values to stored company settings"""
        company = self.env.company
        self.write({
            'ngsign_qr_position_type': company.ngsign_qr_position_type,
            'ngsign_qr_position_x': company.ngsign_qr_position_x,
            'ngsign_qr_position_y': company.ngsign_qr_position_y,
            'ngsign_qr_size': company.ngsign_qr_size,
            'ngsign_label_position_x': company.ngsign_label_position_x,
            'ngsign_label_position_y': company.ngsign_label_position_y,
            'ngsign_label_width': company.ngsign_label_width,
            'ngsign_label_text': company.ngsign_label_text,
            'ngsign_label_font_size': company.ngsign_label_font_size,
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
