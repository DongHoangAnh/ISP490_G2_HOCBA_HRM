{
    'name': 'HR Holidays Modern UI',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'author': 'Modern UI Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays'],
    'data': [
        'views/hr_holidays_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hr_holidays_modern/static/src/css/hr_holidays_modern.css',
            'hr_holidays_modern/static/src/js/hr_holidays_modern.js',
        ],
    },
    'installable': True,
    'auto_install': False,
    'images': ['static/description/icon.png'],
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
}
