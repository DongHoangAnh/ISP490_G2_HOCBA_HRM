import pytz
from datetime import datetime, time as dt_time
from markupsafe import Markup, escape
from psycopg2 import IntegrityError

from odoo import http, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request


def _d(v):
    """date/datetime → chuỗi ISO (None-safe)."""
    return v.isoformat() if v else None


# Map key payload (camelCase) -> field hr.applicant cho form Thêm/Sửa CV.
# 'int' đánh dấu field many2one cần ép kiểu id.
APP_FORM_FIELDS = {
    'name': ('partner_name', 'str'),
    'phone': ('partner_phone', 'str'),
    'email': ('email_from', 'str'),
    'jobId': ('job_id', 'int'),
    'dateReceived': ('date_received', 'str'),
    'ctv': ('ctv_tuyen_dung', 'str'),
    'cvLink': ('cv_link', 'str'),
    'cvResult': ('cv_filter_result', 'str'),
    'cvNote': ('cv_note', 'str'),
    'callStatus': ('call_status', 'str'),
    'interviewDate': ('interview_date', 'str'),
    'interviewTime': ('interview_time', 'str'),
    'interviewer': ('interviewer_name', 'str'),
    'stageId': ('stage_id', 'int'),
    # Sheet 7.5/7.6 — Phỏng vấn & Offer
    'attendanceStatus': ('attendance_status', 'str'),
    'interviewResult': ('interview_result', 'str'),
    'offerContent': ('offer_content', 'str'),
    'startDate': ('start_date', 'str'),
    'offerNote': ('offer_note', 'str'),
    'candidateConfirmed': ('candidate_confirmed', 'str'),
}

# Map key payload (camelCase) -> field hr.job cho form Thêm/Sửa vị trí.
JOB_FORM_FIELDS = {
    'name': ('name', 'str'),
    'depId': ('department_id', 'int'),
    'status': ('recruitment_status', 'str'),
    'published': ('x_published', 'bool'),
    'jdLink': ('jd_google_link', 'str'),
    'expected': ('no_of_recruitment', 'num'),
    'teachingLevel': ('x_teaching_level', 'str'),
    'sessionsPerWeek': ('x_required_sessions_per_week', 'num'),
    'description': ('description', 'str'),
}

# Map key payload (camelCase) -> field hb.recruitment.request cho form Thêm/Sửa.
REQUEST_FORM_FIELDS = {
    'dateRequest': ('date_request', 'str'),
    'depId': ('department_id', 'int'),
    'jobId': ('job_id', 'int'),
    'jobTitle': ('job_title', 'str'),
    'jdLink': ('jd_link', 'str'),
    'qty': ('qty_expected', 'num'),
    'reason': ('reason', 'str'),
    'level': ('level', 'str'),
    'education': ('education', 'str'),
    'experienceYears': ('experience_years', 'float'),
    'skillDescription': ('skill_description', 'str'),
    'languageRequirement': ('language_requirement', 'str'),
    'expectedStartDate': ('expected_start_date', 'str'),
    'salaryRange': ('salary_range', 'str'),
    'salaryFrom': ('salary_from', 'float'),
    'salaryTo': ('salary_to', 'float'),
    'workType': ('work_type', 'str'),
    'note': ('note', 'str'),
}

# action SPA -> method workflow trên hb.recruitment.request
REQUEST_ACTIONS = {
    'submit': 'action_submit',
    'approve': 'action_approve',
    'close': 'action_close',
    'refuse': 'action_refuse',
    'reset': 'action_reset_draft',
}

# Tách vai theo sheet quy trình: TBP (người order) chỉ GỬI DUYỆT / mở lại nháp;
# DUYỆT / TỪ CHỐI / ĐÓNG phiếu là việc của BP tuyển dụng/HR (_is_hr).
REQUEST_HR_ACTIONS = frozenset({'approve', 'refuse', 'close'})


def _conv(typ, v):
    """Ép kiểu giá trị payload theo loại field."""
    if typ == 'int':
        return int(v) if v else False
    if typ == 'num':
        return int(v) if v not in ('', None) else 0
    if typ == 'float':
        return float(v) if v not in ('', None) else 0.0
    if typ == 'bool':
        return bool(v)
    return v if v not in ('', None) else False


