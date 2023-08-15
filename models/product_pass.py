from odoo import fields, models

class product_pass(models.Model):
    _inherit = 'product.template'
    password = fields.Char(string="Mật khẩu")

