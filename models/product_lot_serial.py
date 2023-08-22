from odoo import fields, models

class stoct_lot(models.Model):
    _inherit = 'stock.lot'
    location_id  = fields.Many2one('stock.location', string="Vị Trí",default=55)
    state = fields.Char(string="Trạng Thái")

