from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestPromotionCriteria(TransactionCase):
    def test_seed_criteria_exist_with_weight(self):
        crits = self.env['hr.promotion.criteria'].search([('active', '=', True)])
        self.assertTrue(len(crits) >= 4, 'Phải seed >= 4 tiêu chí mặc định')
        self.assertTrue(all(c.weight > 0 for c in crits), 'Mọi tiêu chí có trọng số > 0')
        self.assertTrue(all(c.max_score > 0 for c in crits))

    def test_duplicate_code_rejected(self):
        from psycopg2 import IntegrityError
        from odoo.tools import mute_logger
        Crit = self.env['hr.promotion.criteria']
        Crit.create({'name': 'Dup A', 'code': 'dup_test', 'weight': 10})
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                Crit.create({'name': 'Dup B', 'code': 'dup_test', 'weight': 10})
                self.env.flush_all()


@tagged('post_install', '-at_install')
class TestPromotionEvaluation(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Eval Target',
            'identification_id': '012345678901',
        })
        Crit = self.env['hr.promotion.criteria']
        self.c1 = Crit.create({'name': 'C1', 'code': 'c1', 'weight': 60, 'max_score': 5})
        self.c2 = Crit.create({'name': 'C2', 'code': 'c2', 'weight': 40, 'max_score': 5})

    def _make_eval(self, s1, s2):
        return self.env['hr.promotion.evaluation'].create({
            'employee_id': self.emp.id,
            'line_ids': [
                (0, 0, {'criteria_id': self.c1.id, 'score': s1}),
                (0, 0, {'criteria_id': self.c2.id, 'score': s2}),
            ],
        })

    def test_total_score_weighted_percent(self):
        ev = self._make_eval(5, 5)            # full → 100%
        self.assertAlmostEqual(ev.total_score, 100.0, places=1)
        ev2 = self._make_eval(4, 2)           # (4/5*60 + 2/5*40)/100*100 = 64
        self.assertAlmostEqual(ev2.total_score, 64.0, places=1)

    def test_line_copies_weight_and_max(self):
        ev = self._make_eval(3, 3)
        line1 = ev.line_ids.filtered(lambda l: l.criteria_id == self.c1)
        self.assertEqual(line1.weight, 60)
        self.assertEqual(line1.max_score, 5)

    def test_verdict_auto_thresholds(self):
        self.assertEqual(self._make_eval(5, 5).verdict_auto, 'qualified')   # 100
        self.assertEqual(self._make_eval(4, 2).verdict_auto, 'consider')    # 64
        self.assertEqual(self._make_eval(2, 2).verdict_auto, 'not_yet')     # 40

    def test_empty_evaluation_scores_zero(self):
        ev = self.env['hr.promotion.evaluation'].create({
            'employee_id': self.emp.id})
        self.assertEqual(ev.total_score, 0.0)
        self.assertEqual(ev.verdict_auto, 'not_yet')

    def test_score_out_of_range_raises(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.env['hr.promotion.evaluation'].create({
                'employee_id': self.emp.id,
                'line_ids': [(0, 0, {'criteria_id': self.c1.id, 'score': 9})],
            })

    def test_confirm_requires_verdict_final(self):
        from odoo.exceptions import UserError
        ev = self._make_eval(4, 4)
        with self.assertRaises(UserError):
            ev.action_confirm()
        ev.verdict_final = 'qualified'
        ev.action_confirm()
        self.assertEqual(ev.state, 'confirmed')

    def test_confirmed_cannot_be_deleted(self):
        from odoo.exceptions import UserError
        ev = self._make_eval(4, 4)
        ev.verdict_final = 'qualified'
        ev.action_confirm()
        with self.assertRaises(UserError):
            ev.unlink()

    def test_24h_rule_blocks_content_edit_but_allows_confirm(self):
        from odoo.exceptions import AccessError
        ev = self._make_eval(4, 4)
        # backdate create_date quá 24h
        self.env.cr.execute(
            "UPDATE hr_promotion_evaluation "
            "SET create_date = (now() - interval '2 days') WHERE id = %s",
            (ev.id,))
        ev.invalidate_recordset()
        user = self.env['res.users'].create({
            'name': 'NonMgr Eval', 'login': 'eval_24h_user',
            'group_ids': [(6, 0, [self.env.ref('hr.group_hr_user').id])]})
        # sửa nội dung sau 24h → chặn
        with self.assertRaises(AccessError):
            ev.with_user(user).write({'conclusion_note': 'late edit'})
        # nhưng chuyển trạng thái (confirm) vẫn cho phép
        ev.with_user(user).write({'state': 'confirmed'})
        self.assertEqual(ev.state, 'confirmed')

    def test_auto_metrics_keys_and_attendance_guard(self):
        # Tạo 1 mốc thăng tiến để có "tháng từ thăng tiến gần nhất"
        self.env['hr.promotion.history'].create({
            'employee_id': self.emp.id,
            'x_change_type': 'join',
            'date_effective': fields.Date.today(),
        })
        m = self.emp._promo_auto_metrics()
        for key in ('tenureMonths', 'monthsSincePromo', 'currentJob',
                    'attendance'):
            self.assertIn(key, m)
        # Không có module chấm công/khoá → attendance là None hoặc dict, không lỗi
        self.assertTrue(m['attendance'] is None or isinstance(m['attendance'], dict))

    def test_tenure_months_uses_probation_start(self):
        from dateutil.relativedelta import relativedelta
        self.emp.x_probation_start = fields.Date.today() - relativedelta(months=3)
        m = self.emp._promo_auto_metrics()
        # ~3 tháng, không bị rơi về create_date (hôm nay → ~0)
        self.assertGreater(m['tenureMonths'], 2.5)
        self.assertLess(m['tenureMonths'], 3.5)


@tagged('post_install', '-at_install')
class TestPromotionEvalAccess(TransactionCase):
    def setUp(self):
        super().setUp()
        self.emp = self.env['hr.employee'].create({
            'name': 'Acc Target', 'identification_id': '019999999901'})
        self.crit = self.env['hr.promotion.criteria'].create(
            {'name': 'X', 'code': 'accx', 'weight': 100, 'max_score': 5})
        self.regular = self.env['res.users'].create({
            'name': 'Reg', 'login': 'reg_eval_acc',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})

    def test_regular_user_cannot_create_evaluation(self):
        from odoo.exceptions import AccessError
        Ev = self.env['hr.promotion.evaluation'].with_user(self.regular)
        with self.assertRaises(AccessError):
            Ev.create({
                'employee_id': self.emp.id,
                'line_ids': [(0, 0, {'criteria_id': self.crit.id, 'score': 3})]})
