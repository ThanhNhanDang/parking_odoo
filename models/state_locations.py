from odoo import fields, models

class state_locations(models.Model):
    _inherit = 'stock.location'
    state = fields.Selection([('empty', 'Trống'), ('full', 'Đầy')], string="Trạng thái", default='empty')

