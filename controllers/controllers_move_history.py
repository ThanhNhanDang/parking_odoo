# -*- coding: utf-8 -*-
from odoo import http

class ControllerMoveHistory(http.Controller):
   

    @http.route('/parking/get/move_history/get_all', auth='public', website=False,csrf=False, type='json', methods=['GET'], auth='public')
    def get_all_move_history(self, **kw):
        move_histories = self.env['stock.move.line'].sudo().search_read(
            fields=['date','lot_name', 'reference','location_id','location_dest_id'],
        )
        return move_histories

   
