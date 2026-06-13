{
    'name': 'HB Time Off — Xác thực Chứng từ Y tế Nghỉ Ốm',
    'version': '19.0.2.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Validate chứng từ y tế (PDF/JPG/PNG ≤5MB) — HR Manager bypass BR-011 — re-validate BR-012 (FUNC-TO-002)',
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
