{
    'name': 'HB Time Off — Nghỉ Khẩn Cấp Fast-Track',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Thông báo tức thời HR + Manager khi có đơn nghỉ khẩn cấp; badge Khẩn Cấp trên form (AUT-TO-001)',
    'author': 'Học Bá HRM Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays', 'hb_timeoff_config'],
    'data': [
        'data/hb_emergency_leave_type_flag.xml',
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
