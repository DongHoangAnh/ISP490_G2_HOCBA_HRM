"""Màn Cấu hình đánh giá — HR sửa bộ câu hỏi, trọng số, thang điểm, ngưỡng.

Spec: docs/superpowers/specs/2026-08-21-reviews-config-design.md
Công thức (không đổi): docs/CONG_THUC_DANH_GIA.md
"""
import json

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools import mute_logger

PWD = 'Hocba@2026'


def _row(name, weight, max_score=5, **kw):
    """Một dòng câu hỏi trong payload cấu hình (khoá snake_case của model)."""
    vals = {
        'id': 0, 'name': name, 'weight': weight, 'max_score': max_score,
        'auto_source': 'none', 'guideline': '', 'active': True,
        'anchor_top': 'Mốc cao', 'anchor_mid': 'Mốc giữa', 'anchor_low': 'Mốc thấp',
    }
    vals.update(kw)
    return vals


@tagged('post_install', '-at_install')
class TestCriteriaConfig(TransactionCase):
    """`apply_group` — lưu cả bộ tiêu chí của một nhóm trong 1 transaction."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Criteria = cls.env['hb.review.criteria']
        cls.Review = cls.env['hb.performance.review']
        # Bộ mặc định của nhóm 'office' tắt đi để test tự dựng bộ của mình:
        # check_group_weight đếm trên TOÀN BỘ tiêu chí đang bật của nhóm.
        cls.Criteria.with_context(active_test=False).search(
            [('role_group', '=', 'office')]).write({'active': False})
        cls.type_office = cls.env.ref(
            'hocba_employees.employee_type_office_staff')
        cls.staff = cls.env['hr.employee'].create({
            'name': 'NV Cấu Hình Test',
            'identification_id': '090000000301',
            'x_employee_type_id': cls.type_office.id,
        })
        cls.year = fields.Date.today().year - 1

    def _active(self):
        return self.Criteria.search(
            [('role_group', '=', 'office')], order='sequence, id')

    def _apply(self, rows, group='office'):
        return self.Criteria.apply_group(group, rows)

    # ------------------------------------------------------------------
    # Trọng số
    # ------------------------------------------------------------------
    def test_60_apply_group_saves_full_set(self):
        self._apply([_row('Kết quả công việc', 60), _row('Thái độ', 40)])
        crits = self._active()
        self.assertEqual(len(crits), 2)
        self.assertEqual(crits.mapped('name'),
                         ['Kết quả công việc', 'Thái độ'])
        self.assertEqual(crits.mapped('weight'), [60.0, 40.0])
        # Thứ tự do vị trí trong danh sách gửi lên, không cần HR tự đánh số.
        self.assertEqual(crits[0].sequence < crits[1].sequence, True)

    def test_61_weight_sum_must_be_100(self):
        with mute_logger('odoo.sql_db'), self.assertRaises(ValidationError):
            self._apply([_row('A', 60), _row('B', 35)])

    def test_62_bad_sum_leaves_database_untouched(self):
        """Chặn cứng nghĩa là KHÔNG có nửa vời: cả lô phải bị rollback."""
        self._apply([_row('Kết quả công việc', 60), _row('Thái độ', 40)])
        before = {c.name: c.weight for c in self._active()}
        rows = [_row('Kết quả công việc', 70, id=self._active()[0].id),
                _row('Thái độ', 25, id=self._active()[1].id)]
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self._apply(rows)
        self.assertEqual({c.name: c.weight for c in self._active()}, before)

    def test_63_disabled_criteria_not_counted_in_sum(self):
        self._apply([_row('A', 60), _row('B', 40)])
        rows = [_row('A', 100, id=self._active()[0].id),
                _row('B', 40, id=self._active()[1].id, active=False)]
        self._apply(rows)  # tổng phần đang bật = 100 -> hợp lệ
        self.assertEqual(self._active().mapped('name'), ['A'])

    # ------------------------------------------------------------------
    # Thang điểm 1..10
    # ------------------------------------------------------------------
    def test_64_max_score_range(self):
        for bad in (0, 11):
            with self.assertRaises(ValidationError), self.env.cr.savepoint():
                self._apply([_row('A', 100, max_score=bad)])

    def test_65_max_score_ten_scales_anchors(self):
        self._apply([_row('A', 100, max_score=10)])
        crit = self._active()
        self.assertEqual(crit.max_score, 10)
        self.assertEqual([s for s, _t in crit.anchor_levels()], [10, 5, 1])

    # ------------------------------------------------------------------
    # Thêm / tắt câu hỏi
    # ------------------------------------------------------------------
    def test_66_new_criteria_get_unique_codes(self):
        self._apply([_row('Câu hỏi mới', 50), _row('Câu hỏi mới', 50)])
        codes = self._active().mapped('code')
        self.assertEqual(len(set(codes)), 2, 'Mã tiêu chí phải duy nhất')
        self.assertTrue(all(c.startswith('o_') for c in codes), codes)

    def test_67_disabled_criteria_still_readable_from_old_review(self):
        self._apply([_row('Kết quả công việc', 100)])
        crit = self._active()
        review = self.Review.create({
            'employee_id': self.staff.id, 'role_group': 'office',
            'period_year': self.year, 'period_index': 1,
        })
        self.assertEqual(review.line_ids.criteria_id, crit)
        self._apply([_row('Kết quả công việc', 100, id=crit.id, active=False),
                     _row('Tiêu chí thay thế', 100)])
        # Tiêu chí đã tắt: phiếu cũ vẫn tra được tên (không xoá cứng).
        self.assertEqual(review.line_ids.criteria_id.with_context(
            active_test=False).name, 'Kết quả công việc')

    # ------------------------------------------------------------------
    # Ảnh hưởng tới phiếu đã tạo
    # ------------------------------------------------------------------
    def test_68_draft_review_keeps_old_snapshot(self):
        self._apply([_row('A', 60), _row('B', 40)])
        first, second = self._active()
        review = self.Review.create({
            'employee_id': self.staff.id, 'role_group': 'office',
            'period_year': self.year, 'period_index': 1,
        })
        for line in review.line_ids:
            line.score = line.max_score  # 100 điểm
        self.assertAlmostEqual(review.total_score, 100.0, places=2)

        self._apply([_row('A', 20, id=first.id, max_score=10),
                     _row('B', 80, id=second.id)])
        review.invalidate_recordset()
        self.assertEqual(review.line_ids.mapped('weight'), [60.0, 40.0],
                         'Phiếu Nháp phải giữ trọng số lúc tạo')
        self.assertEqual(review.line_ids.mapped('max_score'), [5, 5])
        self.assertAlmostEqual(review.total_score, 100.0, places=2)

    def test_69_new_review_uses_new_config(self):
        self._apply([_row('A', 60), _row('B', 40)])
        first, second = self._active()
        self._apply([_row('A', 20, id=first.id, max_score=10),
                     _row('B', 80, id=second.id)])
        review = self.Review.create({
            'employee_id': self.staff.id, 'role_group': 'office',
            'period_year': self.year, 'period_index': 2,
        })
        self.assertEqual(sorted(review.line_ids.mapped('weight')), [20.0, 80.0])
        self.assertEqual(sorted(review.line_ids.mapped('max_score')), [5, 10])


@tagged('post_install', '-at_install')
class TestGradingConfig(TransactionCase):
    """Ngưỡng xếp loại + tham số — vẫn nằm ở ir.config_parameter."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Review = cls.env['hb.performance.review']
        cls.Criteria = cls.env['hb.review.criteria']
        cls.type_office = cls.env.ref(
            'hocba_employees.employee_type_office_staff')
        cls.staff = cls.env['hr.employee'].create({
            'name': 'NV Ngưỡng Test',
            'identification_id': '090000000302',
            'x_employee_type_id': cls.type_office.id,
        })

    def test_70_thresholds_must_descend(self):
        for bad in ({'grade_a': 70, 'grade_b': 80, 'grade_c': 55},
                    {'grade_a': 85, 'grade_b': 70, 'grade_c': 70},
                    {'grade_a': 120, 'grade_b': 70, 'grade_c': 55},
                    {'grade_a': 85, 'grade_b': 70, 'grade_c': 0}):
            with self.assertRaises(ValidationError), self.env.cr.savepoint():
                self.Review.set_grading(dict(bad, sessions_target=60))

    def test_71_sessions_target_must_be_positive(self):
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.Review.set_grading({
                'grade_a': 85, 'grade_b': 70, 'grade_c': 55,
                'sessions_target': 0})

    def test_72_new_thresholds_change_the_grade(self):
        crit = self.Criteria.create({
            'name': 'Tiêu chí ngưỡng', 'code': 'test_grade_cfg',
            'role_group': 'office', 'weight': 100, 'max_score': 10,
            'sequence': 950})
        review = self.Review.create({
            'employee_id': self.staff.id, 'role_group': 'office',
            'period_year': fields.Date.today().year - 1, 'period_index': 3,
            'line_ids': [(0, 0, {'criteria_id': crit.id, 'score': 7.6})],
        })
        self.Review.set_grading({'grade_a': 90, 'grade_b': 75, 'grade_c': 60,
                                 'sessions_target': 60})
        review.line_ids.write({'score': 7.6})  # kích hoạt tính lại
        self.assertAlmostEqual(review.total_score, 76.0, places=2)
        self.assertEqual(review.grade, 'b')

        self.Review.set_grading({'grade_a': 70, 'grade_b': 60, 'grade_c': 50,
                                 'sessions_target': 60})
        review.line_ids.write({'score': 7.6})
        self.assertEqual(review.grade, 'a')

    def test_73_grading_config_reads_back(self):
        self.Review.set_grading({'grade_a': 88, 'grade_b': 72, 'grade_c': 58,
                                 'sessions_target': 45})
        cfg = self.Review.grading_config()
        self.assertEqual(
            (cfg['grade_a'], cfg['grade_b'], cfg['grade_c'],
             cfg['sessions_target']), (88.0, 72.0, 58.0, 45.0))


