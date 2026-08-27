# -*- coding: utf-8 -*-
{
    'name': 'Học Bá — Branding website công khai',
    'version': '19.0.1.0.0',
    'summary': 'Thương hiệu Học Bá cho website công khai (trang /jobs, header, footer)',
    'description': '''
Dong goi phan rebrand trang tuyen dung cong khai thanh CODE.

Truoc day phan nay duoc lam bang trinh soan website cua Odoo nen chi nam trong
bang ir_ui_view / website / res_company cua dung mot DB (neondb). Dung DB moi
la mat sach, web tra ve bo mac dinh cua Odoo. Module nay khien branding di theo
repo. Chi tiet: xem README.md.
''',
    'author': 'ISP490_G2 — Học Bá HRM',
    'category': 'Website',
    'license': 'LGPL-3',
    'depends': ['website', 'website_hr_recruitment'],
    'data': [
        'data/branding_data.xml',
        'views/website_branding_templates.xml',
        'views/recruitment_branding_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'hocba_website_branding/static/src/scss/branding.scss',
            'hocba_website_branding/static/src/js/apply_form_cv_required.js',
        ],
    },
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'application': False,
    'auto_install': False,
}
