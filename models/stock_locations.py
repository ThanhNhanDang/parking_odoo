from odoo import fields, models, api
from odoo.exceptions import ValidationError
import logging
_logger = logging.getLogger(__name__)


class stock_locations(models.Model):
    _inherit = 'stock.location'
    complete_name = fields.Char(string="Vị trí")
    state = fields.Selection(
        [("empty", "Trống"), ("full", "Đầy"),], string="Trạng thái", default="empty", compute="_compute_sate")
    product_id = fields.Many2one(
        "product.template", string="Biển số")  # compute="_compute_product_id")
    location_id = fields.Many2one("stock.location", string="Vị trí cha")

    @api.depends("product_id")
    def _compute_sate(self):
        for record in self:
            if record.product_id:
                record.state = "full"
            else:
                record.state = "empty"
   
    @api.model
    def create(self, vals):
        record = self.search([('name', '=', vals['name'])])
        if record:
            raise ValidationError("VỊ TRÍ ĐÃ TỒN TẠI!!")
        new_record = super(stock_locations, self).create(vals)
        return new_record
