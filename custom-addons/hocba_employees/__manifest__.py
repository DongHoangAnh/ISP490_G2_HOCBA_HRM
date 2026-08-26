{
    'name': 'HOCBA Employee Management',
    'version': '19.0.6.0.0',
    'category': 'Human Resources',
    'author': 'HOCBA Team',
    'license': 'LGPL-3',
    'summary': 'Quản lý hồ sơ & vòng đời nhân sự — Học Bá (Phân hệ Employees)',
    'description': """
HOCBA Employees — Phân hệ Quản lý Nhân sự (theo đặc tả v2.1)
============================================================
Pha 1 (nền/MVP): mở rộng hr.employee với 4 trục phân loại Học Bá
(Hình thức / Tình trạng / Loại vị trí / Phòng ban), mã nhân sự tự sinh
(HB.xx) và seed 6 phòng ban chuẩn. Là lớp nền cho Attendance, Users,
Payroll, Recruitment.
    """,
    'depends': ['hr', 'hr_skills', 'hocba_notify'],
    'data': [
        'security/hocba_security.xml',
        'security/ir.model.access.csv',
        'security/hocba_offboarding_rules.xml',
        'data/hr_promotion_criteria_data.xml',
        'data/hr_employee_sequence.xml',
        'data/hocba_offboarding_data.xml',
        'data/hr_department_data.xml',
        'data/ir_cron_data.xml',
        'data/hocba_asset_type_data.xml',
        'data/hocba_employee_type_data.xml',
        'data/hb_onboarding_template_data.xml',
        'data/hr_skill_data.xml',
        'views/hr_employee_views.xml',
        'views/hr_employee_asset_views.xml',
        'views/hr_promotion_history_views.xml',
        'views/hocba_offboarding_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hocba_employees/static/src/js/face_descriptor_field.js',
            'hocba_employees/static/src/xml/face_descriptor_field.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 2,
}
