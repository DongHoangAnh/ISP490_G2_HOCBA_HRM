"""Chỉ tiêu tuyển của vị trí phải cộng VÀ trừ theo vòng đời phiếu yêu cầu.

Duyệt phiếu ⇒ cộng `qty_expected` vào `hr.job.no_of_recruitment` (core Odoo coi
trường này là "còn thiếu bao nhiêu người"). Mỗi ứng viên vào bước hired thì core
tự trừ 1. Nhưng ĐÓNG phiếu khi chưa tuyển đủ thì trước đây không ai trả lại phần
còn thiếu — chỉ tiêu ma nằm lại vĩnh viễn, kéo theo hai hậu quả:
  - Số "còn cần tuyển" của vị trí sai mãi.
  - `_hb_auto_close_if_filled` chặn ở `no_of_recruitment > 0` nên tính năng tự
    ngừng đăng khi tuyển đủ KHÔNG BAO GIỜ kích hoạt lại cho vị trí đó.

Quyết định 2026-08-26: đóng phiếu ⇒ trả lại đúng phần chưa tuyển của phiếu đó.
Kèm theo: "Mở lại nháp" chỉ HR và chỉ từ trạng thái Từ chối — phiếu đang tuyển
muốn sửa thì phải Đóng trước, không được lách về Nháp trong khi chỉ tiêu đã cộng.
"""
import json

from odoo.exceptions import UserError
from odoo.tests import HttpCase, TransactionCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestRequestHeadcount(TransactionCase):

    def setUp(self):
        super().setUp()
        self.dept = self.env['hr.department'].create(
            {'name': 'Phòng (test headcount)'})
        self.job = self.env['hr.job'].create({
            'name': 'Vị trí (test headcount)', 'department_id': self.dept.id,
            'no_of_recruitment': 0,
        })
        self.st_hired = self.env.ref('hocba_recruitments.hb_stage_hired')

    def _request(self, qty=5):
        return self.env['hb.recruitment.request'].create({
            'department_id': self.dept.id, 'job_id': self.job.id,
            'job_title': self.job.name, 'qty_expected': qty,
        })

    def _hire(self, req, name):
        """Ứng viên của phiếu ĐI TỚI bước Bàn giao — core trừ chỉ tiêu ở write().

        Phải tạo ở bước trước rồi mới chuyển: core Odoo trừ `no_of_recruitment`
        trong `hr_applicant.write`, tạo thẳng ở bước hired thì không trừ.
        """
        a = self.env['hr.applicant'].create({
            'partner_name': name, 'job_id': self.job.id,
            'hb_request_id': req.id,
            'stage_id': self.env.ref('hocba_recruitments.hb_stage_onboarding').id,
        })
        a.write({'stage_id': self.st_hired.id})
        return a

    # ── Cộng khi duyệt (giữ nguyên hành vi cũ) ───────────────────────────────

    def test_01_duyet_cong_chi_tieu(self):
        req = self._request(5)
        req.action_submit()
        req.action_approve()
        self.assertEqual(self.job.no_of_recruitment, 5)

    # ── Trả lại khi đóng ─────────────────────────────────────────────────────

    def test_02_dong_phieu_chua_tuyen_ai_tra_lai_het(self):
        req = self._request(5)
        req.action_submit()
        req.action_approve()
        req.action_close()
        self.assertEqual(self.job.no_of_recruitment, 0)

    def test_03_dong_phieu_tuyen_mot_phan_chi_tra_phan_con_thieu(self):
        req = self._request(5)
        req.action_submit()
        req.action_approve()
        self._hire(req, 'UV 1')
        self._hire(req, 'UV 2')
        self.assertEqual(self.job.no_of_recruitment, 3, 'core đã trừ 2 người')
        req.action_close()
        self.assertEqual(self.job.no_of_recruitment, 0,
                         'Trả lại đúng 3 chỉ tiêu chưa tuyển, không trừ lố')

    def test_04_khong_lam_chi_tieu_am(self):
        """Tuyển vượt chỉ tiêu — chỉ tiêu không bao giờ âm.

        Tuyển đủ thì hệ thống TỰ đóng phiếu (_hb_auto_close_if_filled) nên
        không còn nút Đóng để bấm; đường tự đóng cũng phải trả chỉ tiêu đúng.
        """
        req = self._request(2)
        req.action_submit()
        req.action_approve()
        for i in range(3):
            self._hire(req, 'UV %s' % i)
        self.assertEqual(req.state, 'closed', 'Tuyển đủ ⇒ phiếu tự đóng')
        self.assertGreaterEqual(self.job.no_of_recruitment, 0)

    def test_05_chi_tieu_cua_phieu_khac_khong_bi_dung_toi(self):
        req_a = self._request(3)
        req_a.action_submit()
        req_a.action_approve()
        req_b = self._request(4)
        req_b.action_submit()
        req_b.action_approve()
        self.assertEqual(self.job.no_of_recruitment, 7)
        req_a.action_close()
        self.assertEqual(self.job.no_of_recruitment, 4,
                         'Chỉ trả phần của phiếu A, phiếu B giữ nguyên')

    def test_06_dong_roi_khong_tra_lai_lan_hai(self):
        req = self._request(3)
        req.action_submit()
        req.action_approve()
        req.action_close()
        with self.assertRaises(UserError):
            req.action_close()
        self.assertEqual(self.job.no_of_recruitment, 0)

    def test_07_phieu_khong_gan_vi_tri_dong_binh_thuong(self):
        req = self.env['hb.recruitment.request'].create({
            'department_id': self.dept.id, 'job_title': 'Vị trí tự do',
            'qty_expected': 2,
        })
        req.action_submit()
        req.action_approve()
        req.action_close()
        self.assertEqual(req.state, 'closed')

    # ── Mở lại nháp ──────────────────────────────────────────────────────────

    def test_10_reset_tu_tu_choi_duoc(self):
        req = self._request(2)
        req.action_submit()
        req.action_refuse()
        req.action_reset_draft()
        self.assertEqual(req.state, 'draft')

    def test_11_reset_phieu_dang_tuyen_bi_chan(self):
        req = self._request(2)
        req.action_submit()
        req.action_approve()
        with self.assertRaises(UserError):
            req.action_reset_draft()
        self.assertEqual(req.state, 'recruiting')
        self.assertEqual(self.job.no_of_recruitment, 2,
                         'Không được lách về Nháp khi chỉ tiêu đang treo')

    def test_12_reset_phieu_da_dong_bi_chan(self):
        req = self._request(2)
        req.action_submit()
        req.action_approve()
        req.action_close()
        with self.assertRaises(UserError):
            req.action_reset_draft()


