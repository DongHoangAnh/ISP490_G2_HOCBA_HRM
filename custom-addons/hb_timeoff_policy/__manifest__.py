{
    'name': 'HB Time Off — Chính sách Nghỉ phép theo Loại Nhân viên',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Tự động phân bổ phép năm theo loại nhân viên (FUNC-TO-003)',
    'author': 'Học Bá HRM Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays', 'hb_timeoff_config'],
    'data': [
        'security/ir.model.access.csv',
        'data/hb_timeoff_policy_rule_data.xml',
        'views/hb_timeoff_policy_rule_views.xml',
        'views/hr_employee_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
