{
    'name': 'HB Time Off Configuration',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Cấu hình nghỉ phép chuẩn cho Trung tâm Ngoại ngữ Học Bá',
    'author': 'Học Bá HRM Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays'],
    'data': [
        'data/hr_leave_type_data.xml',
        'data/hr_leave_accrual_plan_data.xml',
        'data/hr_leave_mandatory_day_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
