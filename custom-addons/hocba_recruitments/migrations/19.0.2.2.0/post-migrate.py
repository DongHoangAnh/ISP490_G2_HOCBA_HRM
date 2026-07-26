# Migration 19.0.2.2.0 — Cấu hình tuyển dụng (spec 2026-07-23-recruitment-config-design.md)
# DB đã cài bản cũ: XML stages đổi sang noupdate="1" nên không tự ghi nữa →
# tự tay (1) set cờ noupdate cho 10 stage xmlid để admin sửa không bị ghi đè,
# (2) seed sla_days mặc định cho stage chưa đặt (0/NULL).

STAGE_SLA_DEFAULTS = {
    'hb_stage_screening': 1,
    'hb_stage_schedule': 1,
    'hb_stage_invite': 1,
    'hb_stage_result': 1,
    'hb_stage_offer': 1,
    'hb_stage_onboarding': 2,
}

STAGE_XMLIDS = [
    'hb_stage_request', 'hb_stage_sourcing', 'hb_stage_screening',
    'hb_stage_schedule', 'hb_stage_invite', 'hb_stage_interview',
    'hb_stage_result', 'hb_stage_offer', 'hb_stage_onboarding',
    'hb_stage_hired',
]


def migrate(cr, version):
    cr.execute("""
        UPDATE ir_model_data SET noupdate = TRUE
        WHERE module = 'hocba_recruitments' AND name = ANY(%s)
    """, (STAGE_XMLIDS,))
    for name, days in STAGE_SLA_DEFAULTS.items():
        cr.execute("""
            UPDATE hr_recruitment_stage s SET sla_days = %s
            FROM ir_model_data d
            WHERE d.module = 'hocba_recruitments' AND d.name = %s
              AND d.model = 'hr.recruitment.stage' AND d.res_id = s.id
              AND COALESCE(s.sla_days, 0) = 0
        """, (days, name))
