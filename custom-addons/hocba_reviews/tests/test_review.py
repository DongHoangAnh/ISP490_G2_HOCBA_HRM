"""Đánh giá nhân viên định kỳ — công thức, chỉ số tự động, luồng trạng thái.

Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md
Công thức + ví dụ tính tay: docs/CONG_THUC_DANH_GIA.md
"""
from datetime import date, datetime, timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestReviewBase(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Review = cls.env['hb.performance.review']
        cls.Criteria = cls.env['hb.review.criteria']
        cls.type_teacher = cls.env.ref(
            'hocba_employees.employee_type_teacher')
        cls.type_office = cls.env.ref(
            'hocba_employees.employee_type_office_staff')
        cls.teacher = cls.env['hr.employee'].create({
            'name': 'GV Đánh Giá Test',
            'identification_id': '090000000101',
            'x_employee_type_id': cls.type_teacher.id,
        })
        cls.staff = cls.env['hr.employee'].create({
            'name': 'NV VP Đánh Giá Test',
            'identification_id': '090000000102',
            'x_employee_type_id': cls.type_office.id,
        })
        # Kỳ dùng chung: Quý 1 năm trước (dữ liệu test nằm gọn trong kỳ).
        cls.year = fields.Date.today().year - 1

    def _review(self, employee, lines=None, **kw):
        vals = {
            'employee_id': employee.id,
            'period_type': 'quarter',
            'period_year': self.year,
            'period_index': 1,
        }
        vals.update(kw)
        if lines is not None:
            vals['line_ids'] = lines
        return self.Review.create(vals)


@tagged('post_install', '-at_install')
class TestReviewScore(TestReviewBase):
    """§2 — tổng điểm có trọng số và ngưỡng xếp loại."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.c60 = cls.Criteria.create({
            'name': 'Tiêu chí 60', 'code': 'test_w60', 'role_group': 'office',
            'weight': 60, 'max_score': 5, 'sequence': 910})
        cls.c40 = cls.Criteria.create({
            'name': 'Tiêu chí 40', 'code': 'test_w40', 'role_group': 'office',
            'weight': 40, 'max_score': 5, 'sequence': 920})

    def _scored(self, s1, s2, index=1):
        return self._review(self.staff, lines=[
            (0, 0, {'criteria_id': self.c60.id, 'score': s1}),
            (0, 0, {'criteria_id': self.c40.id, 'score': s2}),
        ], period_index=index)

    def test_01_weighted_total(self):
        # (4/5×60 + 3/5×40) / 100 × 100 = 48 + 24 = 72
        r = self._scored(4, 3)
        self.assertAlmostEqual(r.total_score, 72.0, places=2)

    def test_02_grade_thresholds(self):
        # 5/5 & 5/5 = 100 -> A ; 4&3 = 72 -> B ; 3&3 = 60 -> C ; 2&2 = 40 -> D
        self.assertEqual(self._scored(5, 5, 1).grade, 'a')
        self.assertEqual(self._scored(4, 3, 2).grade, 'b')
        self.assertEqual(self._scored(3, 3, 3).grade, 'c')
        self.assertEqual(self._scored(2, 2, 4).grade, 'd')

    def test_03_weight_sum_not_100(self):
        """Mẫu số là Σ weight thực tế, không phải 100 cứng (§5.3)."""
        r = self._review(self.staff, lines=[
            (0, 0, {'criteria_id': self.c60.id, 'score': 5}),
        ])
        self.assertAlmostEqual(r.total_score, 100.0, places=2)

    def test_04_line_snapshot_weight(self):
        """Sửa trọng số tiêu chí KHÔNG đổi phiếu đã tạo."""
        r = self._scored(4, 3)
        self.c60.weight = 10
        r.line_ids.invalidate_recordset()
        self.assertAlmostEqual(r.total_score, 72.0, places=2)

    def test_05_score_out_of_range_rejected(self):
        with self.assertRaises(ValidationError):
            self._scored(6, 3)


@tagged('post_install', '-at_install')
class TestReviewMetrics(TestReviewBase):
    """§4 — chỉ số tự động từ dữ liệu vận hành."""

    def _teaching(self, day, **flags):
        vals = {
            'cms_session_id': 'S-%s-%s' % (day.isoformat(), id(self)),
            'employee_id': self.teacher.id,
            'session_date': day,
            'check_in': datetime.combine(day, datetime.min.time()),
        }
        vals.update(flags)
        return self.env['hocba.teaching.attendance'].create(vals)

    def _office_day(self, day, late=0, early=0):
        rec = self.env['hocba.attendance'].create({
            'employee_id': self.staff.id,
            'check_in': datetime.combine(day, datetime.min.time()),
        })
        # late_minutes/early_leave_minutes là computed-store theo ca làm việc;
        # test ghi thẳng giá trị để cô lập công thức chuyên cần.
        rec.write({'late_minutes': late, 'early_leave_minutes': early})
        return rec

    def test_10_teacher_punctuality(self):
        """20 buổi, 1 ngoài cửa sổ + 1 sai vị trí -> 18/20 = 90% -> 3 điểm."""
        base = date(self.year, 1, 5)
        for i in range(20):
            flags = {}
            if i == 0:
                flags['out_of_window'] = True
            if i == 1:
                flags['out_of_zone'] = True
            self._teaching(base + timedelta(days=i), **flags)
        r = self._review(self.teacher, lines=[])
        r.compute_metrics()
        self.assertEqual(r.metric_total_units, 20)
        self.assertEqual(r.metric_ok_units, 18)
        self.assertAlmostEqual(r.metric_punctual_pct, 90.0, places=1)
        self.assertEqual(r._auto_score_for('punctuality', 5), 3)

    def test_11_office_punctuality(self):
        """10 ngày, 1 trễ + 1 về sớm -> 8/10 = 80% -> 2 điểm."""
        base = date(self.year, 2, 3)
        for i in range(10):
            self._office_day(base + timedelta(days=i),
                             late=15 if i == 0 else 0,
                             early=20 if i == 1 else 0)
        r = self._review(self.staff, lines=[])
        r.compute_metrics()
        self.assertEqual(r.metric_total_units, 10)
        self.assertEqual(r.metric_ok_units, 8)
        self.assertAlmostEqual(r.metric_punctual_pct, 80.0, places=1)
        self.assertEqual(r._auto_score_for('punctuality', 5), 2)

    def test_12_no_attendance_no_auto_score(self):
        """Không có dữ liệu chấm công -> KHÔNG tự chấm (không phạt oan)."""
        r = self._review(self.staff, lines=[])
        r.compute_metrics()
        self.assertEqual(r.metric_total_units, 0)
        self.assertEqual(r._auto_score_for('punctuality', 5), 0)

    def test_13_workload_scaled_by_period_length(self):
        """40 buổi: quý (chỉ tiêu 60) = 66.7% -> 2đ; nửa năm (120) = 33% -> 1đ."""
        base = date(self.year, 1, 2)
        for i in range(40):
            self._teaching(base + timedelta(days=i))
        rq = self._review(self.teacher, lines=[])
        rq.compute_metrics()
        self.assertEqual(rq.metric_total_units, 40)
        self.assertEqual(rq._auto_score_for('workload', 5), 2)

        rh = self._review(self.teacher, lines=[], period_type='half')
        rh.compute_metrics()
        self.assertEqual(rh._session_target(), 120.0)
        self.assertEqual(rh._auto_score_for('workload', 5), 1)

    def _cert(self, expiry, verified=True):
        skill_type = self.env['hr.skill.type'].create({'name': 'Cert Test %s' % expiry})
        skill = self.env['hr.skill'].create({
            'name': 'Skill %s' % expiry, 'skill_type_id': skill_type.id})
        level = self.env['hr.skill.level'].create({
            'name': 'L1', 'skill_type_id': skill_type.id, 'level_progress': 50})
        return self.env['hr.employee.skill'].create({
            'employee_id': self.teacher.id,
            'skill_type_id': skill_type.id,
            'skill_id': skill.id,
            'skill_level_id': level.id,
            'x_cert_verified': verified,
            'x_cert_expiry': expiry,
        })

    def test_14_cert_none_scores_one(self):
        r = self._review(self.teacher, lines=[])
        r.compute_metrics()
        self.assertEqual(r._auto_score_for('cert', 5), 1)

    def test_15_cert_expired_scores_two(self):
        today = fields.Date.today()
        self._cert(today - timedelta(days=10))
        self._cert(today + timedelta(days=400))
        r = self._review(self.teacher, lines=[])
        r.compute_metrics()
        self.assertEqual(r.metric_cert_expired, 1)
        self.assertEqual(r._auto_score_for('cert', 5), 2)

    def test_16_cert_two_valid_scores_five(self):
        today = fields.Date.today()
        self._cert(today + timedelta(days=400))
        self._cert(today + timedelta(days=500))
        r = self._review(self.teacher, lines=[])
        r.compute_metrics()
        self.assertEqual(r.metric_cert_valid, 2)
        self.assertEqual(r._auto_score_for('cert', 5), 5)


@tagged('post_install', '-at_install')
class TestReviewFlow(TestReviewBase):
    """Sinh dòng theo nhóm, luồng trạng thái, mở đợt hàng loạt."""

    def test_20_lines_generated_per_role_group(self):
        rt = self._review(self.teacher)
        ro = self._review(self.staff)
        self.assertEqual(rt.role_group, 'teacher')
        self.assertEqual(ro.role_group, 'office')
        self.assertTrue(rt.line_ids)
        self.assertTrue(ro.line_ids)
        self.assertTrue(all(l.criteria_id.role_group == 'teacher'
                            for l in rt.line_ids))
        self.assertTrue(all(l.criteria_id.role_group == 'office'
                            for l in ro.line_ids))
        # Dòng tự động của giảng viên: chuyên cần, khối lượng, chứng chỉ.
        auto_codes = set(rt.line_ids.filtered('is_auto').mapped('criteria_id.code'))
        self.assertEqual(auto_codes, {'t_punctual', 't_workload', 't_expertise'})

    def test_21_period_range(self):
        r = self._review(self.staff, period_index=3)
        self.assertEqual(r.date_from, date(self.year, 7, 1))
        self.assertEqual(r.date_to, date(self.year, 9, 30))
        self.assertEqual(r.period_label, 'Quý 3/%s' % self.year)
        ry = self._review(self.teacher, period_type='year')
        self.assertEqual(ry.date_from, date(self.year, 1, 1))
        self.assertEqual(ry.date_to, date(self.year, 12, 31))

    def test_22_invalid_period_index_rejected(self):
        with self.assertRaises(ValidationError):
            self._review(self.staff, period_index=5)

    def test_23_duplicate_period_rejected(self):
        self._review(self.staff)
        from psycopg2 import IntegrityError
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self._review(self.staff)
                self.env.flush_all()

    def test_24_confirm_requires_score_and_note(self):
        r = self._review(self.staff)
        r.line_ids.write({'score': 0})
        with self.assertRaises(UserError):
            r.action_confirm()
        r.line_ids[0].score = 4
        with self.assertRaises(UserError):   # thiếu nhận xét quản lý
            r.action_confirm()
        r.manager_note = 'Hoàn thành tốt công việc trong kỳ.'
        r.action_confirm()
        self.assertEqual(r.state, 'confirmed')
        self.assertTrue(r.confirmed_on)

    def test_25_publish_notifies_employee(self):
        user = self.env['res.users'].create({
            'name': 'NV VP Review User', 'login': 'review_user_test',
            'email': 'review_user_test@hocba.vn'})
        self.staff.user_id = user.id
        r = self._review(self.staff)
        r.line_ids[0].score = 5
        r.manager_note = 'Tốt.'
        r.action_confirm()
        r.action_publish()
        self.assertEqual(r.state, 'published')
        notif = self.env['hb.notification'].search([
            ('recipient_id', '=', user.id), ('category', '=', 'review')])
        self.assertTrue(notif, 'Công bố phải sinh thông báo cho nhân viên')

    def test_26_publish_requires_confirmed(self):
        r = self._review(self.staff)
        with self.assertRaises(UserError):
            r.action_publish()

    def test_27_confirmed_review_cannot_be_deleted(self):
        r = self._review(self.staff)
        r.line_ids[0].score = 4
        r.manager_note = 'OK.'
        r.action_confirm()
        with self.assertRaises(UserError):
            r.unlink()

    def test_28_reset_to_draft_reopens(self):
        r = self._review(self.staff)
        r.line_ids[0].score = 4
        r.manager_note = 'OK.'
        r.action_confirm()
        r.action_reset_draft()
        self.assertEqual(r.state, 'draft')
        self.assertFalse(r.confirmed_on)

    def test_29_manual_override_survives_recompute(self):
        """Quản lý sửa đè điểm tự động -> tính lại chỉ số không ghi đè."""
        r = self._review(self.teacher)
        line = r.line_ids.filtered(lambda l: l.criteria_id.code == 't_expertise')
        line.write({'score': 5, 'manual_override': True})
        r.compute_metrics()
        self.assertEqual(line.score, 5)

    def test_30_untyped_employee_counts_as_office(self):
        """NV CHƯA gán loại phải nằm nhóm văn phòng.
        Domain '!=' trên field related đi qua JOIN sẽ bỏ sót bản ghi NULL —
        lỗi này từng làm tab Văn phòng trống trơn trên Neon (21 NV)."""
        untyped = self.env['hr.employee'].create({
            'name': 'NV Chưa Gán Loại Test',
            'identification_id': '090000000103',
        })
        self.assertFalse(untyped.x_employee_type_id)
        Employee = self.env['hr.employee']
        office = Employee.search(
            self.Review.role_group_domain('office') + [('id', '=', untyped.id)])
        self.assertIn(untyped, office, 'NV chưa gán loại phải thuộc nhóm office')
        teachers = Employee.search(
            self.Review.role_group_domain('teacher') + [('id', '=', untyped.id)])
        self.assertNotIn(untyped, teachers)
        self.assertEqual(self.Review._role_group_of(untyped), 'office')

    def test_31_bulk_open_is_idempotent(self):
        first = self.Review.open_period(
            'teacher', 'quarter', self.year, 4)
        self.assertGreaterEqual(first['created'], 1)
        second = self.Review.open_period(
            'teacher', 'quarter', self.year, 4)
        self.assertEqual(second['created'], 0)
        self.assertGreaterEqual(second['skipped'], 1)
