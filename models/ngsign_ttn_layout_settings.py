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
    
    preview_html = fields.Html(string='Preview', compute='_compute_preview_html')
    
    @api.depends('ngsign_qr_position_x', 'ngsign_qr_position_y', 'ngsign_label_position_x', 'ngsign_label_position_y', 
                 'company_logo', 'company_name', 'primary_color', 'secondary_color', 'font', 'layout_background')
    def _compute_preview_html(self):
        for record in self:
            # A4 dimensions: 210mm x 297mm
            # Scale factor for display (1mm = 2.5px for better visibility)
            scale = 2.5
            page_width = 210 * scale
            page_height = 297 * scale
            
            qr_x = (record.ngsign_qr_position_x or 10) * scale
            qr_y = (record.ngsign_qr_position_y or 10) * scale
            label_x = (record.ngsign_label_position_x or 150) * scale
            label_y = (record.ngsign_label_position_y or 10) * scale
            
            # QR code is typically 30mm
            qr_size = 30 * scale
            
            # Get company colors and styling
            primary_color = record.primary_color or '#875A7B'
            secondary_color = record.secondary_color or '#666666'
            company_name = record.company_name or 'Your Company'
            
            # Get company logo as base64
            logo_html = ''
            if record.company_logo:
                logo_html = f'<img src="data:image/png;base64,{record.company_logo.decode("utf-8") if isinstance(record.company_logo, bytes) else record.company_logo}" style="max-height: 60px; max-width: 150px;"/>'
            else:
                logo_html = f'<div style="font-size: 24px; font-weight: bold; color: {primary_color};">{company_name}</div>'
            
            # Font family based on selection
            font_family = 'Arial, sans-serif'
            if record.font:
                font_map = {
                    'Lato': 'Lato, sans-serif',
                    'Roboto': 'Roboto, sans-serif',
                    'Open_Sans': 'Open Sans, sans-serif',
                    'Montserrat': 'Montserrat, sans-serif',
                    'Oswald': 'Oswald, sans-serif',
                    'Raleway': 'Raleway, sans-serif',
                }
                font_family = font_map.get(record.font, font_family)
            
            # Background styling based on layout_background
            page_bg_style = 'background: white;'
            if record.layout_background == 'Geometric':
                page_bg_style = f'background: linear-gradient(135deg, {primary_color}15 0%, white 100%);'
            elif record.layout_background == 'Custom':
                page_bg_style = f'background: linear-gradient(to bottom, white 0%, {primary_color}08 100%);'
            
            record.preview_html = f'''
            <div style="position: relative; width: {page_width}px; height: {page_height}px; border: 1px solid #ddd; {page_bg_style} margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.15); overflow: hidden;">
                
                <!-- Invoice Template Background -->
                <div style="padding: 40px; font-family: {font_family}; font-size: 11px; color: #333;">
                    
                    <!-- Header -->
                    <div style="display: flex; justify-content: space-between; margin-bottom: 30px; border-bottom: 2px solid {primary_color}; padding-bottom: 15px;">
                        <div>
                            {logo_html}
                            <div style="margin-top: 8px; font-size: 10px; color: {secondary_color};">
                                123 Business Street<br/>
                                City, Country 12345<br/>
                                Phone: +1 234 567 890
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 28px; font-weight: bold; color: {primary_color};">INVOICE</div>
                            <div style="margin-top: 5px; font-size: 10px; color: {secondary_color};">
                                INV/2025/00001<br/>
                                Date: 27/12/2025
                            </div>
                        </div>
                    </div>
                    
                    <!-- Customer Info -->
                    <div style="margin-bottom: 25px;">
                        <div style="font-weight: bold; margin-bottom: 8px; color: {primary_color};">Bill To:</div>
                        <div style="font-size: 10px; color: {secondary_color};">
                            Customer Name<br/>
                            456 Customer Avenue<br/>
                            City, Country 54321
                        </div>
                    </div>
                    
                    <!-- Invoice Lines Table -->
                    <table style="width: 100%; border-collapse: collapse; margin-bottom: 25px; font-size: 10px;">
                        <thead>
                            <tr style="background: #f5f5f5; border-top: 1px solid #ddd; border-bottom: 1px solid #ddd;">
                                <th style="padding: 8px; text-align: left; color: {primary_color};">Description</th>
                                <th style="padding: 8px; text-align: right; color: {primary_color};">Quantity</th>
                                <th style="padding: 8px; text-align: right; color: {primary_color};">Unit Price</th>
                                <th style="padding: 8px; text-align: right; color: {primary_color};">Amount</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr style="border-bottom: 1px solid #eee;">
                                <td style="padding: 8px;">Product or Service</td>
                                <td style="padding: 8px; text-align: right;">2.00</td>
                                <td style="padding: 8px; text-align: right;">€50.00</td>
                                <td style="padding: 8px; text-align: right;">€100.00</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #eee;">
                                <td style="padding: 8px;">Another Product</td>
                                <td style="padding: 8px; text-align: right;">1.00</td>
                                <td style="padding: 8px; text-align: right;">€75.00</td>
                                <td style="padding: 8px; text-align: right;">€75.00</td>
                            </tr>
                        </tbody>
                    </table>
                    
                    <!-- Totals -->
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 20px;">
                        <div style="width: 200px;">
                            <div style="display: flex; justify-content: space-between; padding: 5px 0; font-size: 10px;">
                                <span>Subtotal:</span>
                                <span>€175.00</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 5px 0; font-size: 10px;">
                                <span>Tax (20%):</span>
                                <span>€35.00</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; padding: 8px 0; font-weight: bold; font-size: 12px; border-top: 2px solid {primary_color}; margin-top: 5px; color: {primary_color};">
                                <span>Total:</span>
                                <span>€210.00</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Footer -->
                    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px solid #ddd; font-size: 9px; color: #999; text-align: center;">
                        Thank you for your business
                    </div>
                </div>
                
                <!-- QR Code Overlay -->
                <div style="position: absolute; left: {qr_x}px; top: {qr_y}px; width: {qr_size}px; height: {qr_size}px; border: 3px dashed #00a09d; background: rgba(0,160,157,0.15); display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 11px; color: #00a09d; font-weight: bold; z-index: 10;">
                    <div>TTN</div>
                    <div>QR Code</div>
                    <div style="font-size: 8px; margin-top: 3px;">({record.ngsign_qr_position_x or 10}, {record.ngsign_qr_position_y or 10})</div>
                </div>
                
                <!-- Label Overlay -->
                <div style="position: absolute; left: {label_x}px; top: {label_y}px; padding: 8px 12px; border: 3px dashed {primary_color}; background: rgba(135,90,123,0.15); font-size: 10px; color: {primary_color}; font-weight: bold; white-space: nowrap; z-index: 10;">
                    TTN: ABC123XYZ
                    <div style="font-size: 8px; margin-top: 2px;">({record.ngsign_label_position_x or 150}, {record.ngsign_label_position_y or 10})</div>
                </div>
                
                <!-- Info overlay -->
                <div style="position: absolute; bottom: 10px; left: 50%; transform: translateX(-50%); background: rgba(255,255,255,0.95); padding: 8px 16px; border-radius: 4px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); font-size: 10px; color: #666; z-index: 5;">
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
