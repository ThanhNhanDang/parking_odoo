import logging
from odoo import api, fields, models, http, exceptions
import uuid
import time
import json
import os
from websockets.sync.client import connect

_logger = logging.getLogger(__name__)

topic = "t4tek/odoo/uid"
jsonLoad = {"uid": -1, "mes": 0}


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


def check_exit_user(sEPC, cmnd_cccd, signup_token):
    product = http.request.env['res.partner'].sudo().search(
        domain=["|", ('ref', '=', sEPC), ('vat', '=', cmnd_cccd),
                ('signup_token', '=', signup_token)],
        limit=1)
    if not product:
        return 1
    if (product.ref == sEPC):
        return -1
    if (product.vat == cmnd_cccd):
        return -2
    if (product.signup_token == signup_token):
        return -3


def check_epc_user(sEPC):
    user = http.request.env['res.partner'].sudo().search(
        domain=[('ref', '=', sEPC)],
        limit=1)
    return user


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

    display_name = fields.Char(string="Họ tên", required=False)
    name = fields.Char(string="Họ tên")
    vat = fields.Char(string="Số CMND/CCCD", required=True)
    phone = fields.Char(string="Số điện thoại", required=True)
    barcode = fields.Char(string="Mật khẩu")
    ref = fields.Char(string="Mã thẻ")
    employee = fields.Boolean(string="Cấp thẻ", default=False)
    signup_token = fields.Char(string="Mã định danh", required=True)
    image_1920 = fields.Image(string="Ảnh đại diện",
                              max_width=1920, max_height=1920)
    image_1920_cmnd_cccd_truoc = fields.Image(
        string="Ảnh mặt trước CMND/CCCD", max_width=1920, max_height=1920)
    image_1920_cmnd_cccd_sau = fields.Image(
        string="Ảnh mặt sau CMND/CCCD", max_width=1920, max_height=1920)
    

    @api.model
    def create(self, vals):
        result = check_cmnd_cccd_code_user(vals['vat'], vals['signup_token'])
        if result == -2:
            raise exceptions.UserError("CMND/CCCD ĐÃ TỒN TẠI!")
        if result == -3:
            raise exceptions.UserError("MÃ ĐỊNH DANH ĐÃ TỒN TẠI!")
        if result == 1:  # Thẻ không tồn tại
            new_record = super(Contact, self).create({'image_1920': vals['image_1920'],
                                                      'name':  vals['name'],
                                                      'vat': vals['vat'],
                                                      'phone': vals['phone'],
                                                      'signup_token': vals['signup_token'],
                                                      'display_name': vals['name'],
                                                      'email': vals['email'],
                                                      'image_1920_cmnd_cccd_truoc': vals['image_1920_cmnd_cccd_truoc'],
                                                      'image_1920_cmnd_cccd_sau': vals['image_1920_cmnd_cccd_sau']
                                                      })
            return new_record

    def write(self, vals):
        # Code before write: 'self' has the old values
        record = super(Contact, self).write(vals)
        # Code after write: can use 'self' with the updated
        # values
        _logger.info('Write a %s', self._name)
        return record

    def quet_the(self):
        HOST = "localhost"
        REMOTE_PORT = http.request.httprequest.environ['REMOTE_PORT']
        PORT = 62536  # The port used by the server
        _logger.info(HOST)
        with connect("ws://"+HOST+":"+str(62536)+"/") as websocket:
            websocket.send("Hello world!")
            message = websocket.recv()
            print(f"Received: {message}")
            # raise exceptions.UserError("CHƯA CÀI ĐẶT PLUGIN!!")
        
        # #Nhận được dữ liệu từ server gửi tới
        # content = s.recv(1024).decode()
        # if ':' in content:
        #     s.close()
        #     raise exceptions.UserError(content)

        # user = check_epc_user(content)
        # if user:
        #     raise exceptions.UserError("LỖI: THẺ ĐÃ TỒN TẠI!!")
        # hex_arr = uuid.uuid4().hex
        # if check_epc_user("0" + hex_arr[1:24]):
        #     raise exceptions.UserError(
        #         "Không thể tạo được UUID liên hệ nhà phát triển để sử lý")

        # message = "ghi the|"+"0" + hex_arr[1:24] +"|"+hex_arr[24:] # quét thẻ người
        # s.send(message.encode())
        # content = s.recv(1024).decode()
        # if ':' in content:
        #     s.close()
        #     raise exceptions.UserError(content)
        # s.close()
        # super(Contact, self).write({
        #     'ref' : "0" + hex_arr[1:24],
        #     'barcode': hex_arr[24:],
        #     'employee': True
        # })



        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'display_notification',
        #     'params': {
        #         'message': content + "| Quét thành công",
        #         'type': 'success',
        #         'sticky': False,
        #     }
        # }

    def doi_the(self):

        HOST = http.request.httprequest.environ['REMOTE_ADDR']
        REMOTE_PORT = http.request.httprequest.environ['REMOTE_PORT']
        PORT = 62536  # The port used by the server
        _logger.info(HOST)
        s = socket.socket()
        try:
            s.connect((HOST, PORT)) #lắng nghe ở cổng 12536
        except:
            raise exceptions.UserError("CHƯA CÀI ĐẶT PLUGIN!!")
        
        #Nhập vào tên file 
        
        #Gửi tên file cho server
        message = "quet the|false" # quét thẻ người
        s.send(message.encode())

        #Nhận được dữ liệu từ server gửi tới
        content = s.recv(1024).decode()
        if ':' in content:
            s.close()
            raise exceptions.UserError(content)

        user = check_epc_user(content)
        if user:
            raise exceptions.UserError("LỖI: THẺ ĐÃ TỒN TẠI!!")
        hex_arr = uuid.uuid4().hex
        if check_epc_user("0" + hex_arr[1:24]):
            raise exceptions.UserError(
                "Không thể tạo được UUID liên hệ nhà phát triển để sử lý")

        message = "ghi the|"+"0" + hex_arr[1:24] +"|"+hex_arr[24:] # quét thẻ người
        s.send(message.encode())
        content = s.recv(1024).decode()
        if ':' in content:
            s.close()
            raise exceptions.UserError(content)
        s.close()
        super(Contact, self).write({
            'ref' : "0" + hex_arr[1:24],
            'barcode': hex_arr[24:],
            'employee': True
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': content,
                'type': 'success',
                'sticky': False,
            }
        }




        # global jsonLoad
        # hex_arr = uuid.uuid4().hex
        # if check_epc_user("0" + hex_arr[1:24]):
        #     raise exceptions.UserError(
        #         "Không thể tạo được UUID liên hệ nhà phát triển để sử lý")

        # msg = json.dumps({
        #     'sEPC': "0" + hex_arr[1:24], 'cmnd_cccd': self.vat, 'password': hex_arr[24:], 'is_car': False
        # })
        # info = Contact.mqttClient.publish(
        #     topic=topic+'/'+str(self.env.uid),
        #     payload=msg.encode('utf-8'),
        #     qos=0,
        # )
        # # Because published() is not synchronous,
        # # it returns false while he is not aware of delivery that's why calling wait_for_publish() is mandatory.
        # info.wait_for_publish()
        # if (jsonLoad['uid'] == self.env.uid):
        #     mes = jsonLoad['mes']
        #     if (mes == 4):
        #         raise exceptions.UserError("KHÔNG PHÁT HIỆN ĐẦU ĐỌC!")
        #     elif (mes == 2):
        #         raise exceptions.UserError("KHÔNG PHÁT HIỆN THẺ!")
        #     elif (mes == 3):
        #         self.write({
        #             "barcode":  hex_arr[24:],
        #             "ref": "0" + hex_arr[1:24],
        #             "employee": True
        #         })

        #         return 
        # while (jsonLoad['uid'] == -1):
        #     if (jsonLoad['uid'] == self.env.uid):
        #         mes = jsonLoad['mes']
        #         if (mes == 4):
        #             raise exceptions.UserError("KHÔNG PHÁT HIỆN ĐẦU ĐỌC!")
        #         elif (mes == 2):
        #             raise exceptions.UserError("KHÔNG PHÁT HIỆN THẺ!")
        #         elif (mes == 3):
        #             self.write({
        #                 "barcode":  hex_arr[24:],
        #                 "ref": "0" + hex_arr[1:24],
        #                 "employee": True
        #             })

        #             return 
        #         break

    def action_new_product(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.product_template_action_product")
        return action
