from odoo import models, fields, api, _
from odoo.exceptions import UserError

class NgsignSignOptionsWizard(models.TransientModel):
    _name = 'ngsign.sign.options.wizard'
    _description = 'NGSign Signature Options'

    move_id = fields.Many2one('account.move', string='Invoice', required=True, default=lambda self: self.env.context.get('active_id'))
    action_type = fields.Selection([
        ('sign_now', 'Sign Now'),
        ('send', 'Send for Signature')
    ], string='Action', default='sign_now', required=True)
    
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
        if self.action_type == 'sign_now':
            if not self.can_sign_now:
                raise UserError(_("You don't have permission to sign invoices. Please configure authorized users in settings."))
            
            return {
                'type': 'ir.actions.client',
                'tag': 'ngsign_einvoice_odoo.action_sign_ngsign_js',
                'context': {
                    'active_ids': [self.move_id.id],
                    'ngsign_action_type': 'sign_now'
                },
            }
        elif self.action_type == 'send':
            if not self.authorized_user_id:
                raise UserError(_("Please select a user to send the signature link to."))
            
            return {
                'type': 'ir.actions.client',
                'tag': 'ngsign_einvoice_odoo.action_sign_ngsign_js',
                'context': {
                    'active_ids': [self.move_id.id],
                    'ngsign_action_type': 'send',
                    'ngsign_send_to_user_id': self.authorized_user_id.id,
                    'ngsign_send_to_user_name': self.authorized_user_id.name,
                },
            }
