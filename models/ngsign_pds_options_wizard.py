from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class NgsignPdsOptionsWizard(models.TransientModel):
    _name = 'ngsign.pds.options.wizard'
    _description = 'NGSign Signing Page Options'

    move_id = fields.Many2one('account.move', string='Invoice', required=True, default=lambda self: self.env.context.get('active_id'))
    action_type = fields.Selection([
        ('open_pds', 'Open Signing Page'),
        ('send_email', 'Send via Email')
    ], string='Action', default='open_pds', required=True)
    
    authorized_user_id = fields.Many2one(
        'res.users', 
        string='Select User', 
        domain="[('id', 'in', authorized_user_ids)]"
    )
    authorized_user_ids = fields.Many2many('res.users', compute='_compute_authorized_user_ids')
    
    can_sign_now = fields.Boolean(compute='_compute_can_sign_now')

    @api.depends('action_type')
    def _compute_authorized_user_ids(self):
        auth_users = self.env['ir.config_parameter'].sudo().get_param('ngsign.authorized_users', '')
        auth_users_ids = [int(u) for u in auth_users.split(',')] if auth_users else []
        for wiz in self:
            wiz.authorized_user_ids = [(6, 0, auth_users_ids)]

    @api.depends('action_type', 'authorized_user_ids')
    def _compute_can_sign_now(self):
        for wiz in self:
            if not wiz.authorized_user_ids:
                wiz.can_sign_now = True
            else:
                wiz.can_sign_now = self.env.user.id in wiz.authorized_user_ids.ids

    def action_confirm(self):
        self.ensure_one()
        if self.action_type == 'open_pds':
            if not self.can_sign_now:
                raise UserError(_("You don't have permission to sign invoices. Please configure authorized users in settings."))
            
            if not self.move_id.ngsign_pds_url:
                raise UserError(_("No Signing Page URL found for this invoice."))
                
            return {
                'type': 'ir.actions.act_url',
                'url': self.move_id.ngsign_pds_url,
                'target': 'new',
            }
        elif self.action_type == 'send_email':
            if not self.authorized_user_id:
                raise UserError(_("Please select a user to send the signature link to."))
            
            if not self.move_id.ngsign_pds_url:
                raise UserError(_("No Signing Page URL found for this invoice."))
            
            params = self.env['ir.config_parameter'].sudo()
            template_id_str = params.get_param('ngsign.email_template_id')
            if template_id_str:
                template = self.env['mail.template'].browse(int(template_id_str))
                if template.exists():
                    try:
                        template.sudo().with_context(
                            ngsign_pds_url=self.move_id.ngsign_pds_url,
                            ngsign_send_to_user_name=self.authorized_user_id.name
                        ).send_mail(self.move_id.id, force_send=True, email_values={'email_to': self.authorized_user_id.email})
                        _logger.info(f"NGSign: Sent signature request email to {self.authorized_user_id.email}")
                        
                        # Add notification logic
                        return {
                            'type': 'ir.actions.client',
                            'tag': 'display_notification',
                            'params': {
                                'title': _('Email Sent'),
                                'message': _('Signature request email was successfully sent to %s.') % self.authorized_user_id.name,
                                'type': 'success',
                                'sticky': False,
                                'next': {'type': 'ir.actions.act_window_close'},
                            }
                        }
                    except Exception as e:
                        _logger.error(f"NGSign: Failed to send signature email: {e}")
                        raise UserError(_("Failed to send signature email: %s") % str(e))
                else:
                    raise UserError(_("Configured email template does not exist. Please check Settings."))
            else:
                raise UserError(_("No email template configured. Please set one in Settings."))
