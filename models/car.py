
from odoo import models, fields, api


class car(models.Model):
    _name = 'parking_management.car'
    _description = "Car Record"

    name = fields.Char(string="Tên Khách")
    number_plate = fields.Char(string="Biển số xe")
    tag_id = fields.Char(string="Tag ID", required=True)
    out_sum = fields.Integer(string="Tổng Ra")
    in_sum = fields.Integer(string="Tổng Vào")
    location = fields.Char(string="Vị trí")
    state = fields.Selection([('in', 'Vào'), ('out', 'Ra')], string="Trạng thái")
