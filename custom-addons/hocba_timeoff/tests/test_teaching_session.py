# ============================================================
# Test Step 1 — Model hocba.teaching.session + _import_from_cms.
# Lịch dạy là nguồn chính trong Neon; CMS chỉ import 1 lần làm dữ liệu mẫu.
# Mock cms_connector để không phụ thuộc MySQL thật. Owner: Nhật Anh.
# ============================================================
from datetime import date
from unittest.mock import patch

from odoo.tests.common import TransactionCase
from odoo.tests import tagged

# Hàm đọc CMS (read-only) được import động trong model — patch tại nguồn.
CONNECTOR = 'odoo.addons.hocba_attendance.utils.cms_connector.get_sessions_for_tutor'


def _raw(sid, d, cls='HSK4-A'):
    """1 row giả lập như trả về từ CMS MySQL (DictCursor)."""
    return {
        'id': sid, 'class_id': 5, 'class_name': cls,
        'date': d, 'start_time': '08:00:00', 'end_time': '10:00:00',
        'status': 'PLANING', 'role_type': 'TEACHER',
    }


@tagged('post_install', '-at_install')
class TestTeachingSession(TransactionCase):

    def setUp(self):
        super().setUp()
        self.teacher = self.env['hr.employee'].create({
            'name': 'GV Import A', 'x_cms_user_id': 'CMS_T1',
        })
        self.Session = self.env['hocba.teaching.session']

    # ---------- Model & default ----------
    def test_create_sets_original_employee_and_planned(self):
        """Tạo buổi: state mặc định 'planned', original_employee_id = employee."""
        s = self.Session.create({
            'cms_session_id': 'S1', 'employee_id': self.teacher.id,
            'class_name': 'HSK4-A', 'session_date': '2026-07-06',
            'start_time': '08:00', 'end_time': '10:00',
        })
        self.assertEqual(s.state, 'planned')
        self.assertEqual(s.original_employee_id, self.teacher)

    # ---------- Import từ CMS ----------
    def test_import_from_cms_creates_sessions(self):
        """Import map x_cms_user_id → employee, set original + planned."""
        def side(tid, day):
            if tid == 'CMS_T1' and day == date(2026, 7, 6):
                return [_raw(1001, day)]
            return []
        with patch(CONNECTOR, side_effect=side):
            self.Session._import_from_cms('2026-07-06', '2026-07-06')

        s = self.Session.search([('cms_session_id', '=', '1001')])
        self.assertEqual(len(s), 1)
        self.assertEqual(s.employee_id, self.teacher)
        self.assertEqual(s.original_employee_id, self.teacher)
        self.assertEqual(s.state, 'planned')
        self.assertEqual(s.class_name, 'HSK4-A')
        self.assertEqual(str(s.session_date), '2026-07-06')
        self.assertEqual(s.start_time, '08:00')

    def test_import_idempotent(self):
        """Chạy import 2 lần cùng dữ liệu → không nhân đôi (upsert theo cms_session_id)."""
        def side(tid, day):
            if tid == 'CMS_T1' and day == date(2026, 7, 6):
                return [_raw(1001, day)]
            return []
        with patch(CONNECTOR, side_effect=side):
            self.Session._import_from_cms('2026-07-06', '2026-07-06')
            self.Session._import_from_cms('2026-07-06', '2026-07-06')

        self.assertEqual(
            self.Session.search_count([('cms_session_id', '=', '1001')]), 1)
