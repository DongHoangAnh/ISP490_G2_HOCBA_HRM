{
    'name': 'HOCBA Employee Management',
    'version': '19.0.1.0.0',
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
    'depends': ['hr'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_employee_sequence.xml',
        'data/hr_department_data.xml',
        'data/ir_cron_data.xml',
        'views/hr_employee_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    'sequence': 2,
}
