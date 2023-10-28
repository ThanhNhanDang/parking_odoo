import logging

from odoo import fields, models
_logger = logging.getLogger(__name__)


class state_move_line(models.Model):
    _inherit = 'stock.move.line'
    picking_id = fields.Many2one(
        'stock.picking', 'Transfer', auto_join=True,
        check_company=True,
        index=True,
        help='The stock operation where the packing has been made')
    picking_code = fields.Selection(
        related='picking_id.picking_type_id.code', store=True, readonly=False)
    
    def create(self, vals):
        for val in vals:
            val['picking_code'] = 'outgoing'
        new_record = super(state_move_line, self).create(vals)
        return new_record


class state_picking_type(models.Model):
    _inherit = 'stock.picking.type'

    code = fields.Selection([('incoming', 'Vào bãi'), ('outgoing', 'Ra bãi'), (
        'internal', "Internal Transfer")], string="Ra/vào bãi", default="outgoing")


class state_picking(models.Model):
    _inherit = 'stock.picking'
    picking_type_id = fields.Many2one(
        'stock.picking.type', 'Operation Type',
        required=True, readonly=False, index=True,
        states={'draft': [('readonly', False)]})
