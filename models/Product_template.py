from odoo import api, fields, models

class Product_template(models.Model):
    _inherit = 'product.template'
    name = fields.Char(string="Biển số")
    responsible_id = fields.Many2one('res.users', string="Chủ sở hữu")
    barcode = fields.Char(string="Mật khẩu")
    default_code = fields.Char(string="Mã định danh")
    user_ids = fields.Many2many('res.users', string="Danh sách người dùng xe")
