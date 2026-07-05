# ============================================================
# Test Step 3 — Dò xung đột lịch dạy + áp dụng cách xử lý khi tạo đơn.
# Kiểm logic ở mức helper controller (không cần HTTP). Owner: Nhật Anh.
# Spec: 2026-06-25-timeoff-teacher-leave-teaching-conflict-design §5,§6.
# ============================================================
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _find_teaching_conflicts, _apply_resolutions,
)


@tagged('post_install', '-at_install')
class TestTeachingConflict(TransactionCase):

    def setUp(self):
        super().setUp()
        self.teacher = self.env['hr.employee'].create({
            'name': 'GV C1', 'x_cms_user_id': 'CMS_C1'})
        self.sub = self.env['hr.employee'].create({
            'name': 'GV C2', 'x_cms_user_id': 'CMS_C2'})
        self.plain = self.env['hr.employee'].create({'name': 'NV thường C'})

        Session = self.env['hocba.teaching.session']
        self.s1 = Session.create({
            'cms_session_id': 'C-1', 'employee_id': self.teacher.id,
            'class_name': 'L1', 'session_date': '2026-07-06',
            'start_time': '08:00', 'end_time': '10:00'})
        self.s2 = Session.create({
            'cms_session_id': 'C-2', 'employee_id': self.teacher.id,
            'class_name': 'L2', 'session_date': '2026-07-07',
            'start_time': '08:00', 'end_time': '10:00'})
        # Buổi đã hủy bởi đơn khác → KHÔNG tính là xung đột mới.
        self.s_cancel = Session.create({
            'cms_session_id': 'C-3', 'employee_id': self.teacher.id,
            'class_name': 'L3', 'session_date': '2026-07-06',
            'start_time': '13:00', 'end_time': '15:00', 'state': 'cancelled'})
        # Buổi của GV khác cùng ngày → không thuộc phạm vi.
        Session.create({
            'cms_session_id': 'C-9', 'employee_id': self.sub.id,
            'class_name': 'LX', 'session_date': '2026-07-06',
            'start_time': '08:00', 'end_time': '10:00'})

        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')

    def _leave(self, d_from='2026-07-06', d_to='2026-07-07', emp=None):
        return self.env['hr.leave'].create({
            'name': 'Nghỉ', 'holiday_status_id': self.unpaid.id,
            'employee_id': (emp or self.teacher).id,
            'request_date_from': d_from, 'request_date_to': d_to})

    # ---------- Dò xung đột ----------
    def test_finds_planned_sessions_in_range(self):
        c = _find_teaching_conflicts(self.env, self.teacher, '2026-07-06', '2026-07-07')
        self.assertEqual(c, self.s1 | self.s2)

    def test_excludes_cancelled_and_other_employee(self):
        c = _find_teaching_conflicts(self.env, self.teacher, '2026-07-06', '2026-07-06')
        self.assertEqual(c, self.s1)               # s_cancel & buổi GV khác bị loại

    def test_non_teacher_has_no_conflicts(self):
        c = _find_teaching_conflicts(self.env, self.plain, '2026-07-06', '2026-07-07')
        self.assertFalse(c)

    # ---------- Áp dụng cách xử lý ----------
    def test_apply_creates_rows_for_each_conflict(self):
        leave = self._leave()
        conflicts = self.s1 | self.s2
        rows = _apply_resolutions(self.env, leave, conflicts, [
            {'sessionId': self.s1.id, 'type': 'class_off'},
            {'sessionId': self.s2.id, 'type': 'substitute',
             'substituteId': self.sub.id},
        ])
        self.assertEqual(len(rows), 2)
        r1 = rows.filtered(lambda r: r.session_id == self.s1)
        r2 = rows.filtered(lambda r: r.session_id == self.s2)
        self.assertEqual(r1.resolution, 'class_off')
        self.assertEqual(r1.state, 'accepted')
        self.assertEqual(r2.resolution, 'substitute')
        self.assertEqual(r2.substitute_id, self.sub)
        self.assertEqual(r2.state, 'pending')

    def test_apply_blocks_when_session_unresolved(self):
        leave = self._leave()
        conflicts = self.s1 | self.s2
        with self.assertRaises(ValidationError):
            _apply_resolutions(self.env, leave, conflicts, [
                {'sessionId': self.s1.id, 'type': 'class_off'},
            ])

    def test_apply_blocks_substitute_without_teacher(self):
        leave = self._leave('2026-07-06', '2026-07-06')
        conflicts = self.s1
        with self.assertRaises(ValidationError):
            _apply_resolutions(self.env, leave, conflicts, [
                {'sessionId': self.s1.id, 'type': 'substitute'},
            ])
