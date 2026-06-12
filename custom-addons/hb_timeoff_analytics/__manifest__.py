{
    'name': 'HB Time Off — Báo cáo & Phân tích Nghỉ phép',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': (
        'Dashboard phân tích nghỉ phép nâng cao: 6 widgets, '
        'xuất Excel/PDF, cảnh báo burnout (FUNC-TO-005)'
    ),
    'author': 'Học Bá HRM Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays', 'hb_timeoff_policy'],
    'data': [
        'security/ir.model.access.csv',
        'security/hb_timeoff_analytics_rules.xml',
        'report/hb_timeoff_analytics_pdf.xml',
        'wizard/hb_timeoff_export_wizard_views.xml',
        'views/hb_leave_analysis_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
