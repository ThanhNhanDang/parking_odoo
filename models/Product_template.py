from odoo import api, fields, models, http, exceptions
import uuid
import logging
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from base64 import b64encode
import json

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

#Hàm lấy màu sắc:
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
    barcode = fields.Char(readonly=False)
    default_code = fields.Char(string="Mã thẻ", readonly=False)
    
    domain = fields.Char(compute='_compute_domain', readonly=True)
    user_ids = fields.Many2many(
        'res.partner',  string="Người sử dụng", readonly=False)
    
    # partner_id = fields.Many2one("res.partner", string="Liên hệ")
    # partner_ids = fields.One2many("res.partner", "partner_id",string="Danh sách liên hệ")
    
    # partner_gid = fields.Many2many('res.partner', string="Người sử dụng"
    
    # color = fields.Selection([
    #     ('black', 'Đen'),
    #     ('white', 'Trắng'),
    #     ('red', 'Đỏ'),
    # ], string="Màu xe", default=True)
    # computed_field = fields.Char(string='Computed Field', compute='_compute_computed_field')
    # ------------------------------------------------
    
    color_id = fields.Many2one('product.color.main', string='Màu xe')
    html_color = fields.Char(related='color_id.html_color', readonly=True)
    # html_color = fields.Char(readonly=True)
    
    categ_id = fields.Many2one(
        'product.category', 'Hãng xe',
        change_default=True,domain=[("parent_id.name", "!=", "All")])   
    
    so_loai = fields.Char(string="Mã loại xe", readonly=False)

    so_khung = fields.Char(string="Số khung", store=True)

    check_doi_the = fields.Boolean(string="Đã đổi thẻ", default=False)
    
    avatar_128 = fields.Image(
        string="avatar 128", compute='_compute_avatar_128', max_width=128, max_height=128)
    image_1920 = fields.Image(
        string="Ảnh trước xe", max_width=256, max_height=256)
    image_1920_sau_xe = fields.Image(
        string="Ảnh sau xe", max_width=256, max_height=256)
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

    so_may = fields.Char(string="Số máy", readonly=False)
    so_dang_ky = fields.Char(string="Số đăng ký", readonly=False)
    move_history_ids = fields.One2many("stock.move.line", "product_id", string="Lịch sử di chuyển",
                                  )
# ---------------------------
    def _compute_domain(self):
        for rec in self:
            _logger.info(rec.contact_id["id"])
            _logger.info("_compute_domain")
            arr = []
            if not rec.contact_id["id"]:
                rec.domain = "[]"
            for contact in rec.contact_id.partner_ids:
                arr.append(contact["id"])
            rec.domain = json.dumps([('id', '!=',rec.contact_id["id"]), ('id', 'in',arr) ])
            
            # if self.contact_id["id"]:
            #     _logger.info("_get_domain") 
            #     arr = []
            #     for contact in self.contact_id.partner_ids:
            #         arr.append(contact["id"])
            #     _logger.info(arr)
            # rec.domain = json.dumps(
            #     [('id', '!=', rec.c)]
            # )
            
            
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
        ], ['product_id'], ['__count'])
        outgoing_moves = self.env['stock.move.line']._read_group([
            ('product_id', 'in', self.ids),
            ('picking_code', '=', 'outgoing'),
            ('date', '>=', fields.Datetime.now() - relativedelta(years=1))
        ], ['product_id'], ['__count'])
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
                
    def _compute_user_ids(self):
        for record in self:
            _logger.info(record.contact_id.partner_ids)
            #record.user_ids = record.contact_id.partner_ids
            _logger.info("_compute_user_ids")
            
            
            # location = record.location_id.search(
            #     [('product_id', '=', record.id)])
            # if not location:
            #     record.location_id = None
            # else:
            #     record.location_id = location.id

    @api.model
    def create(self, vals):
        vals['name'] = vals['name'].upper()
        vals["tracking"] = "serial"
        vals['type'] = 'product'  # Set the type explicitly ODOO 17
        vals['detailed_type'] = 'product'
        _logger.info(vals)
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
            domain=[('default_code', '=', "1" + hex_arr[1:24])], limit=1)
        if check_epc_xe:
            return "LỖI: KHÔNG THỂ TẠO UUID DO BỊ ĐÃ TỒN TẠI [1" + hex_arr[1:24]+"]!!"
        message = "ghi epc|"+"1" + hex_arr[1:24] + "|"+hex_arr[24:]
        return message

# TẠO BẢNG LƯU HÃNG XE:
# class Product_template_2(models.Model):
#     _name = 'partner_table'
#     child_id = fields.Many2one('product.template', string="Mã thẻ xe", required=True)
#     name_user = fields.Char(string="Mã thẻ xe", required=True)

# class CardXeView(models.Model):
#     _inherit = "product.template"
#     card_id = fields.One2many('the_xe','card_id', string="Mã thẻ xe" )   
   
class ProductTable(models.Model):
    _name = 'product_table_block_description'
    product_table_block_id = fields.Many2one('product.template', string="Product FK block title ID")
    password_card = fields.Char(string="Mật khẩu", required=True)
    product_table_block_description = fields.Text(string="Mã thẻ xe")

    sequence = fields.Integer(string="Sequence" , index = True)

class ProductTableView(models.Model):
    _inherit = "product.template"
    product_template_id = fields.One2many('product_table_block_description','product_table_block_id', string="Product Block ID" )   


