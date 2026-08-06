from odoo import models, fields, api
from odoo.exceptions import ValidationError


class AttendanceOfficeLocation(models.Model):
    """Một vị trí chấm công hợp lệ (cơ sở). Nhiều location/policy, mỗi
    location gắn một bán kính cho phép. Check `is_within_any_office` trên
    `hocba.attendance.policy` sẽ match nếu nằm trong BẤT KỲ location active."""
    _name = 'hocba.attendance.office.location'
    _description = 'Vị trí chấm công hợp lệ (cơ sở)'
    _order = 'sequence, id'

    policy_id = fields.Many2one(
        'hocba.attendance.policy', string='Chính sách',
        required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Tên cơ sở', required=True)
    lat = fields.Float(string='Vĩ độ', digits=(10, 7), required=True)
    lng = fields.Float(string='Kinh độ', digits=(10, 7), required=True)
    radius_m = fields.Float(string='Bán kính cho phép (m)', default=150.0)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10, index=True)
    map_url = fields.Char(
        string='Google Maps', compute='_compute_map_url',
        help='Link mở vị trí trên Google Maps.')

    _loc_required_geo = models.Constraint(
        'CHECK(lat IS NOT NULL AND lng IS NOT NULL)',
        'Vị trí phải có lat/lng hợp lệ.',
    )

    @api.depends('lat', 'lng')
    def _compute_map_url(self):
        for rec in self:
            if rec.lat and rec.lng:
                rec.map_url = (
                    'https://www.google.com/maps/search/?api=1&query='
                    '%s,%s' % (rec.lat, rec.lng))
            else:
                rec.map_url = False

    @api.constrains('radius_m')
    def _check_radius(self):
        for rec in self:
            if rec.radius_m is None or rec.radius_m <= 0:
                raise ValidationError(
                    'Bán kính cho phép phải > 0 (cơ sở: %s).' % rec.name)

    def is_within(self, lat, lng):
        """True nếu (lat, lng) nằm trong bán kính của location này."""
        self.ensure_one()
        if not lat or not lng or not self.lat or not self.lng:
            return False
        # _haversine_m nằm trên `hocba.attendance.policy` (shared helper).
        dist = self.env['hocba.attendance.policy']._haversine_m(
            self.lat, self.lng, lat, lng)
        return dist <= self.radius_m
