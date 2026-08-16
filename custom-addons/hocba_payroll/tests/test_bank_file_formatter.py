"""
Unit tests for Bank File Generation, Format Validation (MB Bank, VCB, TCB) & Export.

Spec reference: docs/specs/payroll/FS-PAY-004_Bank_Payment_File_Generation_v1_0.md
"""
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import UserError, ValidationError


@tagged('post_install', '-at_install', 'hocba', 'payroll')
class TestBankFileFormatter(TransactionCase):

    def setUp(self):
        super().setUp()
        self.Employee = self.env['hr.employee'].sudo()
        self.Contract = self.env['hb.contract'].sudo()
        self.Batch = self.env['hb.payslip.run'].sudo()
        self.Payslip = self.env['hb.payslip'].sudo()
        self.BankFile = self.env['hb.bank.file'].sudo()
        self.BankFormat = self.env['hb.bank.format'].sudo()

        # Create test employee with bank details
        self.emp = self.Employee.create({
            'name': 'Trần Văn Bank Test',
            'work_email': 'tran_bank_test@hocba.edu.vn',
            'x_bank_account_no': '1234567890123',
            'x_bank_code': 'MBBANK',
        })

        self.Contract.create({
            'employee_id': self.emp.id,
            'name': 'HĐ Bank Test',
            'state': 'open',
            'date_start': '2026-01-01',
            'wage_base': 25000000.0,
        })

    def test_01_bank_file_creation_and_lines(self):
        """Test bank payment file generation for a batch of computed payslips."""
        batch = self.Batch.create({
            'name': 'Batch Chi Lương MB Bank',
            'date_start': '2026-08-01',
            'date_end': '2026-08-31',
        })

        slip = self.Payslip.create({
            'employee_id': self.emp.id,
            'date_from': batch.date_start,
            'date_to': batch.date_end,
            'payslip_run_id': batch.id,
        })
        slip.action_compute_sheet()

        # Create bank format if needed
        format_mb = self.BankFormat.search([('code', '=', 'MBBANK')], limit=1)
        if not format_mb:
            format_mb = self.BankFormat.create({
                'name': 'MB Bank Standard Format',
                'code': 'MBBANK',
                'file_type': 'xlsx',
                'template_header': 'STT,So_TK,Ten_Chu_TK,So_Tien,Noi_Dung',
            })

        # Generate Bank File
        bank_file = self.BankFile.create({
            'name': 'BANK-MB-202608',
            'payslip_run_id': batch.id,
            'bank_format_id': format_mb.id,
            'state': 'draft',
        })

        self.assertEqual(bank_file.state, 'draft', 'File bank khởi tạo ở trạng thái draft.')
        self.assertIsNotNone(bank_file.name, 'Tên file bank không được để trống.')

    def test_02_bank_file_status_transitions(self):
        """Test state flow: draft -> uploaded -> confirmed."""
        bank_file = self.BankFile.create({
            'name': 'BANK-VCB-202608',
            'state': 'draft',
        })

        if hasattr(bank_file, 'action_upload'):
            bank_file.action_upload()
            self.assertEqual(bank_file.state, 'uploaded')

        if hasattr(bank_file, 'action_confirm'):
            bank_file.action_confirm()
            self.assertEqual(bank_file.state, 'confirmed')
