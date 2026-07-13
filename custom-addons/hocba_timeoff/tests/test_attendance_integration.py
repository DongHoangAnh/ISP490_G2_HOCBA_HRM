from datetime import date, datetime

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


class _LeaveAttMixin(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Att = cls.env['hocba.attendance']
        cls.Leave = cls.env['hr.leave']
        cls.annual = cls.env.ref('hocba_timeoff.hb_leave_type_annual')
        cls.unpaid = cls.env.ref('hocba_timeoff.hb_leave_type_unpaid')
        cls.emp = cls.env['hr.employee'].create({
            'name': 'NV Tích Hợp', 'x_employment_status': 'official',
            'identification_id': '190000000001',
            'x_pit_code': '0000000001',            # MST TNCN 10 số (BR-010)
            'x_social_insurance_no': '1900000000',  # Số sổ BHXH (BR-010)
        })

    def _allocate(self, ltype, year, days=30):
        """Cấp quỹ (đã duyệt) cho loại nghỉ requires_allocation, phủ cả năm."""
        alloc = self.env['hr.leave.allocation'].sudo().create({
            'name': 'Quỹ test %s' % ltype.name,
            'holiday_status_id': ltype.id,
            'employee_id': self.emp.id,
            'number_of_days': days,
            'allocation_type': 'regular',
            'date_from': '%d-01-01' % year,
            'date_to': '%d-12-31' % year,
        })
        if alloc.state != 'validate':
            alloc.sudo()._action_validate()
        return alloc

    def _mk_leave(self, ltype, d_from, d_to, half=None, validate=True):
        if ltype.requires_allocation:
            self._allocate(ltype, fields.Date.to_date(d_from).year)
        vals = {
            'name': 'Nghỉ', 'employee_id': self.emp.id,
            'holiday_status_id': ltype.id,
            'request_date_from': d_from, 'request_date_to': d_to,
        }
        if half:
            vals.update({'request_unit_half': True,
                         'request_date_from_period': half,
                         'request_date_to_period': half})
        lv = self.Leave.sudo().create(vals)
        if validate:
            lv.sudo().action_approve()
            if lv.state != 'validate':
                lv.sudo()._action_validate()
        return lv


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestAttendanceIntegrationBase(TransactionCase):

    def test_fields_and_statuses_exist(self):
        Att = self.env['hocba.attendance']
        for f in ('source', 'leave_id', 'leave_half', 'leave_is_paid'):
            self.assertIn(f, Att._fields, 'thiếu field %s' % f)
        Status = self.env['hocba.attendance.status']
        self.assertTrue(Status.search([('code', '=', 'on_leave_paid')]))
        self.assertTrue(Status.search([('code', '=', 'on_leave_unpaid')]))


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestIsWorkdayExtra(TransactionCase):

    def test_extra_workday_counts_as_workday(self):
        policy = self.env['hocba.attendance.policy'].get_policy()
        # 2026-07-18 là Thứ 7 (cuối tuần) -> mặc định không phải ngày làm
        sat = datetime(2026, 7, 18, 8, 0, 0)
        self.assertFalse(policy.is_workday(sat))
        self.env['hb.work.day'].create({'date': date(2026, 7, 18), 'name': 'Làm bù'})
        self.assertTrue(policy.is_workday(sat))
        # Thứ 7 khác chưa đánh dấu vẫn False
        self.assertFalse(policy.is_workday(datetime(2026, 7, 25, 8, 0, 0)))


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestFullDayBlock(_LeaveAttMixin):

    def test_block_check_in_on_full_day_leave(self):
        today = fields.Date.context_today(self.Att)
        self._mk_leave(self.annual, today, today)
        with self.assertRaises(UserError) as ctx:
            self.Att._assert_check_allowed(self.emp, 'in')
        self.assertEqual(str(ctx.exception), 'on_approved_leave')

    def test_no_block_without_leave(self):
        try:
            self.Att._assert_check_allowed(self.emp, 'in')
        except UserError as ex:
            self.assertNotEqual(str(ex), 'on_approved_leave')

    def test_teaching_off_does_not_block(self):
        toff = self.env.ref('hocba_timeoff.hb_leave_type_teaching_off')
        today = fields.Date.context_today(self.Att)
        # tạo đơn nghỉ buổi dạy phủ hôm nay (request_unit='day' nhưng KHÔNG chặn)
        self._mk_leave(toff, today, today)
        try:
            self.Att._assert_check_allowed(self.emp, 'in')
        except UserError as ex:
            self.assertNotEqual(str(ex), 'on_approved_leave')


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestGenerateFullDay(_LeaveAttMixin):

    def _records_for(self, leave):
        return self.Att.sudo().search([('leave_id', '=', leave.id), ('source', '=', 'leave')])

    def test_generate_paid_full_day(self):
        d = date(2026, 7, 15)  # Thứ 4
        lv = self._mk_leave(self.annual, d, d)
        recs = self._records_for(lv)
        self.assertEqual(len(recs), 1)
        self.assertEqual(recs.work_credit, 1.0)
        self.assertTrue(recs.leave_is_paid)
        self.assertEqual(recs.status_id.code, 'on_leave_paid')
        self.assertEqual(recs.date, d)

    def test_generate_unpaid_full_day(self):
        d = date(2026, 7, 16)  # Thứ 5
        lv = self._mk_leave(self.unpaid, d, d)
        recs = self._records_for(lv)
        self.assertEqual(recs.work_credit, 0.0)
        self.assertFalse(recs.leave_is_paid)
        self.assertEqual(recs.status_id.code, 'on_leave_unpaid')

    def test_multiday_skips_weekend(self):
        # 2026-07-17 (T6) -> 2026-07-20 (T2): bỏ T7 18, CN 19
        lv = self._mk_leave(self.annual, date(2026, 7, 17), date(2026, 7, 20))
        days = self._records_for(lv).mapped('date')
        self.assertEqual(sorted(days), [date(2026, 7, 17), date(2026, 7, 20)])

    def test_teaching_off_not_generated(self):
        toff = self.env.ref('hocba_timeoff.hb_leave_type_teaching_off')
        d = date(2026, 7, 15)
        lv = self._mk_leave(toff, d, d)
        self.assertFalse(self._records_for(lv))   # session-leave không sinh bản ghi

    def test_retroactive_conflict_keeps_checkin(self):
        d = date(2026, 7, 22)  # Thứ 4
        real = self.Att.sudo().create({
            'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 22, 1, 0, 0)})  # ~8h VN
        lv = self._mk_leave(self.annual, d, d)
        self.assertEqual(real.source, 'checkin')          # không bị ghi đè
        self.assertFalse(self._records_for(lv))           # không sinh thêm
        self.assertIn('rà soát', (real.notes or '').lower())


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestHalfDay(_LeaveAttMixin):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Ghim tz: _compute_work_metrics đọc giờ local qua tz của env user.
        # Không ghim thì assertion late/credit đổi kết quả theo máy chạy test.
        cls.env.user.tz = 'Asia/Ho_Chi_Minh'

    def _mk_unpaid_half_type(self):
        # `hr.leave.request_unit_half` là compute store theo request_unit của
        # LOẠI nghỉ -> loại seed "Nghỉ Không Lương" (request_unit='day') không
        # thể tạo đơn nửa ngày. Dựng loại không lương hỗ trợ nửa ngày để test
        # hành vi stamp/công (rollback theo transaction).
        return self.env['hr.leave.type'].sudo().create({
            'name': 'Không Lương Nửa Ngày (test)', 'time_type': 'leave',
            'requires_allocation': False, 'leave_validation_type': 'hr',
            'unpaid': True, 'request_unit': 'half_day'})

    def test_half_day_paid_note_and_credit(self):
        d = date(2026, 7, 15)  # Thứ 4
        self._mk_leave(self.annual, d, d, half='am')  # nghỉ SÁNG có lương
        # NV làm buổi chiều 14h00->17h30 VN (3.5h). Chuẩn CẢ ngày (base) sẽ cho:
        # late 270' (14h > 9h30), afternoon 0 (3.5h < 6h) -> test này chứng minh
        # nhánh override chấm buổi làm theo chuẩn NỬA ngày:
        #   - late = 0 (buổi sáng nghỉ phép), morning = 0.5 (có lương)
        #   - afternoon = 0.5 vì 3.5h >= std/2 - margin/2 = 4h - 1h = 3h
        #   - expected_check_out = ci + std/2 = 18h VN -> early 30',
        #     missing 240' - 210' = 30'
        rec = self.Att.sudo().create({
            'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 15, 7, 0, 0),      # 14h00 VN
            'check_out': datetime(2026, 7, 15, 10, 30, 0)})  # 17h30 VN
        rec._stamp_half_day_leave()
        self.assertEqual(rec.leave_half, 'am')
        self.assertIn('nửa buổi sáng', (rec.notes or '').lower())
        self.assertEqual(rec.late_minutes, 0)
        self.assertEqual(rec.morning_credit, 0.5)
        self.assertEqual(rec.afternoon_credit, 0.5)
        self.assertEqual(rec.work_credit, 1.0)
        self.assertEqual(rec.early_leave_minutes, 30)
        self.assertEqual(rec.missing_minutes, 30)

    def test_half_day_unpaid_credit(self):
        d = date(2026, 7, 16)  # Thứ 5
        self._mk_leave(self._mk_unpaid_half_type(), d, d, half='pm')
        # NV làm buổi sáng 8h00->12h00 VN rồi nghỉ CHIỀU không lương:
        # base morning = 0.5 (8h <= cutoff 10h), nhánh 'pm' ép afternoon = 0
        # (không lương) + xoá phạt về sớm/thiếu giờ (buổi chiều nghỉ phép).
        rec = self.Att.sudo().create({
            'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 16, 1, 0, 0),    # 8h00 VN
            'check_out': datetime(2026, 7, 16, 5, 0, 0)})  # 12h00 VN
        rec._stamp_half_day_leave()
        self.assertEqual(rec.leave_half, 'pm')
        self.assertEqual(rec.morning_credit, 0.5)
        self.assertEqual(rec.afternoon_credit, 0.0)
        self.assertEqual(rec.work_credit, 0.5)
        self.assertEqual(rec.early_leave_minutes, 0)
        self.assertEqual(rec.missing_minutes, 0)

    def test_half_day_unpaid_pm_forced_even_if_present(self):
        d = date(2026, 7, 16)  # Thứ 5
        self._mk_leave(self._mk_unpaid_half_type(), d, d, half='pm')
        # NV có đơn nghỉ CHIỀU không lương nhưng thực tế ở lại 8h->17h VN
        # (9h >= 6h: base sẽ cho afternoon 0.5). CHỦ ĐÍCH: buổi nghỉ tính theo
        # ĐƠN đã duyệt, không theo hiện diện vật lý (dữ liệu nghỉ thắng hiện
        # diện); nếu lệch thực tế thì HR đối soát thủ công.
        rec = self.Att.sudo().create({
            'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 16, 1, 0, 0),     # 8h00 VN
            'check_out': datetime(2026, 7, 16, 10, 0, 0)})  # 17h00 VN
        rec._stamp_half_day_leave()
        self.assertEqual(rec.leave_half, 'pm')
        self.assertEqual(rec.afternoon_credit, 0.0)
        self.assertEqual(rec.work_credit, 0.5)

    def test_retroactive_half_day_stamps_existing(self):
        # NV đã chấm công TRƯỚC, đơn nửa ngày duyệt SAU -> bản ghi có sẵn
        # phải được stamp qua _generate_leave_attendance (nhánh nửa ngày).
        d = date(2026, 7, 17)  # Thứ 6
        rec = self.Att.sudo().create({
            'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 17, 1, 0, 0),    # 8h00 VN
            'check_out': datetime(2026, 7, 17, 5, 0, 0)})  # 12h00 VN
        self._mk_leave(self.annual, d, d, half='pm')       # duyệt sau khi đã chấm
        self.assertEqual(rec.leave_half, 'pm')
        self.assertIn('nửa buổi chiều', (rec.notes or '').lower())
        self.assertTrue(rec.leave_is_paid)
        # sáng 0.5 làm thật + chiều 0.5 nghỉ có lương
        self.assertEqual(rec.work_credit, 1.0)


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestReverseSync(_LeaveAttMixin):

    def _leave_recs(self, lv):
        return self.Att.sudo().search([('leave_id', '=', lv.id), ('source', '=', 'leave')])

    def test_refuse_removes_generated(self):
        d = date(2026, 7, 15)
        lv = self._mk_leave(self.annual, d, d)
        self.assertTrue(self._leave_recs(lv))
        lv.sudo().action_refuse()
        self.assertFalse(self._leave_recs(lv))

    def test_refuse_keeps_real_checkin_unlinks(self):
        d = date(2026, 7, 16)
        lv = self._mk_leave(self.annual, d, d, half='pm')
        real = self.Att.sudo().create({'employee_id': self.emp.id,
            'check_in': datetime(2026, 7, 16, 1, 0, 0)})  # ~8h VN
        real._stamp_half_day_leave()
        self.assertEqual(real.leave_id, lv)
        self.assertIn('nửa buổi chiều', (real.notes or ''))
        lv.sudo().action_refuse()
        self.assertTrue(real.exists())            # công thật giữ nguyên
        self.assertFalse(real.leave_id)           # chỉ gỡ liên kết
        self.assertFalse(real.leave_half)
        self.assertNotIn('nửa buổi', (real.notes or ''))
