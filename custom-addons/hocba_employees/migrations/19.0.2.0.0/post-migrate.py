# Migration 19.0.2.0.0 — map field cổng thử việc cứng cũ (x_eval_*,
# x_trial_*, x_equip_grant_date) sang bước động hb.onboarding.step.
# Idempotent: NV đã có bước bị bỏ qua. Cột cũ GIỮ NGUYÊN để đối chiếu.
# Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md
from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    env['hr.employee']._hocba_migrate_legacy_gates()
