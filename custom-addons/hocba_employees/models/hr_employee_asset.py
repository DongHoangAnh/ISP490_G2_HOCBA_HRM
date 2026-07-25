from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrEmployeeAsset(models.Model):
    """F-006 (rút gọn): danh sách tài sản nhân viên ĐANG giữ.

    Không có vòng đời: thu hồi = xoá dòng; bàn giao = xoá dòng người cũ +
    thêm dòng người mới. Quyết định theo góp ý giảng viên, xem
    docs/superpowers/specs/2026-07-24-asset-simplify-design.md
    """
    _name = 'hr.employee.asset'
    _description = 'Tài sản nhân viên đang giữ'
    _order = 'employee_id, grant_date desc'

    employee_id = fields.Many2one(
        'hr.employee', string='Nhân viên giữ',
        required=True, ondelete='cascade', index=True)
    asset_type_id = fields.Many2one(
        'hocba.asset.type', string='Loại tài sản', required=True)
    asset_code = fields.Char(string='Mã tài sản', required=True)
    grant_date = fields.Date(
        string='Ngày cấp phát', required=True,
        default=fields.Date.context_today)
    condition_in = fields.Selection(
        selection=[('new', 'Mới'), ('good', 'Tốt'), ('fair', 'Trung bình')],
        string='Tình trạng khi cấp', required=True, default='good')

    # Odoo 19: _sql_constraints không còn được hỗ trợ → models.Constraint
    _asset_code_uniq = models.Constraint(
        'unique (asset_code)',
        'Mã tài sản này đang có trong danh sách — '
        'gỡ dòng của người đang giữ trước khi cấp lại.',
    )

    def _check_asset_code_free(self, codes, keep=None):
        """Chặn trùng mã TRƯỚC khi INSERT/UPDATE chạm SQL constraint.

        Không dùng @api.constrains được: SQL unique bắn psycopg2.IntegrityError
        ngay tại câu INSERT, tức TRƯỚC khi ORM chạy constrains, mà controller
        SPA chỉ bắt (AccessError, ValidationError, UserError) → route http trả
        500 thay vì báo lỗi inline. SQL constraint vẫn giữ vai trò chốt chặn
        cuối ở tầng DB.
        """
        codes = [c for c in codes if c]
        if not codes:
            return
        # Trùng ngay trong cùng một lô (import CSV, mass-edit): search() không
        # thấy vì các dòng này chưa/đang cùng được ghi.
        if len(codes) != len(set(codes)):
            dup_code = next(c for c in codes if codes.count(c) > 1)
            raise ValidationError(_(
                'Mã tài sản "%s" bị lặp trong cùng một lần cấp phát.') % dup_code)
        domain = [('asset_code', 'in', codes)]
        if keep:
            domain.append(('id', 'not in', keep.ids))
        dup = self.search(domain, limit=1)
        if dup:
            raise ValidationError(_(
                'Mã tài sản "%s" đang có trong danh sách — '
                'gỡ dòng của người đang giữ trước khi cấp lại.') % dup.asset_code)

    @api.model_create_multi
    def create(self, vals_list):
        self._check_asset_code_free([v.get('asset_code') for v in vals_list])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('asset_code'):
            # Ghi cùng một mã lên nhiều dòng thì tự nó đã trùng nhau.
            if len(self) > 1:
                raise ValidationError(_(
                    'Không thể gán mã "%s" cho %d dòng tài sản cùng lúc — '
                    'mỗi mã chỉ thuộc về một người.') % (vals['asset_code'], len(self)))
            self._check_asset_code_free([vals['asset_code']], keep=self)
        return super().write(vals)
