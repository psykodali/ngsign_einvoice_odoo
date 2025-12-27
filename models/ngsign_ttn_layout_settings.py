from odoo import models, fields, api
from odoo.exceptions import UserError
import base64

class NGSignTTNLayoutSettings(models.TransientModel):
    _name = 'ngsign.ttn.layout.settings'
    _description = 'TTN Layout Configuration'

    # Company-specific related fields
    ngsign_qr_position_x = fields.Integer(
        related='company_id.ngsign_qr_position_x', 
        readonly=False, 
        string='QR Position X (mm)',
        help='Horizontal position of the QR code from the left edge'
    )
    ngsign_qr_position_y = fields.Integer(
        related='company_id.ngsign_qr_position_y', 
        readonly=False, 
        string='QR Position Y (mm)',
        help='Vertical position of the QR code from the top edge'
    )
    ngsign_label_position_x = fields.Integer(
        related='company_id.ngsign_label_position_x', 
        readonly=False, 
        string='Label Position X (mm)',
        help='Horizontal position of the TTN reference label from the left edge'
    )
    ngsign_label_position_y = fields.Integer(
        related='company_id.ngsign_label_position_y', 
        readonly=False, 
        string='Label Position Y (mm)',
        help='Vertical position of the TTN reference label from the top edge'
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
    
    preview_html = fields.Html(string='Preview', compute='_compute_preview_html', sanitize=False)
    
    @api.depends('ngsign_qr_position_x', 'ngsign_qr_position_y', 'ngsign_label_position_x', 'ngsign_label_position_y', 
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
                
                try:
                    # Use a Savepoint to mock data without committing
                    with self.env.cr.savepoint():
                        # 1. Force V2 Endpoint (required for report to show overlays)
                        self.env['ir.config_parameter'].sudo().set_param('ngsign.use_v2_endpoint', 'True')
                        
                        # 2. Update Company Settings with current Wizard values so report picks them up
                        # The report calls o.get_ngsign_print_config() which reads from company
                        sample_invoice.company_id.write({
                            'ngsign_qr_position_x': record.ngsign_qr_position_x,
                            'ngsign_qr_position_y': record.ngsign_qr_position_y,
                            'ngsign_label_position_x': record.ngsign_label_position_x,
                            'ngsign_label_position_y': record.ngsign_label_position_y,
                        })
                        
                        # 3. Mock NGSign data on the invoice record
                        dummy_qr = b'iVBORw0KGgoAAAANSUhEUgAAAJYAAACWAQMAAAAGz+OhAAAABlBMVEX///8AAABVwtN+AAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAJElEQVRIie3BAQ0AAADCoPdPbQ43oAAAAAAAAAAAAAAAAABwJjCgAAEx/46RAAAAAElFTkSuQmCC'
                        
                        sample_invoice.write({
                            'ngsign_status': 'TTN Signed',
                            'ngsign_ttn_reference': 'ABC123XYZ-PREVIEW',
                            'ngsign_ttn_qr_code': dummy_qr
                        })
                        
                        # Render the PDF
                        report_action = self.env.ref('account.account_invoices')
                        pdf_content, _ = report_action.with_context(force_report_rendering=True)._render_qweb_pdf(report_action, sample_invoice.ids)
                        
                        # Capture result
                        pdf_base64_result = base64.b64encode(pdf_content).decode('utf-8')
                        
                        # Force rollback to prevent saving changes
                        raise UserError("Rollback")
                        
                except UserError as e:
                    if str(e) == "Rollback":
                        pass # Expected rollback
                    else:
                        raise e
                except Exception as e:
                     import logging
                     _logger = logging.getLogger(__name__)
                     _logger.error(f"Error rendering PDF preview: {str(e)}")
                     error_message = str(e)
                
                # Assign field value AFTER rollback/context exit
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
        """Save and close the wizard - related fields auto-save to company"""
        return {'type': 'ir.actions.act_window_close'}
