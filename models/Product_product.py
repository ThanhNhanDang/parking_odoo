from odoo import api, fields, models


class Product_product(models.Model):
    _inherit = 'product.product'
    name = fields.Char(string="Biển số")
    responsible_id = fields.Many2one('res.partner', string="Chủ sở hữu")
    barcode = fields.Char(string="Mật khẩu")
    default_code = fields.Char(string="Mã định danh")
    check_doi_the = fields.Boolean(string="Đã đổi thẻ", default=False)
    activity_summary = fields.Char(string="Hãng xe", store=True)

    @api.constrains('barcode')
    def _check_barcode_uniqueness(self):
        return 0
