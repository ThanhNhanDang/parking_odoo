from odoo import api, fields, models, http, exceptions
import uuid
import logging
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from base64 import b64encode

_logger = logging.getLogger(__name__)


def check_bien_so_xe(bien_so):
    xe = http.request.env['product.template'].sudo().search(
        domain=[('name', '=', bien_so)],
        limit=1)
    return xe


def check_exist_xe(bien_so, ma_dinh_danh):
    xe = http.request.env['product.template'].sudo().search(
        domain=['|', ('default_code', '=', ma_dinh_danh),
                ("name", "=", bien_so)],
        limit=1)
    if not xe:
        return 1
    if (xe.default_code == ma_dinh_danh):
        return -1
    if (xe.name == bien_so):
        return -2


class Product_template(models.Model):
    _inherit = 'product.template'
    _sql_constraints = [
        ('field_unique',
         'unique(name)',
         'BIỂN SỐ ĐÃ TỒN TẠI!!')
    ]
    name = fields.Char(string="Biển số")
    location_id = fields.Many2one(
        "stock.location", string="Vị trí", compute="_compute_location_id")
    contact_id = fields.Many2one(
        'res.partner', string='Chủ sở hữu', required=True)
    #barcode = fields.Char(string="Mật khẩu", readonly=False)
    default_code = fields.Char(string="Mã thẻ", readonly=False)
    user_ids = fields.Many2many(
        'res.partner', string="D/S người dùng", readonly=False, domain="[('id', '!=',contact_id)]")
    check_doi_the = fields.Boolean(string="Đã đổi thẻ", default=False)
    activity_summary = fields.Char(string="Hãng xe", store=True)
    avatar_128 = fields.Image(
        "avatar 128", compute='_compute_avatar_128', max_width=128, max_height=128)
    image_1920 = fields.Image(
        string="Ảnh xe", max_width=1920, max_height=1920)
    image_1920_bien_so = fields.Image(
        string="Ảnh biển số xe", max_width=1920, max_height=1920)
    image_1920_cavet_sau = fields.Image(
        string="Mặt trước cà vẹt xe", max_width=1920, max_height=1920)
    image_1920_cavet_truoc = fields.Image(
        string="Mặt sau cà vẹt xe", max_width=1920, max_height=1920)
    nbr_moves_in = fields.Integer(compute='_compute_nbr_moves', compute_sudo=False,
                                  help="Number of incoming stock moves in the past 12 months")
    nbr_moves_out = fields.Integer(compute='_compute_nbr_moves', compute_sudo=False,
                                   help="Number of outgoing stock moves in the past 12 months")
    date_in = fields.Datetime(string="T/G VÀO bãi gần nhất")
    date_out = fields.Datetime(string="T/G RA bãi gần nhất")
    move_history_id = fields.Many2one(
        'stock.move.line', string="Trạng thái", readonly=True)

    def name_get(self):
        # Prefetch the fields used by the `name_get`, so `browse` doesn't fetch other fields
        self.browse(self.ids).read(['name', 'default_code'])
        return [(template.id, '%s' % (template.name))
                for template in self]

    def action_view_stock_move_lines(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id(
            "stock.stock_move_line_action")
        action['domain'] = [('product_id.id', 'in', self.ids)]
        return action

    def _compute_avatar_128(self):
        for record in self:
            avatar = record['image_1920']
            if not avatar:
                if record.id and record[record._avatar_name_field]:
                    avatar = record._avatar_generate_svg()
                else:
                    avatar = b64encode(record._avatar_get_placeholder())
            record['avatar_128'] = avatar

    def _compute_nbr_moves(self):
        res = defaultdict(lambda: {'moves_in': 0, 'moves_out': 0})
        incoming_moves = self.env['stock.move.line']._read_group([
            ('product_id', 'in', self.ids),
            ('picking_code', '=', 'incoming'),
            ('date', '>=', fields.Datetime.now() - relativedelta(years=1))
        ], ['product_id'], ['product_id'])
        outgoing_moves = self.env['stock.move.line']._read_group([
            ('product_id', 'in', self.ids),
            ('picking_code', '=', 'outgoing'),
            ('date', '>=', fields.Datetime.now() - relativedelta(years=1))
        ], ['product_id'], ['product_id'])
        for move in incoming_moves:
            product = self.env['product.template'].browse(
                [move['product_id'][0]])
            product_tmpl_id = product.id
            res[product_tmpl_id]['moves_in'] += int(move['product_id_count'])
        for move in outgoing_moves:
            product = self.env['product.template'].browse(
                [move['product_id'][0]])
            product_tmpl_id = product.id
            res[product_tmpl_id]['moves_out'] += int(move['product_id_count'])
        for template in self:
            template.nbr_moves_in = int(res[template.id]['moves_in'])
            template.nbr_moves_out = int(res[template.id]['moves_out'])

    @api.depends("location_id")
    def _compute_location_id(self):
        for record in self:
            location = record.location_id.search(
                [('product_id', '=', record.id)])
            if not location:
                record.location_id = None
            else:
                record.location_id = location.id

    @api.model
    def create(self, vals):
        vals['name'] = vals['name'].upper()
        vals["tracking"] = "serial"
        new_record = super(Product_template, self).create(vals)
        vals['user_ids'] = vals['contact_id']

        # result = check_exist_xe(vals['name'], "123")
        # if result == -1:
        #     raise exceptions.UserError("THẺ ĐÃ TỒN TẠI!")
        # if result == -2:
        #     raise exceptions.UserError("BIỂN SỐ ĐÃ TỒN TẠI!")
        # hex_arr = uuid.uuid4().hex
        # if check_epc_xe("0" + hex_arr[1:24]):
        #     raise exceptions.UserError(
        #         "Không thể tạo được UUID liên hệ nhà phát triển để sử lý")
        # new_record = super(Product_template, self).create({
        #     'name':  vals['name'],
        #     'image_1920': vals['image_1920'],
        #     'default_code': "1" + hex_arr[1:24],
        #     'contact_id': vals['contact_id'],
        #     'barcode': hex_arr[24:],
        #     'user_ids': [(4, vals['contact_id'])],
        #     'detailed_type': 'product'
        # })
        new_record.product_variant_id.write({
            'name':  vals['name'],
            'responsible_id': vals['contact_id'],
        })
        # create_product_move_history(
        #     "BX/OUT", new_record.product_variant_id.id, 4, 5, "123")
        return new_record

    def write(self, vals):
        if 'name' in vals:
            vals['name'] = vals['name'].upper()
        result = super(Product_template, self).write(vals)
        return result

    def createUUID(self):
        hex_arr = uuid.uuid4().hex
        check_epc_xe = self.search(
            domain=[('default_code', '=', "1" + hex_arr[1:24])],
            limit=1)
        if check_epc_xe:
            return "LỖI: KHÔNG THỂ TẠO UUID DO BỊ ĐÃ TỒN TẠI [1" + hex_arr[1:24]+"]!!"
        message = "ghi epc|"+"1" + hex_arr[1:24] + "|"+hex_arr[24:]
        return message