@tagged('post_install', '-at_install')
class TestReviewConfigApi(HttpCase):
    """API màn Cấu hình đánh giá — chỉ HR Manager/Admin."""

    URL = '/hocba-hrm/api/reviews/config'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Criteria = cls.env['hb.review.criteria']
        cls.user_hr = cls.env['res.users'].create({
            'name': 'HR (test cfg)', 'login': 'test_cfg_hr', 'password': PWD,
            'group_ids': [(4, cls.env.ref('hr.group_hr_manager').id)],
        })
        cls.user_giaovu = cls.env['res.users'].create({
            'name': 'Giáo vụ (test cfg)', 'login': 'test_cfg_gv',
            'password': PWD,
            'group_ids': [
                (4, cls.env.ref('hr.group_hr_user').id),
                (4, cls.env.ref('hocba_employees.group_hocba_giaovu').id)],
        })
        cls.user_plain = cls.env['res.users'].create({
            'name': 'NV thường (test cfg)', 'login': 'test_cfg_nv',
            'password': PWD,
            'group_ids': [(4, cls.env.ref('base.group_user').id)],
        })

    def _get(self, login='test_cfg_hr', expect=200):
        self.authenticate(login, PWD)
        res = self.url_open(self.URL)
        self.assertEqual(res.status_code, expect, res.text[:400])
        return res.json()

    def _post(self, path, payload, login='test_cfg_hr', expect=200):
        self.authenticate(login, PWD)
        res = self.url_open(self.URL + path, data=json.dumps(payload),
                            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, expect, res.text[:400])
        return res.json()

    def test_80_only_hr_manager_can_read(self):
        self._get()
        for login in ('test_cfg_gv', 'test_cfg_nv'):
            self.authenticate(login, PWD)
            self.assertEqual(self.url_open(self.URL).status_code, 403, login)

    def test_81_get_returns_both_groups_with_sums(self):
        body = self._get()
        self.assertEqual(set(body['groups']), {'teacher', 'office'})
        for group, rows in body['groups'].items():
            crits = self.Criteria.sudo().with_context(
                active_test=False).search([('role_group', '=', group)],
                                          order='sequence, id')
            self.assertEqual([r['id'] for r in rows], crits.ids)
            self.assertAlmostEqual(
                body['weightSum'][group],
                sum(c.weight for c in crits if c.active), places=2)
        self.assertIn('draftCount', body)
        self.assertIn('grades', body)

    def test_82_save_criteria_rejects_bad_sum(self):
        body = self._get()
        rows = [dict(r) for r in body['groups']['teacher']]
        rows[0]['weight'] = rows[0]['weight'] + 5
        err = self._post('/criteria', {'group': 'teacher', 'criteria': rows},
                         expect=400)
        self.assertEqual(err['error'], 'rejected')
        self.assertIn('100', err['message'])
        # Rollback thật: trọng số trên DB không đổi.
        after = self._get()['groups']['teacher']
        self.assertEqual([r['weight'] for r in after],
                         [r['weight'] for r in body['groups']['teacher']])

    def test_83_save_criteria_applies_changes(self):
        body = self._get()
        rows = [dict(r) for r in body['groups']['teacher'] if r['active']]
        rows[0]['weight'] = rows[0]['weight'] + 5
        rows[1]['weight'] = rows[1]['weight'] - 5
        rows[0]['maxScore'] = 10
        rows[0]['name'] = rows[0]['name'] + ' (đã sửa)'
        saved = self._post('/criteria', {'group': 'teacher', 'criteria': rows})
        first = saved['groups']['teacher'][0]
        self.assertEqual(first['weight'], rows[0]['weight'])
        self.assertEqual(first['maxScore'], 10)
        self.assertTrue(first['name'].endswith('(đã sửa)'))
        self.assertAlmostEqual(saved['weightSum']['teacher'], 100.0, places=2)

    def test_84_add_new_question(self):
        body = self._get()
        rows = [dict(r) for r in body['groups']['office'] if r['active']]
        rows[0]['weight'] = rows[0]['weight'] - 10
        rows.append({'id': 0, 'name': 'Câu hỏi HR thêm', 'weight': 10,
                     'maxScore': 8, 'autoSource': 'none', 'guideline': 'Thử',
                     'anchorTop': 'cao', 'anchorMid': 'giữa',
                     'anchorLow': 'thấp', 'active': True})
        saved = self._post('/criteria', {'group': 'office', 'criteria': rows})
        added = [r for r in saved['groups']['office']
                 if r['name'] == 'Câu hỏi HR thêm']
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]['maxScore'], 8)
        self.assertTrue(added[0]['code'].startswith('o_'))

    def test_85_save_grading(self):
        saved = self._post('/grading', {
            'gradeA': 88, 'gradeB': 72, 'gradeC': 58, 'sessionsTarget': 50})
        self.assertEqual(saved['grades']['a'], 88)
        self.assertEqual(saved['params']['sessionsTarget'], 50)
        err = self._post('/grading', {
            'gradeA': 60, 'gradeB': 72, 'gradeC': 58, 'sessionsTarget': 50},
            expect=400)
        self.assertEqual(err['error'], 'rejected')

    def test_86_plain_user_cannot_write(self):
        self._post('/criteria', {'group': 'office', 'criteria': []},
                   login='test_cfg_nv', expect=403)
        self._post('/grading', {'gradeA': 85, 'gradeB': 70, 'gradeC': 55,
                                'sessionsTarget': 60},
                   login='test_cfg_gv', expect=403)