class HocBaTuyenDung(http.Controller):

    # ------------------------------------------------------------------
    # JSON API cho SPA Học Bá HRM (features/recruitment).
    # Spec: docs/SPEC_API_RECRUITMENT.md · Owner FE: Việt.
    # Quy ước: docs/QUY_UOC_FRONTEND.md (camelCase, ngày ISO, lỗi {error}).
    # Đọc: mọi user đăng nhập. Ghi (thêm/sửa/đổi stage): chỉ nhóm tuyển dụng.
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Phân quyền tuyển dụng (theo họp phân quyền):
    #   - HR toàn quyền = Admin (group_system) / HR Manager / nhóm tuyển dụng
    #     → xem & thao tác MỌI phòng ban.
    #   - Trưởng phòng = người đứng manager_id của phòng ban (gồm phòng con)
    #     → chỉ thao tác dữ liệu tuyển dụng THUỘC phòng mình.
    # ------------------------------------------------------------------

    def _has_recruit_group(self):
        u = request.env.user
        return (u.has_group('hr_recruitment.group_hr_recruitment_user')
                or u.has_group('hr_recruitment.group_hr_recruitment_manager'))

    def _is_hr(self):
        """HR toàn quyền tuyển dụng (xem/sửa mọi phòng ban)."""
        u = request.env.user
        return (u.has_group('base.group_system')
                or u.has_group('hr.group_hr_manager')
                or self._has_recruit_group())

    def _is_admin(self):
        """Chỉ Admin hệ thống — dùng cho màn Cấu hình tuyển dụng."""
        return request.env.user.has_group('base.group_system')

    def _managed_department_ids(self):
        """Phòng ban (gồm phòng con) mà user làm trưởng phòng (manager_id)."""
        emp = request.env.user.employee_id
        if not emp:
            return []
        Dept = request.env['hr.department'].sudo()
        managed = Dept.search([('manager_id', '=', emp.id)])
        if not managed:
            return []
        result, frontier = set(managed.ids), managed
        while frontier:
            children = Dept.search([('parent_id', 'in', frontier.ids)])
            frontier = children.filtered(lambda d: d.id not in result)
            result.update(frontier.ids)
        return list(result)

    def _is_dept_manager(self):
        return bool(self._managed_department_ids())

    def _is_recruiter(self):
        """Có quyền thao tác tuyển dụng (thêm/sửa/xóa/đổi stage):
        HR toàn quyền hoặc trưởng phòng (giới hạn phòng ban mình)."""
        return self._is_hr() or self._is_dept_manager()

    def _dept_scope_ids(self):
        """Phạm vi phòng ban được phép thao tác.
        None = không giới hạn (HR); list = chỉ các phòng này (trưởng phòng);
        [] = không có quyền nào."""
        if self._is_hr():
            return None
        return self._managed_department_ids()

    def _dep_in_scope(self, dep_id):
        """dep_id (int/False) có nằm trong phạm vi cho phép không."""
        scope = self._dept_scope_ids()
        if scope is None:
            return True
        return bool(dep_id) and dep_id in scope

    def _applicant_dep_id(self, a):
        """Phòng ban của ứng viên: ưu tiên field department_id, fallback theo vị trí."""
        return a.department_id.id or a.job_id.department_id.id or False

    def _forbidden(self, message='Bạn không có quyền với phòng ban này.'):
        return request.make_json_response(
            {'error': 'forbidden', 'message': message}, status=403)

    def _sel_labels(self, model, fname):
        """Dict {key: label} của field Selection (theo ngôn ngữ context)."""
        env = request.env
        return dict(env[model]._fields[fname]._description_selection(env))

    def _cv_row(self, a):
        """Một dòng CV cho SPA (wire format camelCase) — dùng cho cả list & detail."""
        Att = request.env['ir.attachment'].sudo()
        att = Att.search(
            [('res_model', '=', 'hr.applicant'), ('res_id', '=', a.id),
             ('description', '=', 'hb_cv')], order='id desc', limit=1)
        if not att:
            # CV nộp từ form công khai /jobs/apply: website form lưu attachment
            # thường (không nhãn hb_cv) → fallback file mới nhất của ứng viên.
            att = Att.search(
                [('res_model', '=', 'hr.applicant'), ('res_id', '=', a.id)],
                order='id desc', limit=1)
        row = {
            'id': a.id,
            'dateReceived': _d(a.date_received or (a.create_date and a.create_date.date())),
            'ctv': a.ctv_tuyen_dung or '',
            'name': a.partner_name or '',
            'phone': a.partner_phone or '',
            'email': a.email_from or '',
            'jobId': a.job_id.id or False,
            'jobName': a.job_id.name or '',
            'cvLink': a.cv_link or '',
            'cvFileId': att.id or False,
            'cvFileName': att.name or '',
            'cvFileUrl': ('/web/content/%s?download=false' % att.id) if att else '',
            'cvResult': a.cv_filter_result or '',
            'cvNote': a.cv_note or '',
            'callStatus': a.call_status or '',
            'interviewDate': _d(a.interview_date),
            'interviewTime': a.interview_time or '',
            'interviewer': a.interviewer_name or '',
            'stageId': a.stage_id.id or False,
            'stage': a.stage_id.name or '',
            # Phỏng vấn & Offer (Sheet 7.5/7.6)
            'attendanceStatus': a.attendance_status or '',
            'interviewResult': a.interview_result or '',
            'offerContent': a.offer_content or '',
            'startDate': _d(a.start_date),
            'offerNote': a.offer_note or '',
            'candidateConfirmed': a.candidate_confirmed or '',
            # Liên kết hồ sơ nhân viên (sau khi nhận việc)
            'employeeId': a.employee_id.id or False,
            'employeeName': a.employee_id.name or '',
            'employeeCode': a.employee_id.x_employee_code or '',
        }
        # SLA theo bước (spec 2026-07-23-recruitment-config-design.md)
        days, sla, overdue = a._hb_sla_state()
        row.update({'daysInStage': days, 'slaDays': sla, 'slaOverdue': overdue})
        return row

    def _meta(self):
        """Stages + jobs + nhãn select — cho kanban và form Thêm/Sửa."""
        env = request.env
        stages = env['hr.recruitment.stage'].sudo().search([], order='sequence, id')
        jobs = env['hr.job'].sudo().search([], order='name')
        return {
            'stages': [{'id': s.id, 'name': s.name, 'sequence': s.sequence,
                        'hiredStage': bool(s.hired_stage), 'slaDays': s.sla_days or 0}
                       for s in stages],
            'jobs': [{'id': j.id, 'name': j.name} for j in jobs],
            'cvResultLabels': self._sel_labels('hr.applicant', 'cv_filter_result'),
            'callStatusLabels': self._sel_labels('hr.applicant', 'call_status'),
            'attendanceLabels': self._sel_labels('hr.applicant', 'attendance_status'),
            'interviewResultLabels': self._sel_labels('hr.applicant', 'interview_result'),
        }

    def _app_vals(self, payload):
        """Lọc payload -> vals hr.applicant (whitelist + ép kiểu)."""
        vals = {}
        for key, (field, typ) in APP_FORM_FIELDS.items():
            if key not in payload:
                continue
            v = payload[key]
            if typ == 'int':
                vals[field] = int(v) if v else False
            else:
                vals[field] = v if v not in ('', None) else False
        return vals

    @http.route('/hocba-hrm/api/recruitment/cv', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_cv(self, **kw):
        """Danh sách CV ứng viên cho tab "Danh sách CV" (list + kanban).
        Trưởng phòng chỉ thấy ứng viên thuộc phòng ban mình quản lý."""
        env = request.env
        scope = self._dept_scope_ids()
        domain = []
        if scope is not None:
            domain = ['|', ('department_id', 'in', scope),
                      ('job_id.department_id', 'in', scope)]
        applicants = env['hr.applicant'].sudo().search(
            domain, order='date_received desc, id desc')
        data = {'isRecruiter': self._is_recruiter(),
                'rows': [self._cv_row(a) for a in applicants]}
        data.update(self._meta())
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/recruitment/applicant/<int:app_id>', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_applicant(self, app_id, **kw):
        """Chi tiết một CV/ứng viên."""
        a = request.env['hr.applicant'].sudo().browse(app_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(self._applicant_dep_id(a)):
            return self._forbidden()
        return request.make_json_response(self._cv_row(a))

    @http.route('/hocba-hrm/api/recruitment/cv', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_cv_create(self, **kw):
        """Thêm CV thủ công (chỉ nhóm tuyển dụng)."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data()
        vals = self._app_vals(payload)
        if not (vals.get('partner_name') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập họ tên ứng viên.'},
                status=400)
        if not self._is_hr():
            job_id = vals.get('job_id')
            dep_id = (request.env['hr.job'].sudo().browse(job_id).department_id.id
                      if job_id else False)
            if not self._dep_in_scope(dep_id):
                return self._forbidden('Vị trí không thuộc phòng ban bạn quản lý.')
        Applicant = request.env['hr.applicant'].sudo()
        # hr.applicant.name (tiêu đề đơn) tồn tại ở các bản Odoo cũ và bắt buộc;
        # Odoo 19 đã bỏ field này (dùng partner_name) -> chỉ set khi model còn field 'name'.
        if 'name' in Applicant._fields:
            vals.setdefault('name', vals['partner_name'])
        try:
            a = Applicant.create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._cv_row(a))

    @http.route('/hocba-hrm/api/recruitment/applicant/<int:app_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_applicant_update(self, app_id, **kw):
        """Cập nhật CV/ứng viên (chỉ nhóm tuyển dụng)."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        a = request.env['hr.applicant'].sudo().browse(app_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(self._applicant_dep_id(a)):
            return self._forbidden()
        vals = self._app_vals(request.get_json_data())
        if not self._is_hr() and vals.get('job_id'):
            new_dep = request.env['hr.job'].sudo().browse(vals['job_id']).department_id.id
            if not self._dep_in_scope(new_dep):
                return self._forbidden('Vị trí không thuộc phòng ban bạn quản lý.')
        try:
            if vals:
                a.write(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._cv_row(a))

    @http.route('/hocba-hrm/api/recruitment/applicant/<int:app_id>/cv-file',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_applicant_cv_upload(self, app_id, **kw):
        """Tải lên file CV (PDF…) cho ứng viên — lưu thành ir.attachment (chỉ nhóm tuyển dụng).
        Đánh dấu description='hb_cv' để phân biệt với file đính kèm khác."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        a = request.env['hr.applicant'].sudo().browse(app_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(self._applicant_dep_id(a)):
            return self._forbidden()
        f = request.httprequest.files.get('file')
        if not f:
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Thiếu file.'}, status=400)
        data = f.read()
        if not data:
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'File rỗng.'}, status=400)
        if len(data) > 15 * 1024 * 1024:
            return request.make_json_response(
                {'error': 'too_large', 'message': 'File vượt quá 15MB.'}, status=400)
        try:
            # Xoá file CV cũ (giữ 1 file CV mới nhất) rồi tạo file mới.
            request.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'hr.applicant'), ('res_id', '=', a.id),
                ('description', '=', 'hb_cv')]).unlink()
            request.env['ir.attachment'].sudo().create({
                'name': f.filename or 'cv.pdf',
                'raw': data,
                'res_model': 'hr.applicant',
                'res_id': a.id,
                'mimetype': f.mimetype or 'application/pdf',
                'description': 'hb_cv',
            })
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._cv_row(a))

    @http.route('/hocba-hrm/api/recruitment/applicant/<int:app_id>/stage',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_applicant_stage(self, app_id, **kw):
        """Đổi stage (kéo-thả kanban) — chỉ nhóm tuyển dụng."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        a = request.env['hr.applicant'].sudo().browse(app_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(self._applicant_dep_id(a)):
            return self._forbidden()
        stage_id = (request.get_json_data() or {}).get('stageId')
        if not stage_id:
            return request.make_json_response({'error': 'bad_request'}, status=400)
        try:
            a.write({'stage_id': int(stage_id)})
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._cv_row(a))

    def _sync_employee_code_sequence(self):
        """Đẩy sequence mã NV (hocba.employee.code) vượt qua mã lớn nhất đang có.
        Cần thiết khi dữ liệu được import với mã HB.xx cố định mà không nâng sequence,
        khiến next_by_code trả về mã đã tồn tại → trùng khoá."""
        env = request.env
        seq = env['ir.sequence'].sudo().search(
            [('code', '=', 'hocba.employee.code')], limit=1)
        if not seq:
            return
        env.cr.execute(r"""
            SELECT COALESCE(MAX(CAST(substring(x_employee_code FROM '[0-9]+$') AS INTEGER)), 0)
            FROM hr_employee
            WHERE x_employee_code ~ '^HB\.[0-9]+$'
        """)
        max_num = env.cr.fetchone()[0] or 0
        if seq.number_next_actual <= max_num:
            seq.number_next_actual = max_num + 1

    @http.route('/hocba-hrm/api/recruitment/applicant/<int:app_id>/create-employee',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_create_employee(self, app_id, **kw):
        """Tạo hồ sơ nhân viên từ ứng viên đã nhận việc (chỉ nhóm tuyển dụng).
        Map sẵn họ tên / vị trí / phòng ban / liên hệ, đặt trạng thái Thử việc,
        liên kết ngược applicant ↔ employee. Chống tạo trùng: nếu đã có thì trả về luôn."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        a = request.env['hr.applicant'].sudo().browse(app_id)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(self._applicant_dep_id(a)):
            return self._forbidden()
        # Đã tạo rồi → trả về hồ sơ hiện có (không tạo trùng).
        if a.employee_id:
            return request.make_json_response({
                'created': False, 'employeeId': a.employee_id.id,
                'employeeName': a.employee_id.name or '',
                'employeeCode': a.employee_id.x_employee_code or '',
                'message': 'Ứng viên này đã có hồ sơ nhân viên.',
            })
        if not (a.partner_name or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Ứng viên chưa có họ tên.'}, status=400)
        # Đồng bộ sequence mã NV để tránh trùng mã đã tồn tại (DB import lệch sequence).
        self._sync_employee_code_sequence()
        try:
            emp_vals = {
                'name': a.partner_name,
                'job_id': a.job_id.id or False,
                'job_title': a.job_id.name or False,
                'department_id': self._applicant_dep_id(a) or False,
                'work_email': a.email_from or False,
                'work_phone': a.partner_phone or False,
                'private_email': a.email_from or False,
                'private_phone': a.partner_phone or False,
                'x_employment_status': 'probation',
                'applicant_ids': [(6, 0, [a.id])],
            }
            # "Ngày nhận việc" ở Offer → ngày bắt đầu thử việc của hồ sơ NV
            # (đồng thời là mốc tính các cổng đánh giá thử việc tuần-2/tháng-1).
            if a.start_date:
                emp_vals['x_probation_start'] = a.start_date
            emp = request.env['hr.employee'].sudo().create(emp_vals)
            # Đảm bảo liên kết ngược (phòng khi o2m không tự set inverse).
            if not a.employee_id:
                a.write({'employee_id': emp.id})
        except IntegrityError:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Mã nhân sự bị trùng, vui lòng thử lại. Nếu vẫn lỗi, '
                            'kiểm tra dãy số mã nhân sự (sequence hocba.employee.code).'},
                status=400)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({
            'created': True, 'employeeId': emp.id,
            'employeeName': emp.name or '',
            'employeeCode': emp.x_employee_code or '',
        })

    # ------------------------------------------------------------------
    # Vị trí tuyển dụng / JD (hr.job) — tab "Vị trí / JD" của SPA.
    # ------------------------------------------------------------------

    def _job_row(self, j, detail=False):
        """Một vị trí tuyển dụng (wire format camelCase)."""
        data = {
            'id': j.id,
            'name': j.name or '',
            'depId': j.department_id.id or False,
            'depName': j.department_id.name or 'Chưa gán',
            'status': j.recruitment_status or '',
            # published = trạng thái hiển thị trên WEBSITE công khai (is_published) — nguồn sự thật.
            # x_published (badge nội bộ kanban) được giữ đồng bộ khi ghi.
            'published': bool(getattr(j, 'is_published', j.x_published)),
            # Link trang tuyển dụng công khai (/jobs/detail/<slug>) — để copy đi truyền thông.
            'websiteUrl': getattr(j, 'website_url', '') or '',
            'jdLink': j.jd_google_link or '',
            'expected': j.no_of_recruitment or 0,
            'hired': j.no_of_hired_employee or 0,
            'applications': j.application_count or 0,
            'newApplications': j.new_application_count or 0,
            'location': j.address_id.name or '',
            'teachingLevel': j.x_teaching_level or '',
            'requiresTeaching': bool(j.x_requires_teaching_level),
            'sessionsPerWeek': j.x_required_sessions_per_week or 0,
        }
        if detail:
            data['description'] = j.description or ''
        return data

    def _build_website_description(self, j):
        """Tổng hợp TOÀN BỘ thông tin vị trí + phiếu yêu cầu tuyển dụng gắn với nó
        thành nội dung JD công khai (website_description) cho trang /jobs.
        Ưu tiên phiếu ĐANG TUYỂN mới nhất; không có thì lấy phiếu mới nhất bất kỳ.
        Trả về Markup an toàn (đã escape)."""
        env = request.env

        def sel_label(rec, fname):
            val = rec[fname]
            if not val:
                return ''
            return dict(rec._fields[fname]._description_selection(env)).get(val, val)

        def money(v):
            return '{:,.0f}'.format(v).replace(',', '.')

        Req = env['hb.recruitment.request'].sudo()
        req = Req.search([('job_id', '=', j.id), ('state', '=', 'recruiting')],
                         order='id desc', limit=1)
        if not req:
            req = Req.search([('job_id', '=', j.id)], order='id desc', limit=1)

        # ── Thông tin tuyển dụng ─────────────────────────────────────────────
        info = []
        if j.department_id:
            info.append(('Phòng ban', j.department_id.name or ''))
        if req and req.level:
            info.append(('Cấp bậc', sel_label(req, 'level')))
        if j.no_of_recruitment:
            info.append(('Số lượng cần tuyển', str(int(j.no_of_recruitment))))
        if req and req.work_type:
            info.append(('Hình thức làm việc', sel_label(req, 'work_type')))
        if req:
            # Mức lương: ưu tiên mô tả chữ, fallback khoảng số, trống → Thoả thuận
            if req.salary_range:
                info.append(('Mức lương', req.salary_range))
            elif req.salary_from or req.salary_to:
                if req.salary_from and req.salary_to:
                    sal = '%s – %s VNĐ' % (money(req.salary_from), money(req.salary_to))
                else:
                    sal = 'Từ %s VNĐ' % money(req.salary_from or req.salary_to)
                info.append(('Mức lương', sal))
            else:
                info.append(('Mức lương', 'Thoả thuận'))
            if req.expected_start_date:
                info.append(('Thời gian nhận việc dự kiến',
                             req.expected_start_date.strftime('%d/%m/%Y')))
        if j.x_teaching_level and j.x_teaching_level != 'na':
            info.append(('Trình độ giảng dạy', sel_label(j, 'x_teaching_level')))
        if j.x_required_sessions_per_week:
            info.append(('Số buổi/tuần tối thiểu', str(int(j.x_required_sessions_per_week))))

        # ── Yêu cầu ứng viên (từ phiếu yêu cầu) ──────────────────────────────
        require = []
        if req:
            if req.education and req.education != 'none':
                require.append(('Bằng cấp tối thiểu', sel_label(req, 'education')))
            if req.experience_years:
                require.append(('Kinh nghiệm tối thiểu', '%g năm' % req.experience_years))
            if req.language_requirement:
                require.append(('Yêu cầu ngoại ngữ', req.language_requirement))
            if req.skill_description:
                require.append(('Kỹ năng yêu cầu', req.skill_description))

        def ul(rows):
            items = Markup('').join(
                Markup('<li class="mb-1"><strong>%s:</strong> %s</li>')
                % (k, escape(v).replace('\n', Markup('<br/>'))) for k, v in rows)
            return Markup('<ul>%s</ul>') % items

        parts = []
        if info:
            parts.append(Markup('<h4>Thông tin tuyển dụng</h4>%s') % ul(info))
        if require:
            parts.append(Markup('<h4 class="mt-4">Yêu cầu ứng viên</h4>%s') % ul(require))
        if j.description:
            desc = escape(j.description).replace('\n', Markup('<br/>'))
            parts.append(Markup('<h4 class="mt-4">Mô tả công việc</h4><p>%s</p>') % desc)
        if j.jd_google_link:
            link = j.jd_google_link
            parts.append(Markup('<p class="mt-3"><strong>JD chi tiết:</strong> '
                                '<a href="%s" target="_blank" rel="noreferrer">%s</a></p>') % (link, link))
        if not parts:
            return False
        body = Markup('').join(parts)
        return Markup('<section class="oe_structure"><div class="container my-3">%s</div></section>') % body

    def _sync_website_description(self, j):
        """Ghi lại website_description theo thông tin vị trí hiện tại (None-safe)."""
        if 'website_description' in j._fields:
            j.website_description = self._build_website_description(j) or False

    def _job_meta(self):
        env = request.env
        deps = env['hr.department'].sudo().search([], order='name')
        return {
            'departments': [{'id': d.id, 'name': d.name} for d in deps],
            'teachingLevels': self._sel_labels('hr.job', 'x_teaching_level'),
            'statusLabels': self._sel_labels('hr.job', 'recruitment_status'),
        }

    def _job_vals(self, payload):
        vals = {}
        for key, (field, typ) in JOB_FORM_FIELDS.items():
            if key not in payload:
                continue
            v = payload[key]
            if typ == 'int':
                vals[field] = int(v) if v else False
            elif typ == 'num':
                vals[field] = int(v) if v not in ('', None) else 0
            elif typ == 'bool':
                vals[field] = bool(v)
            else:
                vals[field] = v if v not in ('', None) else False
        # "published" đẩy lên website thật: set cả is_published (web) lẫn
        # x_published (badge kanban nội bộ) để hai nơi luôn khớp; đồng thời gắn
        # trạng thái tuyển theo published: bật -> Đang tuyển, tắt -> Dừng tuyển.
        if 'published' in payload:
            pub = bool(payload['published'])
            vals['is_published'] = pub
            vals['recruitment_status'] = 'recruiting' if pub else 'stopped'
        return vals

    @http.route('/hocba-hrm/api/recruitment/jobs', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_jobs(self, **kw):
        """Danh sách vị trí tuyển dụng / JD.
        Trưởng phòng chỉ thấy vị trí/phiếu thuộc phòng ban mình quản lý."""
        env = request.env
        scope = self._dept_scope_ids()
        job_domain = [] if scope is None else [('department_id', 'in', scope)]
        jobs = env['hr.job'].sudo().search(job_domain, order='name')
        data = {'isRecruiter': self._is_recruiter(),
                'rows': [self._job_row(j) for j in jobs]}
        data.update(self._job_meta())
        # Vị trí cần tuyển = phiếu yêu cầu ĐANG TUYỂN. Cần tuyển = SL phiếu;
        # đã tuyển = số ứng viên đã onboard thực tế (stage hired) của JD gắn với phiếu.
        req_domain = [('state', '=', 'recruiting')]
        if scope is not None:
            req_domain.append(('department_id', 'in', scope))
        reqs = env['hb.recruitment.request'].sudo().search(
            req_domain, order='department_id, job_title')
        level_labels = self._sel_labels('hb.recruitment.request', 'level')
        Applicant = env['hr.applicant'].sudo().with_context(active_test=False)
        data['requests'] = [{
            'id': r.id,
            'code': r.name or '',
            'jobTitle': r.job_title or '',
            'depId': r.department_id.id or False,
            'depName': r.department_id.name or 'Chưa gán phòng ban',
            'qty': r.qty_expected or 0,
            'hired': Applicant.search_count([
                ('job_id', '=', r.job_id.id), ('stage_id.hired_stage', '=', True),
            ]) if r.job_id else 0,
            'jobId': r.job_id.id or False,
            'jobName': r.job_id.name or '',
            'published': bool(getattr(r.job_id, 'is_published', False)) if r.job_id else False,
            'websiteUrl': (getattr(r.job_id, 'website_url', '') or '') if r.job_id else '',
            'levelLabel': level_labels.get(r.level, '') if r.level else '',
            'jdLink': r.jd_link or '',
        } for r in reqs]
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/recruitment/job/<int:job_id>', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_job(self, job_id, **kw):
        """Chi tiết vị trí (kèm mô tả JD)."""
        j = request.env['hr.job'].sudo().browse(job_id)
        if not j.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(j.department_id.id):
            return self._forbidden()
        return request.make_json_response(self._job_row(j, detail=True))

    @http.route('/hocba-hrm/api/recruitment/jobs', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_job_create(self, **kw):
        """Thêm vị trí tuyển dụng (chỉ nhóm tuyển dụng)."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        vals = self._job_vals(request.get_json_data())
        if not (vals.get('name') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập tên vị trí.'},
                status=400)
        if not self._is_hr() and not self._dep_in_scope(vals.get('department_id')):
            return self._forbidden('Vị trí phải thuộc phòng ban bạn quản lý.')
        try:
            j = request.env['hr.job'].sudo().create(vals)
            self._sync_website_description(j)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._job_row(j, detail=True))

    @http.route('/hocba-hrm/api/recruitment/job/<int:job_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_job_update(self, job_id, **kw):
        """Cập nhật vị trí / toggle đăng tuyển (chỉ nhóm tuyển dụng)."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        j = request.env['hr.job'].sudo().browse(job_id)
        if not j.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(j.department_id.id):
            return self._forbidden()
        vals = self._job_vals(request.get_json_data())
        if (not self._is_hr() and 'department_id' in vals
                and not self._dep_in_scope(vals['department_id'])):
            return self._forbidden('Vị trí phải thuộc phòng ban bạn quản lý.')
        try:
            if vals:
                j.write(vals)
            self._sync_website_description(j)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._job_row(j, detail=True))

    # ------------------------------------------------------------------
    # Phiếu yêu cầu tuyển dụng (hb.recruitment.request) — tab "Phiếu yêu cầu".
    # Workflow: draft -> submitted -> recruiting -> closed | refused.
    # ------------------------------------------------------------------

    def _req_row(self, r, detail=False):
        data = {
            'id': r.id,
            'name': r.name or '',
            'dateRequest': _d(r.date_request),
            'requester': r.requester_id.name or '',
            'depId': r.department_id.id or False,
            'depName': r.department_id.name or '',
            'jobId': r.job_id.id or False,
            'jobTitle': r.job_title or '',
            'jdLink': r.jd_link or '',
            'qty': r.qty_expected or 0,
            'reason': r.reason or '',
            'level': r.level or '',
            'state': r.state or '',
        }
        if detail:
            data.update({
                'education': r.education or '',
                'experienceYears': r.experience_years or 0,
                'skillDescription': r.skill_description or '',
                'languageRequirement': r.language_requirement or '',
                'expectedStartDate': _d(r.expected_start_date),
                'salaryRange': r.salary_range or '',
                'salaryFrom': r.salary_from or 0,
                'salaryTo': r.salary_to or 0,
                'workType': r.work_type or '',
                'manager': r.manager_id.name or '',
                'hrManager': r.hr_manager_id.name or '',
                'director': r.director_id.name or '',
                'refuseReason': r.refuse_reason or '',
                'note': r.note or '',
            })
        return data

    def _req_meta(self):
        env = request.env
        deps = env['hr.department'].sudo().search([], order='name')
        jobs = env['hr.job'].sudo().search([], order='name')
        return {
            'departments': [{'id': d.id, 'name': d.name} for d in deps],
            'jobs': [{'id': j.id, 'name': j.name, 'dep': j.department_id.id} for j in jobs],
            'reasonLabels': self._sel_labels('hb.recruitment.request', 'reason'),
            'levelLabels': self._sel_labels('hb.recruitment.request', 'level'),
            'educationLabels': self._sel_labels('hb.recruitment.request', 'education'),
            'workTypeLabels': self._sel_labels('hb.recruitment.request', 'work_type'),
            'stateLabels': self._sel_labels('hb.recruitment.request', 'state'),
        }

    def _req_vals(self, payload):
        vals = {}
        for key, (field, typ) in REQUEST_FORM_FIELDS.items():
            if key in payload:
                vals[field] = _conv(typ, payload[key])
        return vals

    @http.route('/hocba-hrm/api/recruitment/requests', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_requests(self, **kw):
        """Danh sách phiếu yêu cầu tuyển dụng.
        Trưởng phòng chỉ thấy phiếu thuộc phòng ban mình quản lý."""
        env = request.env
        scope = self._dept_scope_ids()
        domain = [] if scope is None else [('department_id', 'in', scope)]
        reqs = env['hb.recruitment.request'].sudo().search(
            domain, order='create_date desc')
        data = {'isRecruiter': self._is_recruiter(),
                'canApprove': self._is_hr(),
                'rows': [self._req_row(r) for r in reqs]}
        data.update(self._req_meta())
        return request.make_json_response(data)

    @http.route('/hocba-hrm/api/recruitment/request/<int:req_id>', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_request(self, req_id, **kw):
        r = request.env['hb.recruitment.request'].sudo().browse(req_id)
        if not r.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(r.department_id.id):
            return self._forbidden()
        return request.make_json_response(self._req_row(r, detail=True))

    @http.route('/hocba-hrm/api/recruitment/requests', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_request_create(self, **kw):
        """Thêm phiếu yêu cầu. Theo sheet, người order là TBP (trưởng phòng) — họ
        KHÔNG có ACL ghi trên model, nên ghi qua .sudo() SAU khi đã kiểm vai + phạm vi.
        requester_id vẫn = người đăng nhập (sudo giữ nguyên env.user)."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data()
        vals = self._req_vals(payload)
        if not (vals.get('job_title') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập tên vị trí.'}, status=400)
        if not vals.get('department_id'):
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng chọn phòng ban.'}, status=400)
        if not self._is_hr() and not self._dep_in_scope(vals.get('department_id')):
            return self._forbidden('Phiếu phải thuộc phòng ban bạn quản lý.')
        try:
            r = request.env['hb.recruitment.request'].sudo().create(vals)
            if r.job_id:
                self._sync_website_description(r.job_id)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._req_row(r, detail=True))

    @http.route('/hocba-hrm/api/recruitment/request/<int:req_id>', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_request_update(self, req_id, **kw):
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        r = request.env['hb.recruitment.request'].sudo().browse(req_id)
        if not r.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(r.department_id.id):
            return self._forbidden()
        vals = self._req_vals(request.get_json_data())
        if (not self._is_hr() and 'department_id' in vals
                and not self._dep_in_scope(vals['department_id'])):
            return self._forbidden('Phiếu phải thuộc phòng ban bạn quản lý.')
        try:
            if vals:
                r.write(vals)
            if r.job_id:
                self._sync_website_description(r.job_id)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._req_row(r, detail=True))

    @http.route('/hocba-hrm/api/recruitment/request/<int:req_id>/action',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_request_action(self, req_id, **kw):
        """Chuyển trạng thái phiếu (gửi duyệt / duyệt / đóng / từ chối / về nháp)."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        r = request.env['hb.recruitment.request'].sudo().browse(req_id)
        if not r.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(r.department_id.id):
            return self._forbidden()
        payload = request.get_json_data() or {}
        action = payload.get('action')
        method = REQUEST_ACTIONS.get(action)
        if not method:
            return request.make_json_response({'error': 'bad_request'}, status=400)
        # Duyệt/từ chối/đóng phiếu: chỉ BP tuyển dụng/HR; TBP order không tự duyệt.
        if action in REQUEST_HR_ACTIONS and not self._is_hr():
            return self._forbidden(
                'Chỉ Bộ phận tuyển dụng/HR mới được duyệt, từ chối hoặc đóng phiếu.')
        try:
            if action == 'refuse' and payload.get('refuseReason'):
                r.write({'refuse_reason': payload['refuseReason']})
            getattr(r, method)()
            if r.job_id:
                self._sync_website_description(r.job_id)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._req_row(r, detail=True))

    # ------------------------------------------------------------------
    # Mail mẫu tuyển dụng (mail.template, model hr.applicant) — tab "Mail mẫu".
    # Liệt kê / tạo / sửa template + gửi cho ứng viên được chọn.
    # ------------------------------------------------------------------

    def _tmpl_row(self, t, detail=False):
        data = {
            'id': t.id,
            'name': t.name or '',
            'subject': t.subject or '',
        }
        if detail:
            data['bodyHtml'] = t.body_html or ''
            data['emailTo'] = t.email_to or ''
        return data

    def _applicant_recipients(self):
        """Ứng viên có email để chọn làm người nhận."""
        apps = request.env['hr.applicant'].sudo().search(
            [('email_from', '!=', False)], order='date_received desc, id desc')
        return [{
            'id': a.id, 'name': a.partner_name or '(Chưa có tên)',
            'email': a.email_from or '', 'jobName': a.job_id.name or '',
            'stage': a.stage_id.name or '',
        } for a in apps]

    @http.route('/hocba-hrm/api/recruitment/mail-templates', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_mail_templates(self, **kw):
        """Danh sách mail mẫu (model hr.applicant) + ứng viên để gửi."""
        env = request.env
        applicant_model = env.ref('hr_recruitment.model_hr_applicant')
        tmpls = env['mail.template'].sudo().search(
            [('model_id', '=', applicant_model.id)], order='name')
        return request.make_json_response({
            # Mail mẫu là cấu hình email toàn hệ thống (không theo phòng ban) →
            # chỉ HR toàn quyền quản lý; trưởng phòng không thấy nút thêm/sửa/gửi.
            'isRecruiter': self._is_hr(),
            'rows': [self._tmpl_row(t) for t in tmpls],
            'recipients': self._applicant_recipients(),
        })

    @http.route('/hocba-hrm/api/recruitment/mail-template/<int:tmpl_id>',
                auth='user', type='http', methods=['GET'])
    def api_recruitment_mail_template(self, tmpl_id, **kw):
        t = request.env['mail.template'].sudo().browse(tmpl_id)
        if not t.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        return request.make_json_response(self._tmpl_row(t, detail=True))

    def _tmpl_vals(self, payload):
        vals = {}
        for key, field in (('name', 'name'), ('subject', 'subject'),
                           ('bodyHtml', 'body_html')):
            if key in payload:
                vals[field] = payload[key] if payload[key] not in (None,) else False
        return vals

    @http.route('/hocba-hrm/api/recruitment/mail-templates', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_mail_template_create(self, **kw):
        """Tạo mail mẫu mới (model cố định hr.applicant) — chỉ HR toàn quyền."""
        if not self._is_hr():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data()
        vals = self._tmpl_vals(payload)
        if not (vals.get('name') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập tên mẫu.'}, status=400)
        vals['model_id'] = request.env.ref('hr_recruitment.model_hr_applicant').id
        vals.setdefault('email_to', '{{ object.email_from or \'\' }}')
        try:
            t = request.env['mail.template'].sudo().create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._tmpl_row(t, detail=True))

    @http.route('/hocba-hrm/api/recruitment/mail-template/<int:tmpl_id>',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_mail_template_update(self, tmpl_id, **kw):
        if not self._is_hr():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        t = request.env['mail.template'].sudo().browse(tmpl_id)
        if not t.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        vals = self._tmpl_vals(request.get_json_data())
        try:
            if vals:
                t.write(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._tmpl_row(t, detail=True))

    @http.route('/hocba-hrm/api/recruitment/mail-template/<int:tmpl_id>/delete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_mail_template_delete(self, tmpl_id, **kw):
        """Xoá mail mẫu — chỉ HR toàn quyền (cấu hình email toàn hệ thống)."""
        if not self._is_hr():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        t = request.env['mail.template'].sudo().browse(tmpl_id)
        if not t.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            t.unlink()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True})

    @http.route('/hocba-hrm/api/recruitment/mail-template/<int:tmpl_id>/send',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_mail_template_send(self, tmpl_id, **kw):
        """Gửi mail mẫu cho danh sách ứng viên được chọn — chỉ HR toàn quyền."""
        if not self._is_hr():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        t = request.env['mail.template'].sudo().browse(tmpl_id)
        if not t.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        payload = request.get_json_data() or {}
        ids = [int(i) for i in (payload.get('applicantIds') or [])]
        if not ids:
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Chưa chọn ứng viên nào.'}, status=400)
        # Nội dung đã chỉnh sửa ở màn xem trước (áp cho mọi người nhận trong lần gửi này).
        ovr_subject = payload.get('subject')
        ovr_body = payload.get('bodyHtml')
        Applicant = request.env['hr.applicant'].sudo()
        sent, skipped = 0, 0
        for aid in ids:
            a = Applicant.browse(aid)
            if not a.exists() or not a.email_from:
                skipped += 1
                continue
            try:
                if ovr_subject is not None or ovr_body is not None:
                    ev = {}
                    if ovr_subject is not None:
                        ev['subject'] = ovr_subject
                    if ovr_body is not None:
                        ev['body_html'] = ovr_body
                else:
                    # Render subject/body bằng inline_template ({{ }}) rồi ghi đè khi gửi,
                    # tránh body_html (qweb) để nguyên placeholder.
                    r = self._render_tmpl(t, aid)
                    ev = {'subject': r['subject'], 'body_html': r['body_html']}
                t.send_mail(aid, force_send=False, email_values=ev)
                sent += 1
            except (AccessError, ValidationError, UserError):
                skipped += 1
        return request.make_json_response({'sent': sent, 'skipped': skipped})

    @http.route('/hocba-hrm/api/recruitment/mail-template/<int:tmpl_id>/preview',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_mail_template_preview(self, tmpl_id, **kw):
        """Render mail mẫu theo 1 ứng viên để XEM TRƯỚC (không gửi) — kiểm tra
        thông tin đã điền đúng chưa, không cần SMTP."""
        t = request.env['mail.template'].sudo().browse(tmpl_id)
        if not t.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        aid = (request.get_json_data() or {}).get('applicantId')
        if not aid:
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Thiếu ứng viên.'}, status=400)
        aid = int(aid)
        a = request.env['hr.applicant'].sudo().browse(aid)
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            rendered = self._render_tmpl(t, aid)
        except Exception as ex:  # noqa: BLE001 - render lỗi cú pháp template
            return request.make_json_response(
                {'error': 'render_failed', 'message': str(ex)}, status=400)
        return request.make_json_response({
            'subject': rendered['subject'],
            'bodyHtml': rendered['body_html'],
            'emailTo': rendered['email_to'] or (a.email_from or ''),
        })

    def _render_tmpl(self, t, aid):
        """Render subject/body/email_to của mail mẫu cho 1 ứng viên bằng inline_template
        engine (đúng cú pháp {{ }} mà template dùng — body_html mặc định là qweb nên
        không tự thay placeholder). Dùng chung cho xem trước & gửi."""
        def rend(src):
            return t._render_template(src, t.model, [aid],
                                      engine='inline_template').get(aid, '') if src else ''
        return {
            'subject': rend(t.subject),
            'body_html': rend(t.body_html),
            'email_to': rend(t.email_to),
        }

    @http.route('/hocba-hrm/api/recruitment/mail-logs', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_mail_logs(self, **kw):
        """Lịch sử email đã gửi cho ứng viên (nguồn: mail.message, bền vững vì
        template auto_delete xoá mail.mail sau khi gửi). Trạng thái lấy từ notification."""
        env = request.env
        tz = self._user_tz()
        msgs = env['mail.message'].sudo().search(
            [('model', '=', 'hr.applicant'),
             ('message_type', 'in', ['email', 'email_outgoing'])],
            order='date desc', limit=500)
        Applicant = env['hr.applicant'].sudo()
        rows = []
        for m in msgs:
            a = Applicant.browse(m.res_id).exists() if m.res_id else Applicant.browse()
            notifs = m.notification_ids
            statuses = set(notifs.mapped('notification_status')) if notifs else set()
            if statuses & {'exception', 'bounce'}:
                status = 'failed'
            elif statuses and statuses <= {'sent'}:
                status = 'sent'
            elif 'ready' in statuses:
                status = 'outgoing'
            else:
                status = 'sent'  # đã có message = đã xử lý gửi
            fail = ', '.join(filter(None, notifs.mapped('failure_reason')))[:200] if notifs else ''
            rows.append({
                'id': m.id,
                'applicantId': m.res_id or False,
                'applicant': (a.partner_name or a.display_name or '—') if a else '—',
                'email': a.email_from or '' if a else '',
                'subject': m.subject or '(không tiêu đề)',
                'date': pytz.utc.localize(m.date).astimezone(tz).isoformat() if m.date else None,
                'status': status,
                'failure': fail,
            })
        return request.make_json_response({'isRecruiter': self._is_hr(), 'rows': rows})

    # ------------------------------------------------------------------
    # Gửi mail qua Gmail (chuyển hướng tab) — bỏ phụ thuộc SMTP server.
    # FE mở Gmail compose điền sẵn nội dung (render từ mail mẫu của app), người dùng
    # gửi bằng Gmail của mình, rồi gọi /mail/log-sent để ghi lịch sử (tab Mail logs).
    # ------------------------------------------------------------------

    @http.route('/hocba-hrm/api/recruitment/mail/log-sent', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_mail_log_sent(self, **kw):
        """Ghi lịch sử mail đã gửi (qua Gmail) — chỉ nhóm tuyển dụng.
        body: {logs: [{applicantId, subject}]}. Tạo mail.message (message_type='email')
        để tab Mail logs hiển thị như mail gửi qua server."""
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        logs = (request.get_json_data() or {}).get('logs') or []
        Applicant = request.env['hr.applicant'].sudo()
        logged = 0
        for item in logs:
            aid = item.get('applicantId')
            if not aid:
                continue
            a = Applicant.browse(int(aid))
            if not a.exists():
                continue
            subject = (item.get('subject') or 'Email tuyển dụng').strip() or 'Email tuyển dụng'
            a.message_post(
                subject=subject,
                body=Markup('<p>Đã gửi email <b>%s</b> tới %s (qua Gmail).</p>')
                     % (subject, a.email_from or '—'),
                message_type='email',
                subtype_xmlid='mail.mt_note',
            )
            logged += 1
        return request.make_json_response({'logged': logged})

    # ------------------------------------------------------------------
    # Lịch rảnh phỏng vấn (hb.interview.slot) — tab "Danh sách PV".
    # HR/BP tạo slot rảnh theo tuần; SPA xem lịch theo ngày/giờ.
    # ------------------------------------------------------------------

    def _can_manage_slots(self):
        u = request.env.user
        return (self._is_hr()
                or self._is_dept_manager()
                or u.has_group('hr_recruitment.group_hr_recruitment_interviewer'))

    def _user_tz(self):
        return pytz.timezone(request.env.user.tz or 'Asia/Ho_Chi_Minh')

    def _local_to_utc(self, day, hour_float, tz):
        h = int(hour_float)
        m = int(round((hour_float - h) * 60))
        naive = datetime.combine(day, dt_time(h, m))
        return tz.localize(naive).astimezone(pytz.utc).replace(tzinfo=None)

    def _slot_row(self, s):
        # Dùng cùng _user_tz() (có fallback Asia/Ho_Chi_Minh) như lúc tạo slot,
        # tránh lệch giờ khi user chưa cấu hình timezone (context_timestamp khi đó để nguyên UTC).
        tz = self._user_tz()
        start_local = pytz.utc.localize(s.start_datetime).astimezone(tz)
        end_local = pytz.utc.localize(s.stop_datetime).astimezone(tz)
        return {
            'id': s.id,
            'date': start_local.strftime('%Y-%m-%d'),
            'startTime': start_local.strftime('%H:%M'),
            'endTime': end_local.strftime('%H:%M'),
            'interviewerId': s.user_id.id or False,
            'interviewer': s.user_id.name or '',
            'department': s.department_id.name or '',
            'state': s.state or 'available',
            'applicant': s.applicant_id.partner_name or '',
            'applicantId': s.applicant_id.id or False,
            'notes': s.notes or '',
        }

    @http.route('/hocba-hrm/api/recruitment/interview-slots', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_slots(self, **kw):
        """Lịch rảnh PV trong khoảng [from, to] (mặc định 7 ngày từ hôm nay)."""
        env = request.env
        tz = self._user_tz()
        today = fields.Date.context_today(env.user)
        from_d = fields.Date.from_string(kw.get('from')) if kw.get('from') else today
        to_d = fields.Date.from_string(kw.get('to')) if kw.get('to') else from_d
        start_utc = self._local_to_utc(from_d, 0.0, tz)
        end_utc = tz.localize(datetime.combine(to_d, dt_time(23, 59, 59))).astimezone(pytz.utc).replace(tzinfo=None)
        slots = env['hb.interview.slot'].sudo().search(
            [('start_datetime', '>=', start_utc), ('start_datetime', '<=', end_utc)],
            order='start_datetime')
        # Danh sách người phỏng vấn (nhân viên có tài khoản) để chọn khi tạo slot
        emps = env['hr.employee'].sudo().search([('user_id', '!=', False)], order='name')
        interviewers = [{'id': e.user_id.id, 'name': e.name} for e in emps]
        return request.make_json_response({
            'canManage': self._can_manage_slots(),
            'meId': env.user.id,
            'meName': env.user.name,
            'interviewers': interviewers,
            'rows': [self._slot_row(s) for s in slots],
        })

    @http.route('/hocba-hrm/api/recruitment/interview-slots', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_slots_create(self, **kw):
        """Tạo nhiều slot rảnh PV (theo tuần). body: {userId, slots:[{date,startHour,endHour}]}."""
        if not self._can_manage_slots():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data() or {}
        lines = payload.get('slots') or []
        if not lines:
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Chưa có slot nào để tạo.'}, status=400)
        tz = self._user_tz()
        user_id = int(payload.get('userId') or request.env.user.id)
        Slot = request.env['hb.interview.slot'].sudo()
        created = []
        try:
            for ln in lines:
                day = fields.Date.from_string(ln['date'])
                sh = float(ln['startHour'])
                eh = float(ln['endHour'])
                if eh <= sh:
                    raise UserError('Giờ kết thúc phải sau giờ bắt đầu.')
                rec = Slot.create({
                    'start_datetime': self._local_to_utc(day, sh, tz),
                    'stop_datetime': self._local_to_utc(day, eh, tz),
                    'user_id': user_id,
                })
                created.append(rec)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'created': len(created)})

    @http.route('/hocba-hrm/api/recruitment/interview-slot/<int:slot_id>/delete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_slot_delete(self, slot_id, **kw):
        if not self._can_manage_slots():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        s = request.env['hb.interview.slot'].sudo().browse(slot_id)
        if not s.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            s.unlink()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True})

    @http.route('/hocba-hrm/api/recruitment/interview-slot/<int:slot_id>/book',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_slot_book(self, slot_id, **kw):
        """Đặt slot rảnh cho 1 ứng viên: slot -> 'booked' + gán applicant_id, đồng thời
        điền lịch PV lên hồ sơ ứng viên (ngày/giờ/người PV) để khép vòng với tab
        Danh sách CV và mail Thư mời phỏng vấn (biến interview_date/time)."""
        if not self._can_manage_slots():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        s = request.env['hb.interview.slot'].sudo().browse(slot_id)
        if not s.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        aid = (request.get_json_data() or {}).get('applicantId')
        if not aid:
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Chưa chọn ứng viên.'}, status=400)
        a = request.env['hr.applicant'].sudo().browse(int(aid))
        if not a.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            start_local = pytz.utc.localize(s.start_datetime).astimezone(self._user_tz())
            s.write({'state': 'booked', 'applicant_id': a.id})
            a.write({
                'interview_date': start_local.date(),
                'interview_time': start_local.strftime('%H:%M'),
                'interviewer_name': s.user_id.name or a.interviewer_name,
            })
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._slot_row(s))

    @http.route('/hocba-hrm/api/recruitment/interview-slot/<int:slot_id>/unbook',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_slot_unbook(self, slot_id, **kw):
        """Hủy đặt slot: trả về 'available' + gỡ ứng viên (giữ nguyên lịch PV đã ghi
        trên hồ sơ ứng viên — chỉ giải phóng slot)."""
        if not self._can_manage_slots():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        s = request.env['hb.interview.slot'].sudo().browse(slot_id)
        if not s.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            s.write({'state': 'available', 'applicant_id': False})
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._slot_row(s))

    # ------------------------------------------------------------------
    # Cấu hình tuyển dụng (admin/HR) — tab "Cấu hình" của SPA.
    # Spec: docs/superpowers/specs/2026-07-23-recruitment-config-design.md
    # Stages CRUD + kéo-thả thứ tự + SLA; chế độ tự đóng tuyển (auto_close_mode).
    # ------------------------------------------------------------------

    STAGE_CONFIG_FIELDS = {
        'name': ('name', 'str'),
        'supportPerson': ('support_person', 'str'),
        'requirements': ('requirements', 'str'),
        'successCriteria': ('success_criteria', 'str'),
        'slaDays': ('sla_days', 'num'),
        'hiredStage': ('hired_stage', 'bool'),
    }

    AUTO_CLOSE_LABELS = {
        'full': 'Ngừng đăng tuyển + đóng phiếu yêu cầu (mặc định)',
        'stop': 'Chỉ ngừng đăng tuyển (giữ phiếu đang tuyển)',
        'warn': 'Chỉ cảnh báo trên chatter, không đổi trạng thái',
        'off': 'Tắt — không làm gì khi tuyển đủ chỉ tiêu',
    }

    def _stage_config_row(self, s, applicant_counts=None):
        count = (applicant_counts or {}).get(s.id)
        if count is None:
            count = request.env['hr.applicant'].sudo().with_context(
                active_test=False).search_count([('stage_id', '=', s.id)])
        return {
            'id': s.id,
            'name': s.name or '',
            'sequence': s.sequence,
            'hiredStage': bool(s.hired_stage),
            'slaDays': s.sla_days or 0,
            'supportPerson': s.support_person or '',
            'requirements': s.requirements or '',
            'successCriteria': s.success_criteria or '',
            'applicantCount': count,
        }

    def _stage_config_vals(self, payload):
        vals = {}
        for key, (field, typ) in self.STAGE_CONFIG_FIELDS.items():
            if key in payload:
                vals[field] = _conv(typ, payload[key])
        return vals

    @http.route('/hocba-hrm/api/recruitment/config', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_config(self, **kw):
        """Toàn bộ cấu hình tuyển dụng — CHỈ Admin hệ thống."""
        if not self._is_admin():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        env = request.env
        stages = env['hr.recruitment.stage'].sudo().search([], order='sequence, id')
        counts = dict(env['hr.applicant'].sudo().with_context(
            active_test=False)._read_group(
            [('stage_id', 'in', stages.ids)], ['stage_id'], ['__count']))
        counts = {s.id: c for s, c in counts.items()}
        return request.make_json_response({
            'isAdmin': True,
            'autoCloseMode': env['hr.applicant']._hb_auto_close_mode(),
            'autoCloseLabels': self.AUTO_CLOSE_LABELS,
            'stages': [self._stage_config_row(s, counts) for s in stages],
        })

    @http.route('/hocba-hrm/api/recruitment/config/stages', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_config_stage_create(self, **kw):
        """Thêm bước quy trình (vào cuối) — chỉ Admin."""
        if not self._is_admin():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        vals = self._stage_config_vals(request.get_json_data() or {})
        if not (vals.get('name') or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Vui lòng nhập tên bước.'},
                status=400)
        Stage = request.env['hr.recruitment.stage'].sudo()
        last = Stage.search([], order='sequence desc, id desc', limit=1)
        vals.setdefault('sequence', (last.sequence or 0) + 10)
        try:
            s = Stage.create(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._stage_config_row(s))

    @http.route('/hocba-hrm/api/recruitment/config/stage/<int:stage_id>',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_config_stage_update(self, stage_id, **kw):
        if not self._is_admin():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        s = request.env['hr.recruitment.stage'].sudo().browse(stage_id)
        if not s.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        vals = self._stage_config_vals(request.get_json_data() or {})
        if 'name' in vals and not (vals['name'] or '').strip():
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Tên bước không được rỗng.'},
                status=400)
        try:
            if vals:
                s.write(vals)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response(self._stage_config_row(s))

    @http.route('/hocba-hrm/api/recruitment/config/stage/<int:stage_id>/delete',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_config_stage_delete(self, stage_id, **kw):
        """Xoá bước — guard ondelete (còn ứng viên / bước cuối cùng) trả 400. Chỉ Admin."""
        if not self._is_admin():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        s = request.env['hr.recruitment.stage'].sudo().browse(stage_id)
        if not s.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        try:
            s.unlink()
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True})

    @http.route('/hocba-hrm/api/recruitment/config/stages/reorder',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_config_stage_reorder(self, **kw):
        """Kéo-thả đổi thứ tự: body {ids: [id theo thứ tự mới]}. Chỉ Admin."""
        if not self._is_admin():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        ids = (request.get_json_data() or {}).get('ids') or []
        if not ids:
            return request.make_json_response({'error': 'bad_request'}, status=400)
        try:
            request.env['hr.recruitment.stage'].sudo().action_reorder(ids)
        except (AccessError, ValidationError, UserError) as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': 'rejected', 'message': str(ex)}, status=400)
        return request.make_json_response({'ok': True})

    @http.route('/hocba-hrm/api/recruitment/config/settings', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_config_settings(self, **kw):
        """Lưu cấu hình chung: {autoCloseMode: full|stop|warn|off}. Chỉ Admin."""
        if not self._is_admin():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data() or {}
        mode = payload.get('autoCloseMode')
        if mode is not None:
            if mode not in self.AUTO_CLOSE_LABELS:
                return request.make_json_response(
                    {'error': 'bad_request', 'message': 'Chế độ không hợp lệ.'},
                    status=400)
            request.env['ir.config_parameter'].sudo().set_param(
                'hocba_recruitments.auto_close_mode', mode)
        return request.make_json_response(
            {'ok': True,
             'autoCloseMode': request.env['hr.applicant']._hb_auto_close_mode()})
