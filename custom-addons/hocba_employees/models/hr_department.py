from odoo import models, fields, api
from odoo.exceptions import UserError


class HrDepartment(models.Model):
    _inherit = 'hr.department'

    x_function_desc = fields.Char(
        string='Chức năng phòng ban',
        help='Mô tả ngắn chức năng nghiệp vụ của phòng ban (theo Lookup 8.4 Lark).',
    )

    @api.ondelete(at_uninstall=False)
    def _prevent_delete_with_members_or_children(self):
        """Chặn xóa cứng phòng ban còn nhân viên hoặc còn phòng con.
        Người dùng nên LƯU TRỮ (active=False) thay vì xóa — giữ lịch sử."""
        for dept in self:
            if dept.member_ids:
                raise UserError(
                    "Phòng ban '%s' còn %d nhân viên. Vui lòng chuyển nhân viên "
                    "sang phòng khác trước, hoặc lưu trữ phòng ban."
                    % (dept.name, len(dept.member_ids)))
            if dept.child_ids:
                raise UserError(
                    "Phòng ban '%s' còn phòng ban con. Vui lòng xử lý phòng con "
                    "trước, hoặc lưu trữ phòng ban." % dept.name)
