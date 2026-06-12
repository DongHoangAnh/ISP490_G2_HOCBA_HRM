{
    'name': 'Tuyển dụng Học Bá',
    'version': '19.0.2.0.0',
    'author': 'Học Bá Education',
    'license': 'LGPL-3',
    'category': 'Human Resources/Recruitment',
    'summary': 'Mở rộng tuyển dụng Học Bá — Pipeline Kanban, badge PUBLISHED, trình độ giảng viên',
    'description': '''
        Module mở rộng hr_recruitment cho Học Bá Education.
        - x_published: toggle Đăng tuyển (badge PUBLISHED xanh trên Kanban)
        - x_teaching_level: HSK2 / HSK3 / TOCFL / N/A (Tab Recruitment)
        - x_required_sessions_per_week: số buổi/tuần tối thiểu
        - Constraint: không trùng tên vị trí trong cùng phòng ban (active)
        - Constraint: phòng Giảng viên / Trợ giảng bắt buộc chọn trình độ ≠ N/A
    ''',
    'depends': ['hr_recruitment'],
    'data': [
        'security/ir.model.access.csv',
        'data/hr_recruitment_stages.xml',
        'data/hb_recruitment_request_sequence.xml',
        'data/hb_job_positions.xml',
        'data/hb_recruitment_request_data.xml',
        'data/hb_applicant_data.xml',
        'data/hb_applicant_data2.xml',
        'data/hb_applicant_data3.xml',
        'data/hb_interview_results.xml',
        'data/hb_mail_templates.xml',
        'views/hr_recruitment_stage_views.xml',
        'views/hr_job_form_inherit.xml',
        'views/hr_applicant_kanban.xml',
        'views/hb_recruitment_request_views.xml',
        'views/hb_cv_list_views.xml',
        'views/hb_interview_list_views.xml',
        'views/hb_interview_slot_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
