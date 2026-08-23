"""Lên chính thức → tự sinh hợp đồng đang hiệu lực.

Trước đây chuỗi tuyển dụng → nhận việc → thử việc → chính thức KHÔNG tạo hợp
đồng ở bước nào, nên nhân viên mới lên chính thức là biến mất khỏi bảng lương
(bảng lương lọc theo hb.contract state=open). Hook này bịt đúng chỗ rò đó.

Chỉ điền phần chắc chắn đúng: trạng thái Đang hiệu lực, hiệu lực từ ngày lên
chính thức, lương lấy theo hồ sơ nếu đã có. Loại hợp đồng / ngày ký / hết hạn
để HR bổ sung sau trong tab Hợp đồng.
"""
from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestContractAutoCreate(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Contract = self.env['hb.contract'].sudo()
        self.Employee = self.env['hr.employee'].sudo()

    def _employee(self, cccd, **kw):
        # BR-010: NV chính thức phải đủ CCCD 12 số + MST TNCN + số sổ BHXH.
        vals = {
            'name': 'NV Tự Sinh HĐ %s' % cccd[-3:],
            'identification_id': cccd,
            'x_pit_code': '812345%s' % cccd[-4:],
            'x_social_insurance_no': '31%s' % cccd[-8:],
            'x_employment_status': 'probation',
        }
        vals.update(kw)
        return self.Employee.create(vals)

    def _go_official(self, emp, when=None):
        emp.write({'x_employment_status': 'official',
                   'x_official_date': when or date(2026, 3, 1)})
        return self.Contract.search([('employee_id', '=', emp.id)])

    def test_30_contract_created_on_going_official(self):
        emp = self._employee('090000000401')
        contracts = self._go_official(emp)
        self.assertEqual(len(contracts), 1)
        self.assertEqual(contracts.state, 'open')
        self.assertEqual(contracts.date_start, date(2026, 3, 1),
                         'Hiệu lực từ = ngày lên chính thức')
        self.assertFalse(contracts.date_end, 'Thời hạn để HR bổ sung sau')
        self.assertFalse(contracts.x_contract_type,
                         'Loại hợp đồng để HR bổ sung sau')
        self.assertIn(emp.name, contracts.name)

    def test_31_wage_taken_from_profile_when_available(self):
        emp = self._employee('090000000402')
        version = emp.version_id
        if version and 'wage' in version._fields:
            version.sudo().write({'wage': 14000000})
        contracts = self._go_official(emp)
        self.assertEqual(contracts.wage, 14000000)

    def test_32_no_official_date_falls_back_to_today(self):
        emp = self._employee('090000000403')
        emp.write({'x_employment_status': 'official'})
        contracts = self.Contract.search([('employee_id', '=', emp.id)])
        self.assertEqual(contracts.date_start, date.today())

    def test_33_idempotent_on_repeat_write(self):
        emp = self._employee('090000000404')
        self._go_official(emp)
        emp.write({'x_employment_status': 'official'})
        self.assertEqual(
            self.Contract.search_count([('employee_id', '=', emp.id)]), 1)

    def test_34_existing_open_contract_is_left_alone(self):
        emp = self._employee('090000000405')
        existing = self.Contract.create({
            'name': 'HĐ có sẵn', 'employee_id': emp.id,
            'date_start': date(2025, 1, 1), 'wage': 9000000, 'state': 'open'})
        contracts = self._go_official(emp)
        self.assertEqual(contracts, existing,
                         'Đã có hợp đồng hiệu lực thì không sinh thêm')

    def test_35_closed_contract_does_not_block_new_one(self):
        """Hết hợp đồng thử việc rồi lên chính thức → phải có hợp đồng mới."""
        emp = self._employee('090000000406')
        self.Contract.create({
            'name': 'HĐ thử việc', 'employee_id': emp.id,
            'x_contract_type': 'probation', 'date_start': date(2025, 12, 1),
            'date_end': date(2026, 2, 28), 'wage': 8000000, 'state': 'close'})
        contracts = self._go_official(emp)
        self.assertEqual(len(contracts), 2)
        self.assertEqual(len(contracts.filtered(lambda c: c.state == 'open')), 1)

    def test_36_other_status_changes_create_nothing(self):
        emp = self._employee('090000000407')
        emp.write({'x_employment_status': 'exiting'})
        self.assertFalse(self.Contract.search([('employee_id', '=', emp.id)]))

    def test_37_gate_automation_path_also_creates(self):
        """Đường chính thức của quy trình nhận việc (_hocba_make_official)."""
        emp = self._employee('090000000408')
        emp._hocba_make_official('nhận việc (test)')
        contracts = self.Contract.search([('employee_id', '=', emp.id)])
        self.assertEqual(len(contracts), 1)
        self.assertEqual(contracts.date_start, emp.x_official_date)
