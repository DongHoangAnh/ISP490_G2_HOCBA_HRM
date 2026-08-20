"""Badge "phiếu yêu cầu chờ duyệt" cạnh menu Tuyển dụng.

Nguyên tắc chung của badge trong dự án (bê từ /api/timeoff/pending-count):
  1. Đếm đúng thứ NGƯỜI ĐANG ĐĂNG NHẬP bấm được — không phải tồn đọng toàn hệ
     thống. Số trên menu phải khớp số phiếu có nút Duyệt trên màn danh sách.
  2. Không quyền → 200 {count: 0}, KHÔNG 403: badge chỉ là trang trí, bắt SPA
     bắt lỗi cho một con số cạnh menu là thừa.

Theo quy trình 7.1: TBP order phiếu → HR duyệt. Nên trưởng phòng đếm 0 dù họ
nhìn thấy phiếu của phòng mình — họ không phải người duyệt.
"""
import json

from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
URL = '/hocba-hrm/api/recruitment/requests/pending-count'


@tagged('post_install', '-at_install')
class TestRequestPendingCount(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        Dept = cls.env['hr.department']

        cls.dept = Dept.create({'name': 'Phòng Badge (test pending count)'})

        cls.user_hr = Users.create({
            'name': 'HR (test pending count)',
            'login': 'test_cnt_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref(
                'hr_recruitment.group_hr_recruitment_user').id)],
        })
        cls.user_mgr = Users.create({
            'name': 'TBP (test pending count)',
            'login': 'test_cnt_mgr', 'password': PWD,
        })
        cls.emp_mgr = cls.env['hr.employee'].create({
            'name': 'TBP (test pending count)',
            'user_id': cls.user_mgr.id, 'department_id': cls.dept.id,
        })
        cls.dept.manager_id = cls.emp_mgr
        cls.user_nv = Users.create({
            'name': 'NV thường (test pending count)',
            'login': 'test_cnt_nv', 'password': PWD,
        })

    def _req(self, state='submitted'):
        r = self.env['hb.recruitment.request'].create({
            'department_id': self.dept.id,
            'job_title': 'Vị trí test badge',
            'qty_expected': 1,
            'requester_id': self.user_mgr.id,
        })
        if state != 'draft':
            r.state = state
        self.env.flush_all()
        return r

    def _count(self, login):
        self.authenticate(login, PWD)
        res = self.url_open(URL)
        self.assertEqual(res.status_code, 200)
        return json.loads(res.content)['count']

    def test_hr_counts_submitted_requests(self):
        before = self._count('test_cnt_hr')
        self._req()
        self._req()
        self.assertEqual(self._count('test_cnt_hr'), before + 2)

    def test_only_submitted_state_counted(self):
        before = self._count('test_cnt_hr')
        self._req(state='draft')
        self._req(state='recruiting')
        self._req(state='refused')
        self._req(state='closed')
        self.assertEqual(self._count('test_cnt_hr'), before)

    def test_approving_lowers_the_count(self):
        r = self._req()
        before = self._count('test_cnt_hr')
        r.with_user(self.user_hr).action_approve()
        self.env.flush_all()
        self.assertEqual(self._count('test_cnt_hr'), before - 1)

    def test_department_manager_counts_zero(self):
        """TBP là người ORDER phiếu, không phải người duyệt → không có việc."""
        self._req()
        self.assertEqual(self._count('test_cnt_mgr'), 0)

    def test_plain_employee_gets_zero_not_403(self):
        self._req()
        self.authenticate('test_cnt_nv', PWD)
        res = self.url_open(URL)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(json.loads(res.content)['count'], 0)
