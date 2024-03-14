# -*- coding: utf-8 -*-
{
    'name': "parking",

    'summary': """
       Ứng dụng sử dụng cho bãi giữ xe, kế thừa những chức năng của những ứng dụng liên quan đến quản lý Kho.
       """,

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
    'depends': ['stock', 'product', 'base', 'web'],
    "application": True,
    # always loaded
    'data': [
        "views/Contact.xml",
        "views/ProductTemplate.xml",
        "views/StockLocation.xml",
        "views/StockMoveLine.xml",
    ],
    'assets': {
        'web.assets_backend': [
            '/parking_odoo/static/src/scss/*.scss',
            '/parking_odoo/static/src/js/*.js',
            # '/image_capture_upload_widget/static/src/js/image_upload.js',
            '/parking_odoo/static/src/xml/*.xml',
        ],
    },
}
