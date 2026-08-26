"""Nối vòng đời nhân sự với hợp đồng: lên Chính thức là có hợp đồng.

Trước đây không luồng nào trong app tạo `hb.contract` — tuyển dụng, nhận việc,
thử việc, lên chính thức đều không — nên nhân viên mới lên chính thức không
xuất hiện trên bảng lương (bảng lọc theo hợp đồng `state = open`). Hook đặt ở
`hocba_payroll` vì module này phụ thuộc `hocba_employees`, không phải chiều
ngược lại.

Thiết kế: chỉ điền phần chắc chắn đúng — trạng thái Đang hiệu lực, hiệu lực từ
ngày lên chính thức, lương lấy theo hồ sơ nếu đã nhập. Loại hợp đồng, ngày ký,
thời hạn để HR bổ sung trong tab Hợp đồng của hồ sơ.
"""
from odoo import fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    def write(self, vals):
        res = super().write(vals)
        # Bắt ở write() chứ không chỉ trong _hocba_make_official(): HR Manager
        # đổi thẳng trạng thái trên form nhân viên cũng phải sinh hợp đồng.
        if vals.get('x_employment_status') == 'official':
            self._hb_ensure_official_contract()
        return res

    def _hb_ensure_official_contract(self):
        """Tạo hợp đồng hiệu lực cho NV vừa lên chính thức (idempotent).

        Bỏ qua người đã có hợp đồng `open` — không bao giờ để một nhân viên có
        hai hợp đồng cùng hiệu lực. Hợp đồng đã đóng (vd HĐ thử việc) KHÔNG
        chặn: hết thử việc lên chính thức thì đúng là phải có hợp đồng mới.
        """
        Contract = self.env['hb.contract'].sudo()
        today = fields.Date.context_today(self)
        for emp in self:
            if Contract.search_count([('employee_id', '=', emp.id),
                                      ('state', '=', 'open')]):
                continue
            version = emp.sudo().version_id
            wage = 0.0
            if version and 'wage' in version._fields:
                wage = version.wage or 0.0
            date_start = emp.x_official_date or today
            Contract.create({
                'name': 'HĐLĐ %s - %s' % (emp.x_employee_code or emp.id,
                                          emp.name),
                'employee_id': emp.id,
                'date_start': date_start,
                'wage': wage,
                'state': 'open',
            })
            emp.sudo().message_post(body=_(
                '📄 Đã tạo hợp đồng hiệu lực từ %(date)s%(wage)s. '
                'Vui lòng bổ sung loại hợp đồng, ngày ký và thời hạn trong tab '
                'Hợp đồng.') % {
                    'date': fields.Date.to_string(date_start),
                    'wage': (_(' với lương %s ₫') % '{:,.0f}'.format(wage)
                             if wage else _(' — CHƯA có mức lương')),
                })
        return True
