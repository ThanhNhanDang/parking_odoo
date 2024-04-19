# -*- coding: utf-8 -*-
from odoo import http
import uuid
import pytz
import os
import logging
import pytz
from datetime import date
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)


def create_product_move_history(state, product_id, location_id):
    stock_move_history = http.request.env["stock.move.line"].sudo().create(
        {'reference': state,
         'product_id': product_id,
         'reserved_uom_qty': 1.0,
         'location_id': location_id,
         'qty_done': 1.0,
         'company_id': 1})


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


def check_exist_xe(bien_so, ma_the):
    xe = http.request.env['product.template'].sudo().search(
        domain=['|', ('default_code', '=', ma_the),
                ("name", "=", bien_so)],
        limit=1)
    if not xe:
        return 1
    if (xe.default_code == ma_the):
        return -1
    if (xe.name == bien_so):
        return -2


def check_epc_xe(ma_the):
    xe = http.request.env['product.template'].sudo().search(
        domain=[('default_code', '=', ma_the)],
        limit=1)
    return xe


def contains(list, filter):
    for x in list:
        if filter(x):
            return x
    return None
    # do stuff


def changeDate(date_in):
    user_tz = pytz.timezone(str(http.request.env.context.get(
        'tz') or http.request.env.user.tz or pytz.utc))
    # Convert the date to a Python `datetime` object
    python_date = date_in.strptime(
        str(date_in), "%Y-%m-%d %H:%M:%S")
    timezone = pytz.utc.localize(python_date).astimezone(user_tz)
    # if (timezone.date() == today):
    display_date_result = timezone.strftime("%H:%M:%S %d/%m/%Y")
    return display_date_result


class ControllerProduct(http.Controller):
    @http.route('/parking/get/move_history/', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def get_move_history_by_day(self, **kw):
        # datetime.date(2023, 11, 4)
        if kw['mode'] == 1:
            domain = [('date', '>=', date.today()), ('contact_id', '=', kw['user_id']),
                      ('picking_code', '!=', False)]
        elif kw['mode'] == 2:
            domain = [('date', '<=', date.today()), ('date', '>=', date.today() + relativedelta(months=1)), ('contact_id', '=', kw['user_id']),
                      ('picking_code', '!=', False)]
        move_histories = http.request.env['stock.move.line'].sudo().search_read(
            domain=domain,
            fields=['id', 'date', 'bien_so_realtime', 'picking_code', 'location_id',
                    'product_id', 'contact_id'],
            order="id desc")
        res = []
        for move_history in move_histories:
            display_date_result = changeDate(move_history['date'])
            if move_history['picking_code'] == 'incoming':
                move_history['picking_code'] = "Vào bãi"
            elif move_history['picking_code'] == 'outgoing':
                move_history['picking_code'] = "Ra bãi"
            _json = {
                'date': display_date_result,
                'history_id': move_history['id'],
                'product_name': move_history['product_id'][1],
                'location_name': move_history['location_id'][1],
                'user_name': move_history['contact_id'][1],
                'bien_so_realtime': move_history['bien_so_realtime'],
                'picking_code': move_history['picking_code'],
            }
            res.append(_json)
        return res

    @http.route('/parking/get/all/stock/location/empty', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def post_all_stock_location(self, **kw):
        stock_location = http.request.env['stock.location'].sudo().search(
            domain=[('state', '=', 'empty')],
        )
        i = 0
        for location_empty in stock_location:
            location = location_empty.complete_name.split('/')
            # Tìm BX của mình và tìm Bãi nào có định dạng là 3 phần tử
            # BX\A\A1 or BX\B\B2

            if 'BX' in location and len(location) > 2 and location_empty.state == 'empty':
                i += 1
        return i

    @http.route('/parking/car/users/is_match', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def car_users(self, **kw):
        # _logger.info(kw['the_xe'])
        xe = http.request.env['product.template'].sudo().search(
            domain=[('default_code', '=', kw['the_xe'])],
            limit=1)
        if not xe:
            return {
                "message": "XE KHÔNG TỒN TẠI"
            }
        id_ng = xe.contact_id.id
        location_id = xe.location_id.id
        if location_id == False:  # Xe chưa có vị trí, đã ra rồi
            location_id = -1
        if kw['ra'] == 1:
            the_ng_arr = []
            pass_ng_arr = []
            id_ng_arr = []
            id_ng_arr.append(id_ng)
            the_ng_arr.append(xe.contact_id.ref)
            pass_ng_arr.append(xe.contact_id.barcode)
            for u in xe.user_ids:
                the_ng_arr.append(u.ref)
                pass_ng_arr.append(u.barcode)
                id_ng_arr.append(u.id)

            return {
                'bien_so': xe.name,
                'the_xe': kw['the_xe'],
                'password_xe': "00000000",
                'the_ng_arr':the_ng_arr,
                'pass_ng_arr': pass_ng_arr,
                'id_ng_arr': id_ng_arr,
                'location_id': location_id,
                "message": "0"
            }
        return {
            'bien_so': xe.name,
            'the_xe': kw['the_xe'],
            'password_xe': "00000000",
            'user_id': id_ng,
            'location_id': location_id,
            "message": "0"
        }

    @http.route('/parking/get/history/by_id', website=False, csrf=False, type='json', methods=['POST'],  auth='public')
    def getHistoryById(self, **kw):
        history = http.request.env["stock.move.line"].sudo().search(
            [('id', '=', kw['history_id'])], limit=1)
        date_result = changeDate(history.date)
        if history.picking_code == "incoming":
            _date_in = date_result
        elif history.picking_code == "outgoing":
            _date_in = changeDate(history.date_in)
        return {
            "bien_so_realtime": history.bien_so_realtime,
            "bien_so_dk": history.product_id.name,
            "image_1920_ng": history.image_1920_ng,
            "image_1920_xe": history.image_1920_xe,
            "image_1920_truoc": history.image_1920_camera_truoc,
            "image_1920_sau": history.image_1920_camera_sau,
            "date_vao": _date_in,
            "date_ra": date_result,
            "location_name": history.location_id.complete_name,
            "user_name": history.contact_id.name,
            "ma_the": history.product_id.default_code,
            "user_id": history.contact_id.id,
            "history_id": history.id,
        }
