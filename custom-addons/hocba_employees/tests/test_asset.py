from datetime import timedelta

from odoo import fields
from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestEmployeeAssetSimple(TransactionCase):
    """F-006 rút gọn: danh sách phẳng 'ai đang giữ tài sản nào'."""

    def setUp(self):
        super().setUp()
        self.atype = self.env['hocba.asset.type'].create({
            'name': 'Laptop Test', 'code': 'LAPTST'})
        # BR-010: NV phải có CCCD 12 số, mỗi người một giá trị.
        self.emp = self.env['hr.employee'].create({
            'name': 'Asset Holder', 'identification_id': '021111111101'})
        self.emp2 = self.env['hr.employee'].create({
            'name': 'Asset Holder 2', 'identification_id': '021111111102'})

    def _grant(self, emp, code, **kw):
        vals = {
            'employee_id': emp.id,
            'asset_type_id': self.atype.id,
            'asset_code': code,
            'grant_date': fields.Date.today(),
        }
        vals.update(kw)
        return self.env['hr.employee.asset'].create(vals)

    def test_lifecycle_fields_removed(self):
        fnames = self.env['hr.employee.asset']._fields
        for gone in ('state', 'return_date', 'transferred_to',
                     'condition_out_note'):
            self.assertNotIn(gone, fnames)

    def test_delete_row_allowed(self):
        rec = self._grant(self.emp, 'LAPTST-DEL')
        rec.unlink()
        self.assertFalse(rec.exists())

    def test_asset_code_unique(self):
        self._grant(self.emp, 'LAPTST-DUP')
        with mute_logger('odoo.sql_db'), self.assertRaises(ValidationError):
            with self.cr.savepoint():
                self._grant(self.emp2, 'LAPTST-DUP')
                self.env.flush_all()

    def test_grant_before_week2_gate_allowed(self):
        # Ràng buộc "ngày cấp >= mốc tuần-2" đã bị bỏ.
        self.emp.sudo().x_eval_2w_date = fields.Date.today()
        rec = self._grant(self.emp, 'LAPTST-EARLY',
                          grant_date=fields.Date.today() - timedelta(days=30))
        self.assertTrue(rec.id)

    def test_archive_employee_with_asset(self):
        self._grant(self.emp, 'LAPTST-ARCH')
        self.emp.active = False
        self.assertFalse(self.emp.active)

    def test_hr_user_can_delete_row(self):
        # ACL perm_unlink 0→1: root bypass ACL nên phải xoá bằng user thật.
        hr_user = self.env['res.users'].create({
            'name': 'HR User Asset', 'login': 'asset_hr_user',
            'group_ids': [(6, 0, [
                self.env.ref('base.group_user').id,
                self.env.ref('hr.group_hr_user').id])]})
        rec = self._grant(self.emp, 'LAPTST-ACL')
        rec.with_user(hr_user).unlink()
        self.assertFalse(rec.exists())

    def test_employee_fk_is_on_delete_cascade(self):
        """ondelete='cascade': xoá NV thì dòng tài sản đi theo.

        Không kiểm được bằng emp.unlink() thật: mọi NV đều có bản ghi
        hr.promotion.history 'Nhận việc' (FK restrict + unlink bị chặn theo
        BR-060 audit trail) nên NV không thể xoá qua ORM. Kiểm thẳng luật FK
        trong catalog — đó chính là điều 'cascade' hứa.
        """
        self._grant(self.emp2, 'LAPTST-CASCADE')
        self.env.cr.execute("""
            SELECT confdeltype FROM pg_constraint
             WHERE conrelid = 'hr_employee_asset'::regclass
               AND conname = 'hr_employee_asset_employee_id_fkey'
        """)
        row = self.env.cr.fetchone()
        self.assertTrue(row, 'Thiếu FK hr_employee_asset.employee_id')
        self.assertEqual(row[0], 'c', 'FK employee_id chưa ON DELETE CASCADE')

    def test_asset_count_counts_all_rows(self):
        self._grant(self.emp, 'LAPTST-C1')
        self._grant(self.emp, 'LAPTST-C2')
        self.assertEqual(self.emp.x_asset_count, 2)
