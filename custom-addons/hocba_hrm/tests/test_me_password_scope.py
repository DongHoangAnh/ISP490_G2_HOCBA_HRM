# ---------------------------------------------------------------------------
# Hai nhóm test cho phần vừa bổ sung 2026-08-14/15:
#   1. /hocba-hrm/api/me/password — người dùng tự đổi mật khẩu.
#   2. Sửa hồ sơ NV có kèm "Loại nhân sự" (empTypeId) — field này quyết định
#      phạm vi của Giáo vụ, nên đổi nó là đổi luôn quyền nhìn thấy hồ sơ.
#
# Dùng HttpCase vì cả hai đều nằm ở tầng route (get_json_data/make_json_response),
# giống hocba_recruitments/tests/test_mail_acl.py.
# ---------------------------------------------------------------------------
import json

from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
NEW_PWD = 'HocBaMoi@2026'


def _post(case, url, payload):
    """POST JSON tới route type='http' và trả (status, body-dict)."""
    resp = case.url_open(
        url, data=json.dumps(payload),
        headers={'Content-Type': 'application/json'})
    try:
        return resp.status_code, resp.json()
    except ValueError:
        return resp.status_code, {}


@tagged('post_install', '-at_install')
class TestMeChangePassword(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = cls.env['res.users'].create({
            'name': 'NV doi mat khau', 'login': 'test_pw_self', 'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]})

    def setUp(self):
        super().setUp()
        self.authenticate('test_pw_self', PWD)

    def test_missing_current_rejected(self):
        st, body = _post(self, '/hocba-hrm/api/me/password', {
            'password': NEW_PWD, 'password_confirm': NEW_PWD})
        self.assertEqual(st, 400)
        self.assertIn('hiện tại', body.get('message', ''))

    def test_wrong_current_rejected(self):
        st, body = _post(self, '/hocba-hrm/api/me/password', {
            'currentPassword': 'SaiHoanToan@2026',
            'password': NEW_PWD, 'password_confirm': NEW_PWD})
        self.assertEqual(st, 400)
        self.assertIn('không đúng', body.get('message', ''))

    def test_short_password_rejected(self):
        st, body = _post(self, '/hocba-hrm/api/me/password', {
            'currentPassword': PWD, 'password': 'abc', 'password_confirm': 'abc'})
        self.assertEqual(st, 400)
        self.assertIn('8', body.get('message', ''))

    def test_confirm_mismatch_rejected(self):
        st, body = _post(self, '/hocba-hrm/api/me/password', {
            'currentPassword': PWD, 'password': NEW_PWD,
            'password_confirm': NEW_PWD + 'x'})
        self.assertEqual(st, 400)
        self.assertIn('không khớp', body.get('message', ''))

    def test_same_as_current_rejected(self):
        st, body = _post(self, '/hocba-hrm/api/me/password', {
            'currentPassword': PWD, 'password': PWD, 'password_confirm': PWD})
        self.assertEqual(st, 400)
        self.assertIn('khác mật khẩu hiện tại', body.get('message', ''))

    def test_change_ok_and_new_password_works(self):
        st, body = _post(self, '/hocba-hrm/api/me/password', {
            'currentPassword': PWD, 'password': NEW_PWD,
            'password_confirm': NEW_PWD})
        self.assertEqual(st, 200)
        self.assertTrue(body.get('ok'))
        # FE dựa vào cờ này để đá người dùng về màn đăng nhập.
        self.assertTrue(body.get('relogin'))
        # Mật khẩu mới phải dùng được ngay.
        self.authenticate('test_pw_self', NEW_PWD)
        self.assertEqual(self.session.uid, self.user.id)


@tagged('post_install', '-at_install')
class TestEmpTypeScopeOnUpdate(HttpCase):
    """Giáo vụ chỉ quản giáo viên (_emp_scope_domain). Form NV nay có ô 'Loại
    nhân sự', nên phải chặn đường tự đẩy hồ sơ ra khỏi phạm vi của mình."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Emp = cls.env['hr.employee']
        Type = cls.env['hocba.employee.type']
        cls.t_teacher = Type.search([('code', '=', 'teacher')], limit=1)
        cls.t_office = Type.search([('code', '=', 'office_staff')], limit=1)

        cls.user_gv = cls.env['res.users'].create({
            'name': 'Giao vu (scope test)', 'login': 'test_gv_scope',
            'password': PWD,
            'group_ids': [(6, 0, [
                cls.env.ref('base.group_user').id,
                cls.env.ref('hocba_employees.group_hocba_giaovu').id])]})
        cls.emp_gv = Emp.create({
            'name': 'Giao vu (scope test)', 'user_id': cls.user_gv.id,
            'x_employee_type_id': cls.t_teacher.id})
        cls.teacher = Emp.create({
            'name': 'Giao vien (scope test)',
            'x_employee_type_id': cls.t_teacher.id})

    def _update(self, emp_id, payload):
        return _post(self, '/hocba-hrm/api/employee/%d' % emp_id, payload)

    def test_giaovu_can_edit_teacher_in_scope(self):
        self.authenticate('test_gv_scope', PWD)
        st, _ = self._update(self.teacher.id, {'phone': '0900000001'})
        self.assertEqual(st, 200)
        self.assertEqual(self.teacher.work_phone, '0900000001')

    def test_giaovu_cannot_move_teacher_out_of_scope(self):
        self.authenticate('test_gv_scope', PWD)
        st, _ = self._update(self.teacher.id,
                             {'empTypeId': self.t_office.id})
        self.assertEqual(st, 403)
        # Quan trọng hơn cả mã lỗi: dữ liệu KHÔNG được đổi.
        self.assertEqual(self.teacher.x_employee_type_id, self.t_teacher)

    def test_giaovu_meta_offers_only_teacher_type(self):
        """Form không được bày lựa chọn mà chính nó sẽ từ chối lúc lưu."""
        self.authenticate('test_gv_scope', PWD)
        meta = self.url_open('/hocba-hrm/api/form/meta').json()
        self.assertEqual([t['code'] for t in meta['empTypes']], ['teacher'])

    def test_hr_meta_offers_every_type(self):
        self.env['res.users'].create({
            'name': 'HR (meta test)', 'login': 'test_hr_meta', 'password': PWD,
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr.group_hr_user').id])]})
        self.authenticate('test_hr_meta', PWD)
        meta = self.url_open('/hocba-hrm/api/form/meta').json()
        codes = [t['code'] for t in meta['empTypes']]
        self.assertIn('teacher', codes)
        self.assertIn('office_staff', codes)

    def test_hr_manager_can_change_emp_type(self):
        self.env['res.users'].create({
            'name': 'HR Mgr (scope test)', 'login': 'test_hrm_scope',
            'password': PWD,
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr.group_hr_manager').id])]})
        self.authenticate('test_hrm_scope', PWD)
        st, _ = self._update(self.teacher.id, {'empTypeId': self.t_office.id})
        self.assertEqual(st, 200)
        self.assertEqual(self.teacher.x_employee_type_id, self.t_office)
