import json
import math

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

    @api.depends('check_in')
    def _compute_date(self):
        for record in self:
            if record.check_in:
                local_dt = fields.Datetime.context_timestamp(record, record.check_in)
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

    @api.depends('check_in')
    def _compute_status(self):
        Status = self.env['hocba.attendance.status']
        on_time_status = Status.search([('code', '=', 'on_time')], limit=1)
        late_status = Status.search([('code', '=', 'late')], limit=1)
        policy = self.env['hocba.attendance.policy'].get_policy()
        cutoff = policy.morning_start

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
                'https://www.google.com/maps?q=%s,%s'
                % (rec.check_in_lat, rec.check_in_lng)
                if rec.check_in_lat and rec.check_in_lng else False)
            rec.check_out_map_url = (
                'https://www.google.com/maps?q=%s,%s'
                % (rec.check_out_lat, rec.check_out_lng)
                if rec.check_out_lat and rec.check_out_lng else False)

    @staticmethod
    def _face_distance(desc_a, desc_b):
        """Euclidean distance between two 128-d descriptors (lists of floats).
        Returns None if either is empty or lengths differ."""
        if not desc_a or not desc_b or len(desc_a) != len(desc_b):
            return None
        return math.sqrt(sum((x - y) ** 2 for x, y in zip(desc_a, desc_b)))

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
            self.with_context(tz=self.env.user.tz or 'UTC'), now
        ).replace(tzinfo=None)
        today = now_local.date()

        lat = payload.get('latitude') or 0.0
        lng = payload.get('longitude') or 0.0

        # Face matching
        face_score = None
        face_suspect = False
        enrolled = []
        if employee.x_face_descriptor:
            try:
                enrolled = json.loads(employee.x_face_descriptor)
            except (ValueError, TypeError):
                enrolled = []
        dist = self._face_distance(payload.get('descriptor') or [], enrolled)
        if dist is None:
            face_suspect = True   # cannot verify -> flag for review
        else:
            face_score = dist
            face_suspect = dist > policy.face_threshold

        # Only enforce the geofence when the office location is configured;
        # otherwise we cannot judge the location and must not flag everyone.
        if policy.office_lat and policy.office_lng:
            out_of_zone = not policy.is_within_office(lat, lng)
        else:
            out_of_zone = False
        out_of_window = not policy.is_within_window(now_local, kind)

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
        return self.sudo()._do_check(payload, 'in')

    @api.model
    def action_check_out(self, payload):
        """RPC entry: self-service check-out for the current user's employee."""
        payload = dict(payload or {})
        employee = self.env.user.employee_id
        if not employee:
            raise UserError('Tài khoản của bạn chưa được gắn với hồ sơ nhân viên.')
        payload['employee_id'] = employee.id
        return self.sudo()._do_check(payload, 'out')
