# -*- coding: utf-8 -*-
from odoo import http
import uuid
from datetime import date
import os
import logging
_logger = logging.getLogger(__name__)


def create_product_move_history(state, product_id, location_id):
    stock_move_history = http.request.env["stock.move.line"].sudo().create(
        {'reference': state,
         'product_id': product_id,
         'reserved_uom_qty': 1.0,
         'location_id': location_id,
         'qty_done': 1.0,
         'company_id': 1})


def find_location_empty():
    # Tìm danh sách vị trí trống trong bãi lấy danh sách tên của bãi
    locations_empty = http.request.env["stock.location"].sudo().search([
        ('state', '=', 'empty')])
    # Tìm danh vị trí trống đầu tiên trong danh sách
    for location_empty in locations_empty:
        _logger.info(location_empty)
        # Có nhiều bãi xe nên tìm bãi xe của mình
        # Tìm bãi xe trống đầu tiên rồi cập nhật danh sách trống
        location = location_empty.complete_name.split('/')
        # Tìm BX của mình và tìm Bãi nào có định dạng là 3 phần tử
        # BX\A\A1 or BX\B\B2

        if 'BX' in location and len(location) > 2 and location_empty.state == 'empty':
            return location_empty
    return []


def create_product_move_history2():
    location_empty = find_location_empty()

    if not location_empty:
        return
    location_empty.write({'product_id': 1})
    stock_move_history = http.request.env["stock.move.line"].sudo().create(
        {
            'picking_code': 'incoming',
            'product_id': 1,
            'contact_id': 8,
            'location_id': location_empty.id,
            'location_dest_id': location_empty.id,
            'company_id': 1,
        })
    return stock_move_history


def get_all_move_history_by_day(epc):
    move_histories = http.request.env['stock.move.line'].sudo().search_read(
        domain=[('lot_name', '=', epc)],
        fields=['date', 'lot_name', 'reference',
                'location_id', 'location_dest_id'],
        order="id desc",
        limit=20
    )
    today = date.today()

    res = [move_history for move_history in move_histories if move_history['date'].date()
           == today]
    return res


def update_stock_lot(sEPC, state, location_dest_id):
    serial_ids = http.request.env["stock.lot"].sudo().search(
        [('name', '=', sEPC)])
    serial_ids.write(
        {'state': state, 'location_id': location_dest_id})


def update_location(state, location_dest_id, product_id, product_lot_id):
    locations_empty = http.request.env["stock.location"].sudo().search([
        ('id', '=', location_dest_id)])
    locations_empty.write(
        {'state': state, 'product_id_name': product_id, 'lot_name': product_lot_id})


class ControllerProduct(http.Controller):
    @http.route('/parking/post/check_product', website=False, csrf=False, type='json', methods=['POST'], auth='public')
    def parking_create_product(self, **kw):
        serial_ids = http.request.env["stock.lot"].sudo().search(
            [('name', '=', kw['sEPC'])])
        if not serial_ids:
            # Tìm danh sách vị trí trống trong bãi lấy danh sách tên của bãi
            locations_empty = http.request.env["stock.location"].sudo().search([
                ('state', '=', 'empty')])
            # Tìm danh vị trí trống đầu tiên trong danh sách
            for location_empty in locations_empty:
               # Có nhiều bãi xe nên tìm bãi xe của mình
               # Tìm bãi xe trống đầu tiên rồi cập nhật danh sách trống
                location = location_empty.complete_name.split('/')
                # Tìm BX của mình và tìm Bãi nào có định dạng là 3 phần tử
                # BX\A\A1 or BX\B\B2
                if 'BX' in location and len(location) > 2:
                    password_tag = uuid.uuid4().hex[:8]
                    password_tag += "s"
                    return password_tag
            return "-1"
        else:
            return serial_ids.product_id.password

    @http.route('/parking/post/check_xe', website=False, csrf=False, type='json', methods=['POST'], auth='public')
    def parking_check_xe(self, **kw):
        serial_ids = http.request.env["product.template"].sudo().search(
            [('ref', '=', kw['sEPC'])], limit=1)
        if not serial_ids:
            return "none"
        else:
            json = {
                'password_xe': serial_ids.password_xe,
                'password_ng': serial_ids.product_id.password,
                'epc_ng': serial_ids.product_id.ma_dinh_danh,
                'epc_xe': serial_ids.name,
            }

            return json

    

    @http.route('/parking/post/out/move_history', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post_out_move_history(self, **kw):
        # lấy danh sách ID của thẻ trong kho move history
        product_move_list = http.request.env["stock.move.line"].sudo().search(
            [('lot_name', '=', kw['sEPC'])])
        if not product_move_list:
            return "-2"
        # tìm ID lớn nhất (thời gian đi vào gần nhất)
        max_object = max(product_move_list, key=lambda x: x['id'])
        # lấy thông tin của ID lớn nhất
        # kiểm tra ra hay vào nếu ra thì thêm vào và ngược lại

        if 'IN' in max_object.reference:
            update_stock_lot(kw['sEPC'], "BX/OUT", 55)  # Không có

            update_location(
                'empty', max_object.location_dest_id.id, 212, 66)  # Không có

            create_product_move_history(
                "BX/OUT", max_object.product_id.id, max_object.location_dest_id.id, 5, kw['sEPC'])
            return get_all_move_history_by_day(kw['sEPC'])

        return "-2"  # Da ra roi

    @http.route('/parking/get/all/move_history', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post_all_move_history(self, **kw):

        move_histories = http.request.env['stock.move.line'].sudo().search_read(
            fields=['date', 'lot_name', 'reference',
                    'location_id', 'location_dest_id'],
            order="id desc")

        today = date.today()
        res = [move_history for move_history in move_histories if move_history['date'].date()
               == today]
        return res

    @http.route('/parking/get/all/product', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post_all_product(self, **kw):
        product_product = http.request.env['product.template'].sudo().search_read(
            domain=[('ma_dinh_danh', '!=', ""), ('phone', '!=', False)],
            fields=['name', 'sdt',
                    'ma_dinh_danh', 'id', "cmnd_cccd"],
            order="id desc")
        return product_product

    @http.route('/parking/get/all/stock/lot', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post_all_stock_lot(self, **kw):
        stock_lot = http.request.env['stock.lot'].sudo().search_read(
            domain=[('state', '!=', False), ('location_id',
                                             '!=', False), ("bien_so", "!=", False)],
            fields=['name', 'state',
                    'location_id', 'bien_so', 'product_id'],
            order="id desc")
        return stock_lot

    @http.route('/parking/get/all/stock/location', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post_all_stock_location(self, **kw):
        stock_location = http.request.env['stock.location'].sudo().search_read(
            domain=[('lot_name', '!=', False)],
            fields=['complete_name', 'lot_name', 'state'
                    ],
            order="id desc")
        return stock_location

    @http.route('/web/test', website=False, type='json', auth='public', methods=['POST'])
    def download_file(self, **kw):
        create_product_move_history2()
