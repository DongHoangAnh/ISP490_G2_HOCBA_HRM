"""Trường hợp đồng theo bảng Excel của khách (sheet "2.5. Theo dõi ký hợp đồng").

Bổ sung 4 thứ Excel đang quản lý mà `hb.contract` chưa có: loại hợp đồng,
ngày ký (tách khỏi ngày hiệu lực), lần ký, file hợp đồng.
"""
from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestContractFields(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Contract = self.env['hb.contract'].sudo()
        self.emp = self.env['hr.employee'].sudo().create({
            'name': 'NV Hợp Đồng Test',
            'work_email': 'nv_hd_test@hocba.edu.vn',
        })

    def _contract(self, **kw):
        vals = {
            'name': 'HĐ test', 'employee_id': self.emp.id,
            'date_start': date(2025, 1, 1), 'wage': 10000000.0,
            'state': 'open',
        }
        vals.update(kw)
        return self.Contract.create(vals)

    def test_01_contract_type_options_match_customer_sheet(self):
        """Đủ 4 loại trong sheet + 2 loại hình lao động khác của Học Bá."""
        keys = dict(self.Contract._fields['x_contract_type'].selection).keys()
        self.assertEqual(
            set(keys),
            {'probation', 'fixed_6m', 'fixed_12m', 'permanent',
             'service', 'teaching'})

    def test_02_signed_date_is_separate_from_start_date(self):
        """HB.04 trong sheet: vào làm 30/12/2024 nhưng ký 01/07/2025."""
        c = self._contract(date_start=date(2025, 7, 1),
                           x_date_signed=date(2025, 7, 1),
                           x_contract_type='fixed_12m',
                           date_end=date(2026, 7, 1))
        self.assertEqual(c.x_date_signed, date(2025, 7, 1))
        self.assertNotEqual(c.x_date_signed, self.emp.create_date.date())

    def test_03_sign_count_numbers_contracts_in_order(self):
        """Lần ký tự đánh số theo thứ tự ký — HR không phải nhập tay."""
        second = self._contract(name='HĐ tái ký',
                                x_date_signed=date(2026, 1, 1),
                                date_start=date(2026, 1, 1))
        first = self._contract(name='HĐ đầu',
                               x_date_signed=date(2025, 1, 1),
                               date_start=date(2025, 1, 1))
        self.assertEqual((first.x_sign_count, second.x_sign_count), (1, 2))

    def test_04_sign_count_counts_per_employee(self):
        """Hợp đồng của người khác không làm lệch số lần ký."""
        other = self.env['hr.employee'].sudo().create({'name': 'NV Khác HĐ'})
        self._contract(employee_id=other.id, x_date_signed=date(2024, 1, 1))
        mine = self._contract(x_date_signed=date(2025, 1, 1))
        self.assertEqual(mine.x_sign_count, 1)

    def test_05_contract_file_can_be_attached(self):
        """Sheet có cột "Link hợp đồng" — hệ thống lưu file thật, không dán link."""
        c = self._contract()
        att = self.env['ir.attachment'].sudo().create({
            'name': 'HDLD.pdf', 'datas': b'JVBERi0=',
        })
        c.x_attachment_ids = [(4, att.id)]
        self.assertEqual(c.x_attachment_ids.mapped('name'), ['HDLD.pdf'])

    def test_06_type_is_optional_for_legacy_contracts(self):
        """8 hợp đồng seed cũ không có loại — không được vỡ khi đọc."""
        c = self._contract()
        self.assertFalse(c.x_contract_type)
        self.assertFalse(c.x_date_signed)
