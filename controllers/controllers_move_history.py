# -*- coding: utf-8 -*-
from odoo import http
from odoo import fields
from datetime import date

class ControllerMoveHistory(http.Controller):
   

    @http.route('/parking/get/move_history/get_all/epc', website=False,csrf=False, type='json', methods=['POST'], auth='public')
    def get_all_move_history(self, **kw):
        move_histories = http.request.env['stock.move.line'].sudo().search_read(
            domain=[('lot_name', '=', kw['sEPC'])],
            fields=['date','lot_name', 'reference','location_id','location_dest_id'],
        )
        today = date.today()
        for  i in range(len(move_histories)):
            if move_histories[i]['date'].today() != today:
               del move_histories[i]
                
        return move_histories

   
