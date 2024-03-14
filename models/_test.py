from odoo import models,fields
import logging
_logger = logging.getLogger(__name__)

class Product_template_test(models.Model):
    _inherit = 'product.template'
    barcode  = fields.Char(string="Mật khẩu sửa")
    barcode2  = fields.Char(string="Mật khẩu hai", readonly=True)

    