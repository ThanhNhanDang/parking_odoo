# -*- coding: utf-8 -*-
from odoo import http, exceptions
import uuid
import base64
import json
import os


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


def check_exist_product(sEPC, cmnd_cccd):
    product = http.request.env['res.partner'].sudo().search(
        domain=["|", ('ref', '=', sEPC), ('vat', '=', cmnd_cccd)],
        limit=1)
    if not product:
        return 1
    if (product.ref == sEPC):
        return -1
    if (product.vat == cmnd_cccd):
        return -2


def check_epc_user(ma_dinh_danh):
    user = http.request.env['res.partner'].sudo().search(
        domain=[('ref', '=', ma_dinh_danh)],
        limit=1)
    return user


def check_cmnd_cccd_product(cmnd_cccd):
    user = http.request.env['res.partner'].sudo().search(
        domain=[('vat', '=', cmnd_cccd)],
        limit=1)
    return user


def check_bien_so_xe(bien_so):
    xe = http.request.env['product.template'].sudo().search(
        domain=[('name', '=', bien_so)],
        limit=1)
    return xe


def check_exist_xe(bien_so, ma_dinh_danh):
    xe = http.request.env['product.product'].sudo().search(
        domain=['|', ('default_code', '=', ma_dinh_danh),
                ("name", "=", bien_so)],
        limit=1)
    if not xe:
        return 1
    if (xe.default_code == ma_dinh_danh):
        return -1
    if (xe.name == bien_so):
        return -2


def check_epc_xe(ma_dinh_danh):
    xe = http.request.env['product.product'].sudo().search(
        domain=[('default_code', '=', ma_dinh_danh)],
        limit=1)
    return xe


def contains(list, filter):
    for x in list:
        if filter(x):
            return x
    return None
    # do stuff

