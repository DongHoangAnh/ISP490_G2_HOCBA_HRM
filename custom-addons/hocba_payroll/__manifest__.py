{
    'name': 'Hoc Ba Payroll',
    'version': '19.0.4.0.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Payroll management for Hoc Ba Education — rule-based salary engine, bank files',
    'description': """
        Rule-based salary engine with configurable structures:
        • STRUCT_OFFLINE: Lương thời gian + phụ cấp
        • STRUCT_ONLINE: Lương + thưởng − tạm ứng

        Features:
        • FUNC-PR-001: Tính lương (offline / online / teacher)
        • FUNC-PR-003: Sinh file thanh toán ngân hàng (VCB / Techcombank)

        Standalone — không phụ thuộc Odoo Enterprise (hr_payroll).
    """,
    'author': 'Hoc Ba Education',
    'license': 'LGPL-3',
    'depends': [
        'hr',
        'mail',
        'hocba_employees',
        'hocba_attendance',
    ],
    'data': [
        # Security first
        'security/ir.model.access.csv',
        # Seed data (order matters: categories → structures → rules)
        'data/work_entry_type_data.xml',
        'data/bank_format_data.xml',
        'data/ir_sequence_data.xml',
        'data/salary_rule_category_data.xml',
        'data/salary_structure_data.xml',
        'data/confirm_cron.xml',
        # Views & Wizards
        'views/salary_structure_views.xml',
        'views/hr_contract_views.xml',
        'views/work_entry_views.xml',
        'views/payslip_views.xml',
        'views/bank_format_views.xml',
        'views/bank_file_views.xml',
        'views/menu.xml',
        'views/payslip_public_templates.xml',
        'wizards/bank_file_wizard_views.xml',
        'wizards/formula_help_wizard_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
