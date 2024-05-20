from odoo import api, fields, models, http, exceptions
import uuid
from odoo.tools import re
from odoo.exceptions import UserError

class  ProductColor2(models.Model):
    _name = 'product.color.main'
    _description = 'Product Color'
    # ----------------------------
    color_ids = fields.One2many('product.color.values',
                    inverse_name='color_id',  
                    index=True,
                    string="Color list")
    
    name        = fields.Char(string='Tên màu',store=True)
    html_color  = fields.Char('Mã màu',store=True)
    sequence    = fields.Integer('Sequence', default=0)
    
    
    @api.model
    def save_method(self):
        # Logic to save the form can be defined here
        return True
    
    # @api.constrains('html_color')
    # def _check_html_color_format(self):
    #     for record in self:
    #         if not re.match("^#[0-9a-fA-F]{6}$", record.html_color):
    #             raise UserError("Mã màu không hợp lệ. Vui lòng nhập đúng cú pháp '#RRGGBB'.")