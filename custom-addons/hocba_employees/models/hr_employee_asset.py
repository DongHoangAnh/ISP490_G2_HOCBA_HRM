from odoo import models, fields


class HrEmployeeAsset(models.Model):
    """F-006 (rút gọn): danh sách tài sản nhân viên ĐANG giữ.

    Không có vòng đời: thu hồi = xoá dòng; bàn giao = xoá dòng người cũ +
    thêm dòng người mới. Quyết định theo góp ý giảng viên, xem
    docs/superpowers/specs/2026-07-24-asset-simplify-design.md
    """
    _name = 'hr.employee.asset'
    _description = 'Tài sản nhân viên đang giữ'
    _order = 'employee_id, grant_date desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên giữ',
        required=True, ondelete='cascade', index=True)
    asset_type_id = fields.Many2one(
        'hocba.asset.type', string='Loại tài sản', required=True)
    asset_code = fields.Char(string='Mã tài sản', required=True)
    grant_date = fields.Date(
        string='Ngày cấp phát', required=True,
        default=fields.Date.context_today)
    condition_in = fields.Selection(
        selection=[('new', 'Mới'), ('good', 'Tốt'), ('fair', 'Trung bình')],
        string='Tình trạng khi cấp', required=True, default='good')

    # Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint
    _asset_code_uniq = models.Constraint(
        'unique (asset_code)',
        'Mã tài sản này đã được gán cho nhân viên khác!',
    )
