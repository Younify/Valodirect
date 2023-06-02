# -*- coding: utf-8 -*-

{
    'name': "Valo Vendor bill approval",
    'author': "REVO TECH",
    'summary': "",
    'description': "",
    'qweb': [],
    'demo': [],
    'depends': ['account','analytic', 'account_3way_match'],
    'data': [
        'security/account_security.xml',
        'security/ir.model.access.csv',
        'views/account_move_line.xml',
        'views/account_move.xml',
        'views/res_config_settings_views.xml',
        'views/product_template.xml',
        'wizards/account_move_approval_wizard.xml'
        ],
    'installable': True,
    'application': True,
    'license': 'OEEL-1',
}
