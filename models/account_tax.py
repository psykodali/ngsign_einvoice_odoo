from odoo import models, fields

class AccountTax(models.Model):
    _inherit = 'account.tax'

    teif_code = fields.Selection([
        ('I-1602', 'TVA (VAT)'),
        ('I-162', 'FODEC'),
        ('I-161', 'DC (Droit de Consommation)'),
        ('I-1604', 'Retenue à la source'),
        ('I-1601', 'Timbre Fiscal'),
        ('I-1603', 'Taxe sur les séjours'),
        ('I-1605', 'TCL'),
        ('I-1606', 'Autre Taxe')
    ], string='TEIF Tax Code', help="Code used for Tunisian Electronic Invoice Format")
