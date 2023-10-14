import logging
from odoo import models
import uuid


class User(models.Model):
    _inherit = 'res.partner'

