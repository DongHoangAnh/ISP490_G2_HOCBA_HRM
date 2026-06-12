from odoo import fields, models


class HrRecruitmentStageHocBaExt(models.Model):
    _inherit = 'hr.recruitment.stage'

    # ── Sheet 7.1 — Quy trình tuyển dụng ────────────────────────────────────
    success_criteria = fields.Text(
        string='Tiêu chí thành công',
        help='Điều kiện để coi bước này hoàn thành đúng nghĩa',
    )
    support_person = fields.Char(
        string='Người hỗ trợ',
        help='Bộ phận / cá nhân phối hợp hỗ trợ trong bước này',
    )
