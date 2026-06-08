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
    'depends': ['base', 'hr'],
    'data': [
        'views/menu.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}
