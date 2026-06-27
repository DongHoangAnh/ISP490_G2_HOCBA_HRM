"""
Bank Format configuration model.
FUNC-PR-003: Mỗi ngân hàng = 1 record cấu hình + 1 formatter class (Strategy).
Cũng chứa danh sách ngân hàng tham chiếu (trước đây là hb.mb.bank.entry).
"""
from odoo import fields, models

TRANSFER_TYPE_SELECTION = [
    ('normal', 'CHUYỂN KHOẢN THƯỜNG'),
    ('fast_247', 'Chuyển khoản NHANH liên ngân hàng 24/7 tới số tài khoản'),
]


class BankFormat(models.Model):
    _name = 'hb.bank.format'
    _description = 'Bank Payment File Format'
    _order = 'sequence, name'

    name = fields.Char(string='Tên ngân hàng', required=True)
    code = fields.Char(string='Mã ngắn', help='VD: VCB, TCB')
    sequence = fields.Integer(default=10)
    transfer_type = fields.Selection(
        TRANSFER_TYPE_SELECTION,
        string='Hình thức chuyển',
        default='normal',
    )
    formatter_class = fields.Char(
        string='Formatter Class',
        help='Tên Python class trong bank_formatter.py (VD: VCBFormatter)',
    )
    encoding = fields.Selection([
        ('utf-8', 'UTF-8'),
        ('utf-8-sig', 'UTF-8 with BOM'),
        ('cp1252', 'ANSI (Windows-1252)'),
    ], string='Encoding', default='utf-8')
    file_extension = fields.Selection([
        ('xlsx', 'Excel (XLSX)'),
        ('csv', 'CSV'),
        ('txt', 'Text'),
    ], string='File Extension', default='xlsx')
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
