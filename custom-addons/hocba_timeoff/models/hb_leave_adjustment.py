from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HbLeaveAdjustment(models.Model):
    """Nhật ký điều chỉnh quỹ phép thủ công của HR (Phase 2).

    Mỗi lần HR cộng/trừ phép cho 1 nhân viên ghi lại 1 dòng (ai, khi nào, loại
    nghỉ, +/- bao nhiêu, lý do, allocation bị tác động). Append-only — không cho
    sửa/xoá để giữ vết kiểm toán (HR Manager chỉ read/write/create)."""
    _name = 'hb.leave.adjustment'
    _description = 'Điều chỉnh quỹ phép thủ công (HR)'
    _order = 'applied_date desc, id desc'
    _rec_name = 'employee_id'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        required=True, ondelete='cascade', index=True,
    )
    leave_type_id = fields.Many2one(
        'hr.leave.type', string='Loại nghỉ',
        required=True, ondelete='cascade',
    )
    delta_days = fields.Float(
        string='Số ngày điều chỉnh', required=True,
        help='Dương = cấp thêm, âm = trừ bớt.',
    )
    reason = fields.Text(string='Lý do', required=True)
    allocation_id = fields.Many2one(
        'hr.leave.allocation', string='Allocation liên quan',
        ondelete='set null',
        help='Allocation được tạo (khi cấp thêm) hoặc bị giảm/từ chối (khi trừ).',
    )
    applied_by = fields.Many2one(
        'hr.employee', string='Người điều chỉnh',
        default=lambda self: self.env.user.employee_id.id,
    )
    applied_date = fields.Datetime(
        string='Thời điểm', default=fields.Datetime.now, required=True,
    )

    @api.constrains('delta_days')
    def _check_delta_nonzero(self):
        for rec in self:
            if not rec.delta_days:
                raise ValidationError(_('Số ngày điều chỉnh phải khác 0.'))
