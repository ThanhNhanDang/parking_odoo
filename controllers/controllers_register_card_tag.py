# -*- coding: utf-8 -*-
from odoo import http

def check_epc_user(ma_the):
    user = http.request.env['res.partner'].sudo().search(
        domain=[('ref', '=', ma_the)],
        limit=1)
    return user



def check_bien_so_xe(bien_so):
    xe = http.request.env['product.template'].sudo().search(
        domain=[('name', '=', bien_so)],
        limit=1)
    return xe

class ControllerRegisterCardTag(http.Controller):

    @http.route('/parking/get/car_by_bien_so', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def get_car_by_bien_so(self, **kw):
        xe = check_bien_so_xe(kw['bien_so'])
        if not xe:
            return "BIỂN SỐ KHÔNG TỒN TẠI!"
        return xe

    @http.route('/parking/get/car_by_the_nguoi', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def get_car_the_nguoi(self, **kw):
        user = check_epc_user(kw['ma_the'])
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