class ControllerRegisterCardTag(http.Controller):

    # @http.route('/parking/test', website=False, csrf=False, type='json', methods=['POST'], auth='public')
    # def test(self, **kw):
    #     return obj.SayHello(kw["name"])
    @http.route('/parking/user/update/card', website=False, csrf=False, type='json',  auth='public', methods=['POST'])
    def users_save(self, **kw):
        user = check_epc_user(kw['sEPC_card'])
        if user:
            return "THẺ ĐÃ TỒN TẠI!"
        return "1"

    @http.route('/parking/update/person', website=False, csrf=False, type='http', methods=['POST'],  auth='public')
    def update_person(self, **kw):
        user = check_epc_user(kw['ma_dinh_danh'])
        if user:
            return "THẺ ĐÃ TỒN TẠI!"
        user = check_cmnd_cccd_product(kw['cmnd_cccd'])
        if not user:
            return "CMND/CCCD KHÔNG TỒN TẠI!"
        hex_arr = uuid.uuid4().hex
        if check_epc_user("0" + hex_arr[1:24]):
            return "Không thể tạo được UUID liên hệ nhà phát triển để sử lý"
        file = kw['image']
        img_attachment = file.read()
        user.write({
            'phone': kw['sdt'],
            'barcode': hex_arr[24:],
            "ref": "0" + hex_arr[1:24],
            'email': kw['email'],
            'image_1920': base64.b64encode(img_attachment),
        })
        return json.dumps({
            "ma_dinh_danh": user.ref, "password": user.barcode
        })

    @http.route('/parking/product/save', website=False, csrf=False, type='http',  auth='public', methods=['POST'])
    def product_save(self, **kw):
        result = check_exist_xe(kw['bien_so'], kw['ma_dinh_danh'])
        if result == -1:
            return "THẺ ĐÃ TỒN TẠI!"
        if result == -2:
            return "BIỂN SỐ ĐÃ TỒN TẠI!"
        hex_arr = uuid.uuid4().hex
        if check_epc_xe("0" + hex_arr[1:24]):
            return "Không thể tạo được UUID liên hệ nhà phát triển để sử lý"
        file = kw['image']
        img_attachment = file.read()
        product_create = http.request.env['product.template'].sudo().create({
            'name':  kw['bien_so'],
            'image_1920': base64.b64encode(img_attachment),
            'default_code': "1" + hex_arr[1:24],
            'responsible_id': int(kw['users_id']),
            'barcode': hex_arr[24:],
            'user_ids': [(4, int(kw['users_id']))],
            'detailed_type': 'product'
        })
        product_create.product_variant_id.write({
            'name':  kw['bien_so'],
            'responsible_id': int(kw['users_id']),
        })
        create_product_move_history(
            "BX/OUT", product_create.product_variant_id.id, 4, 5, kw['ma_dinh_danh'])
        return json.dumps({
            "ma_dinh_danh": product_create.default_code, "password": product_create.barcode
        })

    @http.route('/parking/get/car_by_bien_so', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def get_car_by_bien_so(self, **kw):
        xe = check_bien_so_xe(kw['bien_so'])
        if not xe:
            return "BIỂN SỐ KHÔNG TỒN TẠI!"
        return xe

    @http.route('/parking/get/car_by_the_nguoi', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def get_car_the_nguoi(self, **kw):
        user = check_epc_user(kw['ma_dinh_danh'])
        if not user:
            return "THẺ KHÔNG TỒN TẠI!"
        result = http.request.env['product.template'].sudo().search(
            domain=[('responsible_id', '=', user.id)])
        if not result:
            return "NGƯỜI DÙNG CHƯA ĐĂNG KÝ XE!"
        bien_so = []
        images = []
        for car in result:
            bien_so.append(car.name)
            images.append(car.image_1920)
        return {
            "id": user.id,
            "name": user.name,
            "cmnd_cccd": user.vat,
            "sdt": user.phone,
            "cars": bien_so,
            "images": images,
            "image": user.image_1920
        }
    @http.route('/parking/update/car', website=False, csrf=False, type='http', methods=['POST'],  auth='public')
    def update_car(self, **kw):
        xe = check_exist_xe(kw['bien_so'], kw['ma_dinh_danh'])
        if (xe == -1):
            return "THẺ XE ĐÃ TỒN TẠI!"
        if xe == -2:
            hex_arr = uuid.uuid4().hex
            if check_epc_xe("0" + hex_arr[1:24]):
                return "Không thể tạo được UUID liên hệ nhà phát triển để sử lý"
            xe = check_bien_so_xe(kw['bien_so'])
            file = kw['image']
            img_attachment = file.read()
            xe.write({
                'default_code': "1" + hex_arr[1:24],
                'barcode': hex_arr[24:],
                'image_1920': base64.b64encode(img_attachment),
            })
            return json.dumps({
                "ma_dinh_danh": xe.default_code, "password": xe.barcode
            })
        return "XE KHÔNG TỒN TẠI!"

    @http.route('/parking/car/add/user', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def update_car_add_user(self, **kw):
        xe = check_bien_so_xe(kw['bien_so'])
        if not xe:
            return "XE KHÔNG TỒN TẠI"
        user = contains(xe.user_ids, lambda user: user.id ==
                        int(kw['users_id']))
        if user:
            return "NGƯỜI DÙNG ĐÃ ĐƯỢC THÊM"
        xe.write({
            'user_ids': [(4, int(kw['users_id']))]
        })
        return "1"

    @http.route('/parking/car/users/is_match', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def car_users(self, **kw):
        xe = check_epc_xe(kw['ma_dinh_danh_xe'])
        if not xe:
            return "XE KHÔNG TỒN TẠI!!"
        user = contains(xe.user_ids, lambda user: user.ref ==
                        kw['ma_dinh_danh_ng'])
        if not user:
            return "BIỂN SỐ ["+xe.name+"] KHÔNG TRÙNG VỚI THẺ NGƯỜI!!"
        return {
            'password_xe': xe.barcode,
            'password_ng': user.barcode,
        }
