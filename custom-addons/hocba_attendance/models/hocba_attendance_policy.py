import json
import math

from odoo import models, fields, api


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

    # Face matching: euclidean distance threshold; distance > threshold => suspect
    face_threshold = fields.Float(string='Face match threshold', default=0.6)

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
        """True if (lat, lng) is within office_radius_m of the office point.
        Returns False if any coordinate is missing/unset."""
        self.ensure_one()
        if not lat or not lng or not self.office_lat or not self.office_lng:
            return False
        dist = self._haversine_m(self.office_lat, self.office_lng, lat, lng)
        return dist <= self.office_radius_m
