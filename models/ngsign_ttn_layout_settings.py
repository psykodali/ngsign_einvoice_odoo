from odoo import models, fields, api

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
    
    preview_html = fields.Html(string='Preview', compute='_compute_preview_html')
    
    @api.depends('ngsign_qr_position_x', 'ngsign_qr_position_y', 'ngsign_label_position_x', 'ngsign_label_position_y', 
                 'company_logo', 'company_name', 'primary_color', 'secondary_color', 'font', 'layout_background', 'preview_image')
    def _compute_preview_html(self):
        for record in self:
            # Scale and positioning for overlay
            scale = 2.5  # 1mm = 2.5px
            qr_x = (record.ngsign_qr_position_x or 10) * scale
            qr_y = (record.ngsign_qr_position_y or 10) * scale
            label_x = (record.ngsign_label_position_x or 150) * scale
            label_y = (record.ngsign_label_position_y or 10) * scale
            qr_size = 30 * scale
            
            # Get primary color for overlay
            primary_color = record.primary_color or '#875A7B'
            
            background_content = ''
            
            if record.preview_image:
                # Use uploaded image
                background_content = f'<img src="data:image/png;base64,{record.preview_image.decode("utf-8") if isinstance(record.preview_image, bytes) else record.preview_image}" style="width: 100%; height: auto; display: block;"/>'
            else:
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
                    # Get the invoice report
                    report = self.env.ref('account.account_invoices')
                    
                    # Render the invoice HTML
                    try:
                        html_content = report._render_qweb_html(report, sample_invoice.ids)[0]
                        html_str = html_content.decode('utf-8') if isinstance(html_content, bytes) else html_content
                        # Inject CSS to fix logo size in preview
                        style_inject = '<style>img { max-width: 100% !important; height: auto !important; } .row { display: flex; flex-wrap: wrap; margin-right: -15px; margin-left: -15px; } .col-6 { flex: 0 0 50%; max-width: 50%; } </style>'
                        background_content = style_inject + html_str
                    except Exception as e:
                        import logging
                        _logger = logging.getLogger(__name__)
                        _logger.error(f"Error rendering invoice preview: {str(e)}")
                        background_content = f'<div style="padding: 50px; text-align: center; color: #666;"><h3>Unable to render invoice preview</h3><p style="color: #999; font-size: 12px;">Error: {str(e)}</p></div>'
                else:
                    background_content = '''
                        <div style="padding: 50px; text-align: center; color: #666; background: #f9f9f9; border-radius: 8px;">
                            <h3 style="margin-top: 0;">No Invoice Available for Preview</h3>
                            <p>Please create and save at least one invoice (even as draft) to see the preview.</p>
                            <p style="margin-top: 20px;">
                                <strong>Tip:</strong> You can also upload a custom image (PNG/JPG) of your invoice layout above.<br/>
                                <small>PDF uploads are not supported for preview.</small>
                            </p>
                        </div>
                    '''
            
            # Wrap in container with overlays
            record.preview_html = f'''
            <div style="position: relative; margin: 0 auto; max-width: 900px;">
                <!-- Background (Image or Rendered HTML) -->
                <div style="position: relative; transform: scale(0.8); transform-origin: top left; width: 125%;">
                    <div style="position: relative; border: 1px solid #ddd; box-shadow: 0 4px 12px rgba(0,0,0,0.15); min-height: 800px;">
                        {background_content}
                        
                        <!-- QR Code Overlay -->
                        <div style="position: absolute; left: {qr_x}px; top: {qr_y}px; width: {qr_size}px; height: {qr_size}px; border: 3px dashed #00a09d; background: rgba(0,160,157,0.15); display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 11px; color: #00a09d; font-weight: bold; z-index: 1000; pointer-events: none;">
                            <div>TTN</div>
                            <div>QR Code</div>
                            <div style="font-size: 8px; margin-top: 3px;">({record.ngsign_qr_position_x or 10}, {record.ngsign_qr_position_y or 10})</div>
                        </div>
                        
                        <!-- Label Overlay -->
                        <div style="position: absolute; left: {label_x}px; top: {label_y}px; padding: 8px 12px; border: 3px dashed {primary_color}; background: rgba(135,90,123,0.15); font-size: 10px; color: {primary_color}; font-weight: bold; white-space: nowrap; z-index: 1000; pointer-events: none;">
                            TTN: ABC123XYZ
                            <div style="font-size: 8px; margin-top: 2px;">({record.ngsign_label_position_x or 150}, {record.ngsign_label_position_y or 10})</div>
                        </div>
                    </div>
                </div>
                
                <!-- Info bar -->
                <div style="margin-top: 20px; text-align: center; background: rgba(255,255,255,0.95); padding: 12px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 11px; color: #666;">
                    <strong>Preview:</strong> Positions shown in millimeters from top-left corner
                </div>
            </div>
            '''
    
    def action_save(self):
        """Save and close the wizard - related fields auto-save to company"""
        return {'type': 'ir.actions.act_window_close'}
    
    def _generate_grid_lines(self, width, height, scale):
        """Generate grid lines every 50mm for reference"""
        lines = []
        step = 50 * scale  # 50mm grid
        
        # Vertical lines
        for x in range(int(step), int(width), int(step)):
            lines.append(f'<div style="position: absolute; left: {x}px; top: 0; width: 1px; height: 100%; background: rgba(200,200,200,0.3);"></div>')
        
        # Horizontal lines
        for y in range(int(step), int(height), int(step)):
            lines.append(f'<div style="position: absolute; left: 0; top: {y}px; width: 100%; height: 1px; background: rgba(200,200,200,0.3);"></div>')
        
        return ''.join(lines)
