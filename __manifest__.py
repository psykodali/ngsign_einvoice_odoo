{
    'name': 'NGSign e-invoice',
    "version": "18.0.1.0.0",
    'category': 'Accounting',
    'summary': 'Integration with NGSign for e-invoicing and SEAL signing',
    'description': """
        This module integrates Odoo with NGSign API to:
        - Generate TEIF compliant e-invoices
        - Sign invoices using NGSign SEAL (Electronic Seal)
        - Automatically enrich PDF with TTN QR code and reference
    """,
    'author': 'NGSIGN',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/account_move_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
