# -*- coding: utf-8 -*-
{
    'name': "webhooks",

    'summary': "Webhooks for Odoo",

    'description': """
        Webhooks for Odoo
    """,

    'author': "Steve Liu",
    'website': "https://github.com/NexaMerchant/odoo_webhooks",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'web', 'bus', 'web_editor', 'product', 'sale', 'account', 'stock', 'purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'installable': True,
}

