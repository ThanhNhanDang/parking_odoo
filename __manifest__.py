# -*- coding: utf-8 -*-
{
    'name': "parking",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/16.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'inventory',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'product', 'base','web'],
    "application": True,
    # always loaded
    'data': [
        "views/Contact.xml",
        "views/ProductTemplate.xml",
    ],
    'assets': {
        'web.assets_backend': [
            '/parking_odoo/static/src/scss/*.scss',
            '/parking_odoo/static/src/css/*.css',
            '/parking_odoo/static/src/js/*.js',
            # '/image_capture_upload_widget/static/src/js/image_upload.js',
            '/parking_odoo/static/src/xml/*.xml',
        ],
    },
}
