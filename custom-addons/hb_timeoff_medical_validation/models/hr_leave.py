from odoo import models, fields, api, _


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    x_has_medical_doc = fields.Boolean(
        string='Có chứng từ y tế',
        compute='_compute_has_medical_doc',
        store=True,
    )

    @api.depends('attachment_ids')
    def _compute_has_medical_doc(self):
        for leave in self:
            leave.x_has_medical_doc = bool(leave.attachment_ids)

    def action_approve(self, check_state=True):
        # Ghi chú vào chatter khi HR duyệt đơn có yêu cầu chứng từ nhưng chưa đính kèm (không chặn)
        for leave in self.filtered(
            lambda l: l.leave_type_support_document and not l.x_has_medical_doc
        ):
            leave.message_post(
                body=_('Phê duyệt đơn nghỉ không có chứng từ y tế đính kèm.'),
                subtype_xmlid='mail.mt_note',
            )
        return super().action_approve(check_state=check_state)
