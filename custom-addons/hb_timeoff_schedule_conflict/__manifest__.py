{
    'name': 'HB Time Off — Phát hiện Xung đột Lịch Dạy',
    'version': '19.0.2.0.0',
    'category': 'Human Resources/Time Off',
    'summary': (
        'Phát hiện xung đột giữa đơn xin nghỉ của giảng viên và lịch dạy đã xác nhận; '
        'dò xung đột bất đồng bộ (BR-030); yêu cầu phê duyệt Academic Manager '
        'khi xung đột (AUT-TO-002 / FUNC-TO-004)'
    ),
    'author': 'Học Bá HRM Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays', 'hb_timeoff_policy'],
    'data': [
        'security/res_groups.xml',
        'data/ir_cron_data.xml',
        'views/hr_leave_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
