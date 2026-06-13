{
    'name': 'HB Time Off — Cron Jobs',
    'version': '19.0.1.0.0',
    'category': 'Human Resources/Time Off',
    'summary': 'Cron nhắc nhở số dư nghỉ phép cuối tháng lúc 07:00 (CRON-TO-001)',
    'author': 'Học Bá HRM Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays', 'hb_timeoff_policy'],
    'data': [
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
