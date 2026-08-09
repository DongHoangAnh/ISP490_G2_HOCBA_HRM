from datetime import date

from psycopg2 import IntegrityError

from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import ValidationError
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestHonorEntry(TransactionCase):
    """Bảng vinh danh — spec 2026-08-09 §5."""

    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Honor Target', 'identification_id': '112345678901'})
        Job = self.env['hr.job']
        self.job_old = Job.create({'name': 'Nhân viên Đào tạo'})
        self.job_new = Job.create({'name': 'Trưởng phòng Đào tạo'})
        self.emp.job_id = self.job_old.id

    def _promo(self, **kw):
        vals = {'employee_id': self.emp.id,
                'x_change_type': 'promotion',
                'from_job_id': self.job_old.id,
                'to_job_id': self.job_new.id,
                'date_effective': date(2026, 8, 9)}
        vals.update(kw)
        return self.env['hr.promotion.history'].create(vals)

    def _entries(self):
        return self.env['hb.honor.entry'].search(
            [('employee_id', '=', self.emp.id)])

    # --- tự sinh khi bổ nhiệm (§5.2) ---
    def test_promotion_creates_honor_entry(self):
        promo = self._promo()
        entries = self._entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries.source, 'auto')
        self.assertEqual(entries.category, 'promotion')
        self.assertEqual(entries.promotion_id, promo)
        self.assertIn(self.job_new.name, entries.title)
        self.assertEqual(entries.date_awarded, date(2026, 8, 9))

    def test_salary_change_no_honor(self):
        self._promo(x_change_type='salary', to_job_id=self.job_old.id,
                    from_wage=10000000, to_wage=12000000,
                    reason='Điều chỉnh theo KPI', x_evidence_url='http://kpi')
        self.assertFalse(self._entries())

    def test_join_snapshot_no_honor(self):
        self._promo(x_change_type='join')
        self.assertFalse(self._entries())

    def test_promotion_same_job_no_honor(self):
        # Vẫn là 'promotion' nhưng chức vụ không đổi (chỉ tăng lương) → không
        # có "chức danh mới" để vinh danh.
        self._promo(to_job_id=self.job_old.id,
                    from_wage=10000000, to_wage=12000000,
                    reason='Tăng lương', x_evidence_url='http://kpi')
        self.assertFalse(self._entries())

    # --- kỳ vinh danh (§5.1) ---
    def test_period_key_from_date(self):
        e = self.env['hb.honor.entry'].create({
            'employee_id': self.emp.id, 'title': 'Nhân viên xuất sắc',
            'date_awarded': date(2026, 8, 9)})
        self.assertEqual(e.period_key, '2026-08')
        e.date_awarded = date(2026, 12, 1)
        self.assertEqual(e.period_key, '2026-12')

    def test_unique_auto_entry_per_promotion(self):
        promo = self._promo()
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.env['hb.honor.entry'].create({
                    'employee_id': self.emp.id, 'title': 'Trùng',
                    'promotion_id': promo.id})
                self.env.flush_all()

    def test_manual_entries_do_not_collide(self):
        # promotion_id NULL — Postgres cho phép nhiều NULL trong UNIQUE, nếu
        # không thì HR chỉ thêm được đúng 1 mục vinh danh tay.
        Honor = self.env['hb.honor.entry']
        Honor.create({'employee_id': self.emp.id, 'title': 'A'})
        Honor.create({'employee_id': self.emp.id, 'title': 'B'})
        self.env.flush_all()
        self.assertEqual(len(self._entries()), 2)

    def test_negative_rank_rejected(self):
        with self.assertRaisesRegex(ValidationError, 'Hạng'):
            self.env['hb.honor.entry'].create({
                'employee_id': self.emp.id, 'title': 'X', 'rank': -1})

    def test_blank_title_rejected(self):
        with self.assertRaisesRegex(ValidationError, 'Danh hiệu'):
            self.env['hb.honor.entry'].create({
                'employee_id': self.emp.id, 'title': '   '})
