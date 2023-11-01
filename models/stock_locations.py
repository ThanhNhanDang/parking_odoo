from odoo import fields, models, api

class stock_locations(models.Model):
    _inherit = 'stock.location'
    complete_name = fields.Char(string="Vị trí")
    state = fields.Selection(
        [("empty", "Trống"), ("full", "Đầy"),], string="Trạng thái", default="empty", compute="_compute_sate")
    product_id = fields.Many2one(
        "product.template", string="Biển số")#compute="_compute_product_id")
    location_id = fields.Many2one("stock.location", string="Vị trí cha")
    
    @api.depends("product_id")
    def _compute_sate(self):
        for record in self:
            if record.product_id:
                record.state = "full"
            else:
                record.state = "empty"

    # def _compute_product_id(self):
    #     for record in self:
    #         if record.product_id.check_doi_the == False:
    #             record.product_id = None
