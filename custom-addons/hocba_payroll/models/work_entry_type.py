"""
Work Entry Type — standalone replacement for hr.work.entry.type (Enterprise).
Defines types of work entries: WORK200 (Teaching), WORK110_OT_HOLIDAY, etc.
"""
from odoo import fields, models


class HbWorkEntryType(models.Model):
    _name = 'hb.work.entry.type'
    _description = 'Loại Work Entry'
    _order = 'sequence, name'

    name = fields.Char(string='Tên', required=True)
    code = fields.Char(string='Mã', required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint(
        'unique (code)',
        'Mã loại Work Entry phải là duy nhất!',
    )
