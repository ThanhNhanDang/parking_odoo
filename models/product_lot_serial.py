from odoo import fields, models

class stoct_lot(models.Model):
    _inherit = ['stock.lot']
    location_id_name  = fields.Many2one('stock.location', string="Vị Trí")
    state = fields.Char(string="Trạng Thái")

