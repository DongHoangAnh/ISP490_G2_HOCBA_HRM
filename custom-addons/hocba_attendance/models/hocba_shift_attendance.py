from odoo import models, fields, api
from odoo.exceptions import UserError


class ShiftAttendance(models.Model):
    """Chấm công theo CA (ctv/ot) — 1 bản ghi/ca. Tách khỏi hocba.attendance
    (chỉ dùng cho official ngày thường). Giờ công lấy từ check_in/check_out thực tế."""
    _name = 'hocba.shift.attendance'
    _description = 'Chấm công theo ca'
    _order = 'check_in desc'

    shift_id = fields.Many2one(
        'hocba.work_shift', string='Ca', required=True,
        ondelete='cascade', index=True)
    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên',
        related='shift_id.employee_id', store=True, index=True)
    check_in = fields.Datetime(string='Giờ vào')
    check_out = fields.Datetime(string='Giờ ra')
    check_in_photo = fields.Text(string='Ảnh vào')
    check_out_photo = fields.Text(string='Ảnh ra')
    check_in_lat = fields.Float(string='Lat vào', digits=(10, 7))
    check_in_lng = fields.Float(string='Lng vào', digits=(10, 7))
    check_out_lat = fields.Float(string='Lat ra', digits=(10, 7))
    check_out_lng = fields.Float(string='Lng ra', digits=(10, 7))
    check_in_face_score = fields.Float(string='Điểm khuôn mặt vào')
    check_out_face_score = fields.Float(string='Điểm khuôn mặt ra')
    face_suspect = fields.Boolean(string='Nghi ngờ khuôn mặt')
    out_of_zone = fields.Boolean(string='Ngoài vùng')
    out_of_window = fields.Boolean(string='Ngoài cửa sổ ca')
    notes = fields.Text(string='Ghi chú giải trình')
    worked_hours = fields.Float(
        string='Số giờ chấm', compute='_compute_worked_hours', store=True,
        help='check_out - check_in (giờ); 0 nếu thiếu mốc.')

    _shift_uniq = models.Constraint(
        'unique(shift_id)',
        'Mỗi ca chỉ có một bản ghi chấm công.',
    )

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                rec.worked_hours = (rec.check_out - rec.check_in).total_seconds() / 3600.0
            else:
                rec.worked_hours = 0.0

    @api.model
    def _assert_allowed(self, shift, kind, has_note=False):
        """Validate chấm công 1 ca. Raise UserError mã lỗi để controller map HTTP.
        Nếu has_note=True, cho phép đi tiếp để cập nhật ghi chú giải trình."""
        if not shift or not shift.exists():
            raise UserError('no_shift')
        if shift.state != 'approved':
            raise UserError('shift_not_approved')
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        window = policy.shift_window_minutes or 15
        now = fields.Datetime.now()
        anchor = shift.start if kind == 'in' else shift.end
        if anchor and abs((now - anchor).total_seconds()) > window * 60:
            raise UserError('outside_shift_window')
        rec = self.sudo().search([('shift_id', '=', shift.id)], limit=1)
        if kind == 'in':
            if rec and rec.check_in and not has_note:
                raise UserError('already_checked_in')
        else:
            if not rec or not rec.check_in:
                raise UserError('not_checked_in')
            if rec.check_out and not has_note:
                raise UserError('already_checked_out')

    @api.model
    def _do_check(self, shift, payload, kind):
        """Ghi chấm công cho ca. Tái dùng face/geo của hocba.attendance.
        out_of_window: ngoài cửa sổ ±W quanh start (in) / end (out)."""
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        employee = shift.employee_id
        fg = self.env['hocba.attendance']._eval_face_geo(employee, payload, policy)
        now = fields.Datetime.now()
        window = policy.shift_window_minutes or 15
        anchor = shift.start if kind == 'in' else shift.end
        out_of_window = abs((now - anchor).total_seconds()) > window * 60
        lat = payload.get('latitude') or 0.0
        lng = payload.get('longitude') or 0.0

        rec = self.sudo().search([('shift_id', '=', shift.id)], limit=1)
        if kind == 'in':
            vals = {'check_in': now, 'check_in_photo': payload.get('photo'),
                    'check_in_lat': lat, 'check_in_lng': lng}
            if fg['face_score'] is not None:
                vals['check_in_face_score'] = fg['face_score']
        else:
            vals = {'check_out': now, 'check_out_photo': payload.get('photo'),
                    'check_out_lat': lat, 'check_out_lng': lng}
            if fg['face_score'] is not None:
                vals['check_out_face_score'] = fg['face_score']

        note = payload.get('note')
        if note:
            existing_notes = rec.notes or ""
            new_note = "[%s] %s: %s" % (
                fields.Datetime.context_timestamp(self, now).strftime('%H:%M'),
                'Vào' if kind == 'in' else 'Ra',
                note
            )
            vals['notes'] = (existing_notes + "\n" + new_note) if existing_notes else new_note

        vals.update({'face_suspect': fg['face_suspect'],
                     'out_of_zone': fg['out_of_zone'], 'out_of_window': out_of_window})
        if rec:
            rec.write(vals)
        else:
            vals['shift_id'] = shift.id
            rec = self.create(vals)
        return rec
