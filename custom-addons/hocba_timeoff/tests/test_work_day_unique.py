"""Ràng buộc duy nhất (date, company_id) của hb.work.day.

Bảng này là nguồn chân lý cho `hocba.attendance.policy.is_workday` và
`_count_working_days` (số ngày trừ quỹ phép). Một ngày bị khai hai lần thì mọi
phép đếm ngày làm việc đọc bảng này đều lệch — nên ràng buộc phải nằm ở
Postgres, không chỉ ở Python: `@api.constrains` không chặn được INSERT thẳng
(migration, script dọn dữ liệu, `cr.execute`).

Odoo 19 bỏ `_sql_constraints`: khai theo API cũ chỉ log WARNING rồi bỏ qua,
Postgres không có constraint nào cả. Test dưới đây soi thẳng `pg_constraint`
để bắt đúng kiểu hồi quy đó.
"""
import psycopg2

from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger

CONSTRAINT_NAME = 'hb_work_day_uniq_work_day_date'


@tagged('post_install', '-at_install', 'hocba_timeoff')
class TestWorkDayUnique(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.WorkDay = cls.env['hb.work.day']
        cls.today = fields.Date.context_today(cls.WorkDay)

    def _day(self, offset):
        return fields.Date.add(self.today, days=offset)

    # ------------------------------------------------- constraint có thật chưa
    def test_constraint_exists_in_postgres(self):
        """Constraint phải tồn tại trong pg_constraint và là UNIQUE (date, company_id).

        Đây là test bắt hồi quy `_sql_constraints`: nếu ai đó quay lại API cũ,
        module vẫn load bình thường (chỉ có WARNING) nhưng dòng này sẽ đỏ.
        """
        self.env.cr.execute("""
            SELECT contype, pg_get_constraintdef(oid)
              FROM pg_constraint
             WHERE conrelid = 'hb_work_day'::regclass
               AND conname = %s
        """, (CONSTRAINT_NAME,))
        row = self.env.cr.fetchone()
        self.assertTrue(
            row, "Thiếu constraint %s trên bảng hb_work_day — trùng ngày sẽ lọt "
                 "qua và số ngày làm việc bị đếm sai." % CONSTRAINT_NAME)
        contype, definition = row
        self.assertEqual(contype, 'u')
        self.assertIn('date', definition)
        self.assertIn('company_id', definition)

    # ------------------------------------------------------------- qua ORM
    def test_create_duplicate_date_rejected(self):
        day = self._day(10)
        self.WorkDay.create({'date': day, 'name': 'Làm bù'})
        with self.assertRaises(psycopg2.IntegrityError), \
                mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            self.WorkDay.create({'date': day, 'name': 'Làm bù (khai lại)'})
        self.env.invalidate_all()

    def test_write_onto_existing_date_rejected(self):
        """Không lách được bằng cách tạo ngày khác rồi đổi date về ngày đã có."""
        day = self._day(11)
        self.WorkDay.create({'date': day, 'name': 'Làm bù'})
        other = self.WorkDay.create({'date': self._day(12), 'name': 'Làm bù 2'})
        with self.assertRaises(psycopg2.IntegrityError), \
                mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            other.write({'date': day})
        self.env.invalidate_all()

    # ------------------------------------------------------ qua SQL thẳng
    def test_raw_insert_duplicate_rejected(self):
        """INSERT thẳng cũng bị chặn — chứng minh ràng buộc nằm ở Postgres,
        không phải chỉ ở `@api.constrains` (migration/script đi cửa sau)."""
        rec = self.WorkDay.create({'date': self._day(13), 'name': 'Làm bù'})
        self.env.flush_all()
        with self.assertRaises(psycopg2.errors.UniqueViolation), \
                mute_logger('odoo.sql_db'), self.env.cr.savepoint():
            self.env.cr.execute(
                'INSERT INTO hb_work_day (date, company_id, name) '
                'VALUES (%s, %s, %s)',
                (rec.date, rec.company_id.id, 'Chèn thẳng'))
        self.env.invalidate_all()

    # ---------------------------------------------------------- phạm vi công ty
    def test_same_date_other_company_allowed(self):
        """Ràng buộc theo từng công ty: công ty khác vẫn khai được ngày đó."""
        day = self._day(14)
        self.WorkDay.create({'date': day, 'name': 'Làm bù'})
        other_company = self.env['res.company'].create({'name': 'Cty Test Lịch'})
        rec = self.WorkDay.create({
            'date': day, 'name': 'Làm bù', 'company_id': other_company.id})
        self.assertTrue(rec.exists())
