
from odoo import models, fields, api


class locations(models.Model):
    _name = 'parking_management.locations'
    _description = "Locations Record"
    name = fields.Char(string="Vị trí")
    tag_id = fields.Char(string="Tag ID")
    state = fields.Selection([('empty', 'Trống'), ('full', 'Đầy')], string="Trạng thái")
