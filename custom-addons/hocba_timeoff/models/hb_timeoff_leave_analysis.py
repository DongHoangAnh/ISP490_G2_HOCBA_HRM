from odoo import fields, models, tools


class HbTimeoffLeaveAnalysis(models.Model):
    """Read-only SQL view of approved leave requests — base for Widgets 1-4."""

    _name = 'hb.timeoff.leave.analysis'
    _description = 'Phân tích Đơn Nghỉ phép (Học Bá)'
    _auto = False
    _rec_name = 'employee_id'
    _order = 'date_from desc, employee_id'

    employee_id = fields.Many2one('hr.employee', string='Nhân viên', readonly=True)
    department_id = fields.Many2one('hr.department', string='Phòng ban', readonly=True)
    holiday_status_id = fields.Many2one('hr.leave.type', string='Loại nghỉ phép', readonly=True)
    date_from = fields.Datetime(string='Ngày bắt đầu', readonly=True)
    date_to = fields.Datetime(string='Ngày kết thúc', readonly=True)
    number_of_days = fields.Float(string='Số ngày', readonly=True)
    leave_year = fields.Integer(string='Năm', readonly=True)
    leave_month = fields.Integer(string='Tháng', readonly=True)
    is_sick_leave = fields.Boolean(string='Nghỉ ốm', readonly=True)
    is_emergency_leave = fields.Boolean(string='Nghỉ khẩn cấp', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'hb_timeoff_leave_analysis')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW hb_timeoff_leave_analysis AS (
                SELECT
                    hl.id                                          AS id,
                    hl.employee_id                                 AS employee_id,
                    v.department_id                                AS department_id,
                    hl.holiday_status_id                           AS holiday_status_id,
                    hl.date_from                                   AS date_from,
                    hl.date_to                                     AS date_to,
                    hl.number_of_days                              AS number_of_days,
                    EXTRACT(year  FROM hl.date_from)::int          AS leave_year,
                    EXTRACT(month FROM hl.date_from)::int          AS leave_month,
                    COALESCE(hlt.support_document, False)          AS is_sick_leave,
                    COALESCE(hlt.x_is_emergency_type, False)       AS is_emergency_leave
                FROM hr_leave hl
                INNER JOIN hr_employee    e   ON e.id  = hl.employee_id
                                              AND e.active IS True
                LEFT  JOIN hr_version     v   ON v.id  = e.current_version_id
                INNER JOIN hr_leave_type  hlt ON hlt.id = hl.holiday_status_id
                WHERE hl.state = 'validate'
            )
        """)
