{
    'name': 'Học Bá HRM',
    'version': '19.0.1.0.0',
    'summary': 'Hệ thống Quản lý Nhân sự Học Bá Education',
    'description': """
        Hệ thống HR toàn diện cho Trung tâm Ngôn ngữ Tiếng Trung Học Bá.
        Bao gồm: Dashboard, Nhân viên, Onboarding, Chấm công, Nghỉ phép,
        Bảng lương, Hợp đồng, Tuyển dụng, Đánh giá, Báo cáo.
    """,
    'category': 'Human Resources',
    'author': 'Học Bá Education',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'hocba_employees', 'hocba_attendance'],
    'data': [
        'views/menu.xml',
        'views/webclient_templates.xml',
    ],
    'assets': {
        'web._assets_primary_variables': [
            ('prepend', 'hocba_hrm/static/src/scss/primary_variables.scss'),
        ],
        'web.assets_backend': [
            'hocba_hrm/static/src/scss/hocba_backend.scss',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': True,
}
