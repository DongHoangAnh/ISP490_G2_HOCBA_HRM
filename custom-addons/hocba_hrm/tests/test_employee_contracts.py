"""Tab "Hợp đồng" trong hồ sơ nhân viên — API trả danh sách các lần ký.

Lương là dữ liệu nhạy cảm nên khối `contracts` đi theo đúng cổng `see_salary`
(Admin / HR Manager / Giáo vụ / Trưởng phòng), giống khối ngân hàng & MST.
"""
import json
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


@tagged('post_install', '-at_install')
class TestEmployeeContractsWrite(HttpCase):
    """Tạo / sửa / xoá hợp đồng ngay trong hồ sơ nhân viên.

    Cổng quyền = "được quản lý hồ sơ NV đó" VÀ "được xem lương" — hợp đồng chứa
    mức lương nên HR officer (không xem lương) bị chặn dù quản lý được hồ sơ.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        cls.hr_mgr = Users.create({
            'name': 'HR Mgr Ghi HĐ', 'login': 'hrmgr_ct_w', 'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('hr.group_hr_user').id,
                                  cls.env.ref('hr.group_hr_manager').id])]})
        cls.hr_officer = Users.create({
            'name': 'HR Officer Ghi HĐ', 'login': 'hrofficer_ct_w',
            'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('hr.group_hr_user').id])]})
        cls.tp_user = Users.create({
            'name': 'Trưởng phòng Ghi HĐ', 'login': 'tp_ct_w', 'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]})
        cls.plain = Users.create({
            'name': 'NV thường Ghi HĐ', 'login': 'nv_ct_w', 'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]})

        Emp = cls.env['hr.employee'].sudo()
        cls.tp_emp = Emp.create({'name': 'TP Ghi HĐ', 'user_id': cls.tp_user.id})
        cls.dept = cls.env['hr.department'].sudo().create({
            'name': 'Phòng Ghi HĐ', 'manager_id': cls.tp_emp.id})
        cls.mine = Emp.create({
            'name': 'NV Phòng Tôi', 'x_employee_code': 'EMP-CT-W1',
            'department_id': cls.dept.id})
        cls.outsider = Emp.create({
            'name': 'NV Phòng Khác', 'x_employee_code': 'EMP-CT-W2'})

    def _post(self, path, payload, login='hrmgr_ct_w', expect=200):
        self.authenticate(login, PWD)
        res = self.url_open('/hocba-hrm/api' + path, data=json.dumps(payload),
                            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, expect, res.text[:300])
        return res.json()

    def _create(self, emp, login='hrmgr_ct_w', expect=200, **vals):
        payload = {
            'typeKey': 'fixed_12m', 'dateSigned': '2026-01-05',
            'dateStart': '2026-01-05', 'dateEnd': '2027-01-05',
            'wage': 15000000, 'insuranceBase': 7300000, 'state': 'open',
        }
        payload.update(vals)
        return self._post('/employee/%s/contract' % emp.id, payload,
                          login=login, expect=expect)

    def test_10_hr_manager_creates_contract(self):
        body = self._create(self.mine)
        rows = body['contracts']
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['typeKey'], 'fixed_12m')
        self.assertEqual(rows[0]['wage'], 15000000)
        self.assertEqual(rows[0]['dateSigned'], '2026-01-05')
        self.assertTrue(rows[0]['name'], 'Tên hợp đồng phải tự đặt nếu bỏ trống')

    def test_11_department_manager_edits_own_staff(self):
        """TP sửa được các trường của hợp đồng — trừ mức lương (xem
        TestContractSalaryGuard)."""
        row = self._create(self.mine, login='tp_ct_w', wage=0,
                           insuranceBase=0)['contracts'][0]
        body = self._post('/contract/%s' % row['id'],
                          {'typeKey': 'permanent', 'dateEnd': ''},
                          login='tp_ct_w')
        edited = body['contracts'][0]
        self.assertEqual(edited['typeKey'], 'permanent')
        self.assertIsNone(edited['dateEnd'])

    def test_12_department_manager_blocked_outside_scope(self):
        self._create(self.outsider, login='tp_ct_w', expect=403)

    def test_13_hr_officer_cannot_touch_contracts(self):
        """Không được xem lương thì cũng không được sửa hợp đồng."""
        self._create(self.mine, login='hrofficer_ct_w', expect=403)

    def test_14_plain_user_blocked(self):
        self._create(self.mine, login='nv_ct_w', expect=403)

    def test_15_delete_contract(self):
        row = self._create(self.mine)['contracts'][0]
        body = self._post('/contract/%s/delete' % row['id'], {})
        self.assertEqual(body['contracts'], [])

    def test_16_delete_blocked_when_payslip_uses_it(self):
        row = self._create(self.mine)['contracts'][0]
        self.env['hb.payslip'].sudo().create({
            'employee_id': self.mine.id, 'contract_id': row['id'],
            'date_from': '2026-02-01', 'date_to': '2026-02-28',
        })
        self.env.flush_all()
        err = self._post('/contract/%s/delete' % row['id'], {}, expect=400)
        self.assertEqual(err['error'], 'rejected')
        self.assertIn('phiếu lương', err['message'].lower())

    def test_17_form_options_available(self):
        self.authenticate('hrmgr_ct_w', PWD)
        body = self.url_open(
            '/hocba-hrm/api/employee/%s' % self.mine.id).json()
        opts = body['contractOptions']
        self.assertEqual(len(opts['types']), 6)
        self.assertTrue(all(t['key'] and t['label'] for t in opts['types']))
        self.assertTrue(opts['states'])
        self.assertIn('structures', opts)

    def test_18_start_date_required(self):
        err = self._create(self.mine, dateStart='', expect=400)
        self.assertEqual(err['error'], 'rejected')

    def test_19_second_open_contract_requires_renew(self):
        self._create(self.mine)
        err = self._create(self.mine, dateStart='2027-01-06', expect=400)
        self.assertIn('Tái ký', err['message'])

    def test_20_renew_closes_old_contract(self):
        old = self._create(self.mine)['contracts'][0]
        body = self._create(
            self.mine, dateStart='2027-01-06', dateEnd='2028-01-05',
            renewFromId=old['id'])
        rows = body['contracts']
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['state'], 'close')
        self.assertEqual(rows[0]['dateEnd'], '2027-01-05')
        self.assertEqual(rows[1]['state'], 'open')


@tagged('post_install', '-at_install')
class TestContractSalaryGuard(HttpCase):
    """Ô lương trên hợp đồng: chỉ HR Manager/Admin được đặt và sửa.

    Trưởng phòng vẫn sửa được loại HĐ, ngày ký, thời hạn, trạng thái — đúng
    tinh thần "quản lý nhân sự phòng mình" mà không đụng tới mức lương.
    Đồng thời lương của hợp đồng ĐANG HIỆU LỰC phải khớp với ô "Lương cơ bản"
    ở tab Thông tin — hai tab không được nói hai số khác nhau.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Users = cls.env['res.users']
        cls.hr_mgr = Users.create({
            'name': 'HR Mgr Khoá Lương', 'login': 'hrmgr_lock', 'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id,
                                  cls.env.ref('hr.group_hr_user').id,
                                  cls.env.ref('hr.group_hr_manager').id])]})
        cls.tp_user = Users.create({
            'name': 'TP Khoá Lương', 'login': 'tp_lock', 'password': PWD,
            'group_ids': [(6, 0, [cls.env.ref('base.group_user').id])]})
        Emp = cls.env['hr.employee'].sudo()
        cls.tp_emp = Emp.create({'name': 'TP Lock', 'user_id': cls.tp_user.id})
        cls.dept = cls.env['hr.department'].sudo().create({
            'name': 'Phòng Khoá Lương', 'manager_id': cls.tp_emp.id})
        cls.emp = Emp.create({
            'name': 'NV Khoá Lương', 'x_employee_code': 'EMP-LOCK-1',
            'department_id': cls.dept.id})

    def _post(self, path, payload, login='hrmgr_lock', expect=200):
        self.authenticate(login, PWD)
        res = self.url_open('/hocba-hrm/api' + path, data=json.dumps(payload),
                            headers={'Content-Type': 'application/json'})
        self.assertEqual(res.status_code, expect, res.text[:300])
        return res.json()

    def _seed_contract(self, **kw):
        vals = {'typeKey': 'fixed_12m', 'dateSigned': '2026-01-01',
                'dateStart': '2026-01-01', 'dateEnd': '2027-01-01',
                'wage': 10000000, 'state': 'open'}
        vals.update(kw)
        return self._post('/employee/%s/contract' % self.emp.id,
                          vals)['contracts'][-1]

    def test_20_manager_cannot_change_wage(self):
        row = self._seed_contract()
        err = self._post('/contract/%s' % row['id'], {'wage': 30000000},
                         login='tp_lock', expect=400)
        self.assertIn('lương', err['message'].lower())
        self.assertEqual(self._post('/contract/%s' % row['id'], {},
                                    login='tp_lock')['contracts'][0]['wage'],
                         10000000, 'Mức lương phải giữ nguyên')

    def test_21_manager_edits_other_fields_fine(self):
        row = self._seed_contract()
        body = self._post('/contract/%s' % row['id'], {
            'typeKey': 'permanent', 'dateEnd': '', 'wage': row['wage'],
        }, login='tp_lock')
        edited = body['contracts'][0]
        self.assertEqual(edited['typeKey'], 'permanent')
        self.assertIsNone(edited['dateEnd'])

    def test_22_manager_cannot_seed_wage_on_create(self):
        self._post('/employee/%s/contract' % self.emp.id,
                   {'dateStart': '2026-02-01', 'wage': 25000000},
                   login='tp_lock', expect=400)

    def test_23_manager_creates_contract_without_wage(self):
        body = self._post('/employee/%s/contract' % self.emp.id,
                          {'dateStart': '2026-03-01', 'typeKey': 'probation'},
                          login='tp_lock')
        self.assertTrue(body['contracts'])

    def test_24_active_contract_wage_syncs_to_profile(self):
        """Sửa lương HĐ đang hiệu lực -> tab Thông tin đổi theo."""
        row = self._seed_contract()
        body = self._post('/contract/%s' % row['id'], {'wage': 21000000})
        self.assertEqual(body['contracts'][0]['wage'], 21000000)
        self.assertEqual(body['wage'], 21000000,
                         'Ô "Lương cơ bản" ở tab Thông tin phải khớp')

    def test_25_closed_contract_wage_does_not_touch_profile(self):
        active = self._seed_contract()
        self._post('/contract/%s' % active['id'], {'wage': 21000000})
        old = self._seed_contract(dateStart='2025-01-01', dateEnd='2025-12-31',
                                  wage=9000000, state='close')
        body = self._post('/contract/%s' % old['id'], {'wage': 8000000})
        self.assertEqual(body['wage'], 21000000,
                         'Sửa hợp đồng cũ không được đổi lương hiện tại')

    def test_26_new_active_contract_sets_profile_wage(self):
        self._post('/employee/%s/contract' % self.emp.id,
                   {'dateStart': '2026-04-01', 'wage': 17000000,
                    'state': 'open'})
        self.authenticate('hrmgr_lock', PWD)
        body = self.url_open('/hocba-hrm/api/employee/%s' % self.emp.id).json()
        self.assertEqual(body['wage'], 17000000)

    def test_27_profile_wage_edit_only_touches_active_contract(self):
        """Sửa lương ở tab Thông tin: hợp đồng đang hiệu lực đổi theo, hợp đồng
        cũ giữ nguyên (đó là lịch sử mức lương đã ký)."""
        old = self._seed_contract(dateStart='2024-01-01', dateEnd='2024-12-31',
                                  wage=9000000, state='close')
        active = self._seed_contract(wage=12000000)
        self._post('/employee/%s' % self.emp.id, {'wage': 20000000})
        rows = {r['id']: r for r in self._post(
            '/contract/%s' % active['id'], {})['contracts']}
        self.assertEqual(rows[active['id']]['wage'], 20000000)
        self.assertEqual(rows[old['id']]['wage'], 9000000,
                         'Hợp đồng đã đóng không được ghi đè')
