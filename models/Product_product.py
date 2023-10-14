from odoo import api, fields, models

class Product_product(models.Model):
    _inherit = 'product.product'
    name = fields.Char(string="Biển số")
    responsible_id = fields.Many2one('res.partner', string="Chủ sở hữu")
    barcode = fields.Char(string="Mật khẩu")
    default_code = fields.Char(string="Mã định danh")

    