"""Tab "Hợp đồng" trong hồ sơ nhân viên — API trả danh sách các lần ký.

Lương là dữ liệu nhạy cảm nên khối `contracts` đi theo đúng cổng `see_salary`
(Admin / HR Manager / Giáo vụ / Trưởng phòng), giống khối ngân hàng & MST.
"""
from datetime import date, timedelta

from odoo.tests import HttpCase, tagged

PWD = 'Hocba@2026'


@tagged('post_install', '-at_install')
class TestEmployeeContractsApi(HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        cls.hr_mgr = Users.create({
            'name': 'HR Mgr HĐ', 'login': 'hrmgr_contract', 'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('hr.group_hr_user').id,
                                  cls.env.ref('hr.group_hr_manager').id])]})
        # HR officer: quản lý được hồ sơ nhưng KHÔNG được xem lương.
        cls.hr_officer = Users.create({
            'name': 'HR Officer HĐ', 'login': 'hrofficer_contract',
            'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('hr.group_hr_user').id])]})
        cls.emp = cls.env['hr.employee'].sudo().create({
            'name': 'NV Có Hợp Đồng', 'x_employee_code': 'EMP-HD-1',
        })
        cls.emp_no_contract = cls.env['hr.employee'].sudo().create({
            'name': 'NV Chưa Có Hợp Đồng', 'x_employee_code': 'EMP-HD-2',
        })
        Contract = cls.env['hb.contract'].sudo()
        Contract.create({
            'name': 'HĐ thử việc', 'employee_id': cls.emp.id,
            'x_contract_type': 'probation', 'x_date_signed': date(2025, 1, 1),
            'date_start': date(2025, 1, 1), 'date_end': date(2025, 3, 1),
            'wage': 8000000.0, 'state': 'close',
        })
        # Hợp đồng đang chạy, hết hạn trong 20 ngày -> phải bị đánh dấu sắp hết hạn.
        cls.soon = Contract.create({
            'name': 'HĐ 12 tháng', 'employee_id': cls.emp.id,
            'x_contract_type': 'fixed_12m', 'x_date_signed': date(2025, 3, 1),
            'date_start': date(2025, 3, 1),
            'date_end': date.today() + timedelta(days=20),
            'wage': 12000000.0, 'x_insurance_base': 7300000.0, 'state': 'open',
        })

    def _detail(self, emp, login='hrmgr_contract'):
        self.authenticate(login, PWD)
        res = self.url_open('/hocba-hrm/api/employee/%s' % emp.id)
        self.assertEqual(res.status_code, 200, res.text[:300])
        return res.json()

    def test_01_contracts_listed_oldest_first(self):
        rows = self._detail(self.emp)['contracts']
        self.assertEqual(len(rows), 2)
        self.assertEqual([r['signCount'] for r in rows], [1, 2])
        self.assertEqual([r['typeKey'] for r in rows],
                         ['probation', 'fixed_12m'])
        self.assertTrue(rows[0]['type'], 'Phải có nhãn tiếng Việt của loại HĐ')

    def test_02_row_carries_dates_wage_and_state(self):
        row = self._detail(self.emp)['contracts'][1]
        self.assertEqual(row['dateSigned'], '2025-03-01')
        self.assertEqual(row['dateStart'], '2025-03-01')
        self.assertEqual(row['wage'], 12000000.0)
        self.assertEqual(row['insuranceBase'], 7300000.0)
        self.assertEqual(row['state'], 'open')
        self.assertTrue(row['stateLabel'])
        self.assertEqual(row['files'], [])

    def test_03_expiring_contract_flagged(self):
        rows = self._detail(self.emp)['contracts']
        self.assertFalse(rows[0]['expiringSoon'], 'HĐ đã đóng không cảnh báo')
        self.assertTrue(rows[1]['expiringSoon'])

    def test_04_employee_without_contract_returns_empty_list(self):
        body = self._detail(self.emp_no_contract)
        self.assertEqual(body['contracts'], [],
                         'Phải là mảng rỗng để UI hiện cảnh báo "chưa có hợp đồng"')

    def test_05_hidden_from_roles_that_cannot_see_salary(self):
        body = self._detail(self.emp, login='hrofficer_contract')
        self.assertNotIn('contracts', body,
                         'HR officer không được xem lương -> không thấy hợp đồng')
