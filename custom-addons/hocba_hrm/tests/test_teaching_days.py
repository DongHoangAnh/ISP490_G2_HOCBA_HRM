from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.main import _teaching_days_payload


@tagged('post_install', '-at_install')
class TestTeachingDays(TransactionCase):
    """Endpoint /api/teaching/days — đánh dấu ngày dạy trên tab 'Lịch'.

    Nguồn dữ liệu là model `hocba.teaching.session` trong Neon (không đọc CMS).
    """

    def setUp(self):
        super().setUp()
        # NV không phải giáo viên (không có x_cms_user_id).
        self.emp = self.env['hr.employee'].create({
            'name': 'NV Khong Day',
            'x_employment_status': 'official',
            'identification_id': '012345678901',
            'x_pit_code': '8765432109',
            'x_social_insurance_no': '0123456789',
        })
        self.user = self.env['res.users'].create({
            'name': 'NV User', 'login': 'nv_teach_days',
        })
        self.emp.user_id = self.user
        # Giáo viên (có x_cms_user_id).
        self.teacher = self.env['hr.employee'].create({
            'name': 'Giao Vien',
            'x_employment_status': 'official',
            'identification_id': '012345678902',
            'x_pit_code': '8765432108',
            'x_social_insurance_no': '0123456788',
            'x_cms_user_id': 'cms-tutor-1',
        })
        self.teacher_user = self.env['res.users'].create({
            'name': 'GV User', 'login': 'gv_teach_days',
        })
        self.teacher.user_id = self.teacher_user

    def _session(self, cms_id, day, emp=None, state='planned'):
        return self.env['hocba.teaching.session'].create({
            'cms_session_id': cms_id,
            'employee_id': (emp or self.teacher).id,
            'session_date': day,
            'state': state,
            'class_name': 'Lop ' + cms_id,
        })

    def test_non_teacher_returns_empty(self):
        payload, status = _teaching_days_payload(
            self.env(user=self.user), '2026-01-01', '2026-12-31')
        self.assertEqual(status, 200)
        self.assertFalse(payload['isTeacher'])
        self.assertEqual(payload['days'], [])

    def test_user_without_employee_returns_empty(self):
        nouser = self.env['res.users'].create({
            'name': 'NoEmp', 'login': 'noemp_teach_days',
        })
        payload, status = _teaching_days_payload(
            self.env(user=nouser), '2026-01-01', '2026-12-31')
        self.assertEqual(status, 200)
        self.assertFalse(payload['isTeacher'])

    def test_missing_dates_400(self):
        payload, status = _teaching_days_payload(
            self.env(user=self.teacher_user), None, None)
        self.assertEqual(status, 400)
        self.assertEqual(payload['error'], 'invalid_date')

    def test_bad_date_format_400(self):
        payload, status = _teaching_days_payload(
            self.env(user=self.teacher_user), '2026/01/01', '2026-12-31')
        self.assertEqual(status, 400)
        self.assertEqual(payload['error'], 'invalid_date')

    def test_reversed_range_400(self):
        payload, status = _teaching_days_payload(
            self.env(user=self.teacher_user), '2026-12-31', '2026-01-01')
        self.assertEqual(status, 400)
        self.assertEqual(payload['error'], 'invalid_range')

    def test_range_too_wide_400(self):
        payload, status = _teaching_days_payload(
            self.env(user=self.teacher_user), '2024-01-01', '2026-01-01')
        self.assertEqual(status, 400)
        self.assertEqual(payload['error'], 'invalid_range')

    def test_teacher_days_counted(self):
        # 2 buổi cùng ngày → count 2; 1 buổi ngày khác; 1 buổi đã hủy (loại);
        # 1 buổi ngoài khoảng (loại); 1 buổi của GV khác (loại).
        self._session('s1', '2026-07-01')
        self._session('s2', '2026-07-01')
        self._session('s3', '2026-07-04')
        self._session('s4', '2026-07-10', state='cancelled')
        self._session('s5', '2027-01-05')
        self._session('s6', '2026-07-02', emp=self.emp)

        payload, status = _teaching_days_payload(
            self.env(user=self.teacher_user), '2026-01-01', '2026-12-31')
        self.assertEqual(status, 200)
        self.assertTrue(payload['isTeacher'])
        days = {d['date']: d['count'] for d in payload['days']}
        self.assertEqual(days, {'2026-07-01': 2, '2026-07-04': 1})

    def test_substituted_session_counts_for_current_teacher(self):
        # Buổi đã đổi GV dạy thay vẫn tính cho GV đang phụ trách (employee_id).
        self._session('s7', '2026-08-15', state='substituted')
        payload, status = _teaching_days_payload(
            self.env(user=self.teacher_user), '2026-08-01', '2026-08-31')
        self.assertEqual(status, 200)
        self.assertEqual(payload['days'], [{'date': '2026-08-15', 'count': 1}])
