from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

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
    sla_days = fields.Integer(
        string='SLA (ngày)', default=0,
        help='Số ngày tối đa ứng viên được ở trong bước này; 0 = không áp SLA. '
             'Quá hạn → badge "Trễ SLA" trên kanban CV.',
    )

    @api.constrains('sla_days')
    def _check_sla_days(self):
        for stage in self:
            if stage.sla_days < 0:
                raise ValidationError('SLA (ngày) không được âm.')

    @api.model
    def action_reorder(self, ordered_ids):
        """Ghi lại sequence 10/20/30… theo thứ tự id truyền vào (kéo-thả từ SPA).
        Mirror hb.onboarding.template.action_reorder."""
        stages = self.browse([int(i) for i in ordered_ids])
        stages.check_access('write')
        for seq, stage in zip(range(10, 10 * len(stages) + 1, 10), stages):
            stage.sequence = seq
        return True

    @api.ondelete(at_uninstall=False)
    def _unlink_except_in_use(self):
        """Chặn xoá bằng thông báo dễ hiểu thay vì lỗi khoá ngoại thô."""
        Applicant = self.env['hr.applicant'].sudo().with_context(active_test=False)
        for stage in self:
            count = Applicant.search_count([('stage_id', '=', stage.id)])
            if count:
                raise UserError(
                    'Không thể xoá bước "%s": còn %s ứng viên (kể cả lưu trữ) '
                    'đang ở bước này. Hãy chuyển họ sang bước khác trước.'
                    % (stage.name, count))
        remaining = self.search_count([('id', 'not in', self.ids)])
        if not remaining:
            raise UserError('Quy trình phải còn ít nhất 1 bước.')

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
