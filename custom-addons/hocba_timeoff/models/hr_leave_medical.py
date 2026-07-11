from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

ALLOWED_MIME = frozenset({'application/pdf', 'image/jpeg', 'image/png'})
MAX_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    x_has_medical_doc = fields.Boolean(
        string='Có chứng từ y tế',
        compute='_compute_has_medical_doc',
        store=True,
    )
    x_medical_override = fields.Boolean(
        string='Bỏ qua yêu cầu chứng từ',
        default=False,
        copy=False,
        tracking=True,
    )
    x_medical_override_reason = fields.Text(
        string='Lý do bỏ qua chứng từ',
        copy=False,
    )

    @api.depends('attachment_ids')
    def _compute_has_medical_doc(self):
        for leave in self:
            leave.x_has_medical_doc = bool(leave.attachment_ids)

    def _check_attachment_file_types(self):
        """BR-012: Validate file type và size cho mọi attachment trên đơn nghỉ ốm."""
        for leave in self:
            if not leave.leave_type_support_document:
                continue
            for att in leave.attachment_ids:
                if att.mimetype not in ALLOWED_MIME:
                    raise ValidationError(
                        _('File "%s" không được chấp nhận. Chỉ chấp nhận PDF, JPG, PNG.')
                        % att.name
                    )
                if att.file_size > MAX_SIZE_BYTES:
                    raise ValidationError(
                        _('File "%s" quá lớn (%.1f MB). Tối đa 5 MB mỗi file.')
                        % (att.name, att.file_size / 1024 / 1024)
                    )

    def _validate_medical_requirement(self):
        """BR-011 (đã nới): chứng từ y tế KHÔNG còn bắt buộc để duyệt đơn nghỉ ốm.

        Trước đây thiếu chứng từ thì chỉ HR/Admin mới override duyệt được; nay
        người duyệt nào (HR hoặc Trưởng phòng) cũng duyệt được dù chưa có chứng
        từ — chỉ ghi chú lại vào chatter để truy vết. BR-012 vẫn giữ: nếu CÓ
        đính kèm thì kiểm tra định dạng/dung lượng.
        """
        self._check_attachment_file_types()
        for leave in self:
            if not leave.leave_type_support_document:
                continue
            if leave.attachment_ids:
                continue  # đã có chứng từ, type/size đã kiểm ở trên

            # Không có chứng từ: vẫn cho duyệt (không còn chỉ mỗi HR), chỉ log.
            if leave.x_medical_override and leave.x_medical_override_reason:
                leave.message_post(
                    body=_('Duyệt đơn nghỉ ốm và bỏ qua yêu cầu chứng từ y tế. '
                           'Lý do: %s') % leave.x_medical_override_reason,
                    subtype_xmlid='mail.mt_note',
                )
            else:
                leave.message_post(
                    body=_('Đơn nghỉ ốm được duyệt khi chưa có chứng từ y tế.'),
                    subtype_xmlid='mail.mt_note',
                )

    def action_confirm(self):
        # BR-012: validate file type/size tại Draft → Confirm (chưa yêu cầu có file)
        self._check_attachment_file_types()
        return super().action_confirm()

    def action_approve(self, check_state=True):
        # BR-011, BR-012: validate đầy đủ tại Confirm → Approve
        self._validate_medical_requirement()
        return super().action_approve(check_state=check_state)
