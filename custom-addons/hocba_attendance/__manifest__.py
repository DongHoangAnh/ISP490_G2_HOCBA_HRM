{
    'name': 'HOCBA Attendance Management',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'author': 'HOCBA Team',
    'license': 'LGPL-3',
    'depends': ['hr', 'web', 'hocba_employees'],
    'data': [
        'security/ir.model.access.csv',
        'data/hocba_attendance_policy_data.xml',
        'views/hr_attendance_status_views.xml',
        'views/hr_work_assignment_views.xml',
        'views/hr_attendance_views.xml',
        'views/hocba_attendance_policy_views.xml',
        'views/menus.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hocba_attendance/static/src/js/attendance_kiosk.js',
            'hocba_attendance/static/src/xml/attendance_kiosk.xml',
            'hocba_attendance/static/src/scss/attendance_kiosk.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 1,
}
