from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.tests.common import TransactionCase
from odoo.tests import tagged
from odoo.exceptions import AccessError, ValidationError

from odoo.addons.hocba_hrm.controllers.main import (
    _honor_board, _honor_create, _honor_archive)


@tagged('post_install', '-at_install')
class TestHonorBoard(TransactionCase):
    """Bảng vinh danh trên dashboard chung — spec 2026-08-09 §5.3."""

    def setUp(self):
        super().setUp()
        self.hr = self.env['res.users'].create({
            'name': 'HR Honor', 'login': 'hr_honor',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id,
                                  self.env.ref('hr.group_hr_user').id])]})
        self.plain = self.env['res.users'].create({
            'name': 'Plain Honor', 'login': 'plain_honor',
            'group_ids': [(6, 0, [self.env.ref('base.group_user').id])]})
        self.dept = self.env['hr.department'].create({'name': 'Phòng Vinh danh'})
        self.emp = self.env['hr.employee'].create({
            'name': 'Ngôi Sao', 'x_employee_code': 'EMP-HONOR-1',
            'department_id': self.dept.id})
        self.today = fields.Date.context_today(self.env['hb.honor.entry'])

    def _env(self, user):
        return self.env(user=user)

    def _entry(self, when=None, **kw):
        vals = {'employee_id': self.emp.id, 'title': 'Nhân viên xuất sắc',
                'date_awarded': when or self.today}
        vals.update(kw)
        return self.env['hb.honor.entry'].create(vals)

    def _period(self, d):
        return '%04d-%02d' % (d.year, d.month)

    # --- chọn kỳ ---
    def test_board_current_period(self):
        self._entry()
        out = _honor_board(self._env(self.plain))
        self.assertEqual(out['period'], self._period(self.today))
        self.assertTrue(out['isCurrent'])
        self.assertEqual([e['title'] for e in out['entries']],
                         ['Nhân viên xuất sắc'])
        self.assertEqual(out['entries'][0]['empName'], 'Ngôi Sao')
        self.assertEqual(out['entries'][0]['dep'], 'Phòng Vinh danh')

    def test_board_falls_back_to_previous_period(self):
        # Đầu tháng chưa vinh danh ai → bảng vẫn phải có nội dung, nếu không
        # khung "nhìn thấy đầu tiên" thành ô chết.
        last = self.today - relativedelta(months=1)
        self._entry(when=last, title='Kỳ trước')
        out = _honor_board(self._env(self.plain))
        self.assertEqual(out['period'], self._period(last))
        self.assertFalse(out['isCurrent'])
        self.assertEqual([e['title'] for e in out['entries']], ['Kỳ trước'])

    def test_board_empty_when_no_entries(self):
        out = _honor_board(self._env(self.plain))
        self.assertEqual(out['entries'], [])
        self.assertEqual(out['period'], self._period(self.today))
        self.assertTrue(out['isCurrent'])

    def test_board_ignores_archived_entry(self):
        e = self._entry()
        e.active = False
        self.assertEqual(_honor_board(self._env(self.plain))['entries'], [])

    def test_board_ranked_entries_before_unranked(self):
        # rank=0 nghĩa là "không xếp hạng" — không được leo lên trên hạng 1.
        self._entry(title='Không hạng', rank=0)
        self._entry(title='Hạng nhì', rank=2)
        self._entry(title='Hạng nhất', rank=1)
        titles = [e['title'] for e in _honor_board(self._env(self.hr))['entries']]
        self.assertEqual(titles[:2], ['Hạng nhất', 'Hạng nhì'])
        self.assertEqual(titles[2], 'Không hạng')

    # --- ranking từ đợt đánh giá ---
    def _confirmed_eval(self, emp, score_ratio, when=None):
        crit = self.env['hr.promotion.criteria'].create({
            'name': 'Tiêu chí %s' % emp.name, 'code': 'hb_%s' % emp.id,
            'weight': 100, 'max_score': 10})
        ev = self.env['hr.promotion.evaluation'].create({
            'employee_id': emp.id,
            'eval_date': when or self.today,
            'verdict_final': 'qualified',
            'line_ids': [(0, 0, {'criteria_id': crit.id,
                                 'score': 10 * score_ratio})]})
        ev.action_confirm()
        return ev

    def test_ranking_hides_score_from_plain_user(self):
        self._confirmed_eval(self.emp, 0.9)
        out = _honor_board(self._env(self.plain))
        self.assertEqual(len(out['ranking']), 1)
        self.assertEqual(out['ranking'][0]['empName'], 'Ngôi Sao')
        self.assertNotIn('score', out['ranking'][0])
        self.assertFalse(out['canManage'])

    def test_ranking_shows_score_to_manager(self):
        self._confirmed_eval(self.emp, 0.9)
        out = _honor_board(self._env(self.hr))
        self.assertTrue(out['canManage'])
        self.assertAlmostEqual(out['ranking'][0]['score'], 90.0, places=0)

    def test_ranking_only_qualified_confirmed_in_period(self):
        other = self.env['hr.employee'].create({
            'name': 'Chưa đạt', 'x_employee_code': 'EMP-HONOR-2'})
        draft = self.env['hr.employee'].create({
            'name': 'Còn nháp', 'x_employee_code': 'EMP-HONOR-3'})
        old = self.env['hr.employee'].create({
            'name': 'Kỳ cũ', 'x_employee_code': 'EMP-HONOR-4'})
        self._confirmed_eval(self.emp, 0.9)
        ev_other = self._confirmed_eval(other, 0.5)
        ev_other.verdict_final = 'not_yet'
        crit = self.env['hr.promotion.criteria'].create({
            'name': 'C draft', 'code': 'hb_draft', 'weight': 100,
            'max_score': 10})
        self.env['hr.promotion.evaluation'].create({
            'employee_id': draft.id, 'eval_date': self.today,
            'verdict_final': 'qualified',
            'line_ids': [(0, 0, {'criteria_id': crit.id, 'score': 10})]})
        self._confirmed_eval(old, 1.0, when=self.today - relativedelta(months=2))
        names = [r['empName'] for r in
                 _honor_board(self._env(self.hr))['ranking']]
        self.assertEqual(names, ['Ngôi Sao'])

    # --- HR thêm / gỡ ---
    def test_honor_create_requires_hr(self):
        with self.assertRaises(AccessError):
            _honor_create(self._env(self.plain), {
                'employeeId': self.emp.id, 'title': 'Trộm vinh danh'})

    def test_honor_create_by_hr_appears_on_board(self):
        out = _honor_create(self._env(self.hr), {
            'employeeId': self.emp.id, 'title': 'Sáng kiến của năm',
            'category': 'achievement', 'description': 'Rút gọn quy trình',
            'rank': 1})
        titles = [e['title'] for e in out['entries']]
        self.assertIn('Sáng kiến của năm', titles)
        row = next(e for e in out['entries'] if e['title'] == 'Sáng kiến của năm')
        self.assertEqual(row['source'], 'manual')
        self.assertEqual(row['rank'], 1)

    def test_honor_create_rejects_unknown_employee(self):
        with self.assertRaisesRegex(ValidationError, 'Không tìm thấy nhân viên'):
            _honor_create(self._env(self.hr), {
                'employeeId': 999999, 'title': 'X'})

    def test_honor_create_rejects_blank_title(self):
        with self.assertRaisesRegex(ValidationError, 'Danh hiệu'):
            _honor_create(self._env(self.hr), {
                'employeeId': self.emp.id, 'title': '  '})

    def test_honor_archive_requires_hr(self):
        e = self._entry()
        with self.assertRaises(AccessError):
            _honor_archive(self._env(self.plain), e.id)

    def test_honor_archive_removes_from_board(self):
        e = self._entry()
        out = _honor_archive(self._env(self.hr), e.id)
        self.assertEqual(out['entries'], [])
        self.assertFalse(e.active)

    def test_honor_archive_unknown_id(self):
        with self.assertRaisesRegex(ValidationError, 'Không tìm thấy'):
            _honor_archive(self._env(self.hr), 999999)
