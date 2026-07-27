from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestAttendanceOfficeLocation(TransactionCase):
    """Test the new `hocba.attendance.office.location` model + multi-location
    geofence check. Requires the new fields added to
    `hocba.attendance.policy` (period_start_day / period_end_day /
    office_location_ids)."""

    def setUp(self):
        super().setUp()
        self.Location = self.env['hocba.attendance.office.location']
        self.policy = self.env['hocba.attendance.policy'].create({
            'name': 'Test Multi-Loc',
            # Leave the legacy fields alone: this test exercises the new
            # One2many path only.
        })

    def _add(self, name, lat, lng, radius=150.0):
        return self.Location.create({
            'policy_id': self.policy.id,
            'name': name, 'lat': lat, 'lng': lng, 'radius_m': radius,
        })

    def test_is_within_any_office_picks_first_match(self):
        loc_hn = self._add('Cơ sở Hà Nội', 21.028511, 105.804817, radius=150)
        self._add('Cơ sở HCM', 10.762622, 106.660172, radius=200)
        # ~50m north of Hanoi office → in
        self.assertTrue(self.policy.is_within_any_office(21.028961, 105.804817))
        # ~1km from Hanoi → out (also far from HCM)
        self.assertFalse(self.policy.is_within_any_office(21.037511, 105.804817))
        # ~50m east of HCM office → in
        self.assertTrue(self.policy.is_within_any_office(10.762622, 106.661900))

    def test_is_within_any_office_false_when_no_location_and_no_legacy(self):
        # No location, no legacy lat/lng → outside
        self.assertFalse(self.policy.is_within_any_office(21.0, 105.0))

    def test_is_within_any_office_uses_legacy_when_no_location(self):
        # Legacy fallback so existing data keeps working until admin migrates
        legacy = self.env['hocba.attendance.policy'].create({
            'name': 'Legacy Fallback',
            'office_lat': 21.028511, 'office_lng': 105.804817,
            'office_radius_m': 150,
        })
        self.assertTrue(legacy.is_within_any_office(21.028961, 105.804817))
        self.assertFalse(legacy.is_within_any_office(21.037511, 105.804817))

    def test_map_url_format(self):
        loc = self._add('HN', 21.028511, 105.804817)
        self.assertIn('21.028511,105.804817', loc.map_url)
        self.assertTrue(loc.map_url.startswith('https://'))

    def test_inactive_location_excluded(self):
        loc = self._add('HN inactive', 21.028511, 105.804817)
        loc.active = False
        self.assertFalse(self.policy.is_within_any_office(21.028961, 105.804817))


@tagged('post_install', '-at_install')
class TestAttendancePolicyPeriod(TransactionCase):
    """Test period_start_day / period_end_day validation on policy."""

    def setUp(self):
        super().setUp()
        self.Policy = self.env['hocba.attendance.policy']

    def _make(self, **kw):
        vals = {'name': kw.pop('name', 'P')}
        vals.update(kw)
        return self.Policy.create(vals)

    def test_default_period_is_calendar_month(self):
        p = self._make()
        self.assertEqual(p.period_start_day, 1)
        self.assertEqual(p.period_end_day, 1)

    def test_mid_month_to_mid_month_valid(self):
        p = self._make(period_start_day=15, period_end_day=15)
        self.assertEqual((p.period_start_day, p.period_end_day), (15, 15))

    def test_period_wraps_across_month_boundary_allowed(self):
        # 25 → 5 = period covers 25..end_of_month then 1..5 of next month
        p = self._make(period_start_day=25, period_end_day=5)
        self.assertEqual((p.period_start_day, p.period_end_day), (25, 5))

    def test_period_start_day_zero_invalid(self):
        with self.assertRaises(ValidationError):
            self._make(period_start_day=0)

    def test_period_start_day_above_31_invalid(self):
        with self.assertRaises(ValidationError):
            self._make(period_start_day=32)

    def test_period_end_day_zero_invalid(self):
        with self.assertRaises(ValidationError):
            self._make(period_end_day=0)

    def test_period_end_day_above_31_invalid(self):
        with self.assertRaises(ValidationError):
            self._make(period_end_day=32)

    def test_default_location_is_first_active(self):
        p = self._make()
        loc1 = self.env['hocba.attendance.office.location'].create({
            'policy_id': p.id, 'name': 'A', 'lat': 0, 'lng': 0,
            'sequence': 20,
        })
        loc2 = self.env['hocba.attendance.office.location'].create({
            'policy_id': p.id, 'name': 'B', 'lat': 0, 'lng': 0,
            'sequence': 10,
        })
        # default_location_id picks the lowest sequence among active ones
        self.assertEqual(p.default_location_id, loc2)