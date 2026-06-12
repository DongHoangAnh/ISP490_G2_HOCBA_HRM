import base64
import io
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# BR-042: Export filename format
FILENAME_TPL = 'HocBa_LeaveReport_{ym}_{dept}.xlsx'


class HbTimeoffExportWizard(models.TransientModel):
    _name = 'hb.timeoff.export.wizard'
    _description = 'Xuất báo cáo nghỉ phép (Excel / PDF)'

    date_from = fields.Date(
        string='Từ ngày',
        required=True,
        default=lambda self: fields.Date.today().replace(month=1, day=1),
    )
    date_to = fields.Date(
        string='Đến ngày',
        required=True,
        default=fields.Date.today,
    )
    department_id = fields.Many2one(
        'hr.department',
        string='Phòng ban',
        help='Để trống để xuất tất cả phòng ban.',
    )
    export_type = fields.Selection(
        [('excel', 'Excel (.xlsx)'), ('pdf', 'PDF')],
        string='Định dạng',
        required=True,
        default='excel',
    )

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self):
        for rec in self:
            if rec.date_from > rec.date_to:
                raise UserError(_('Ngày bắt đầu phải trước ngày kết thúc.'))
            # BR: Max 24 months
            delta = (rec.date_to - rec.date_from).days
            if delta > 730:
                raise UserError(_('Khoảng thời gian tối đa là 24 tháng.'))

    def action_export(self):
        self.ensure_one()
        if self.export_type == 'excel':
            return self._export_excel()
        return self._export_pdf()

    # ------------------------------------------------------------------ #
    #  Excel export                                                         #
    # ------------------------------------------------------------------ #

    def _export_excel(self):
        try:
            import xlsxwriter
        except ImportError:
            raise UserError(_('Thư viện xlsxwriter chưa được cài đặt trên server.'))

        domain = self._build_domain()
        records = self.env['hb.timeoff.leave.analysis'].search(domain)

        output = io.BytesIO()
        wb = xlsxwriter.Workbook(output, {'in_memory': True})

        fmt_title = wb.add_format({
            'bold': True, 'font_size': 13, 'align': 'center',
            'bg_color': '#1F497D', 'font_color': '#FFFFFF', 'border': 1,
        })
        fmt_header = wb.add_format({
            'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center',
        })
        fmt_cell = wb.add_format({'border': 1})
        fmt_num = wb.add_format({'border': 1, 'num_format': '#,##0.0'})
        fmt_risk = wb.add_format({'border': 1, 'bg_color': '#FFE0E0', 'bold': True})

        # --- Sheet 1: Leave by Department ---
        ws1 = wb.add_worksheet('W1 - Theo Phòng ban')
        ws1.set_column(0, 0, 30)
        ws1.set_column(1, 2, 15)
        ws1.merge_range('A1:C1', 'Nghỉ phép theo Phòng ban', fmt_title)
        ws1.write_row(1, 0, ['Phòng ban', 'Số đơn', 'Tổng ngày'], fmt_header)
        dept_data = {}
        for r in records:
            dept_name = r.department_id.name if r.department_id else '(Không phòng ban)'
            dept_data.setdefault(dept_name, [0, 0.0])
            dept_data[dept_name][0] += 1
            dept_data[dept_name][1] += r.number_of_days
        for row_i, (dept, (cnt, days)) in enumerate(
            sorted(dept_data.items(), key=lambda x: -x[1][1]), start=2
        ):
            ws1.write(row_i, 0, dept, fmt_cell)
            ws1.write(row_i, 1, cnt, fmt_num)
            ws1.write(row_i, 2, days, fmt_num)

        # --- Sheet 2: Monthly Trend ---
        ws2 = wb.add_worksheet('W2 - Xu hướng Tháng')
        ws2.set_column(0, 0, 12)
        ws2.set_column(1, 2, 15)
        ws2.merge_range('A1:C1', 'Xu hướng nghỉ phép theo tháng', fmt_title)
        ws2.write_row(1, 0, ['Tháng/Năm', 'Số đơn', 'Tổng ngày'], fmt_header)
        month_data = {}
        for r in records:
            key = '%02d/%04d' % (r.leave_month, r.leave_year)
            month_data.setdefault(key, [0, 0.0])
            month_data[key][0] += 1
            month_data[key][1] += r.number_of_days
        for row_i, (ym, (cnt, days)) in enumerate(sorted(month_data.items()), start=2):
            ws2.write(row_i, 0, ym, fmt_cell)
            ws2.write(row_i, 1, cnt, fmt_num)
            ws2.write(row_i, 2, days, fmt_num)

        # --- Sheet 3: Sick Leave Frequency ---
        ws3 = wb.add_worksheet('W3 - Nghỉ ốm')
        ws3.set_column(0, 0, 30)
        ws3.set_column(1, 2, 15)
        ws3.merge_range('A1:C1', 'Tần suất Nghỉ ốm theo Nhân viên', fmt_title)
        ws3.write_row(1, 0, ['Nhân viên', 'Số lần nghỉ ốm', 'Số ngày'], fmt_header)
        sick_data = {}
        for r in records.filtered('is_sick_leave'):
            emp_name = r.employee_id.name or '?'
            sick_data.setdefault(emp_name, [0, 0.0])
            sick_data[emp_name][0] += 1
            sick_data[emp_name][1] += r.number_of_days
        for row_i, (emp, (cnt, days)) in enumerate(
            sorted(sick_data.items(), key=lambda x: -x[1][0]), start=2
        ):
            fmt = fmt_risk if cnt >= 4 else fmt_cell
            ws3.write(row_i, 0, emp, fmt)
            ws3.write(row_i, 1, cnt, fmt)
            ws3.write(row_i, 2, days, fmt)

        # --- Sheet 4: Top Absent Employees ---
        ws4 = wb.add_worksheet('W4 - Vắng nhiều nhất')
        ws4.set_column(0, 0, 30)
        ws4.set_column(1, 3, 15)
        ws4.merge_range('A1:D1', 'Nhân viên vắng nhiều nhất', fmt_title)
        ws4.write_row(1, 0, ['Nhân viên', 'Phòng ban', 'Số đơn', 'Tổng ngày'], fmt_header)
        emp_data = {}
        for r in records:
            eid = r.employee_id.id
            emp_data.setdefault(eid, {
                'name': r.employee_id.name or '?',
                'dept': r.department_id.name if r.department_id else '',
                'cnt': 0, 'days': 0.0,
            })
            emp_data[eid]['cnt'] += 1
            emp_data[eid]['days'] += r.number_of_days
        for row_i, info in enumerate(
            sorted(emp_data.values(), key=lambda x: -x['days'])[:50], start=2
        ):
            ws4.write(row_i, 0, info['name'], fmt_cell)
            ws4.write(row_i, 1, info['dept'], fmt_cell)
            ws4.write(row_i, 2, info['cnt'], fmt_num)
            ws4.write(row_i, 3, info['days'], fmt_num)

        # --- Sheet 5: Burnout Risk ---
        ws5 = wb.add_worksheet('W6 - Burnout Risk')
        ws5.set_column(0, 0, 30)
        ws5.set_column(1, 5, 18)
        ws5.merge_range('A1:F1', 'Cảnh báo Burnout Nhân viên', fmt_title)
        ws5.write_row(
            1, 0,
            ['Nhân viên', 'Phòng ban', 'Nghỉ ốm (3T)', 'Ngày vắng (3T)',
             'Số dư phép', 'Lý do'],
            fmt_header,
        )
        burnout_domain = []
        if self.department_id:
            burnout_domain = [('department_id', '=', self.department_id.id)]
        burnout_recs = self.env['hb.timeoff.burnout.line'].search(burnout_domain)
        for row_i, b in enumerate(
            sorted(burnout_recs, key=lambda x: (not x.burnout_risk, -x.sick_leave_count_3m)),
            start=2,
        ):
            fmt = fmt_risk if b.burnout_risk else fmt_cell
            ws5.write(row_i, 0, b.employee_id.name or '?', fmt)
            ws5.write(row_i, 1, b.department_id.name if b.department_id else '', fmt)
            ws5.write(row_i, 2, b.sick_leave_count_3m, fmt)
            ws5.write(row_i, 3, b.total_absence_days_3m, fmt)
            ws5.write(row_i, 4, b.remaining_leave_balance, fmt)
            ws5.write(row_i, 5, b.risk_reason or '', fmt)

        wb.close()

        dept_label = self.department_id.name.replace(' ', '_') if self.department_id else 'AllDepts'
        filename = FILENAME_TPL.format(
            ym=fields.Date.today().strftime('%Y%m'),
            dept=dept_label,
        )

        attachment = self.env['ir.attachment'].sudo().create({
            'name': filename,
            'type': 'binary',
            'datas': base64.b64encode(output.getvalue()),
            'res_model': self._name,
            'res_id': self.id,
        })
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%d/%s?download=true' % (attachment.id, filename),
            'target': 'new',
        }

    # ------------------------------------------------------------------ #
    #  PDF export                                                           #
    # ------------------------------------------------------------------ #

    def _export_pdf(self):
        return self.env.ref(
            'hb_timeoff_analytics.action_report_hb_timeoff_analytics'
        ).report_action(self)

    # ------------------------------------------------------------------ #
    #  Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _build_domain(self):
        domain = [
            ('date_from', '>=', fields.Datetime.from_string(
                '%s 00:00:00' % self.date_from)),
            ('date_to', '<=', fields.Datetime.from_string(
                '%s 23:59:59' % self.date_to)),
        ]
        if self.department_id:
            domain.append(('department_id', '=', self.department_id.id))
        return domain
