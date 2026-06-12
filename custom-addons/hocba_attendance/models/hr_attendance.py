import json
import math

from odoo import models, fields, api


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
                record.date = record.check_in.date()
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

    @api.depends('check_in', 'working_hours')
    def _compute_status(self):
        on_time_status = self.env['hocba.attendance.status'].search(
            [('code', '=', 'on_time')],
            limit=1
        )
        late_status = self.env['hocba.attendance.status'].search(
            [('code', '=', 'late')],
            limit=1
        )
        
        for record in self:
            if not record.check_in:
                record.status_id = False
                continue
            
            check_in_hour = record.check_in.hour
            if check_in_hour <= 8:
                record.status_id = on_time_status
            else:
                record.status_id = late_status

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for record in self:
            if record.check_out and record.check_in > record.check_out:
                raise models.ValidationError('Check-out time must be after check-in time')

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
