from odoo import models, fields, api
from odoo.exceptions import UserError


class TeachingAttendance(models.Model):
    """Chấm công theo buổi dạy — 1 bản ghi/buổi. Lịch dạy lấy từ CMS MySQL.
    Giáo viên xem lịch (read-only), không tự đăng ký — chỉ check-in/out."""
    _name = 'hocba.teaching.attendance'
    _description = 'Chấm công buổi dạy'
    _order = 'session_date desc, session_start'

    cms_session_id = fields.Char(
        string='CMS Session ID', required=True, index=True,
        help='ID buổi học trong CMS (class_session.id).')
    cms_class_id = fields.Char(string='CMS Class ID', index=True)
    class_name = fields.Char(string='Tên lớp')
    employee_id = fields.Many2one(
        'hr.employee', string='Giáo viên', required=True,
        ondelete='cascade', index=True)
    session_date = fields.Date(string='Ngày buổi học', index=True)
    session_start = fields.Char(string='Giờ bắt đầu', help='HH:MM')
    session_end = fields.Char(string='Giờ kết thúc', help='HH:MM')
    role_type = fields.Char(string='Vai trò', help='MAIN_TEACHER / ASSISTANT / TEACHER')

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
    out_of_window = fields.Boolean(string='Ngoài cửa sổ buổi')
    worked_hours = fields.Float(
        string='Số giờ dạy', compute='_compute_worked_hours', store=True)

    _session_emp_uniq = models.Constraint(
        'unique(cms_session_id, employee_id)',
        'Mỗi giáo viên chỉ có một bản ghi chấm công cho mỗi buổi học.',
    )

    @api.depends('check_in', 'check_out')
    def _compute_worked_hours(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                rec.worked_hours = (rec.check_out - rec.check_in).total_seconds() / 3600.0
            else:
                rec.worked_hours = 0.0

    @api.model
    def _assert_allowed(self, session_info, employee, kind):
        """Validate trước khi chấm công buổi dạy. Raise UserError mã lỗi."""
        from datetime import datetime, timedelta
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        window = policy.shift_window_minutes or 15

        # Parse session start/end thành UTC datetime để so sánh với now()
        session_date = session_info['date']
        start_str = session_info['start_time']  # "HH:MM:SS" từ MySQL timedelta
        end_str = session_info['end_time']

        def _parse_session_time(date_val, time_str):
            if isinstance(time_str, timedelta):
                total_s = int(time_str.total_seconds())
                h, m = divmod(total_s // 60, 60)
            else:
                parts = str(time_str).split(':')
                h, m = int(parts[0]), int(parts[1])
            # Giả sử giờ CMS là ICT (UTC+7), convert sang UTC
            local_dt = datetime(date_val.year, date_val.month, date_val.day, h, m)
            return local_dt - timedelta(hours=7)

        anchor_utc = _parse_session_time(session_date, start_str if kind == 'in' else end_str)
        now_utc = fields.Datetime.now()
        diff_s = abs((now_utc - anchor_utc).total_seconds())
        if diff_s > window * 60:
            raise UserError('outside_shift_window')

        rec = self.sudo().search(
            [('cms_session_id', '=', session_info['id']),
             ('employee_id', '=', employee.id)], limit=1)
        if kind == 'in':
            if rec and rec.check_in:
                raise UserError('already_checked_in')
        else:
            if not rec or not rec.check_in:
                raise UserError('not_checked_in')
            if rec.check_out:
                raise UserError('already_checked_out')

    @api.model
    def _do_check(self, session_info, employee, payload, kind):
        """Ghi chấm công buổi dạy."""
        from datetime import datetime, timedelta
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        fg = self.env['hocba.attendance']._eval_face_geo(employee, payload, policy)
        now = fields.Datetime.now()

        def _parse_session_time(date_val, time_str):
            if isinstance(time_str, timedelta):
                total_s = int(time_str.total_seconds())
                h, m = divmod(total_s // 60, 60)
            else:
                parts = str(time_str).split(':')
                h, m = int(parts[0]), int(parts[1])
            local_dt = datetime(date_val.year, date_val.month, date_val.day, h, m)
            return local_dt - timedelta(hours=7)

        window = policy.shift_window_minutes or 15
        session_date = session_info['date']
        anchor_utc = _parse_session_time(
            session_date,
            session_info['start_time'] if kind == 'in' else session_info['end_time'])
        out_of_window = abs((now - anchor_utc).total_seconds()) > window * 60

        lat = payload.get('latitude') or 0.0
        lng = payload.get('longitude') or 0.0

        rec = self.sudo().search(
            [('cms_session_id', '=', session_info['id']),
             ('employee_id', '=', employee.id)], limit=1)

        def _time_str(ts):
            if isinstance(ts, timedelta):
                total_s = int(ts.total_seconds())
                h, rem = divmod(total_s, 3600)
                m = rem // 60
                return f'{h:02d}:{m:02d}'
            parts = str(ts).split(':')
            return f'{int(parts[0]):02d}:{int(parts[1]):02d}'

        if kind == 'in':
            vals = {
                'check_in': now,
                'check_in_photo': payload.get('photo'),
                'check_in_lat': lat, 'check_in_lng': lng,
            }
            if fg['face_score'] is not None:
                vals['check_in_face_score'] = fg['face_score']
        else:
            vals = {
                'check_out': now,
                'check_out_photo': payload.get('photo'),
                'check_out_lat': lat, 'check_out_lng': lng,
            }
            if fg['face_score'] is not None:
                vals['check_out_face_score'] = fg['face_score']

        vals.update({
            'face_suspect': fg['face_suspect'],
            'out_of_zone': fg['out_of_zone'],
            'out_of_window': out_of_window,
        })

        if rec:
            rec.write(vals)
        else:
            vals.update({
                'cms_session_id': session_info['id'],
                'cms_class_id': session_info.get('class_id', ''),
                'class_name': session_info.get('class_name', ''),
                'employee_id': employee.id,
                'session_date': session_date,
                'session_start': _time_str(session_info.get('start_time', '')),
                'session_end': _time_str(session_info.get('end_time', '')),
                'role_type': session_info.get('role_type', ''),
            })
            rec = self.create(vals)
        return rec
