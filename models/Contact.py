from odoo import api,fields, models
import logging
# import clr
# clr.AddReference("ClassLibrary1.dll")
# from ClassLibrary1 import Class1
# obj = Class1()
_logger = logging.getLogger(__name__)

class Contact(models.Model):
    _inherit = 'res.partner'
    display_name = fields.Char(string="Họ tên")
    vat = fields.Char(string="CMND/CCCD")
    phone = fields.Char(string="Số điện thoại")
    barcode = fields.Char(string="Mật khẩu")
    ref = fields.Char(string="Mã định danh")
   

    @api.model
    def create(self, vals):
        # Code before create: should use the 'vals' dict
        _logger.info('Create a %s with vals %s', self._name, vals)
        new_record = super(Contact,self).create(vals)
        return new_record
        #return "Nhanh"
    def write(self, vals):
        # Code before write: 'self' has the old values
        record = super(Contact,self).write(vals)
        # Code after write: can use 'self' with the updated
        # values
        _logger.info('Write a %s with vals %s', self._name, vals)
        return record