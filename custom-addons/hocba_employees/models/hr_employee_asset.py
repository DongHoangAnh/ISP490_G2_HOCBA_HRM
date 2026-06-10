from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrEmployeeAsset(models.Model):
    _name = 'hr.employee.asset'
    _description = 'Tài sản cấp phát cho nhân viên'
    _order = 'employee_id, grant_date desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên giữ',
        required=True, ondelete='restrict', index=True)
    asset_type_id = fields.Many2one(
        'hocba.asset.type', string='Loại tài sản', required=True)
    asset_code = fields.Char(string='Mã tài sản', required=True)
    grant_date = fields.Date(
        string='Ngày cấp phát', required=True,
        default=fields.Date.context_today)
    condition_in = fields.Selection(
        selection=[('new', 'Mới'), ('good', 'Tốt'), ('fair', 'Trung bình')],
        string='Tình trạng khi cấp', required=True, default='good')
    state = fields.Selection(
        selection=[
            ('assigned', 'Đang giữ'),
            ('returned', 'Đã thu hồi'),
            ('transferred', 'Đã chuyển giao'),
        ],
        string='Trạng thái', required=True, default='assigned', index=True)
    return_date = fields.Date(string='Ngày thu hồi')
    transferred_to = fields.Many2one('hr.employee', string='Chuyển giao cho')
    condition_out_note = fields.Text(string='Ghi chú tình trạng khi thu')

    @api.constrains('asset_code', 'state')
    def _check_asset_code_unique_assigned(self):
        # Mã tài sản = thiết bị vật lý: giữ nguyên khi chuyển giao,
        # nhưng mỗi mã chỉ được có 1 bản ghi "Đang giữ" tại một thời điểm.
        for rec in self:
            if rec.state == 'assigned' and self.search_count([
                    ('asset_code', '=', rec.asset_code),
                    ('state', '=', 'assigned'),
                    ('id', '!=', rec.id)]):
                raise ValidationError(_(
                    'Tài sản "%s" đang được người khác giữ — '
                    'thu hồi/chuyển giao trước khi cấp lại.') % rec.asset_code)

    @api.constrains('grant_date', 'return_date', 'employee_id')
    def _check_dates(self):
        for rec in self:
            # Nhóm B: chỉ cấp sau khi đạt cổng tuần-2 (nếu có mốc đánh giá)
            gate = rec.employee_id.x_eval_2w_date
            if gate and rec.grant_date and rec.grant_date < gate:
                raise ValidationError(_(
                    'Ngày cấp phát phải từ ngày đánh giá tuần-2 (%s) trở đi.') % gate)
            if rec.return_date and rec.grant_date and rec.return_date < rec.grant_date:
                raise ValidationError(_('Ngày thu hồi phải sau ngày cấp phát.'))

    @api.constrains('state', 'return_date', 'transferred_to')
    def _check_state_requirements(self):
        for rec in self:
            if rec.state == 'returned' and not rec.return_date:
                raise ValidationError(_('Thu hồi cần có Ngày thu hồi.'))
            if rec.state == 'transferred' and not rec.transferred_to:
                raise ValidationError(_('Chuyển giao cần chọn nhân viên nhận.'))

    def unlink(self):
        # Spec F-006: không xóa bản ghi — chỉ đổi trạng thái
        raise UserError(_(
            'Không được xóa bản ghi tài sản — hãy Thu hồi hoặc Chuyển giao.'))

    def action_mark_returned(self):
        for rec in self:
            if rec.state != 'assigned':
                raise UserError(_('Chỉ thu hồi tài sản đang ở trạng thái Đang giữ.'))
            rec.write({
                'state': 'returned',
                'return_date': rec.return_date or fields.Date.context_today(rec),
            })

    def action_mark_transferred(self):
        for rec in self:
            if rec.state != 'assigned':
                raise UserError(_('Chỉ chuyển giao tài sản đang ở trạng thái Đang giữ.'))
            if not rec.transferred_to:
                raise UserError(_('Chọn nhân viên nhận trước khi chuyển giao.'))
            return_date = rec.return_date or fields.Date.context_today(rec)
            rec.write({'state': 'transferred', 'return_date': return_date})
            # BR-050: tự tạo bản ghi mới cho người nhận (cùng mã thiết bị),
            # ngày cấp = ngày chuyển giao
            self.create({
                'employee_id': rec.transferred_to.id,
                'asset_type_id': rec.asset_type_id.id,
                'asset_code': rec.asset_code,
                'grant_date': return_date,
                'condition_in': rec.condition_in,
            })
