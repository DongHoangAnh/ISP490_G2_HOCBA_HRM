import json

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import (
    _fmt_hm, _att_me_info, _att_day_table, _att_me_history,
)


@tagged('post_install', '-at_install')
class TestAttendanceApi(TransactionCase):

    def setUp(self):
        super().setUp()
        self.policy = self.env['hocba.attendance.policy'].get_policy()
        self.policy.write({
            'morning_start': 8.0, 'morning_end': 9.5,
            'evening_start': 16.0, 'evening_end': 17.5,
            'office_lat': 0.0, 'office_lng': 0.0,
        })
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Chinh Thuc',
            'x_employment_status': 'official',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
            'x_face_descriptor': json.dumps([0.0] * 128),
        })
        self.emp_user = self.env['res.users'].create({
            'name': 'NV User', 'login': 'nv_att_user',
        })
        self.emp.user_id = self.emp_user
        self.hr_user = self.env['res.users'].create({
            'name': 'HR User', 'login': 'hr_att_user',
            'groups_id': [(4, self.env.ref('hr.group_hr_manager').id)],
        })

    def _checkin(self, emp):
        return self.env['hocba.attendance']._do_check({
            'employee_id': emp.id, 'photo': 'ZmFrZQ==',
            'descriptor': [0.0] * 128, 'latitude': 0.0, 'longitude': 0.0,
        }, 'in')

    def test_fmt_hm(self):
        self.assertEqual(_fmt_hm(8.0), '08:00')
        self.assertEqual(_fmt_hm(9.5), '09:30')

    def test_me_info_no_employee(self):
        user = self.env['res.users'].create({'name': 'NoEmp', 'login': 'noemp_att'})
        self.assertIsNone(_att_me_info(self.env(user=user)))

    def test_me_info_basic(self):
        info = _att_me_info(self.env(user=self.emp_user))
        self.assertEqual(info['employeeId'], self.emp.id)
        self.assertTrue(info['enrolled'])
        self.assertTrue(info['isOfficial'])
        self.assertEqual(info['policy']['checkInStart'], '08:00')
        self.assertIsNone(info['today'])

    def test_me_info_today_after_checkin(self):
        self._checkin(self.emp)
        info = _att_me_info(self.env(user=self.emp_user))
        self.assertIsNotNone(info['today'])
        self.assertIn(info['today']['statusKey'], ('on_time', 'late'))

    def test_day_table_hr_sees_all(self):
        self._checkin(self.emp)
        today = fields.Date.context_today(self.hr_user)
        data = _att_day_table(self.env(user=self.hr_user), str(today))
        self.assertTrue(data['isHrManager'])
        self.assertEqual(len(data['rows']), 1)
        self.assertEqual(data['rows'][0]['empId'], self.emp.id)

    def test_day_table_employee_sees_only_own(self):
        other = self.env['hr.employee'].create({
            'name': 'Other', 'x_employment_status': 'official',
            'x_pit_code': '1112223334', 'x_social_insurance_no': '9998887776',
        })
        self._checkin(self.emp)
        self._checkin(other)
        today = fields.Date.context_today(self.emp_user)
        data = _att_day_table(self.env(user=self.emp_user), str(today))
        self.assertFalse(data['isHr'])
        self.assertEqual(len(data['rows']), 1)
        self.assertEqual(data['rows'][0]['empId'], self.emp.id)

    def test_history_filters_employee(self):
        self._checkin(self.emp)
        today = fields.Date.context_today(self.emp_user)
        month = '%04d-%02d' % (today.year, today.month)
        data = _att_me_history(self.env(user=self.emp_user), month)
        self.assertEqual(data['month'], month)
        self.assertEqual(data['summary']['daysPresent'], 1)
        self.assertEqual(len(data['rows']), 1)

    def test_history_no_employee(self):
        user = self.env['res.users'].create({'name': 'NoEmp2', 'login': 'noemp_att2'})
        self.assertIsNone(_att_me_history(self.env(user=user), None))
