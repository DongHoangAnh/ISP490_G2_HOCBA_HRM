{
    'name': 'HB Time Off — Xác thực Chứng từ Y tế Nghỉ Ốm',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Đính kèm chứng từ y tế (tùy chọn) cho đơn Nghỉ Ốm, cảnh báo HR khi thiếu (FUNC-TO-002)',
    'author': 'Học Bá HRM Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays', 'hb_timeoff_config'],
    'data': [
        'data/hb_sick_leave_support_doc.xml',
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
