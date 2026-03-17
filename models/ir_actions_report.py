import base64
import logging
from odoo import models, api

_logger = logging.getLogger(__name__)

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    @api.model
    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        if not res_ids or len(res_ids) != 1:
            return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
            
        if isinstance(report_ref, str):
            report_name = report_ref
        else:
            report_name = report_ref.report_name
            
        # We only override for standard invoice reports
        if report_name not in ['account.report_invoice_with_payments', 'account.report_invoice']:
            return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)

        # If printing a single invoice that is TTN Signed, we return the downloaded PDF
        move = self.env['account.move'].browse(res_ids[0])
        if move.ngsign_status == 'TTN Signed':
            attachment_name = f"{move.name}_signed.pdf"
            attachment = self.env['ir.attachment'].search([
                ('res_model', '=', 'account.move'),
                ('res_id', '=', move.id),
                ('name', '=', attachment_name)
            ], limit=1)
            
            if attachment:
                _logger.info(f"Returning downloaded NGSign PDF for invoice {move.name}")
                pdf_content = base64.b64decode(attachment.datas)
                return pdf_content, 'pdf'
                
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
