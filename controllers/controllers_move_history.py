# -*- coding: utf-8 -*-
from odoo import http
from datetime import date

class ControllerMoveHistory(http.Controller):
   

    # @http.route('/parking/get/move_history/get_all/epc', website=False,csrf=False, type='json', methods=['POST'], auth='public')
    # def get_all_move_history(self, **kw):
    #     move_histories = http.request.env['stock.move.line'].sudo().search_read(
    #         domain=[('lot_name', '=', kw['sEPC'])],
    #         fields=['date','lot_name', 'reference','location_id','location_dest_id'],
    #     )
    #     today = date.today()

    #     res = [move_history for move_history in move_histories if move_history['date'].date() == today]
    #     return res
    @http.route('/parking/test', website=False,csrf=False, type='json', methods=['POST'], auth='public')
    def test(self, **kw):
        stock_location = http.request.env['stock.location'].sudo().search_read(
            domain=[('lot_name', '!=', False)],
            fields=['complete_name', 'lot_name', 'state'
                    ],
            order="id desc")

        return stock_location
