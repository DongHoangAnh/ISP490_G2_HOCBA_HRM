"""Phạm vi phòng ban của các ô chọn (dropdown) trên SPA.

Backend đã chặn 403 khi LƯU dữ liệu ngoài phạm vi (job_create, request_create,
cv_create). Nhưng nếu payload meta vẫn liệt kê hết phòng ban / vị trí thì trưởng
phòng chọn xong mới ăn lỗi — trải nghiệm sai và dễ bị hiểu là hệ thống hỏng.

Ba builder phải cùng một luật: HR thấy tất cả, trưởng phòng chỉ thấy phòng mình
quản lý (gồm phòng con) và vị trí thuộc các phòng đó.
  _job_meta()  → /jobs      (đã đúng từ trước)
  _req_meta()  → /requests  (vá 2026-08-07)
  _meta()      → /cv        (vá 2026-08-07, cùng lỗi)
"""
from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestMetaScope(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        Dept = cls.env['hr.department']

        cls.dept_a = Dept.create({'name': 'Phòng A (test meta scope)'})
        cls.dept_b = Dept.create({'name': 'Phòng B (test meta scope)'})
        # Phòng con của A — trưởng phòng A quản cả phòng con (_managed_department_ids).
        cls.dept_a_sub = Dept.create({'name': 'Phòng A con (test meta scope)',
                                      'parent_id': cls.dept_a.id})

        cls.user_hr = Users.create({
            'name': 'HR (test meta scope)',
            'login': 'test_meta_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref('hr_recruitment.group_hr_recruitment_user').id)],
        })
        cls.user_mgr = Users.create({
            'name': 'TBP phòng A (test meta scope)',
            'login': 'test_meta_mgr', 'password': PWD,
        })
        cls.emp_mgr = cls.env['hr.employee'].create({
            'name': 'TBP phòng A (test meta scope)',
            'user_id': cls.user_mgr.id,
            'department_id': cls.dept_a.id,
        })
        cls.dept_a.manager_id = cls.emp_mgr

        Job = cls.env['hr.job']
        cls.job_a = Job.create({'name': 'Vị trí phòng A (test meta scope)',
                                'department_id': cls.dept_a.id})
        cls.job_a_sub = Job.create({'name': 'Vị trí phòng A con (test meta scope)',
                                    'department_id': cls.dept_a_sub.id})
        cls.job_b = Job.create({'name': 'Vị trí phòng B (test meta scope)',
                                'department_id': cls.dept_b.id})

    def _meta(self, path, login):
        self.authenticate(login, PWD)
        res = self.url_open('%s/%s' % (BASE, path))
        self.assertEqual(res.status_code, 200)
        return res.json()

    def _names(self, rows):
        return {r['name'] for r in rows}

    # ── HR: thấy tất cả ──────────────────────────────────────────────────────

    def test_01_hr_sees_all_departments_in_request_form(self):
        data = self._meta('requests', 'test_meta_hr')
        names = self._names(data['departments'])
        self.assertIn(self.dept_a.name, names)
        self.assertIn(self.dept_b.name, names)

    def test_02_hr_sees_all_jobs(self):
        self.assertIn(self.job_b.name,
                      self._names(self._meta('requests', 'test_meta_hr')['jobs']))
        self.assertIn(self.job_b.name,
                      self._names(self._meta('cv', 'test_meta_hr')['jobs']))

    # ── Trưởng phòng: chỉ phòng mình + phòng con ─────────────────────────────

    def test_10_manager_departments_limited_in_request_form(self):
        """Lỗi gốc: ô "PHÒNG BAN" ở modal Thêm phiếu yêu cầu liệt kê mọi phòng."""
        names = self._names(self._meta('requests', 'test_meta_mgr')['departments'])
        self.assertIn(self.dept_a.name, names)
        self.assertIn(self.dept_a_sub.name, names, 'Phòng con cũng do TBP A quản')
        self.assertNotIn(self.dept_b.name, names)

    def test_11_manager_jobs_limited_in_request_form(self):
        names = self._names(self._meta('requests', 'test_meta_mgr')['jobs'])
        self.assertIn(self.job_a.name, names)
        self.assertIn(self.job_a_sub.name, names)
        self.assertNotIn(self.job_b.name, names)

    def test_12_manager_jobs_limited_in_cv_form(self):
        """Cùng lỗi ở ô "Vị trí ứng tuyển" của tab Danh sách CV."""
        names = self._names(self._meta('cv', 'test_meta_mgr')['jobs'])
        self.assertIn(self.job_a.name, names)
        self.assertNotIn(self.job_b.name, names)

    def test_13_manager_departments_limited_in_job_form(self):
        """Tab Vị trí tuyển dụng vốn đã đúng — chốt lại để không ai làm hỏng."""
        names = self._names(self._meta('jobs', 'test_meta_mgr')['departments'])
        self.assertIn(self.dept_a.name, names)
        self.assertNotIn(self.dept_b.name, names)

    def test_14_stages_not_filtered(self):
        """Bước quy trình là cấu hình dùng chung — không được lọc theo phòng."""
        hr = self._meta('cv', 'test_meta_hr')['stages']
        mgr = self._meta('cv', 'test_meta_mgr')['stages']
        self.assertTrue(mgr)
        self.assertEqual({s['id'] for s in hr}, {s['id'] for s in mgr})
