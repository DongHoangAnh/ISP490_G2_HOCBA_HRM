{
    'name': 'Học Bá — Dịch vụ Nhân sự (Service)',
    'version': '19.0.1.0.0',
    'category': 'Human Resources',
    'summary': (
        'Yêu cầu dịch vụ nhân sự & góp ý: NV gửi đơn/câu hỏi/đánh giá tới HR '
        'hoặc Trưởng phòng, hội thoại 2 chiều, tuỳ chọn ẩn danh mức 2 '
        '(danh tính tách bảng riêng, không group nào đọc được).'
    ),
    'author': 'Học Bá HRM Team / Nhật Anh',
    'license': 'LGPL-3',
    # hocba_employees: hr.employee mở rộng (x_employment_status) + hr.department
    # hocba_notify:    hb.notification cho chuông SPA (P5)
    'depends': ['hocba_employees', 'hocba_notify'],
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/ir_config_parameter_data.xml',
        'data/hocba_hr_request_type_data.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