@tagged('post_install', '-at_install')
class TestResetPermission(HttpCase):
    """"Mở lại nháp" là việc của HR — TBP order phiếu thì không tự mở lại."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        cls.dept = cls.env['hr.department'].create({'name': 'Phòng (test reset acl)'})
        cls.user_hr = Users.create({
            'name': 'HR (test reset acl)',
            'login': 'test_resetacl_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref(
                'hr_recruitment.group_hr_recruitment_user').id)],
        })
        cls.user_mgr = Users.create({
            'name': 'TBP (test reset acl)',
            'login': 'test_resetacl_mgr', 'password': PWD,
        })
        cls.emp_mgr = cls.env['hr.employee'].create({
            'name': 'TBP (test reset acl)', 'user_id': cls.user_mgr.id,
            'department_id': cls.dept.id,
        })
        cls.dept.manager_id = cls.emp_mgr

    def _req_refused(self):
        req = self.env['hb.recruitment.request'].create({
            'department_id': self.dept.id, 'job_title': 'Vị trí (test reset acl)',
            'qty_expected': 1,
        })
        req.action_submit()
        req.action_refuse()
        return req

    def _action(self, req, action, login, expect):
        self.authenticate(login, PWD)
        res = self.url_open('%s/request/%s/action' % (BASE, req.id),
                            data=json.dumps({'action': action}),
                            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, expect, res.text[:400])
        return res

    def test_20_tbp_khong_reset_duoc(self):
        req = self._req_refused()
        self._action(req, 'reset', 'test_resetacl_mgr', 403)
        self.assertEqual(req.state, 'refused')

    def test_21_hr_reset_duoc(self):
        req = self._req_refused()
        self._action(req, 'reset', 'test_resetacl_hr', 200)
        self.assertEqual(req.state, 'draft')
