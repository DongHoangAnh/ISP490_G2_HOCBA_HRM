import json
import math
from datetime import timedelta

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Attendance(models.Model):
    _name = 'hocba.attendance'
    _description = 'Attendance Record'
    _order = 'date desc, check_in desc'

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True
    )
    check_in = fields.Datetime(
        string='Check In',
        required=True
    )
    check_out = fields.Datetime(string='Check Out')
    work_assignment_id = fields.Many2one(
        'hocba.work_assignment',
        string='Work Assignment',
        ondelete='set null'
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Department',
        related='employee_id.department_id',
        readonly=True,
        store=True
    )
    status_id = fields.Many2one(
        'hocba.attendance.status',
        string='Status',
        compute='_compute_status',
        store=True
    )
    status_code = fields.Char(
        string='Status Code',
        related='status_id.code',
        readonly=True,
        store=True
    )
    notes = fields.Text(string='Notes')
    date = fields.Date(
        string='Date',
        compute='_compute_date',
        store=True,
        index=True
    )
    working_hours = fields.Float(
        string='Working Hours',
        compute='_compute_working_hours',
        store=True,
        help='Number of hours worked'
    )
    expected_check_out = fields.Datetime(
        string='Giờ ra mong đợi',
        compute='_compute_work_metrics', store=True)
    late_minutes = fields.Integer(
        string='Phút đi trễ',
        compute='_compute_work_metrics', store=True)
    early_leave_minutes = fields.Integer(
        string='Phút về sớm',
        compute='_compute_work_metrics', store=True)
    missing_minutes = fields.Integer(
        string='Phút thiếu',
        compute='_compute_work_metrics', store=True)
    morning_credit = fields.Float(
        string='Công sáng',
        compute='_compute_work_metrics', store=True)
    afternoon_credit = fields.Float(
        string='Công chiều',
        compute='_compute_work_metrics', store=True)
    work_credit = fields.Float(
        string='Công ngày',
        compute='_compute_work_metrics', store=True,
        help='0 / 0.5 / 1.0 = công sáng + công chiều.')
    active = fields.Boolean(default=True)

    # --- Face + geolocation check-in (F: face attendance) ---
    check_in_photo = fields.Binary(string='Check-in Photo', attachment=True)
    check_out_photo = fields.Binary(string='Check-out Photo', attachment=True)
    check_in_lat = fields.Float(string='Check-in Latitude', digits=(10, 7))
    check_in_lng = fields.Float(string='Check-in Longitude', digits=(10, 7))
    check_out_lat = fields.Float(string='Check-out Latitude', digits=(10, 7))
    check_out_lng = fields.Float(string='Check-out Longitude', digits=(10, 7))
    check_in_face_score = fields.Float(string='Check-in Face Distance')
    check_out_face_score = fields.Float(string='Check-out Face Distance')
    face_suspect = fields.Boolean(string='Face Suspect')
    out_of_zone = fields.Boolean(string='Out of Office Zone')
    out_of_window = fields.Boolean(string='Out of Time Window')
    needs_review = fields.Boolean(
        string='Needs Review',
        compute='_compute_needs_review',
        store=True,
    )
    check_in_map_url = fields.Char(
        string='Check-in Map', compute='_compute_map_urls')
    check_out_map_url = fields.Char(
        string='Check-out Map', compute='_compute_map_urls')

    @api.depends('check_in', 'employee_id')
    def _compute_date(self):
        for record in self:
            if record.check_in:
                emp_tz = record.employee_id.user_id.tz or 'UTC'
                local_dt = fields.Datetime.context_timestamp(
                    record.with_context(tz=emp_tz), record.check_in)
                record.date = local_dt.date()
            else:
                record.date = False

    @api.depends('check_in', 'check_out')
    def _compute_working_hours(self):
        for record in self:
            if record.check_in and record.check_out:
                delta = record.check_out - record.check_in
                record.working_hours = delta.total_seconds() / 3600.0
            else:
                record.working_hours = 0.0

    @api.depends('check_in', 'check_out')
    def _compute_work_metrics(self):
        policy = self.env['hocba.attendance.policy'].get_policy()
        std = policy.std_work_hours or 8.0
        late_cut = policy.late_cutoff or 9.5
        morn_cut = policy.morning_credit_cutoff or 10.0
        aft_margin = policy.afternoon_margin_hours or 2.0
        for rec in self:
            ci, co = rec.check_in, rec.check_out
            rec.expected_check_out = (ci + timedelta(hours=std)) if ci else False
            if ci:
                local_in = fields.Datetime.context_timestamp(rec, ci)
                in_hour = local_in.hour + local_in.minute / 60.0
                rec.late_minutes = max(0, int(round((in_hour - late_cut) * 60)))
                rec.morning_credit = 0.5 if in_hour <= morn_cut else 0.0
            else:
                rec.late_minutes = 0
                rec.morning_credit = 0.0
            if ci and co:
                worked_min = (co - ci).total_seconds() / 60.0
                expected = ci + timedelta(hours=std)
                rec.early_leave_minutes = max(
                    0, int(round((expected - co).total_seconds() / 60.0)))
                aft_threshold = ci + timedelta(hours=std - aft_margin)
                rec.afternoon_credit = 0.5 if co >= aft_threshold else 0.0
                work_credit = rec.morning_credit + rec.afternoon_credit
                basis = (std / 2.0) if work_credit == 0.5 else std
                rec.missing_minutes = max(
                    0, min(240, int(round(basis * 60 - worked_min))))
            else:
                rec.missing_minutes = 0
                rec.early_leave_minutes = 0
                rec.afternoon_credit = 0.0
            rec.work_credit = rec.morning_credit + rec.afternoon_credit

    @api.depends('check_in')
    def _compute_status(self):
        Status = self.env['hocba.attendance.status']
        on_time_status = Status.search([('code', '=', 'on_time')], limit=1)
        late_status = Status.search([('code', '=', 'late')], limit=1)
        policy = self.env['hocba.attendance.policy'].get_policy()
        cutoff = policy.late_cutoff

        for record in self:
            if not record.check_in:
                record.status_id = False
                continue

            # check_in is stored in UTC; lateness is judged in local time.
            local_dt = fields.Datetime.context_timestamp(record, record.check_in)
            check_in_hour = local_dt.hour + local_dt.minute / 60.0
            if check_in_hour <= cutoff:
                record.status_id = on_time_status
            else:
                record.status_id = late_status

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for record in self:
            if record.check_out and record.check_in > record.check_out:
                raise ValidationError('Check-out time must be after check-in time')

    @api.depends('face_suspect', 'out_of_zone', 'out_of_window')
    def _compute_needs_review(self):
        for rec in self:
            rec.needs_review = (
                rec.face_suspect or rec.out_of_zone or rec.out_of_window)

    @api.depends('check_in_lat', 'check_in_lng',
                 'check_out_lat', 'check_out_lng')
    def _compute_map_urls(self):
        for rec in self:
            rec.check_in_map_url = (
                'https://www.google.com/maps/search/?api=1&query=%s,%s'
                % (rec.check_in_lat, rec.check_in_lng)
                if rec.check_in_lat and rec.check_in_lng else False)
            rec.check_out_map_url = (
                'https://www.google.com/maps/search/?api=1&query=%s,%s'
                % (rec.check_out_lat, rec.check_out_lng)
                if rec.check_out_lat and rec.check_out_lng else False)

    @staticmethod
    def _face_distance(desc_a, desc_b):
        """Euclidean distance between two 128-d descriptors (lists of floats).
        Returns None if either is empty or lengths differ."""
        if not desc_a or not desc_b or len(desc_a) != len(desc_b):
            return None
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(desc_a, desc_b)))

    @api.model
    def _eval_face_geo(self, employee, payload, policy):
        """Tính face_score/face_suspect/out_of_zone dùng chung cho chấm công
        ngày thường và chấm công ca."""
        face_score = None
        enrolled = []
        if employee.x_face_descriptor:
            try:
                enrolled = json.loads(employee.x_face_descriptor)
            except (ValueError, TypeError):
                enrolled = []
        dist = self._face_distance(payload.get('descriptor') or [], enrolled)
        if dist is None:
            face_suspect = True
        else:
            face_score = dist
            face_suspect = dist > policy.face_threshold
        lat = payload.get('latitude') or 0.0
        lng = payload.get('longitude') or 0.0
        if policy.office_lat and policy.office_lng:
            out_of_zone = not policy.is_within_office(lat, lng)
        else:
            out_of_zone = False
        return {'face_score': face_score, 'face_suspect': face_suspect,
                'out_of_zone': out_of_zone}

    def _do_check(self, payload, kind):
        """Core check-in/out logic. `kind` is 'in' or 'out'.
        payload keys: employee_id, photo (base64 str), descriptor (list),
        latitude (float), longitude (float).
        Returns dict {record_id, kind, face_suspect, out_of_zone,
        out_of_window, face_score}."""
        employee = self.env['hr.employee'].browse(payload['employee_id'])
        if not employee.exists():
            raise UserError('Không tìm thấy nhân viên cho điểm danh.')

        policy = self.env['hocba.attendance.policy'].get_policy()
        now = fields.Datetime.now()
        now_local = fields.Datetime.context_timestamp(
            self.with_context(tz=self._context.get('tz') or self.env.user.tz or 'UTC'), now
        ).replace(tzinfo=None)
        today = now_local.date()

        lat = payload.get('latitude') or 0.0
        lng = payload.get('longitude') or 0.0

        fg = self._eval_face_geo(employee, payload, policy)
        face_score = fg['face_score']
        face_suspect = fg['face_suspect']
        out_of_zone = fg['out_of_zone']
        if employee.x_employment_status == 'official':
            out_of_window = not policy.is_within_window(now_local, kind)
        else:
            # non-official (CTV/OT): cờ theo cửa sổ ±W quanh giờ ca approved
            window = policy.shift_window_minutes or 15
            in_win = False
            for s in self._todays_approved_shifts(employee, today):
                anchor = fields.Datetime.context_timestamp(
                    s, s.start if kind == 'in' else s.end).replace(tzinfo=None)
                if abs((now_local - anchor).total_seconds()) <= window * 60:
                    in_win = True
                    break
            out_of_window = not in_win

        # One record per employee per day
        record = self.search([
            ('employee_id', '=', employee.id),
            ('date', '=', today),
        ], limit=1)

        if kind == 'in':
            vals = {
                'check_in_photo': payload.get('photo'),
                'check_in_lat': lat,
                'check_in_lng': lng,
            }
            # Keep the original check-in time on a repeated check-in the same day.
            if not record or not record.check_in:
                vals['check_in'] = now
            if not record:
                vals['employee_id'] = employee.id
        else:  # out
            vals = {
                'check_out': now,
                'check_out_photo': payload.get('photo'),
                'check_out_lat': lat,
                'check_out_lng': lng,
            }
            if not record:
                # checkout with no prior check-in today: still create
                vals['employee_id'] = employee.id
                vals['check_in'] = now

        vals.update({
            'face_suspect': face_suspect,
            'out_of_zone': out_of_zone,
            'out_of_window': out_of_window,
        })

        if face_score is not None:
            vals['check_in_face_score' if kind == 'in' else 'check_out_face_score'] = face_score

        if record:
            record.write(vals)
        else:
            record = self.create(vals)

        return {
            'record_id': record.id,
            'kind': kind,
            'face_suspect': face_suspect,
            'out_of_zone': out_of_zone,
            'out_of_window': out_of_window,
            'face_score': face_score,
        }

    def _assert_check_allowed(self, employee, kind):
        """Chặn check-in/out sai luật: ngày nghỉ, đã check-in/out, chưa check-in.
        Raise UserError với mã lỗi làm message để controller map sang HTTP."""
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        now_local = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.user.tz or 'UTC'),
            fields.Datetime.now()).replace(tzinfo=None)
        if not policy.is_workday(now_local):
            raise UserError('not_workday')
        rec = self.sudo().search([
            ('employee_id', '=', employee.id),
            ('date', '=', now_local.date()),
        ], limit=1)
        if kind == 'in':
            if rec and rec.check_in:
                raise UserError('already_checked_in')
        else:
            if not rec or not rec.check_in:
                raise UserError('not_checked_in')
            if rec.check_out:
                raise UserError('already_checked_out')

    def _todays_approved_shifts(self, employee, today):
        """Ca approved của employee có start rơi vào ngày local `today`."""
        shifts = self.env['hocba.work_shift'].sudo().search([
            ('employee_id', '=', employee.id), ('state', '=', 'approved')])
        emp_tz = employee.user_id.tz or 'UTC'
        tz_ctx = self.with_context(tz=emp_tz)
        return shifts.filtered(
            lambda s: fields.Datetime.context_timestamp(tz_ctx, s.start).date() == today)

    def _assert_shift_check_allowed(self, employee, kind):
        """CTV/OT (non-official): check-in/out theo ca approved + cửa sổ ±W phút.
        Raise UserError mã lỗi: no_shift_today / outside_shift_window /
        already_checked_in / not_checked_in / already_checked_out."""
        policy = self.env['hocba.attendance.policy'].sudo().get_policy()
        window = policy.shift_window_minutes or 15
        emp_tz = employee.user_id.tz or 'UTC'
        now_local = fields.Datetime.context_timestamp(
            self.with_context(tz=emp_tz),
            fields.Datetime.now()).replace(tzinfo=None)
        today = now_local.date()
        shifts = self._todays_approved_shifts(employee, today)
        if not shifts:
            raise UserError('no_shift_today')
        in_window = False
        for s in shifts:
            anchor_utc = s.start if kind == 'in' else s.end
            anchor = fields.Datetime.context_timestamp(
                self.with_context(tz=emp_tz), anchor_utc).replace(tzinfo=None)
            if abs((now_local - anchor).total_seconds()) <= window * 60:
                in_window = True
                break
        if not in_window:
            raise UserError('outside_shift_window')
        rec = self.sudo().search([
            ('employee_id', '=', employee.id), ('date', '=', today)], limit=1)
        if kind == 'in':
            if rec and rec.check_in:
                raise UserError('already_checked_in')
        else:
            if not rec or not rec.check_in:
                raise UserError('not_checked_in')
            if rec.check_out:
                raise UserError('already_checked_out')

    @api.model
    def action_check_in(self, payload):
        """RPC entry: self-service check-in for the current user's employee."""
        payload = dict(payload or {})
        employee = self.env.user.employee_id
        if not employee:
            raise UserError('Tài khoản của bạn chưa được gắn với hồ sơ nhân viên.')
        payload['employee_id'] = employee.id
        # Self-service: regular employees aren't in the HR groups that own the
        # ACL on attendance/policy/status, so run the write under sudo. The
        # employee is already pinned to the caller above, preventing spoofing.
        self._assert_check_allowed(employee, 'in')
        return self.sudo()._do_check(payload, 'in')

    @api.model
    def action_check_out(self, payload):
        """RPC entry: self-service check-out for the current user's employee."""
        payload = dict(payload or {})
        employee = self.env.user.employee_id
        if not employee:
            raise UserError('Tài khoản của bạn chưa được gắn với hồ sơ nhân viên.')
        payload['employee_id'] = employee.id
        self._assert_check_allowed(employee, 'out')
        return self.sudo()._do_check(payload, 'out')
