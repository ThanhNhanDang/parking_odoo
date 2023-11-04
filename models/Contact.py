import logging
from odoo import api, fields, models, http, exceptions
import uuid
import time
import json
import os
from websockets.sync.client import connect
import urllib.request


_logger = logging.getLogger(__name__)


def on_publish(client, userdata, mid):
    print("sent a message")


def create_product_move_history(state, product_id, location_id, location_dest_id, epc):
    stock_move_history = http.request.env["stock.move.line"].sudo().create(
        {'reference': state,
            'product_id': product_id,
            'reserved_uom_qty': 1.0,
            'lot_name': epc,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
            'qty_done': 1.0,
            'company_id': 1})


def check_cmnd_cccd_code_user(cmnd_cccd, signup_token):
    product = http.request.env['res.partner'].sudo().search(
        domain=["|", ('vat', '=', cmnd_cccd),
                ('signup_token', '=', signup_token)],
        limit=1)
    if not product:
        return 1
    if (product.vat == cmnd_cccd):
        return -2
    if (product.signup_token == signup_token):
        return -3


def save_user(vals, hex_arr):
    new_record = http.request.env['res.partner'].sudo().create({
        'image_1920': vals['image_1920'],
        'name':  vals['name'],
        'vat': vals['vat'],
        'phone': vals['phone'],
        'ref': "0" + hex_arr[1:24],
        'login': vals['vat'],
        'barcode': hex_arr[24:],
        'email': vals['email']
    })
    return


def on_message_callback(client, userdata, msg):
    global jsonLoad

    jsonLoad = json.loads(msg.payload.decode('utf-8'))

    _logger.info("%s", jsonLoad)


class Contact(models.Model):
    _inherit = 'res.partner'
    _sql_constraints = [
        ('field_unique',
         'unique(vat)',
         'CMND/CCCD ĐÃ TỒN TẠI!!'),
        ('field_unique',
         'unique(signup_token)',
         'MÃ ĐỊNH DANH ĐÃ TỒN TẠI!')
    ]

    display_name = fields.Char(string="Họ tên", required=False)
    name = fields.Char(string="Họ tên")
    vat = fields.Char(string="Số CMND/CCCD", required=True)
    phone = fields.Char(string="Số điện thoại", required=True)
    barcode = fields.Char(string="Mật khẩu")
    ref = fields.Char(string="Mã thẻ")
    employee = fields.Boolean(string="Cấp thẻ", default=False)
    signup_token = fields.Char(string="Mã định danh", required=True)

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
        new_record = super(Contact, self).create(vals)
        return new_record

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
