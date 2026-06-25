{
    'name': 'Học Bá — Nghỉ phép (Time Off)',
    'version': '19.0.11.0.0',
    'category': 'Human Resources/Time Off',
    'summary': (
        'Module nghỉ phép hợp nhất cho Trung tâm Học Bá: cấu hình loại nghỉ, '
        'chính sách theo loại NV, nghỉ khẩn cấp, xác thực chứng từ y tế, '
        'phát hiện xung đột lịch dạy, cron nhắc nhở, báo cáo & phân tích.'
    ),
    'author': 'Học Bá HRM Team',
    'license': 'LGPL-3',
    'depends': ['hr_holidays'],
    'data': [
        # ---- Security (groups -> access -> record rules) ----
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'security/hb_timeoff_analytics_rules.xml',

        # ---- Seed data (config trước, mở rộng/policy sau) ----
        'data/hr_leave_type_data.xml',
        'data/hr_leave_accrual_plan_data.xml',
        'data/hr_leave_mandatory_day_data.xml',
        'data/resource_calendar_leaves_data.xml',
        'data/hb_sick_leave_support_doc.xml',
        'data/hb_emergency_leave_type_flag.xml',
        'data/hb_timeoff_policy_rule_data.xml',
        'data/ir_cron_reminder_data.xml',
        'data/ir_cron_schedule_conflict_data.xml',

        # ---- Report ----
        'report/hb_timeoff_analytics_pdf.xml',

        # ---- Wizard ----
        'wizard/hb_timeoff_export_wizard_views.xml',

        # ---- Views (action trước menu) ----
        'views/hb_timeoff_policy_rule_views.xml',
        'views/hr_employee_views.xml',
        'views/hr_leave_emergency_views.xml',
        'views/hr_leave_medical_views.xml',
        'views/hr_leave_schedule_conflict_views.xml',
        'views/hb_leave_analysis_views.xml',
        'views/hr_holidays_dashboard_views.xml',
        'views/menu_policy.xml',
        'views/menu_analytics.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'hocba_timeoff/static/src/css/hr_holidays_modern.css',
            'hocba_timeoff/static/src/js/hr_holidays_modern.js',
            'hocba_timeoff/static/src/xml/dashboard.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'application': False,
}
