"""Khoá lịch làm việc theo ngày (hb.work.day).

Quy tắc: chỉ thêm/sửa/xoá được ngày CHƯA ĐẾN. Ngày hôm nay và ngày đã qua bị
đóng băng — vì `hocba.attendance.policy.is_workday` đọc bảng này, nên ngày đã
diễn ra đã có bản ghi chấm công và lương tính theo lịch lúc đó; xoá/đổi ngược
lại là làm sai dữ liệu.
"""
from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestWorkDayLock(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.WorkDay = cls.env['hb.work.day']
        cls.today = fields.Date.context_today(cls.WorkDay)

    def _day(self, offset):
        return fields.Date.add(self.today, days=offset)

    def _past_workday(self, offset=-7):
        """Dựng bản ghi của ngày ĐÃ QUA — mô phỏng "HR khai từ tháng trước, giờ
        ngày đó đã trôi qua". Phải đi cửa sau (UPDATE thẳng) vì ORM đã chặn tạo
        ngày quá khứ; đây chính là dữ liệu hợp lệ mà guard phải bảo vệ."""
        rec = self.WorkDay.create({'date': self._day(30), 'name': 'Làm bù'})
        self.env.cr.execute(
            'UPDATE hb_work_day SET date = %s WHERE id = %s',
            (self._day(offset), rec.id))
        rec.invalidate_recordset()
        return rec

    # ---------------------------------------------------------------- create
    def test_create_future_ok(self):
        rec = self.WorkDay.create({'date': self._day(3), 'name': 'Làm bù'})
        self.assertTrue(rec.exists())
        self.assertFalse(rec.is_locked)

    def test_create_tomorrow_ok(self):
        """Ngày mai là mốc sớm nhất còn thêm được."""
        rec = self.WorkDay.create({'date': self._day(1)})
        self.assertFalse(rec.is_locked)
        self.assertEqual(self.WorkDay._first_editable_date(), self._day(1))

    def test_create_today_blocked(self):
        """Hôm nay cũng khoá: NV có thể đã chấm công từ sáng."""
        with self.assertRaises(UserError):
            self.WorkDay.create({'date': self.today, 'name': 'Làm bù'})

    def test_create_past_blocked(self):
        with self.assertRaises(UserError) as ctx:
            self.WorkDay.create({'date': self._day(-1), 'name': 'Làm bù'})
        self.assertIn('đã đến hoặc đã qua', str(ctx.exception))

    def test_create_multi_rejects_whole_batch(self):
        """1 ngày quá khứ trong lô → nổ cả lô, không tạo một phần."""
        with self.assertRaises(UserError):
            self.WorkDay.create([
                {'date': self._day(5)},
                {'date': self._day(-5)},
            ])

    # ----------------------------------------------------------------- write
    def test_write_future_ok(self):
        rec = self.WorkDay.create({'date': self._day(5), 'name': 'Làm bù'})
        rec.write({'date': self._day(6), 'name': 'Làm bù (đổi ngày)'})
        self.assertEqual(rec.date, self._day(6))
        self.assertEqual(rec.name, 'Làm bù (đổi ngày)')

    def test_write_past_record_blocked(self):
        rec = self._past_workday()
        self.assertTrue(rec.is_locked)
        with self.assertRaises(UserError) as ctx:
            rec.write({'name': 'Sửa ghi chú'})
        self.assertIn('đã diễn ra', str(ctx.exception))

    def test_write_today_record_blocked(self):
        rec = self._past_workday(offset=0)
        self.assertTrue(rec.is_locked)
        with self.assertRaises(UserError):
            rec.write({'name': 'Sửa ghi chú'})

    def test_write_move_to_past_blocked(self):
        """Không được lùi ngày chưa đến về ngày đã qua (lách guard)."""
        rec = self.WorkDay.create({'date': self._day(5)})
        with self.assertRaises(UserError) as ctx:
            rec.write({'date': self._day(-5)})
        self.assertIn('đã đến hoặc đã qua', str(ctx.exception))
        self.assertEqual(rec.date, self._day(5))

    # ---------------------------------------------------------------- unlink
    def test_unlink_future_ok(self):
        rec = self.WorkDay.create({'date': self._day(4)})
        rec.unlink()
        self.assertFalse(rec.exists())

    def test_unlink_past_blocked(self):
        rec = self._past_workday()
        with self.assertRaises(UserError) as ctx:
            rec.unlink()
        self.assertIn('đã diễn ra', str(ctx.exception))
        self.assertTrue(rec.exists())

    def test_unlink_today_blocked(self):
        rec = self._past_workday(offset=0)
        with self.assertRaises(UserError):
            rec.unlink()
        self.assertTrue(rec.exists())

    def test_unlink_batch_with_one_past_blocked(self):
        """Xoá lô có 1 ngày đã qua → chặn cả lô, ngày tương lai cũng còn."""
        future = self.WorkDay.create({'date': self._day(8)})
        past = self._past_workday(offset=-3)
        with self.assertRaises(UserError):
            (future | past).unlink()
        self.assertTrue(future.exists())
        self.assertTrue(past.exists())

    # ------------------------------------------------- hệ quả với chấm công
    def test_locked_day_still_counts_as_workday(self):
        """Ngày đã qua vẫn là ngày làm việc — khoá chỉ chặn GHI, không đổi
        cách đọc lịch (chấm công/lương của ngày đó giữ nguyên)."""
        rec = self._past_workday(offset=-6)
        policy = self.env['hocba.attendance.policy'].get_policy()
        self.assertTrue(policy.is_workday(rec.date))
