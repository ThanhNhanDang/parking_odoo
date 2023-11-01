import logging

from odoo import fields, models, http
_logger = logging.getLogger(__name__)


def find_location_empty(self):
    # Tìm danh sách vị trí trống trong bãi lấy danh sách tên của bãi
    locations_empty = self.env["stock.location"].search([
        ('state', '=', 'empty')])

    # Tìm danh vị trí trống đầu tiên trong danh sách
    for location_empty in locations_empty:
        # Có nhiều bãi xe nên tìm bãi xe của mình
        # Tìm bãi xe trống đầu tiên rồi cập nhật danh sách trống
        location = location_empty.complete_name.split('/')
        # Tìm BX của mình và tìm Bãi nào có định dạng là 3 phần tử
        # BX\A\A1 or BX\B\B2
        if 'BX' in location and len(location) > 2:
            return location_empty.id
    return -1


class stock_move_line(models.Model):
    _inherit = 'stock.move.line'
    picking_id = fields.Many2one(
        'stock.picking', 'Transfer', auto_join=True,
        check_company=True,
        index=True,
        help='The stock operation where the packing has been made')
    picking_code = fields.Selection(
        related='picking_id.picking_type_id.code', store=True, readonly=False)
    bien_so_realtime = fields.Char(string="Biển số nhận diện được")
    location_id = fields.Many2one("stock.location", string="Vị trí")
    product_id = fields.Many2one("product.template", string="Biển số đã đăng ký")
    contact_id = fields.Many2one("res.partner", string="Họ tên")
    image_1920_ng = fields.Image(string="ẢNH NGƯỜI Đ/K",
                                 max_width=1920, max_height=1920, related='contact_id.image_1920')
    image_1920_xe = fields.Image(string="ẢNH XE Đ/K", related='product_id.image_1920_bien_so',
                                 max_width=1920, max_height=1920)
    image_1920_camera_truoc = fields.Image(string="ẢNH CAMRERA TRƯỚC",
                                           max_width=1920, max_height=1920)
    image_1920_camera_sau = fields.Image(string="ẢNH CAMRERA SAU",
                                         max_width=1920, max_height=1920)

    def create(self, vals):
        _logger.info(vals)
        new_record = super(stock_move_line, self).create(vals)
        _logger.info(new_record)

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
