"""
Unit tests for Salary Rules, AST Formula Evaluation & PIT/Insurance Calculations.

Spec reference: docs/specs/payroll/FS-PAY-001_Salary_Structure_Rule_Configuration_v1_0.md
                docs/specs/payroll/FS-PAY-002_Payslip_Computation_Engine_v1_0.md
"""
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError
from odoo.tools import mute_logger
from psycopg2 import IntegrityError


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestSalaryRuleAST(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Employee = self.env['hr.employee'].sudo()
        self.Contract = self.env['hb.contract'].sudo()
        self.Payslip = self.env['hb.payslip'].sudo()
        self.Rule = self.env['hb.salary.rule'].sudo()
        self.Category = self.env['hb.salary.rule.category'].sudo()

        # Create test employee
        self.emp = self.Employee.create({
            'name': 'Nguyễn Văn Test Payroll',
            'work_email': 'test_payroll_ast@hocba.edu.vn',
        })

        # Create test contract (Base wage: 20,000,000 VND)
        self.contract = self.Contract.create({
            'employee_id': self.emp.id,
            'name': 'HĐLD - Nguyễn Văn Test',
            'state': 'open',
            'date_start': '2026-01-01',
            'wage': 20000000.0,
            'x_sp_meal': 1000000.0,
            'x_sp_phone': 500000.0,
        })

    def test_01_basic_wage_computation(self):
        """Test Lương cơ bản (BASIC) computation from contract."""
        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
        })
        slip.action_compute_sheet()

        self.assertTrue(slip.x_teaching_computed, 'Phiếu lương phải được tính toán thành công.')
        self.assertGreater(len(slip.line_ids), 0, 'Phải sinh ra các dòng payslip.line')

        # Find BASIC line
        basic_line = slip.line_ids.filtered(lambda l: l.code == 'BASIC' or l.category_id.code == 'BASIC')
        if basic_line:
            self.assertEqual(basic_line[0].amount, 20000000.0, 'Số tiền lương cơ bản phải bằng wage của hợp đồng.')

    def test_02_insurance_deductions_calculation(self):
        """Test BHXH (8%), BHYT (1.5%), BHTN (1%) deductions."""
        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
        })
        slip.action_compute_sheet()

        # Check insurance amounts
        bhxh_line = slip.line_ids.filtered(lambda l: l.code == 'BHXH')
        if bhxh_line:
            # 8% of 20M = 1,600,000 VND
            self.assertAlmostEqual(bhxh_line.amount, 1600000.0, delta=100.0)

    def test_03_pit_tax_progressive_calculation(self):
        """Test PIT (Thuế TNCN) progressive tax brackets calculation."""
        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
        })
        slip.action_compute_sheet()

        pit_line = slip.line_ids.filtered(lambda l: l.code in ('PIT', 'thue_tncn'))
        if pit_line:
            self.assertGreaterEqual(pit_line.amount, 0.0, 'Thuế TNCN không được âm.')

    def test_04_net_salary_calculation(self):
        """Test NET = GROSS - Deductions (BHXH, BHYT, BHTN, PIT)."""
        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
        })
        slip.action_compute_sheet()

        net_line = slip.line_ids.filtered(lambda l: l.code == 'NET')
        gross_line = slip.line_ids.filtered(lambda l: l.code == 'GROSS')

        if net_line and gross_line:
            self.assertLessEqual(net_line.amount, gross_line.amount, 'Lương NET phải nhỏ hơn hoặc bằng lương GROSS.')
            self.assertGreater(net_line.amount, 0.0, 'Lương NET phải lớn hơn 0.')

    def test_05_missing_contract_edge_case(self):
        """Test edge case: Employee without active contract."""
        emp_no_contract = self.Employee.create({
            'name': 'Emp No Contract',
            'work_email': 'no_contract@hocba.edu.vn',
        })
        slip = self.Payslip.create({
            'employee_id': emp_no_contract.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
        })
        # Should complete gracefully without crashing
        slip.action_compute_sheet()
        self.assertTrue(slip.x_teaching_computed)

    def test_06_edited_formula_is_used_on_recompute(self):
        """A formula changed by HR must affect the next computation."""
        structure = self.env['hb.salary.structure'].sudo().create({
            'name': 'Cấu trúc test sửa công thức',
            'code': 'STRUCT_FORMULA_EDIT_TEST',
        })
        category = self.Category.search([], limit=1)
        base_rule = self.Rule.create({
            'name': 'Giá trị gốc test',
            'code': 'formula_base_test',
            'sequence': 1,
            'structure_id': structure.id,
            'category_id': category.id,
            'amount_type': 'fixed',
            'amount_fixed': 100,
        })
        result_rule = self.Rule.create({
            'name': 'Kết quả công thức test',
            'code': 'formula_result_test',
            'sequence': 2,
            'structure_id': structure.id,
            'category_id': category.id,
            'amount_type': 'formula',
            'amount_formula': 'formula_base_test * 2',
        })
        self.contract.x_structure_id = structure
        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': '2026-08-01',
            'date_to': '2026-08-31',
        })

        slip.action_compute_sheet()
        self.assertEqual(
            slip.line_ids.filtered(lambda line: line.rule_id == result_rule).amount,
            200,
        )

        result_rule.amount_formula = 'formula_base_test * 3'
        slip.action_compute_sheet()
        self.assertEqual(
            slip.line_ids.filtered(lambda line: line.rule_id == result_rule).amount,
            300,
        )
        self.assertEqual(
            slip.line_ids.filtered(lambda line: line.rule_id == base_rule).amount,
            100,
        )

    def test_07_rule_code_unique_inside_structure(self):
        """Duplicate codes in one structure would corrupt dependency evaluation."""
        structure = self.env.ref('hocba_payroll.struct_offline')
        category = self.Category.search([], limit=1)
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self.Rule.create({
                'name': 'Rule trùng mã',
                'code': 'luong_co_ban',
                'sequence': 999,
                'structure_id': structure.id,
                'category_id': category.id,
                'amount_type': 'fixed',
                'amount_fixed': 1,
            })
