import logging

from odoo import fields, models
_logger = logging.getLogger(__name__)

class stoct_lot(models.Model):
    _inherit = 'stock.lot'
    _rec_name = 'name'
   