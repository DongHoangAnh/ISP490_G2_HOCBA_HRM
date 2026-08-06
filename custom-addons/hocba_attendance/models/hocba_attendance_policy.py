import json
import math

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AttendancePolicy(models.Model):
    _name = 'hocba.attendance.policy'
    _description = 'Attendance Policy (geofence, time window, face threshold)'

    name = fields.Char(string='Name', required=True, default='Default Policy')
    active = fields.Boolean(default=True)

    # Time windows (local hours as float: 8.5 = 08:30)
    morning_start = fields.Float(string='Check-in window start', default=8.0)
    morning_end = fields.Float(string='Check-in window end', default=9.5)
    evening_start = fields.Float(string='Check-out window start', default=16.0)
    evening_end = fields.Float(string='Check-out window end', default=17.5)

    # Workdays (Mon..Sun); default Mon-Fri True
    workday_mon = fields.Boolean(string='Monday', default=True)
    workday_tue = fields.Boolean(string='Tuesday', default=True)
    workday_wed = fields.Boolean(string='Wednesday', default=True)
    workday_thu = fields.Boolean(string='Thursday', default=True)
    workday_fri = fields.Boolean(string='Friday', default=True)
    workday_sat = fields.Boolean(string='Saturday', default=False)
    workday_sun = fields.Boolean(string='Sunday', default=False)

    # Geofence
    office_lat = fields.Float(string='Office latitude', digits=(10, 7))
    office_lng = fields.Float(string='Office longitude', digits=(10, 7))
    office_radius_m = fields.Float(string='Allowed radius (m)', default=150.0)
    office_map_url = fields.Char(string='Google Maps Link')

    # Face matching: euclidean distance threshold; distance > threshold => suspect
    face_threshold = fields.Float(string='Face match threshold', default=0.6)

    # --- Tính công (Gói 1): mốc trễ + công sáng/chiều + công thiếu ---
    late_cutoff = fields.Float(
        string='Mốc đi trễ (giờ)', default=9.5,
        help='Check-in sau giờ này (9.5 = 09:30) tính là đi trễ.')
    morning_credit_cutoff = fields.Float(
        string='Hạn công sáng (giờ)', default=10.0,
        help='Check-in sau giờ này mất công sáng (½ công).')
    std_work_hours = fields.Float(
        string='Giờ làm chuẩn/ngày', default=8.0,
        help='Mốc giờ ra mong đợi = check-in + số giờ này.')
    afternoon_margin_hours = fields.Float(
        string='Biên về sớm mất công chiều (giờ)', default=2.0,
        help='Check-out sớm hơn (giờ chuẩn − biên này) so mốc vào → mất công chiều.')
    violation_free_days = fields.Integer(
        string='Số ngày vi phạm miễn trừ/tháng', default=2,
        help='Số ngày vi phạm đầu tháng không tính vào công thiếu.')
    shift_window_minutes = fields.Integer(
        string='Cửa sổ check-in ca (phút)', default=15,
        help='CTV/OT được check-in/out trong ±N phút quanh giờ ca đã duyệt.')

    # --- Kỳ tính công (admin sửa được): 1..31, mặc định 1→1 (tháng dương lịch)
    # Ví dụ 15→15 = kỳ trung tuần; 25→5 = kỳ cuối tháng trước → đầu tháng sau.
    period_start_day = fields.Integer(
        string='Ngày đầu kỳ tính công (1..31)', default=1)
    period_end_day = fields.Integer(
        string='Ngày cuối kỳ tính công (1..31)', default=1,
        help='Nếu < period_start_day, kỳ cuốn sang tháng kế tiếp.')

    # --- Đa vị trí chấm công hợp lệ (cơ sở)
    office_location_ids = fields.One2many(
        'hocba.attendance.office.location', 'policy_id',
        string='Vị trí chấm công hợp lệ')
    default_location_id = fields.Many2one(
        'hocba.attendance.office.location', string='Vị trí mặc định',
        compute='_compute_default_location', store=True)
    default_map_url = fields.Char(
        string='Google Maps (mặc định)',
        related='default_location_id.map_url', readonly=True)

    @api.depends('office_location_ids.sequence', 'office_location_ids.active')
    def _compute_default_location(self):
        for rec in self:
            active = rec.office_location_ids.filtered(lambda l: l.active)
            rec.default_location_id = (
                active.sorted(lambda l: (l.sequence, l.id))[:1]
                if active else False)

    _period_start_range = models.Constraint(
        'CHECK(period_start_day BETWEEN 1 AND 31)',
        'period_start_day phải nằm trong 1..31.')
    _period_end_range = models.Constraint(
        'CHECK(period_end_day BETWEEN 1 AND 31)',
        'period_end_day phải nằm trong 1..31.')

    @api.constrains('period_start_day', 'period_end_day')
    def _check_period_days(self):
        for rec in self:
            if not 1 <= rec.period_start_day <= 31:
                raise ValidationError(
                    'Ngày đầu kỳ (%s) phải nằm trong 1..31.'
                    % rec.period_start_day)
            if not 1 <= rec.period_end_day <= 31:
                raise ValidationError(
                    'Ngày cuối kỳ (%s) phải nằm trong 1..31.'
                    % rec.period_end_day)

    @api.model
    def get_policy(self):
        """Return the active policy, creating a default one if none exists."""
        policy = self.search([], limit=1)
        if not policy:
            policy = self.create({'name': 'Default Policy'})
        return policy

    @staticmethod
    def _haversine_m(lat1, lng1, lat2, lng2):
        """Great-circle distance between two WGS84 points, in meters."""
        r = 6371000.0  # Earth radius (m)
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlmb = math.radians(lng2 - lng1)
        a = (math.sin(dphi / 2) ** 2
             + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2)
        return 2 * r * math.asin(math.sqrt(a))

    def is_within_office(self, lat, lng):
        """Backward-compatible alias for `is_within_any_office`. Returns True
        if (lat, lng) is within any active `office_location_ids` (preferred)
        or, if none, within the legacy single office point."""
        return self.is_within_any_office(lat, lng)

    def is_within_any_office(self, lat, lng):
        """True if (lat, lng) falls within ANY active location on this policy.
        Falls back to the legacy single-office fields when no location has
        been set yet (existing data keeps working until admin migrates)."""
        self.ensure_one()
        if not lat or not lng:
            return False
        active = self.office_location_ids.filtered('active')
        for loc in active:
            if loc.is_within(lat, lng):
                return True
        # Legacy fallback (single office lat/lng/radius)
        if self.office_lat and self.office_lng:
            dist = self._haversine_m(self.office_lat, self.office_lng, lat, lng)
            return dist <= self.office_radius_m
        return False

    def is_workday(self, dt_local):
        """True if dt_local (naive local datetime) falls on an enabled workday."""
        self.ensure_one()
        flags = [
            self.workday_mon, self.workday_tue, self.workday_wed,
            self.workday_thu, self.workday_fri, self.workday_sat,
            self.workday_sun,
        ]
        return bool(flags[dt_local.weekday()])

    def is_within_window(self, dt_local, kind):
        """True if dt_local is on a workday AND within the window for `kind`
        ('in' = check-in / morning, 'out' = check-out / evening)."""
        self.ensure_one()
        if not self.is_workday(dt_local):
            return False
        hour = dt_local.hour + dt_local.minute / 60.0
        if kind == 'in':
            return self.morning_start <= hour <= self.morning_end
        return self.evening_start <= hour <= self.evening_end


class AttendancePeriodHistory(models.Model):
    _name = 'hocba.attendance.period.history'
    _description = 'Lịch sử cấu hình chu kỳ chấm công'
    _order = 'apply_from desc'

    apply_from = fields.Date(
        string='Áp dụng từ ngày', required=True,
        help='Cấu hình này sẽ có hiệu lực cho các tháng tính từ ngày này trở đi.')
    period_start_day = fields.Integer(
        string='Ngày bắt đầu kỳ (1..31)', default=1, required=True)

    _sql_constraints = [
        ('apply_from_unique', 'unique(apply_from)',
         'Mỗi ngày chỉ có một cấu hình áp dụng.')
    ]

    @api.constrains('period_start_day')
    def _check_start_day(self):
        for rec in self:
            if not 1 <= rec.period_start_day <= 31:
                raise ValidationError('Ngày bắt đầu kỳ phải nằm trong 1..31.')
