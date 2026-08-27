"""Xếp lịch phỏng vấn phải tôn trọng phạm vi phòng ban.

Đặt/gỡ ứng viên khỏi slot là thao tác GHI lên hồ sơ ứng viên (ngày hẹn, giờ hẹn,
người PV) và còn đẩy bước kanban. Mọi endpoint khác đụng `hr.applicant` đều kiểm
`_dep_in_scope` — riêng nhóm slot thì trước đây chỉ kiểm "có phải người quản lý
slot không", nên trưởng phòng A xếp lịch được cho ứng viên phòng B.

Luật chốt ở đây:
  - HR toàn quyền: mọi phòng ban, như cũ.
  - Trưởng phòng: chỉ ứng viên thuộc phòng mình (gồm phòng con).
  - Xoá slot: chỉ slot của phòng mình HOẶC slot do chính mình đứng tên — người
    khai lịch rảnh (kể cả nhóm Interviewer không quản phòng nào) vẫn tự dọn được
    lịch của mình.
"""
import json
from datetime import timedelta

from odoo import fields
from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'
BASE = '/hocba-hrm/api/recruitment'


@tagged('post_install', '-at_install')
class TestSlotScope(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        Dept = cls.env['hr.department']
        recruit_group = cls.env.ref('hr_recruitment.group_hr_recruitment_user')

        cls.dept_a = Dept.create({'name': 'Phòng A (test slot scope)'})
        cls.dept_b = Dept.create({'name': 'Phòng B (test slot scope)'})

        cls.user_hr = Users.create({
            'name': 'HR (test slot scope)',
            'login': 'test_slotscope_hr', 'password': PWD,
            'group_ids': [(4, recruit_group.id)],
        })
        # TBP phòng A: KHÔNG ở nhóm tuyển dụng, quyền đến từ manager_id.
        cls.user_mgr_a = Users.create({
            'name': 'TBP phòng A (test slot scope)',
            'login': 'test_slotscope_mgr_a', 'password': PWD,
        })
        cls.emp_mgr_a = cls.env['hr.employee'].create({
            'name': 'TBP phòng A (test slot scope)',
            'user_id': cls.user_mgr_a.id, 'department_id': cls.dept_a.id,
        })
        cls.dept_a.manager_id = cls.emp_mgr_a

        # Người phỏng vấn của phòng B — slot của người này thuộc phòng B.
        cls.user_itv_b = Users.create({
            'name': 'Người PV phòng B (test slot scope)',
            'login': 'test_slotscope_itv_b', 'password': PWD,
        })
        cls.env['hr.employee'].create({
            'name': 'Người PV phòng B (test slot scope)',
            'user_id': cls.user_itv_b.id, 'department_id': cls.dept_b.id,
        })

        Job = cls.env['hr.job']
        cls.job_a = Job.create({'name': 'Vị trí phòng A (test slot scope)',
                                'department_id': cls.dept_a.id})
        cls.job_b = Job.create({'name': 'Vị trí phòng B (test slot scope)',
                                'department_id': cls.dept_b.id})

    def setUp(self):
        super().setUp()
        Applicant = self.env['hr.applicant']
        self.app_a = Applicant.create({'partner_name': 'UV phòng A',
                                       'job_id': self.job_a.id})
        self.app_b = Applicant.create({'partner_name': 'UV phòng B',
                                       'job_id': self.job_b.id})

    def _slot(self, user, applicants=None):
        start = fields.Datetime.now() + timedelta(days=1)
        return self.env['hb.interview.slot'].create({
            'start_datetime': start,
            'stop_datetime': start + timedelta(hours=1),
            'user_id': user.id,
            'applicant_ids': [(6, 0, applicants.ids)] if applicants else False,
        })

    def _post(self, path, payload, login, expect):
        self.authenticate(login, PWD)
        res = self.url_open('%s/%s' % (BASE, path), data=json.dumps(payload),
                            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, expect, res.text[:400])
        return res.json()

    # ── Đặt ứng viên vào slot ────────────────────────────────────────────────

    def test_01_tbp_dat_ung_vien_phong_minh(self):
        slot = self._slot(self.user_mgr_a)
        self._post('interview-slot/%s/book' % slot.id,
                   {'applicantId': self.app_a.id}, 'test_slotscope_mgr_a', 200)
        self.assertIn(self.app_a, slot.applicant_ids)

    def test_02_tbp_khong_dat_duoc_ung_vien_phong_khac(self):
        slot = self._slot(self.user_mgr_a)
        body = self._post('interview-slot/%s/book' % slot.id,
                          {'applicantId': self.app_b.id},
                          'test_slotscope_mgr_a', 403)
        self.assertEqual(body['error'], 'forbidden')
        self.assertNotIn(self.app_b, slot.applicant_ids)
        self.assertFalse(self.app_b.interview_date,
                         'Không được ghi lịch PV lên hồ sơ ngoài phạm vi')

    def test_03_hr_dat_duoc_moi_phong(self):
        slot = self._slot(self.user_hr)
        self._post('interview-slot/%s/book' % slot.id,
                   {'applicantId': self.app_b.id}, 'test_slotscope_hr', 200)
        self.assertIn(self.app_b, slot.applicant_ids)

    # ── Gỡ ứng viên khỏi slot ────────────────────────────────────────────────

    def test_04_tbp_khong_go_duoc_ung_vien_phong_khac(self):
        slot = self._slot(self.user_itv_b, applicants=self.app_b)
        self._post('interview-slot/%s/unbook' % slot.id,
                   {'applicantId': self.app_b.id}, 'test_slotscope_mgr_a', 403)
        self.assertIn(self.app_b, slot.applicant_ids)

    def test_05_tbp_khong_go_sach_slot_co_ung_vien_ngoai_pham_vi(self):
        """Không truyền applicantId = gỡ hết; chỉ cho khi CẢ slot trong phạm vi."""
        slot = self._slot(self.user_mgr_a, applicants=self.app_a | self.app_b)
        self._post('interview-slot/%s/unbook' % slot.id, {},
                   'test_slotscope_mgr_a', 403)
        self.assertIn(self.app_b, slot.applicant_ids)

    def test_06_tbp_go_sach_slot_toan_ung_vien_phong_minh(self):
        slot = self._slot(self.user_mgr_a, applicants=self.app_a)
        self._post('interview-slot/%s/unbook' % slot.id, {},
                   'test_slotscope_mgr_a', 200)
        self.assertFalse(slot.applicant_ids)

    # ── Xoá slot ─────────────────────────────────────────────────────────────

    def test_07_tbp_khong_xoa_duoc_slot_phong_khac(self):
        slot = self._slot(self.user_itv_b)
        self._post('interview-slot/%s/delete' % slot.id, {},
                   'test_slotscope_mgr_a', 403)
        self.assertTrue(slot.exists())

    def test_08_tbp_xoa_duoc_slot_phong_minh(self):
        slot = self._slot(self.user_mgr_a)
        self._post('interview-slot/%s/delete' % slot.id, {},
                   'test_slotscope_mgr_a', 200)
        self.assertFalse(slot.exists())

    def test_09_hr_xoa_duoc_slot_moi_phong(self):
        slot = self._slot(self.user_itv_b)
        self._post('interview-slot/%s/delete' % slot.id, {},
                   'test_slotscope_hr', 200)
        self.assertFalse(slot.exists())

    # ── Xem lịch (GET) ───────────────────────────────────────────────────────

    def _get_slots(self, login, expect=200):
        self.authenticate(login, PWD)
        day = (fields.Datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        res = self.url_open('%s/interview-slots?from=%s&to=%s' % (BASE, day, day))
        self.assertEqual(res.status_code, expect, res.text[:400])
        return res.json()

    def test_10_nhan_vien_thuong_khong_thay_lich_ai(self):
        """User không thuộc nhóm nào: payload kèm HỌ TÊN ứng viên nên phải rỗng.

        Trước đây endpoint này không lọc gì — mọi user đăng nhập đọc được toàn bộ
        lịch PV kèm tên ứng viên, tên vị trí, và danh sách mọi NV có tài khoản.
        Tab Mail mẫu đã bị siết vì đúng lý do này.
        """
        Users = self.env['res.users']
        Users.create({'name': 'NV thường (test slot scope)',
                      'login': 'test_slotscope_nv', 'password': PWD})
        self._slot(self.user_itv_b, applicants=self.app_b)
        body = self._get_slots('test_slotscope_nv')
        self.assertEqual(body['rows'], [])
        self.assertFalse(body['canManage'])
        self.assertEqual(body['interviewers'], [],
                         'Không được liệt kê danh bạ nhân viên cho user thường')

    def test_11_tbp_chi_thay_lich_phong_minh(self):
        slot_a = self._slot(self.user_mgr_a, applicants=self.app_a)
        self._slot(self.user_itv_b, applicants=self.app_b)
        rows = self._get_slots('test_slotscope_mgr_a')['rows']
        self.assertEqual([r['id'] for r in rows], [slot_a.id])

    def test_12_hr_thay_het(self):
        slot_a = self._slot(self.user_mgr_a)
        slot_b = self._slot(self.user_itv_b)
        rows = self._get_slots('test_slotscope_hr')['rows']
        self.assertEqual({r['id'] for r in rows}, {slot_a.id, slot_b.id})
