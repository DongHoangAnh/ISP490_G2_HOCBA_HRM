# ============================================================
# Test Step 2 — Model hocba.leave.session.resolution.
# Mỗi buổi dạy trùng đơn nghỉ = 1 dòng xử lý: 'cả lớp nghỉ' (class_off) hoặc
# 'đổi GV dạy thay' (substitute). Owner: Nhật Anh.
# Spec: 2026-06-25-timeoff-teacher-leave-teaching-conflict-design §3.2.
# ============================================================
from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
from odoo.tools import mute_logger
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install')
class TestLeaveResolution(TransactionCase):

    def setUp(self):
        super().setUp()
        self.teacher = self.env['hr.employee'].create({
            'name': 'GV Nghỉ', 'x_cms_user_id': 'CMS_R1',
        })
        self.sub = self.env['hr.employee'].create({
            'name': 'GV Thay', 'x_cms_user_id': 'CMS_R2',
        })
        self.session = self.env['hocba.teaching.session'].create({
            'cms_session_id': 'R-S1', 'employee_id': self.teacher.id,
            'class_name': 'HSK5-B', 'session_date': '2026-07-06',
            'start_time': '08:00', 'end_time': '10:00',
        })
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')
        self.leave = self.env['hr.leave'].create({
            'name': 'Nghỉ GV', 'holiday_status_id': self.unpaid.id,
            'employee_id': self.teacher.id,
            'request_date_from': '2026-07-06', 'request_date_to': '2026-07-06',
        })
        self.Res = self.env['hocba.leave.session.resolution']

    def _vals(self, **over):
        vals = {'leave_id': self.leave.id, 'session_id': self.session.id}
        vals.update(over)
        return vals

    # ---------- Default state theo loại xử lý ----------
    def test_class_off_defaults_accepted(self):
        """'Cả lớp nghỉ' không cần GV thay; state mặc định 'accepted'."""
        r = self.Res.create(self._vals(resolution='class_off'))
        self.assertEqual(r.state, 'accepted')
        self.assertFalse(r.substitute_id)

    def test_substitute_defaults_pending(self):
        """'Đổi GV thay' chờ GV thay đồng ý; state mặc định 'pending'."""
        r = self.Res.create(self._vals(
            resolution='substitute', substitute_id=self.sub.id))
        self.assertEqual(r.state, 'pending')
        self.assertEqual(r.substitute_id, self.sub)

    # ---------- Ràng buộc GV thay ----------
    def test_substitute_requires_substitute_id(self):
        with self.assertRaises(ValidationError):
            self.Res.create(self._vals(resolution='substitute'))

    def test_substitute_cannot_be_self(self):
        with self.assertRaises(ValidationError):
            self.Res.create(self._vals(
                resolution='substitute', substitute_id=self.teacher.id))

    # ---------- Không trùng buổi trong cùng đơn ----------
    def test_no_duplicate_session_per_leave(self):
        self.Res.create(self._vals(resolution='class_off'))
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.env.cr.savepoint():
                self.Res.create(self._vals(resolution='class_off'))
                self.env.flush_all()
