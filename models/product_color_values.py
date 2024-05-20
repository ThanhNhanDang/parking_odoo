from odoo import api, fields, models, http, exceptions
import uuid
import logging
_logger = logging.getLogger(__name__)


class  ProductColorValue(models.Model):
    _name = 'product.color.values'
    _description = 'Product Color Values'
    color_id = fields.Many2one(
        'product.color.main', 'Thuộc tính', 
        domain="[('color_ids', '=', color_ids)]",
        change_default=True)
    name = fields.Char(string="Tên màu", )
    html_color = fields.Char(string="Mã màu",
                             ) 
    # placeholder="Nhập mã màu..."
    
    # @api.model
    # def create(self, vals):
    #     new_record = super(ProductColorValue, self).create(vals)
    #     return new_record
    
    