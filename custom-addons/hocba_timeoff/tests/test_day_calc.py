# ============================================================
# Test Phase 6 — Tinh chỉnh tính ngày: nửa ngày (sáng/chiều) +
# loại trừ cuối tuần / ngày lễ khỏi số ngày nghỉ. Owner: Nhật Anh.
# ============================================================
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_timeoff.controllers.main import (
    _period_request_vals, _half_day_label,
)


@tagged('post_install', '-at_install')
class TestTimeoffDayCalc(TransactionCase):

    def setUp(self):
        super().setUp()
        self.dept = self.env['hr.department'].create({'name': 'Khối D (daycalc)'})
        self.emp = self.env['hr.employee'].create({
            'name': 'NV daycalc', 'department_id': self.dept.id,
            'x_employment_status': 'official', 'identification_id': '140000000001',
            'x_pit_code': '0000000001', 'x_social_insurance_no': '1400000000',
        })
        self.annual = self.env.ref('hocba_timeoff.hb_leave_type_annual')
        self.unpaid = self.env.ref('hocba_timeoff.hb_leave_type_unpaid')
        # Quỹ phép năm để tạo đơn annual hợp lệ.
        alloc = self.env['hr.leave.allocation'].create({
            'name': 'Quỹ daycalc', 'holiday_status_id': self.annual.id,
            'employee_id': self.emp.id, 'number_of_days': 12,
            'allocation_type': 'regular',
            'date_from': '2026-01-01', 'date_to': '2026-12-31',
        })
        if alloc.state != 'validate':
            alloc._action_validate()

    def _mk_leave(self, d_from, d_to=None, period=None, leave_type=None):
        lt = leave_type or self.annual
        vals = {
            'name': 'Nghỉ daycalc', 'holiday_status_id': lt.id,
            'employee_id': self.emp.id,
            'request_date_from': d_from, 'request_date_to': d_to or d_from,
        }
        vals.update(_period_request_vals(lt, d_from, period or ''))
        return self.env['hr.leave'].create(vals)

    # ---------- Cấu hình loại nghỉ ----------
    def test_leave_types_support_half_day(self):
        """Annual/Sick/Personal/Compensatory/Unpaid/Emergency bật half_day;
        Thai Sản/Buổi Dạy giữ 'day'."""
        for xmlid in ('hb_leave_type_annual', 'hb_leave_type_sick',
                      'hb_leave_type_personal', 'hb_leave_type_compensatory',
                      'hb_leave_type_unpaid', 'hb_leave_type_emergency'):
            lt = self.env.ref('hocba_timeoff.%s' % xmlid)
            self.assertEqual(lt.request_unit, 'half_day',
                             '%s phải hỗ trợ nửa ngày' % xmlid)
        for xmlid in ('hb_leave_type_maternity', 'hb_leave_type_teaching_off'):
            lt = self.env.ref('hocba_timeoff.%s' % xmlid)
            self.assertEqual(lt.request_unit, 'day',
                             '%s giữ nguyên nghỉ cả ngày' % xmlid)

    # ---------- Helper _period_request_vals ----------
    def test_period_vals_only_for_half_day_type(self):
        # Loại half_day + buổi sáng → co về 1 ngày + đặt cùng buổi.
        vals = _period_request_vals(self.annual, '2026-07-06', 'am')
        self.assertEqual(vals, {
            'request_date_to': '2026-07-06',
            'request_date_from_period': 'am',
            'request_date_to_period': 'am',
        })
        # Loại 'day' (Thai Sản) → không áp dụng nửa ngày.
        maternity = self.env.ref('hocba_timeoff.hb_leave_type_maternity')
        self.assertEqual(_period_request_vals(maternity, '2026-07-06', 'am'), {})
        # period rỗng / sai → cả ngày như cũ.
        self.assertEqual(_period_request_vals(self.annual, '2026-07-06', ''), {})
        self.assertEqual(_period_request_vals(self.annual, '2026-07-06', 'xx'), {})

    # ---------- Số ngày nửa buổi ----------
    def test_half_day_morning_counts_half(self):
        # 2026-07-06 là Thứ Hai (ngày làm việc).
        leave = self._mk_leave('2026-07-06', period='am')
        self.assertEqual(leave.number_of_days, 0.5)
        self.assertEqual(_half_day_label(leave), 'Sáng')

    def test_half_day_afternoon_counts_half(self):
        leave = self._mk_leave('2026-07-06', period='pm')
        self.assertEqual(leave.number_of_days, 0.5)
        self.assertEqual(_half_day_label(leave), 'Chiều')

    def test_full_day_on_half_day_type(self):
        # Không truyền period trên loại half_day → cả ngày (am→pm) = 1.0.
        leave = self._mk_leave('2026-07-06')
        self.assertEqual(leave.number_of_days, 1.0)
        self.assertEqual(_half_day_label(leave), '')

    # ---------- Loại trừ cuối tuần ----------
    def test_weekend_excluded(self):
        # Thứ Sáu 2026-07-03 → Thứ Hai 2026-07-06: T7/CN không tính → 2 ngày.
        leave = self._mk_leave('2026-07-03', '2026-07-06')
        self.assertEqual(leave.number_of_days, 2.0)

    # ---------- Loại trừ ngày lễ ----------
    def test_public_holiday_excluded(self):
        # Quốc Khánh seed 2026-09-02..03 (Tư, Năm) là nghỉ lễ toàn cục.
        # Đơn 2026-09-01 (Ba) → 2026-09-03 (Năm): chỉ 01/09 được tính = 1 ngày.
        leave = self._mk_leave('2026-09-01', '2026-09-03')
        self.assertEqual(leave.number_of_days, 1.0)
