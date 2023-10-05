# -*- coding: utf-8 -*-
{
    'name': "ValoDirect Vendor Bill Approval",
    'author': "REVO TECH & Younify",
    'summary': "",
    'description': "",
    'category': "Account",
    'depends': ['account', 'analytic', 'account_3way_match'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_analytic_line.xml',
        'views/account_move.xml',
        'views/account_move_line.xml',
        'views/product_template.xml',
        'views/res_config_settings_views.xml',
        'views/report_saleorder_document.xml',
        'wizards/account_move_approval_wizard.xml'
    ],
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
}
