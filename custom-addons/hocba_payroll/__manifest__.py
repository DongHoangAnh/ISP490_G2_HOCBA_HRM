{
    'name': 'Hoc Ba Payroll',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Payroll management for Hoc Ba Education — teaching hours, bank files, BHXH, eTax',
    'description': """
        FUNC-PR-001: Tính lương giáo viên theo giờ dạy (TEACH_HOURS)
        FUNC-PR-003: Sinh file thanh toán ngân hàng (VCB / Techcombank)
        FUNC-PR-004: Báo cáo BHXH (iBHXH)
        FUNC-PR-005: Báo cáo eTax (05/KK-TNCN)

        Standalone — không phụ thuộc Odoo Enterprise (hr_payroll).
    """,
    'author': 'Hoc Ba Education',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'mail',
        'hocba_employees',
    ],
    'data': [
        # Security first
        'security/ir.model.access.csv',
        # Seed data
        'data/work_entry_type_data.xml',
        'data/bank_format_data.xml',
        # 'data/salary_structure_data.xml',  # logic embedded in payslip.py
        'data/ir_sequence_data.xml',
        # Views & Wizards
        'views/hr_contract_views.xml',
        'views/work_entry_views.xml',
        'views/payslip_views.xml',
        'views/bank_format_views.xml',
        'views/bank_file_views.xml',
        'views/bhxh_report_views.xml',
        'views/etax_report_views.xml',
        'views/menu.xml',
        'wizards/bank_file_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
