import json
from datetime import timedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestCheckinEdgeCases(TransactionCase):

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
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
            'x_face_descriptor': json.dumps([0.0] * 128),
        })

    def _payload(self, **over):
        data = {
            'employee_id': self.employee.id,
            'photo': 'ZmFrZQ==',
            'descriptor': [0.0] * 128,
            'latitude': 21.028961,
            'longitude': 105.804817,
        }
        data.update(over)
        return data

    def test_self_service_checkin_as_regular_employee(self):
        """Bug #2: a non-HR employee must be able to self check-in via RPC."""
        user = self.env['res.users'].create({
            'name': 'Regular Emp',
            'login': 'reg_emp_attendance',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])],
        })
        self.employee.user_id = user.id
        Att = self.env['hocba.attendance'].with_user(user)
        res = Att.action_check_in(self._payload())
        self.assertTrue(res['record_id'])

    def test_second_checkin_does_not_overwrite_check_in(self):
        """Bug #5: re-checking in must keep the original check-in time."""
        Att = self.env['hocba.attendance']
        early = fields.Datetime.now() - timedelta(minutes=45)
        rec = Att.create({'employee_id': self.employee.id, 'check_in': early})
        Att._do_check(self._payload(), 'in')
        rec.invalidate_recordset()
        self.assertEqual(rec.check_in, early)

    def test_face_score_none_when_no_enrolled_descriptor(self):
        """Bug #7: unverifiable face returns None (not a misleading 0.0)."""
        emp = self.env['hr.employee'].create({
            'name': 'No Face',
            'x_employment_status': 'official',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
        })
        res = self.env['hocba.attendance']._do_check(
            self._payload(employee_id=emp.id), 'in')
        self.assertIsNone(res['face_score'])
        self.assertTrue(res['face_suspect'])

    def test_no_out_of_zone_when_office_unconfigured(self):
        """Bug #4: with no office coordinates set, geofence is off."""
        self.policy.write({'office_lat': 0.0, 'office_lng': 0.0})
        res = self.env['hocba.attendance']._do_check(
            self._payload(latitude=10.0, longitude=20.0), 'in')
        self.assertFalse(res['out_of_zone'])
