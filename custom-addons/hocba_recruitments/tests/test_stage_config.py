"""Cấu hình quy trình tuyển dụng — SLA + reorder + guard xoá stage.

Spec: docs/superpowers/specs/2026-07-23-recruitment-config-design.md
- _hb_sla_state(): quá hạn khi ở bước lâu hơn sla_days; bước hired / sla=0 không tính.
- action_reorder(ids): ghi sequence 10/20/30… theo thứ tự truyền vào.
- ondelete: chặn xoá bước còn ứng viên (kể cả archived) bằng UserError dễ hiểu.
"""
from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestStageConfig(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Stage = cls.env['hr.recruitment.stage']
        cls.stage_sla = Stage.create(
            {'name': 'Bước SLA (test)', 'sequence': 210, 'sla_days': 2})
        cls.stage_free = Stage.create(
            {'name': 'Bước không SLA (test)', 'sequence': 220, 'sla_days': 0})
        cls.stage_hired = Stage.create(
            {'name': 'Đã tuyển SLA (test)', 'sequence': 230,
             'sla_days': 2, 'hired_stage': True})
        cls.job = cls.env['hr.job'].create(
            {'name': 'Vị trí Test StageConfig', 'no_of_recruitment': 5})

    def _applicant(self, stage, days_ago=0):
        a = self.env['hr.applicant'].create({
            'partner_name': 'UV SLA %s' % days_ago,
            'job_id': self.job.id,
            'stage_id': stage.id,
        })
        if days_ago:
            a.write({'date_last_stage_update':
                     fields.Datetime.now() - timedelta(days=days_ago)})
        return a

    # ── SLA ──────────────────────────────────────────────────────────────────

    def test_01_sla_within_limit_not_overdue(self):
        a = self._applicant(self.stage_sla, days_ago=1)
        days, sla, overdue = a._hb_sla_state()
        self.assertEqual((days, sla), (1, 2))
        self.assertFalse(overdue)

    def test_02_sla_exceeded_overdue(self):
        a = self._applicant(self.stage_sla, days_ago=3)
        days, sla, overdue = a._hb_sla_state()
        self.assertEqual((days, sla), (3, 2))
        self.assertTrue(overdue)

    def test_03_no_sla_never_overdue(self):
        a = self._applicant(self.stage_free, days_ago=30)
        days, sla, overdue = a._hb_sla_state()
        self.assertEqual(sla, 0)
        self.assertFalse(overdue)

    def test_04_hired_stage_never_overdue(self):
        a = self._applicant(self.stage_hired, days_ago=30)
        self.assertFalse(a._hb_sla_state()[2])

    def test_05_sla_days_negative_rejected(self):
        with self.assertRaises(ValidationError):
            self.stage_sla.sla_days = -1

    # ── Reorder ──────────────────────────────────────────────────────────────

    def test_06_action_reorder_writes_sequence(self):
        Stage = self.env['hr.recruitment.stage']
        Stage.action_reorder(
            [self.stage_hired.id, self.stage_free.id, self.stage_sla.id])
        self.assertEqual(self.stage_hired.sequence, 10)
        self.assertEqual(self.stage_free.sequence, 20)
        self.assertEqual(self.stage_sla.sequence, 30)

    # ── Guard xoá ────────────────────────────────────────────────────────────

    def test_07_delete_stage_with_applicant_blocked(self):
        a = self._applicant(self.stage_sla)
        with self.assertRaises(UserError):
            self.stage_sla.unlink()
        # kể cả khi ứng viên đã lưu trữ (refuse) vẫn chặn
        a.active = False
        with self.assertRaises(UserError):
            self.stage_sla.unlink()

    def test_08_delete_empty_stage_ok(self):
        self.stage_free.unlink()
        self.assertFalse(self.stage_free.exists())

    # ── Guard ẩn / hiện lại ──────────────────────────────────────────────────

    def test_09_hide_stage_with_active_applicant_blocked(self):
        self._applicant(self.stage_sla)
        with self.assertRaises(UserError):
            self.stage_sla.active = False

    def test_10_hide_stage_with_archived_applicant_ok(self):
        """Khác guard xoá: ứng viên đã lưu trữ không chặn ẩn."""
        a = self._applicant(self.stage_sla)
        a.active = False
        self.stage_sla.active = False
        Stage = self.env['hr.recruitment.stage']
        self.assertNotIn(self.stage_sla, Stage.search([]))
        self.assertIn(self.stage_sla,
                      Stage.with_context(active_test=False).search([]))
        # hiện lại được, không mất dữ liệu
        self.stage_sla.active = True
        self.assertIn(self.stage_sla, Stage.search([]))
        self.assertEqual(self.stage_sla.sla_days, 2)

    def test_11_hide_all_visible_stages_blocked(self):
        all_visible = self.env['hr.recruitment.stage'].search([])
        with self.assertRaises(UserError):
            all_visible.write({'active': False})
