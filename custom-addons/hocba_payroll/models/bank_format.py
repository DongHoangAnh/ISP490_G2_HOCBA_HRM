"""
Bank Format configuration model.
FUNC-PR-003: Mỗi ngân hàng = 1 record cấu hình + 1 formatter class (Strategy).
"""
from odoo import fields, models


class BankFormat(models.Model):
    _name = 'hb.bank.format'
    _description = 'Bank Payment File Format'
    _order = 'sequence, name'

    name = fields.Char(string='Tên ngân hàng', required=True)
    code = fields.Char(string='Mã ngắn', required=True, help='VD: VCB, TCB')
    sequence = fields.Integer(default=10)
    formatter_class = fields.Char(
        string='Formatter Class',
        required=True,
        help='Tên Python class trong bank_formatter.py (VD: VCBFormatter)',
    )
    encoding = fields.Selection([
        ('utf-8', 'UTF-8'),
        ('utf-8-sig', 'UTF-8 with BOM'),
        ('cp1252', 'ANSI (Windows-1252)'),
    ], string='Encoding', default='utf-8', required=True)
    file_extension = fields.Selection([
        ('xlsx', 'Excel (XLSX)'),
        ('csv', 'CSV'),
        ('txt', 'Text'),
    ], string='File Extension', default='xlsx', required=True)
    account_format_regex = fields.Char(
        string='STK Regex',
        help='Regex validate số tài khoản. VD: ^\\d{10,14}$',
    )
    max_records_per_file = fields.Integer(
        string='Max records/file',
        default=0,
        help='0 = không giới hạn',
    )
    description_template = fields.Char(
        string='Template mô tả giao dịch',
        default='Luong T{month}/{year}',
    )
    active = fields.Boolean(default=True)

    _code_unique = models.Constraint(
        'unique (code)',
        'Mã ngân hàng phải là duy nhất!',
    )
