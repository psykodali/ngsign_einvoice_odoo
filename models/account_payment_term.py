from odoo import models, fields

class AccountPaymentTerm(models.Model):
    _inherit = 'account.payment.term'

    teif_code = fields.Selection([
        ('I-121', 'Paiement immédiat (Immediate)'),
        ('I-122', 'Paiement bancaire spécifique (Bank Specific)'),
        ('I-123', 'Paiement par n\'importe quelle banque (Any Bank)'),
        ('I-124', 'Paiement mixte (Mixed)'),
        ('I-125', 'Autre (Other)')
    ], string='TEIF Condition Code', help="Payment condition code for TEIF")
