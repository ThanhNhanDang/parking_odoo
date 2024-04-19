import logging
from odoo import api, fields, models, http
import uuid
import json
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class Contact(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [
        ('vat_unique',
         'unique(vat)',
         'CMND/CCCD ĐÃ TỒN TẠI!!'),
        ('ma_dinh_danh_unique',
         'unique(ma_dinh_danh)',
         'MÃ ĐỊNH DANH ĐÃ TỒN TẠI!')
    ]
    display_name = fields.Char(string="Họ tên", required=False)
    name = fields.Char(string="Họ tên")
    vat = fields.Char(string="Số CMND/CCCD", required=True)

    phone = fields.Char(string="Số điện thoại", required=True)  
    barcode = fields.Char(string="Mật khẩu",readonly=False)
    ref = fields.Char(string="Mã thẻ",readonly=False)
    employee = fields.Boolean(string="Cấp thẻ", default=False)
    ma_dinh_danh = fields.Char(string="ID nhân viên", required=False, store=True)
    city = fields.Char(string="Địa chỉ", required=True)
    date_expiration = fields.Datetime(string="Ngày hết hạn", required=True)
    product_ids = fields.One2many("product.template", "contact_id", string="D/S xe",
                                  readonly=True)
    product_ids_public = fields.Many2many("product.template", relation="product_template_res_partner_rel", column1="res_partner_id", column2="product_template_id", string="D/S xe dùng chung",
                                          readonly=True)
    image_1920 = fields.Image(string="Ảnh đại diện",
                              max_width=1920, max_height=1920)
    image_1920_cmnd_cccd_truoc = fields.Image(
        string="Ảnh mặt trước CMND/CCCD", max_width=1920, max_height=1920)
    image_1920_cmnd_cccd_sau = fields.Image(
        string="Ảnh mặt sau CMND/CCCD", max_width=1920, max_height=1920)

    @api.model
    def create(self, vals):
        vals['date_expiration'] = fields.Datetime.now() + \
            relativedelta(months=1)
        new_record = super(Contact, self).create(vals)
        self.env["res.users"].create({'employee_ids': [], 'image_1920': vals['image_1920'], 'name': vals['name'], 'email': vals['email'],
                                     'login': vals['email'], 'company_id': 1, 'sel_groups_1_10_11': 11, 'active': True, 'partner_id': new_record.id, 'password': vals['phone']})
        return new_record
    
    @api.constrains('barcode')
    def _check_barcode_unicity(self):
        return 0

    def write(self, vals):
        # Code before write: 'self' has the old values
        record = super(Contact, self).write(vals)
        # Code after write: can use 'self' with the updated
        # values
        return record

    def createUUID(self):
        hex_arr = uuid.uuid4().hex
        check_epc_user = self.search(
            domain=[('ref', '=', "0" + hex_arr[1:24])],
            limit=1)
        if check_epc_user:
            return "LỖI: KHÔNG THỂ TẠO UUID DO BỊ ĐÃ TỒN TẠI [0" + hex_arr[1:24]+"]!!"
        message = "ghi epc|"+"0" + hex_arr[1:24] + "|"+hex_arr[24:]
        return message
