from odoo import api, fields, models

_ODOO_DEFAULT_STAGE_NAMES = [
    'New', 'Qualification', 'Initial Qualification',
    'First Interview', 'Second Interview',
    'Contract Proposal', 'Contract Signed',
    'Hồ sơ mới',
]


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

    @api.model
    def _hocba_cleanup_default_stages(self):
        """Xóa các stage mặc định của Odoo sau khi đã có Hocba stages.
        Reassign cả active lẫn archived applicants (active_test=False)
        để tránh ForeignKeyViolation.
        """
        old_stages = self.with_context(active_test=False).search(
            [('name', 'in', _ODOO_DEFAULT_STAGE_NAMES)]
        )
        if not old_stages:
            return

        fallback = self.env.ref(
            'hocba_recruitments.hb_stage_request', raise_if_not_found=False
        )
        if not fallback:
            fallback = self.search(
                [('id', 'not in', old_stages.ids)], order='sequence asc', limit=1
            )

        if fallback:
            self.env['hr.applicant'].with_context(active_test=False).search(
                [('stage_id', 'in', old_stages.ids)]
            ).write({'stage_id': fallback.id})

        old_stages.unlink()
