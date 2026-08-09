"""Cổng quyền cụm endpoint mail tuyển dụng (QA 2026-08-07, sub-case A1 #4).

Trước đây 4 route dưới đây chỉ có auth='user' — bất kỳ tài khoản đăng nhập nào,
kể cả nhân viên thường không thấy màn Tuyển dụng, cũng đọc được họ tên · email ·
vị trí · bước của TOÀN BỘ ứng viên (payload `recipients`, bản render xem trước,
lịch sử gửi mail):

    GET  /api/recruitment/mail-templates
    GET  /api/recruitment/mail-template/<id>
    POST /api/recruitment/mail-template/<id>/preview
    GET  /api/recruitment/mail-logs

Chuẩn mới = giống tab Danh sách CV: phải là nhóm tuyển dụng (_is_recruiter =
HR hoặc trưởng phòng), và trưởng phòng chỉ thấy ứng viên phòng mình.

Dùng HttpCase vì controller bám chặt vào `request` (make_json_response, get_json_data)
nên không gọi thẳng helper cấp module như hocba_service được.
"""
import json

from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestMailAcl(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        Dept = cls.env['hr.department']
        Emp = cls.env['hr.employee']

        cls.dept_a = Dept.create({'name': 'Phòng A (test mail acl)'})
        cls.dept_b = Dept.create({'name': 'Phòng B (test mail acl)'})

        # Nhân viên thường: đăng nhập được, không nhóm tuyển dụng, không quản phòng.
        cls.user_plain = Users.create({
            'name': 'NV thường (test mail acl)',
            'login': 'test_macl_plain', 'password': PWD,
        })
        # HR toàn quyền tuyển dụng.
        cls.user_hr = Users.create({
            'name': 'HR tuyển dụng (test mail acl)',
            'login': 'test_macl_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref('hr_recruitment.group_hr_recruitment_user').id)],
        })
        # Trưởng phòng A: quyền qua hr.department.manager_id, không thuộc nhóm HR.
        cls.user_mgr = Users.create({
            'name': 'TBP phòng A (test mail acl)',
            'login': 'test_macl_mgr', 'password': PWD,
        })
        cls.emp_mgr = Emp.create({
            'name': 'TBP phòng A (test mail acl)',
            'user_id': cls.user_mgr.id,
            'department_id': cls.dept_a.id,
        })
        cls.dept_a.manager_id = cls.emp_mgr

        cls.job_a = cls.env['hr.job'].create(
            {'name': 'Vị trí phòng A (test mail acl)', 'department_id': cls.dept_a.id})
        cls.job_b = cls.env['hr.job'].create(
            {'name': 'Vị trí phòng B (test mail acl)', 'department_id': cls.dept_b.id})

        Applicant = cls.env['hr.applicant']
        cls.app_a = Applicant.create({
            'partner_name': 'Ung vien phong A', 'email_from': 'uv_a@example.com',
            'job_id': cls.job_a.id, 'department_id': cls.dept_a.id,
        })
        cls.app_b = Applicant.create({
            'partner_name': 'Ung vien phong B', 'email_from': 'uv_b@example.com',
            'job_id': cls.job_b.id, 'department_id': cls.dept_b.id,
        })

        cls.tmpl = cls.env.ref('hocba_recruitments.email_template_interview_invite')

    # ── helper ───────────────────────────────────────────────────────────────

    def _get(self, url):
        return self.url_open(url)

    def _post_json(self, url, payload):
        return self.url_open(url, data=json.dumps(payload),
                             headers={'Content-Type': 'application/json'})

    def _preview(self, applicant):
        return self._post_json('%s/mail-template/%s/preview' % (BASE, self.tmpl.id),
                               {'applicantId': applicant.id})

    # ── nhân viên thường: chặn sạch cả 4 cửa ─────────────────────────────────

    def test_01_plain_user_cannot_list_templates(self):
        self.authenticate('test_macl_plain', PWD)
        res = self._get('%s/mail-templates' % BASE)
        self.assertEqual(res.status_code, 403)
        self.assertNotIn('uv_a@example.com', res.text)

    def test_02_plain_user_cannot_read_template_detail(self):
        self.authenticate('test_macl_plain', PWD)
        res = self._get('%s/mail-template/%s' % (BASE, self.tmpl.id))
        self.assertEqual(res.status_code, 403)

    def test_03_plain_user_cannot_preview(self):
        self.authenticate('test_macl_plain', PWD)
        res = self._preview(self.app_a)
        self.assertEqual(res.status_code, 403)
        self.assertNotIn('Ung vien phong A', res.text)

    def test_04_plain_user_cannot_read_mail_logs(self):
        self.authenticate('test_macl_plain', PWD)
        res = self._get('%s/mail-logs' % BASE)
        self.assertEqual(res.status_code, 403)

    # ── HR: thấy hết ─────────────────────────────────────────────────────────

    def test_05_hr_sees_all_recipients(self):
        self.authenticate('test_macl_hr', PWD)
        res = self._get('%s/mail-templates' % BASE)
        self.assertEqual(res.status_code, 200)
        emails = {r['email'] for r in res.json()['recipients']}
        self.assertIn('uv_a@example.com', emails)
        self.assertIn('uv_b@example.com', emails)

    # ── Trưởng phòng: chỉ phòng mình ─────────────────────────────────────────

    def test_05b_hr_flags(self):
        """HR: quản mẫu được VÀ gửi được."""
        self.authenticate('test_macl_hr', PWD)
        data = self._get('%s/mail-templates' % BASE).json()
        self.assertTrue(data['canEdit'])
        self.assertTrue(data['canSend'])

    def test_06b_manager_can_send_but_not_edit(self):
        """Trưởng phòng: KHÔNG quản mẫu (cấu hình chung toàn hệ thống) nhưng
        VẪN gửi được mail cho ứng viên phòng mình — khớp /mail/log-sent vốn
        gate bằng _is_recruiter(). Gộp 2 quyền vào 1 cờ là sinh ra bug C1 #5."""
        self.authenticate('test_macl_mgr', PWD)
        data = self._get('%s/mail-templates' % BASE).json()
        self.assertFalse(data['canEdit'])
        self.assertTrue(data['canSend'])

    def test_06c_manager_still_blocked_from_editing_templates(self):
        """Cờ canSend=True không được nới quyền ghi ở backend."""
        self.authenticate('test_macl_mgr', PWD)
        res = self._post_json('%s/mail-templates' % BASE, {'name': 'Mau moi (test)'})
        self.assertEqual(res.status_code, 403)
        res = self._post_json(
            '%s/mail-template/%s/delete' % (BASE, self.tmpl.id), {})
        self.assertEqual(res.status_code, 403)

    def test_06_manager_recipients_limited_to_own_department(self):
        self.authenticate('test_macl_mgr', PWD)
        res = self._get('%s/mail-templates' % BASE)
        self.assertEqual(res.status_code, 200)
        emails = {r['email'] for r in res.json()['recipients']}
        self.assertIn('uv_a@example.com', emails)
        self.assertNotIn('uv_b@example.com', emails,
                         'Trưởng phòng A không được thấy ứng viên phòng B')

    def test_07_manager_can_preview_own_department(self):
        self.authenticate('test_macl_mgr', PWD)
        self.assertEqual(self._preview(self.app_a).status_code, 200)

    def test_08_manager_cannot_preview_other_department(self):
        self.authenticate('test_macl_mgr', PWD)
        res = self._preview(self.app_b)
        self.assertEqual(res.status_code, 403)
        self.assertNotIn('Ung vien phong B', res.text)
