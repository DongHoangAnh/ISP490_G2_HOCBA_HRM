{
    'name': 'Học Bá — Thông báo (Notify)',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': 'Model thông báo in-app dùng chung cho chuông SPA (hb.notification)',
    'author': 'Học Bá / Vu-Tan',
    'license': 'LGPL-3',
    'depends': ['base'],
    'data': [
        'security/ir.model.access.csv',
        'security/hb_notification_rules.xml',
    ],
    'installable': True,
    'application': False,
}
