# -*- coding: utf-8 -*-
from odoo import http

class ControllerMoveHistory(http.Controller):
    @http.route('/parking/get/move_history/ids', website=False,csrf=False, type='json', methods=['GET'], auth='public')
    def parking_move_history(self, **kw):
        move_histories = http.request.env["stock.move.line"].sudo().search([])
        move_histories_fields = []
        for move_history in move_histories:
            move_histories_fields.append({'id':move_history.id})

        return move_histories_fields

    # @http.route('/parking/parking/objects', auth='public')
    # def list(self, **kw):
    #     return http.request.render('parking.listing', {
    #         'root': '/parking/parking',
    #         'objects': http.request.env['parking.parking'].search([]),
    #     })

    # @http.route('/parking/parking/objects/<model("parking.parking"):obj>', auth='public')
    # def object(self, obj, **kw):
    #     return http.request.render('parking.object', {
    #         'object': obj
    #     })
