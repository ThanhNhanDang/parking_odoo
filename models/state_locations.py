from odoo import fields, models


class state_locations(models.Model):
    _inherit = 'stock.location'

    state = fields.Selection(
        [('empty', 'Trống'), ('full', 'Đầy')], string="Trạng thái", default='empty')
    product_id_name = fields.Many2one(
        'product.product', string="Biển số", default=211)
    # product_name  = fields.Many2one('stock.lot', string="Biển số",relation="product_id")
    lot_name = fields.Many2one('stock.lot', string="Mã định danh", default=63)
