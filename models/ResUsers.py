from odoo import api, fields, models, http
import uuid
import json

class ResUsers(models.Model):
    _inherit = 'res.users'
    @api.model
    def create(self, vals):
        users = super(ResUsers, self).create(vals)
        return users
