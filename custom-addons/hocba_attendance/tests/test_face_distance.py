from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestFaceDistance(TransactionCase):

    def test_distance_zero_identical(self):
        Att = self.env['hocba.attendance']
        a = [0.1] * 128
        self.assertAlmostEqual(Att._face_distance(a, a), 0.0, places=6)

    def test_distance_known_value(self):
        Att = self.env['hocba.attendance']
        a = [0.0] * 128
        b = [0.0] * 128
        b[0] = 3.0
        b[1] = 4.0  # euclidean = sqrt(9+16) = 5
        self.assertAlmostEqual(Att._face_distance(a, b), 5.0, places=6)

    def test_distance_none_when_length_mismatch(self):
        Att = self.env['hocba.attendance']
        self.assertIsNone(Att._face_distance([0.1, 0.2], [0.1] * 128))

    def test_distance_none_when_empty(self):
        Att = self.env['hocba.attendance']
        self.assertIsNone(Att._face_distance([], [0.1] * 128))
