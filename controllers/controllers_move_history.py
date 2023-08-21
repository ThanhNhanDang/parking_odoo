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
        for move_history in move_histories: 
            if move_history.date.split(" ")[0] != today:
                move_histories.pop(move_history)
                
        return move_histories

   
