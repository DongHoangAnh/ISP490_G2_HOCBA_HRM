from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPolicyGeofence(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].create({
            'name': 'Test',
            'office_lat': 21.028511,    # Hanoi
            'office_lng': 105.804817,
            'office_radius_m': 150.0,
        })

    def test_distance_zero_for_same_point(self):
        d = self.policy._haversine_m(21.028511, 105.804817,
                                     21.028511, 105.804817)
        self.assertAlmostEqual(d, 0.0, places=3)

    def test_known_distance_about_1km(self):
        # ~0.009 deg latitude ~= 1 km
        d = self.policy._haversine_m(21.028511, 105.804817,
                                     21.037511, 105.804817)
        self.assertTrue(950 < d < 1050, f"expected ~1000m, got {d}")

    def test_within_office_true_inside(self):
        # ~50m north of office
        self.assertTrue(self.policy.is_within_office(21.028961, 105.804817))

    def test_within_office_false_outside(self):
        # ~1km away -> outside 150m radius
        self.assertFalse(self.policy.is_within_office(21.037511, 105.804817))

    def test_within_office_false_when_coords_missing(self):
        self.assertFalse(self.policy.is_within_office(False, False))
