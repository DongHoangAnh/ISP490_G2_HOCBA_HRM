from odoo import models, fields, api


class HbEmployeeAllowance(models.Model):
    """Phụ cấp riêng theo nhân viên — bảng EAV đơn giản.

    Mỗi record = 1 khoản phụ cấp cho 1 nhân viên.
    Không gắn vào salary rule — HR tự nhập tên và số tiền.
    """
    _name = 'hb.employee.allowance'
    _description = 'Phụ cấp riêng theo nhân viên'
    _order = 'employee_id, name'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='cascade', index=True,
    )
    name = fields.Char(
        string='Tên khoản', required=True,
        help='Tên khoản phụ cấp, VD: PC Xăng xe, PC Di chuyển, ...',
    )
    amount = fields.Float(
        string='Số tiền', digits=(16, 0),
    )
    note = fields.Text(string='Ghi chú')
    active = fields.Boolean(default=True)
