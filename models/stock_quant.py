import logging

from odoo import fields, models
_logger = logging.getLogger(__name__)

class stock_quant(models.Model):
    _inherit = 'stock.quant'
