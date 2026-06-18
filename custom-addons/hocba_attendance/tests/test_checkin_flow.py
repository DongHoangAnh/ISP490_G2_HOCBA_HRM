import json

from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCheckinFlow(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'office_lat': 21.028511, 'office_lng': 105.804817,
            'office_radius_m': 150.0, 'face_threshold': 0.6,
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Nguyen Van A',
            'x_employment_status': 'official',
            # BR-010: official employees must declare MST TNCN + BHXH + CCCD
            'identification_id': '012345670003',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
            'x_face_descriptor': json.dumps([0.0] * 128),
        })

    def _payload(self, **over):
        data = {
            'employee_id': self.employee.id,
            'photo': 'ZmFrZQ==',            # base64 "fake"
            'descriptor': [0.0] * 128,       # identical -> distance 0
            'latitude': 21.028961,           # ~50m -> inside zone
            'longitude': 105.804817,
        }
        data.update(over)
        return data

    def test_checkin_creates_record(self):
        res = self.env['hocba.attendance']._do_check(self._payload(), 'in')
        self.assertTrue(res['record_id'])
        rec = self.env['hocba.attendance'].browse(res['record_id'])
        self.assertEqual(rec.employee_id, self.employee)
        self.assertTrue(rec.check_in)
        self.assertEqual(rec.check_in_lat, 21.028961)

    def test_matching_face_not_suspect(self):
        res = self.env['hocba.attendance']._do_check(self._payload(), 'in')
        rec = self.env['hocba.attendance'].browse(res['record_id'])
        self.assertFalse(rec.face_suspect)

    def test_mismatched_face_flagged(self):
        bad = [0.0] * 128
        bad[0] = 5.0  # distance 5 > 0.6
        res = self.env['hocba.attendance']._do_check(
            self._payload(descriptor=bad), 'in')
        rec = self.env['hocba.attendance'].browse(res['record_id'])
        self.assertTrue(rec.face_suspect)

    def test_out_of_zone_flagged(self):
        res = self.env['hocba.attendance']._do_check(
            self._payload(latitude=21.037511, longitude=105.804817), 'in')
        rec = self.env['hocba.attendance'].browse(res['record_id'])
        self.assertTrue(rec.out_of_zone)

    def test_second_checkin_same_day_updates_not_duplicates(self):
        Att = self.env['hocba.attendance']
        r1 = Att._do_check(self._payload(), 'in')
        r2 = Att._do_check(self._payload(), 'in')
        self.assertEqual(r1['record_id'], r2['record_id'])
        count = Att.search_count([('employee_id', '=', self.employee.id)])
        self.assertEqual(count, 1)

    def test_checkout_updates_same_record(self):
        Att = self.env['hocba.attendance']
        r1 = Att._do_check(self._payload(), 'in')
        r2 = Att._do_check(self._payload(), 'out')
        self.assertEqual(r1['record_id'], r2['record_id'])
        rec = Att.browse(r2['record_id'])
        self.assertTrue(rec.check_out)
