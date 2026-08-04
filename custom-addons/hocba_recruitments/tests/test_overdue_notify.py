"""Nhắc CV quá hạn xử lý (CRON-REC-001).

Spec: docs/superpowers/specs/2026-08-03-recruitment-overdue-notification-design.md
- Người nhận: HR nhóm tuyển dụng + Trưởng phòng của phòng ban vị trí.
- 1 thông báo / ứng viên quá hạn, chống trùng bằng dedup_key (dòng CHƯA ĐỌC).
- Loại trừ khớp badge kanban: Fail PV · bước hired · sla_days=0 · UV đã lưu trữ.
"""
from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestOverdueNotify(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Stage = cls.env['hr.recruitment.stage']
        cls.stage_sla = Stage.create(
            {'name': 'Bước nhắc hạn (test)', 'sequence': 310, 'sla_days': 2})
        cls.stage_free = Stage.create(
            {'name': 'Bước không hạn (test)', 'sequence': 320, 'sla_days': 0})
        cls.stage_hired = Stage.create(
            {'name': 'Đã tuyển nhắc hạn (test)', 'sequence': 330,
             'sla_days': 2, 'hired_stage': True})

        # HR tuyển dụng — nhóm user (manager kế thừa nên bắt cả hai qua group user)
        grp_rec = cls.env.ref('hr_recruitment.group_hr_recruitment_user')
        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR Tuyển dụng (test notify)',
            'login': 'test_rec_hr_notify',
            'group_ids': [(4, grp_rec.id)],
        })
        # Trưởng phòng — user + employee gắn làm manager_id của phòng
        cls.user_tp = cls.env['res.users'].create({
            'name': 'Trưởng phòng (test notify)',
            'login': 'test_rec_tp_notify',
        })
        cls.emp_tp = cls.env['hr.employee'].create(
            {'name': 'Trưởng phòng (test notify)', 'user_id': cls.user_tp.id})
        cls.dept = cls.env['hr.department'].create(
            {'name': 'Phòng có TP (test notify)', 'manager_id': cls.emp_tp.id})
        cls.dept_no_mgr = cls.env['hr.department'].create(
            {'name': 'Phòng không TP (test notify)'})

        cls.job = cls.env['hr.job'].create({
            'name': 'Vị trí Test Notify', 'no_of_recruitment': 5,
            'department_id': cls.dept.id,
        })
        cls.job_no_mgr = cls.env['hr.job'].create({
            'name': 'Vị trí Test Notify (không TP)', 'no_of_recruitment': 5,
            'department_id': cls.dept_no_mgr.id,
        })

    # ── helpers ──────────────────────────────────────────────────────────────

    def _applicant(self, stage=None, days_ago=5, job=None, **vals):
        """Ứng viên đứng ở bước `stage` đã `days_ago` ngày."""
        a = self.env['hr.applicant'].create(dict({
            'partner_name': 'UV notify %s' % (vals.get('partner_name') or days_ago),
            'job_id': (job or self.job).id,
            'stage_id': (stage or self.stage_sla).id,
        }, **vals))
        a.write({'date_last_stage_update':
                 fields.Datetime.now() - timedelta(days=days_ago)})
        return a

    def _notifs(self, applicant, user=None):
        dom = [('dedup_key', '=', 'rec_overdue_%s' % applicant.id)]
        if user:
            dom.append(('recipient_id', '=', user.id))
        return self.env['hb.notification'].sudo().search(dom)

    def _run_cron(self):
        self.env['hr.applicant']._cron_overdue_reminder()

    # ── BR-1 · người nhận ────────────────────────────────────────────────────

    def test_br1_hr_and_manager_each_get_one(self):
        a = self._applicant(days_ago=5)
        self._run_cron()
        self.assertEqual(len(self._notifs(a, self.user_hr)), 1,
                         'HR tuyển dụng phải nhận đúng 1 thông báo')
        self.assertEqual(len(self._notifs(a, self.user_tp)), 1,
                         'Trưởng phòng của vị trí phải nhận đúng 1 thông báo')

    def test_br1b_payload_fields(self):
        a = self._applicant(days_ago=5)
        self._run_cron()
        n = self._notifs(a, self.user_hr)
        self.assertEqual(n.category, 'recruitment')
        self.assertEqual(n.kind, 'recruitment_overdue')
        self.assertEqual(n.level, 'warning')
        self.assertEqual(n.target_view, 'recruitment')
        self.assertEqual(n.target_tab, 'cv')
        self.assertEqual(n.target_ref, a.id)
        # quá hạn 3 ngày = 5 ngày ở bước - hạn 2 ngày
        self.assertIn('3', n.body)
        self.assertIn(a.partner_name, n.body)

    # ── BR-2/BR-3 · chống trùng ──────────────────────────────────────────────

    def test_br2_dedup_second_run_no_duplicate(self):
        a = self._applicant(days_ago=5)
        self._run_cron()
        self._run_cron()
        self.assertEqual(len(self._notifs(a, self.user_hr)), 1,
                         'Chạy cron 2 lần vẫn chỉ 1 dòng chưa đọc')

    def test_br3_reminds_again_after_read(self):
        a = self._applicant(days_ago=5)
        self._run_cron()
        self._notifs(a, self.user_hr).write({'is_read': True})
        self._run_cron()
        self.assertEqual(len(self._notifs(a, self.user_hr)), 2,
                         'Đọc rồi mà chưa xử lý thì lần sau phải nhắc lại')

    # ── BR-4 · theo kết quả PV ───────────────────────────────────────────────

    def test_br4a_fail_interview_not_notified(self):
        a = self._applicant(days_ago=5, interview_result='fail')
        self._run_cron()
        self.assertFalse(self._notifs(a), 'Fail PV = đã dừng, không giục nữa')

    def test_br4b_null_interview_result_notified(self):
        """Chưa PV (NULL) là nhóm cần nhắc nhất — khoá hành vi ORM sinh
        `NOT IN (...) OR IS NULL` cho toán tử != (odoo/orm/fields.py)."""
        a = self._applicant(days_ago=5)
        self.assertFalse(a.interview_result)
        self._run_cron()
        self.assertTrue(self._notifs(a, self.user_hr))

    def test_br4c_pass_and_potential_notified(self):
        a_pass = self._applicant(days_ago=5, interview_result='pass',
                                 partner_name='pass')
        a_pot = self._applicant(days_ago=5, interview_result='potential',
                                partner_name='potential')
        self._run_cron()
        self.assertTrue(self._notifs(a_pass, self.user_hr),
                        'Pass PV vẫn có thể kẹt ở bước Offer → phải nhắc')
        self.assertTrue(self._notifs(a_pot, self.user_hr),
                        'Tiềm năng = chưa chốt → phải nhắc')

    # ── BR-5 · theo cấu hình bước ────────────────────────────────────────────

    def test_br5_no_sla_and_hired_stage_not_notified(self):
        a_free = self._applicant(self.stage_free, days_ago=30)
        a_hired = self._applicant(self.stage_hired, days_ago=30)
        self._run_cron()
        self.assertFalse(self._notifs(a_free), 'Bước để hạn = 0 thì không nhắc')
        self.assertFalse(self._notifs(a_hired), 'Bước "Đã tuyển" là đích đến')

    # ── BR-6 · phòng chưa gán Trưởng phòng ───────────────────────────────────

    def test_br6_department_without_manager_only_hr(self):
        a = self._applicant(days_ago=5, job=self.job_no_mgr)
        self._run_cron()          # không được nổ lỗi
        self.assertEqual(len(self._notifs(a, self.user_hr)), 1)
        self.assertFalse(self._notifs(a, self.user_tp))

    # ── BR-7 · ứng viên đã lưu trữ ───────────────────────────────────────────

    def test_br7_archived_applicant_not_notified(self):
        a = self._applicant(days_ago=5)
        a.action_archive()
        self._run_cron()
        self.assertFalse(self._notifs(a), 'UV đã lưu trữ / bị từ chối thì thôi')

    # ── BR-9 · chế độ người nhận (tab Thông báo) ─────────────────────────────

    def _set_mode(self, mode):
        self.env['ir.config_parameter'].sudo().set_param(
            'hocba_recruitments.overdue_notify_mode', mode)

    def test_br9a_mode_off_sends_nothing(self):
        a = self._applicant(days_ago=5)
        self._set_mode('off')
        self._run_cron()
        self.assertFalse(self._notifs(a), 'Chế độ off phải im lặng hoàn toàn')

    def test_br9b_mode_hr_only(self):
        a = self._applicant(days_ago=5)
        self._set_mode('hr_only')
        self._run_cron()
        self.assertTrue(self._notifs(a, self.user_hr))
        self.assertFalse(self._notifs(a, self.user_tp))

    def test_br9c_mode_manager_only(self):
        a = self._applicant(days_ago=5)
        self._set_mode('manager_only')
        self._run_cron()
        self.assertFalse(self._notifs(a, self.user_hr))
        self.assertTrue(self._notifs(a, self.user_tp))

    def test_br9d_unknown_mode_falls_back_to_both(self):
        a = self._applicant(days_ago=5)
        self._set_mode('vo_nghia')
        self._run_cron()
        self.assertTrue(self._notifs(a, self.user_hr))
        self.assertTrue(self._notifs(a, self.user_tp))

    # ── BR-8 · ranh giới đúng ngày hạn ───────────────────────────────────────

    def test_br8_exactly_at_limit_not_overdue(self):
        a = self._applicant(days_ago=2)      # hạn 2 ngày, mới đúng 2 ngày
        self._run_cron()
        self.assertFalse(self._notifs(a),
                         'Đúng ngày hạn chưa tính quá hạn (> chứ không >=)')
