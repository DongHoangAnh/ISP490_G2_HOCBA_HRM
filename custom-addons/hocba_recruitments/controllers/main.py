import pytz
import re
from datetime import date, datetime, time as dt_time
from markupsafe import Markup, escape
from psycopg2 import IntegrityError

from odoo import http, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request
from odoo.tools.mail import is_html_empty, plaintext2html

from ..models.hr_job import HB_TEACHING_LEVELS
from ..models.hb_interview_slot import (
    P_SLOT_CLOSE, P_SLOT_OPEN, P_SLOT_STEP, SLOT_STEPS_ALLOWED, _hour_label,
)


# Nhận diện "chuỗi này đã là HTML chưa". Cố ý CHẶT: phải là `<` + chữ cái (hoặc
# `/`, `!`) rồi mới tới `>`, để câu text thuần kiểu "Lương < 10 triệu" không bị
# nhầm là thẻ và bỏ qua escape.
_HTML_TAG_RE = re.compile(r'<[a-zA-Z!/][^>]*>')


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
    # Đợt tuyển: bỏ trống ở payload thì BE tự điền theo phiếu đang tuyển của vị
    # trí (hr_applicant._hb_fill_request); gửi lên = HR chọn tay, máy không đè.
    'requestId': ('hb_request_id', 'int'),
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
    'onboardResult': ('onboard_result', 'str'),
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

# Tách vai theo sheet quy trình: TBP (người order) chỉ GỬI DUYỆT; DUYỆT / TỪ
# CHỐI / ĐÓNG / MỞ LẠI NHÁP là việc của BP tuyển dụng/HR (_is_hr).
# `reset` vào nhóm này từ 2026-08-26: mở lại nháp đụng tới chỉ tiêu tuyển đã
# cộng cho vị trí, không phải thao tác của người order.
REQUEST_HR_ACTIONS = frozenset({'approve', 'refuse', 'close', 'reset'})


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

    def _stage_refs(self):
        """map stage_id -> mã xmlid ngắn (vd 'hb_stage_invite'), cache 1 lần/request.

        Frontend cần mã ổn định để lọc theo bước: tên bước sửa được trên màn
        Cấu hình nên so tên là hỏng ngay khi admin đổi chữ.
        """
        cache = getattr(self, '_stage_ref_cache', None)
        if cache is None:
            rows = request.env['ir.model.data'].sudo().search_read(
                [('model', '=', 'hr.recruitment.stage'),
                 ('module', '=', 'hocba_recruitments')], ['res_id', 'name'])
            cache = {r['res_id']: r['name'] for r in rows}
            self._stage_ref_cache = cache
        return cache

    # Gửi mẫu mail nào thì đẩy bước nào: {xmlid template: (bước nguồn, bước đích,
    # lý do ghi chatter)}. Gửi mail LÀ hành động nghiệp vụ của bước đó, nên bước
    # tự chạy theo — mẫu không có trong bảng này thì gửi đi không đổi bước.
    # Áp cho cả 2 đường gửi: /send (SMTP) và /log-sent (gửi qua Gmail rồi xác
    # nhận) — SPA đang dùng đường Gmail, đừng chỉ vá một chỗ.
    MAIL_STAGE_RULES = {
        'email_template_interview_invite': (
            ['hb_stage_invite'], 'hb_stage_interview',
            'Do đã gửi thư mời tham gia phỏng vấn.'),
        'email_template_job_offer': (
            ['hb_stage_interview', 'hb_stage_result'], 'hb_stage_offer',
            'Do đã gửi thư mời nhận việc.'),
    }

    def _apply_mail_stage_rule(self, tmpl, applicants):
        """Đẩy bước cho các ứng viên vừa nhận `tmpl` (nếu mẫu có luật).

        Không nổ lỗi khi template/bước bị xoá: đổi bước là hệ quả phụ của việc
        gửi mail, hỏng nó không được phép làm hỏng thao tác gửi.
        """
        if not tmpl or not applicants:
            return
        for xmlid, (src, dst, reason) in self.MAIL_STAGE_RULES.items():
            ref = request.env.ref('hocba_recruitments.' + xmlid,
                                  raise_if_not_found=False)
            if ref and ref.id == tmpl.id:
                applicants._hb_advance_stage(src, dst, reason)
                return

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
        """Chỉ Admin hệ thống."""
        return request.env.user.has_group('base.group_system')

    def _can_config(self):
        """Sửa được màn Cấu hình tuyển dụng — Admin hoặc HR Manager.

        Spec v1.2 (2026-08-03, user yêu cầu) nới từ CHỈ Admin xuống thêm HR
        Manager, cho khớp "Cấu hình nhận việc" (need 'hrm' trên sidebar).
        KHÔNG mở cho nhóm tuyển dụng (group_hr_recruitment_user): họ dùng quy
        trình hằng ngày, không phải người được đổi quy trình/hạn xử lý.
        """
        u = request.env.user
        return (u.has_group('base.group_system')
                or u.has_group('hr.group_hr_manager'))

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
            'requestId': a.hb_request_id.id or False,
            'requestCode': a.hb_request_id.name or '',
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
            'stageRef': self._stage_refs().get(a.stage_id.id, ''),
            # Phỏng vấn & Offer (Sheet 7.5/7.6)
            'attendanceStatus': a.attendance_status or '',
            'interviewResult': a.interview_result or '',
            'offerContent': a.offer_content or '',
            'startDate': _d(a.start_date),
            'offerNote': a.offer_note or '',
            'candidateConfirmed': a.candidate_confirmed or '',
            'onboardResult': a.onboard_result or '',
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
        """Stages + jobs + nhãn select — cho kanban và form Thêm/Sửa.

        `jobs` lọc theo phạm vi phòng ban như _req_meta/_job_meta: ô "Vị trí ứng
        tuyển" của trưởng phòng chỉ liệt kê vị trí phòng mình, khớp với guard
        403 ở api_recruitment_cv_create. Bước (stages) là cấu hình quy trình
        dùng chung toàn hệ thống nên KHÔNG lọc.
        """
        env = request.env
        scope = self._dept_scope_ids()
        job_domain = [] if scope is None else [('department_id', 'in', scope)]
        stages = env['hr.recruitment.stage'].sudo().search([], order='sequence, id')
        jobs = env['hr.job'].sudo().search(job_domain, order='name')
        # Ô "Đợt tuyển" ở form CV: chỉ liệt kê phiếu ĐANG TUYỂN — gán CV vào đợt
        # đã đóng là sửa lại số liệu của đợt đã chốt, không phải việc thường ngày.
        req_domain = [('state', '=', 'recruiting')]
        if scope is not None:
            req_domain.append(('department_id', 'in', scope))
        reqs = env['hb.recruitment.request'].sudo().search(
            req_domain, order='id desc')
        return {
            'stages': [{'id': s.id, 'name': s.name, 'sequence': s.sequence,
                        'hiredStage': bool(s.hired_stage), 'slaDays': s.sla_days or 0,
                        'ref': self._stage_refs().get(s.id, '')}
                       for s in stages],
            'jobs': [{'id': j.id, 'name': j.name} for j in jobs],
            'requests': [{'id': q.id, 'code': q.name or '',
                          'jobId': q.job_id.id or False,
                          'jobTitle': q.job_title or '',
                          'qty': q.qty_expected or 0,
                          'deadline': _d(q.expected_start_date)} for q in reqs],
            'cvResultLabels': self._sel_labels('hr.applicant', 'cv_filter_result'),
            'callStatusLabels': self._sel_labels('hr.applicant', 'call_status'),
            'attendanceLabels': self._sel_labels('hr.applicant', 'attendance_status'),
            'interviewResultLabels': self._sel_labels('hr.applicant', 'interview_result'),
            'onboardResultLabels': self._sel_labels('hr.applicant', 'onboard_result'),
        }

    def _app_vals(self, payload):
        """Lọc payload -> vals hr.applicant (whitelist + ép kiểu).

        Giá trị Selection sai được chặn ngay ở đây thành UserError: hai endpoint
        gọi hàm này đều bắt UserError trả 400, còn để ORM tự vỡ thì ra ValueError
        → 500, SPA chỉ thấy "lỗi máy chủ" thay vì biết mình gửi sai.
        """
        model_fields = request.env['hr.applicant']._fields
        vals = {}
        for key, (field, typ) in APP_FORM_FIELDS.items():
            if key not in payload:
                continue
            v = payload[key]
            if typ == 'int':
                vals[field] = int(v) if v else False
            else:
                vals[field] = v if v not in ('', None) else False
            f = model_fields.get(field)
            if f and f.type == 'selection' and vals[field]:
                allowed = [k for k, _l in (f.selection or [])]
                if vals[field] not in allowed:
                    raise UserError('Giá trị không hợp lệ cho "%s": %s (chấp nhận: %s).'
                                    % (key, vals[field], ', '.join(allowed)))
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
        # Ứng viên mới nhất lên đầu. KHÔNG dùng order SQL vì Postgres xếp
        # NULLS FIRST với DESC ⇒ ứng viên bỏ trống "Ngày nhận CV" nhảy lên đầu
        # bảng, đè cả CV vừa nhập hôm nay. Thiếu date_received thì lấy ngày tạo
        # bản ghi làm mốc (vẫn là "mới" theo nghĩa vừa vào hệ thống).
        applicants = env['hr.applicant'].sudo().search(domain).sorted(
            key=lambda a: (a.date_received
                           or (a.create_date and a.create_date.date())
                           or date.min, a.id),
            reverse=True)
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
        try:
            vals = self._app_vals(payload)
        except UserError as ex:
            return request.make_json_response(
                {'error': 'bad_request', 'message': str(ex)}, status=400)
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
        try:
            vals = self._app_vals(request.get_json_data())
        except UserError as ex:
            return request.make_json_response(
                {'error': 'bad_request', 'message': str(ex)}, status=400)
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
        # BR-OB-02: ứng viên đã đánh "Không nhận việc" thì không có hồ sơ nào để
        # tạo. SPA đã ẩn nút, nhưng ẩn nút chỉ là lớp mềm — gọi thẳng API vẫn vào.
        if a.onboard_result == 'no_show':
            return request.make_json_response({
                'error': 'bad_request',
                'message': 'Ứng viên này đang ghi "Không nhận việc" nên không '
                           'tạo hồ sơ nhân viên được. Nếu người này đã đến, đổi '
                           'ô Kết quả nhận việc thành "Đã đến" rồi tạo lại.',
            }, status=400)
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
        # Đã có hồ sơ nhân viên ⇒ khâu offer khép lại, ứng viên bước vào
        # Onboarding. Chỉ đẩy tới: ai đã ở Onboarding/Bàn giao thì đứng yên.
        a._hb_advance_stage(
            ['hb_stage_result', 'hb_stage_offer'], 'hb_stage_onboarding',
            'Do đã tạo hồ sơ nhân viên (Onboard).')
        self._notify_profile_incomplete(emp)
        return request.make_json_response({
            'created': True, 'employeeId': emp.id,
            'employeeName': emp.name or '',
            'employeeCode': emp.x_employee_code or '',
        })

    def _notify_profile_incomplete(self, emp):
        """Chuông "cần hoàn thiện hồ sơ" cho hồ sơ vừa sinh từ ứng viên.

        Hồ sơ tạo từ tuyển dụng luôn thiếu CCCD / MST / BHXH — tuyển dụng không
        nắm mấy thông tin đó. Thiếu thì BR-010 chặn lên chính thức, mà người
        phát hiện lại là HR ở tận cuối kỳ thử việc. Báo ngay lúc tạo.

        Người nhận: HR Manager (người điền) + chính người vừa bấm Onboard (họ
        biết hồ sơ này vừa sinh ra, và thường là người đi nhắc). dedup theo
        employee để bấm lại nút không sinh thêm chuông.
        """
        missing = emp._hocba_missing_official_fields()
        if not missing:
            return
        env = request.env
        recipients = env['res.users'].sudo().browse(env.user.id)
        grp = env.ref('hr.group_hr_manager', raise_if_not_found=False)
        if grp:
            recipients |= env['res.users'].sudo().search(
                [('all_group_ids', 'in', grp.id), ('active', '=', True)])
        code = emp.x_employee_code or ''
        env['hb.notification'].sudo()._notify(
            recipients, category='onboarding', kind='profile_incomplete',
            level='warning',
            title='Cần hoàn thiện hồ sơ: %s' % (emp.name or ''),
            body='Hồ sơ %s%s vừa tạo từ ứng viên, còn thiếu: %s. Thiếu các mục '
                 'này thì không chuyển sang Chính thức được khi hết thử việc.'
                 % (emp.name or '', ' (%s)' % code if code else '',
                    ', '.join(missing)),
            target_view='employees', target_ref=emp.id,
            dedup_key='profile_incomplete_%s' % emp.id)

    # ------------------------------------------------------------------
    # Vị trí tuyển dụng (hr.job) — dùng chung cho 2 tab SPA:
    # "Theo dõi tuyển dụng" (tên cũ: Vị trí tuyển dụng / JD) và "Kho quản lý JD".
    # ------------------------------------------------------------------

    def _job_published(self, job):
        """Vị trí này có đang đăng tuyển công khai không.

        is_published (website_hr_recruitment) là nguồn sự thật khi có website;
        DB không cài module đó thì lùi về cờ nội bộ x_published. Cả ba chỗ trả
        payload cho SPA phải dùng CHUNG hàm này — trước đây mỗi chỗ getattr một
        kiểu nên tab Theo dõi luôn báo "chưa đăng" và nút Chép link không hiện.
        """
        if not job:
            return False
        if 'is_published' in job._fields:
            return bool(job.is_published)
        return bool(job.x_published)

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
            'published': self._job_published(j),
            # Link trang tuyển dụng công khai (/jobs/detail/<slug>) — để copy đi truyền thông.
            'websiteUrl': getattr(j, 'website_url', '') or '',
            'jdLink': j.jd_google_link or '',
            'expected': j.no_of_recruitment or 0,
            'hired': j.no_of_hired_employee or 0,
            'applications': j.application_count or 0,
            'newApplications': j.new_application_count or 0,
            'location': j.address_id.name or '',
            # Không còn 'requiresTeaching': Trình độ là ô tuỳ chọn, khách không
            # thu thập dữ liệu này ở khâu tuyển dụng (xem models/hr_job.py).
            'teachingLevel': j.x_teaching_level or '',
            'sessionsPerWeek': j.x_required_sessions_per_week or 0,
        }
        if detail:
            data['description'] = j.description or ''
        return data

    def _as_html(self, value):
        """Đưa giá trị về HTML để nhúng vào trang tuyển dụng công khai.

        `hr.job.description` là field **Html** (ORM đã sanitize lúc ghi) nên nội
        dung vốn là thẻ thật. `escape()` nó thì trang /jobs in ra đúng chữ
        "<p>…</p>" cho ứng viên đọc — lỗi đã gặp 2026-08-29. Chỉ giá trị TEXT
        THUẦN mới cần escape + đổi xuống dòng thành <br/>.
        """
        v = value or ''
        if _HTML_TAG_RE.search(v):
            return Markup(v)
        return Markup('<p>%s</p>') % escape(v).replace('\n', Markup('<br/>'))

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
        # x_teaching_level là Char (nhập tự do) — giá trị chính là nhãn hiển thị.
        if (j.x_teaching_level or '').strip().lower() not in ('', 'na', 'n/a'):
            info.append(('Trình độ', j.x_teaching_level.strip()))
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
        if not is_html_empty(j.description):
            parts.append(Markup('<h4 class="mt-4">Mô tả công việc</h4>%s')
                         % self._as_html(j.description))
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
        # Danh sách phòng ban cho ô chọn ở form Thêm/Sửa vị trí: HR thấy tất cả,
        # trưởng phòng chỉ thấy phòng mình quản lý (gồm phòng con). Trước đây trả
        # hết mọi phòng nên TBP chọn được phòng ngoài phạm vi rồi mới ăn 403 lúc
        # lưu (guard ở api_recruitment_job_create) — chặn ngay từ ô chọn cho gọn.
        scope = self._dept_scope_ids()
        dep_domain = [] if scope is None else [('id', 'in', scope)]
        deps = env['hr.department'].sudo().search(dep_domain, order='name')
        return {
            'departments': [{'id': d.id, 'name': d.name} for d in deps],
            # Danh sách GỢI Ý cho ô Trình độ (Char) — SPA đổ vào <datalist>,
            # người dùng vẫn gõ được giá trị ngoài danh sách.
            'teachingLevels': list(HB_TEACHING_LEVELS),
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
        # "published" CHỈ ghi x_published (cờ nội bộ, luôn tồn tại) — hr_job.write()
        # tự soi gương sang is_published khi website_hr_recruitment có cài. Ghi
        # thẳng is_published ở đây thì DB không cài module đó ném ValueError →
        # HTTP 500, nút Đăng tuyển chết (xem tests/test_job_publish.py).
        # Đồng thời gắn trạng thái tuyển: bật -> Đang tuyển, tắt -> Dừng tuyển.
        # Người gửi `published` giờ chỉ còn nút toggle nhanh ở tab Theo dõi
        # tuyển dụng (RequestTracking) vốn chỉ gửi đúng {published} — form
        # Thêm/Sửa vị trí đã bỏ ô tích và drawer Kho JD đã bỏ nút toggle
        # (2026-08-29), cả hai KHÔNG gửi khoá `published` nữa.
        # Vẫn giữ setdefault chứ KHÔNG gán đè, phòng payload gửi cả hai: gán đè
        # thì lựa chọn ở ô "Trạng thái tuyển" bị vứt đi — người dùng đổi sang
        # Đang tuyển, bấm Lưu, trạng thái âm thầm quay về Dừng tuyển, trông y
        # như "lưu không được".
        # Cùng luật với hr_job.write() — xem tests/test_job_publish.py.
        if 'published' in payload:
            pub = bool(payload['published'])
            vals['x_published'] = pub
            vals.setdefault('recruitment_status',
                            'recruiting' if pub else 'stopped')
        # Ô "Mô tả công việc (JD)" trên SPA là textarea TEXT THUẦN (JobForm hiện
        # text để HR khỏi phải nhìn thẻ), trong khi hr.job.description là field
        # Html. Lưu thẳng text vào field Html thì mọi xuống dòng biến mất lúc
        # render ⇒ hoá HTML ngay tại đây. Giá trị đã có thẻ (nhập từ form
        # backend Odoo) thì giữ nguyên, không bọc thêm.
        if vals.get('description') and not _HTML_TAG_RE.search(vals['description']):
            vals['description'] = plaintext2html(vals['description'])
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
        # isHr: chỉ HR mới xem tổng thể theo phòng ban (view "Phòng ban" + bộ lọc
        # phòng ban). Trưởng phòng vốn đã bị giới hạn trong phòng mình nên SPA ẩn
        # cả hai, chỉ còn Thẻ / Bảng.
        data = {'isRecruiter': self._is_recruiter(),
                'isHr': self._is_hr(),
                'rows': [self._job_row(j) for j in jobs]}
        data.update(self._job_meta())
        # Nguồn tab "Theo dõi tuyển dụng". Lấy cả phiếu ĐÃ ĐÓNG chứ không chỉ
        # phiếu đang tuyển: tuyển đủ chỉ tiêu thì hệ thống tự đóng phiếu, chỉ trả
        # 'recruiting' thì dòng BIẾN MẤT khỏi bảng đúng lúc người ta muốn thấy nó
        # chuyển sang "Dừng tuyển". Phiếu nháp/chờ duyệt/từ chối chưa vào guồng
        # tuyển nên vẫn đứng ngoài (xem tab Phiếu yêu cầu).
        req_domain = [('state', 'in', ['recruiting', 'closed'])]
        if scope is not None:
            req_domain.append(('department_id', 'in', scope))
        reqs = env['hb.recruitment.request'].sudo().search(
            req_domain, order='department_id, job_title')
        level_labels = self._sel_labels('hb.recruitment.request', 'level')
        state_labels = self._sel_labels('hb.recruitment.request', 'state')
        stats = self._request_stats(reqs)
        data['requests'] = [dict({
            'id': r.id,
            'code': r.name or '',
            'jobTitle': r.job_title or '',
            'depId': r.department_id.id or False,
            'depName': r.department_id.name or 'Chưa gán phòng ban',
            'qty': r.qty_expected or 0,
            'jobId': r.job_id.id or False,
            'jobName': r.job_id.name or '',
            'published': self._job_published(r.job_id),
            'websiteUrl': (getattr(r.job_id, 'website_url', '') or '') if r.job_id else '',
            'levelLabel': level_labels.get(r.level, '') if r.level else '',
            'state': r.state or '',
            'stateLabel': state_labels.get(r.state, ''),
            # Trạng thái TUYỂN của JD gắn với phiếu — nút Đăng tuyển/Ngừng đăng
            # lật trường này (xem _job_vals). SPA ghép nó với state của phiếu
            # thành cột "Trạng thái": đóng phiếu > dừng tuyển > đang tuyển.
            'jobStatus': (r.job_id.recruitment_status or '') if r.job_id else '',
            'deadline': _d(r.expected_start_date),
            'jdLink': r.jd_link or '',
        }, **stats[r.id]) for r in reqs]
        return request.make_json_response(data)

    # ------------------------------------------------------------------
    # Theo dõi tiến độ theo phiếu yêu cầu — tab "Theo dõi tuyển dụng".
    # ------------------------------------------------------------------

    # Ứng viên gắn thẳng vào đợt tuyển qua hr.applicant.hb_request_id (tự điền
    # khi nhận CV — xem hr_applicant._hb_fill_request). Nhờ vậy hai phiếu cùng
    # một vị trí có sổ riêng, không còn dùng chung số như hồi phải bắc cầu job_id.
    # active_test=False: hồ sơ ứng viên hay bị lưu trữ sau khi nhận việc, bỏ đi
    # thì "đã tuyển" tụt số.

    def _applicant_env(self):
        return request.env['hr.applicant'].sudo().with_context(active_test=False)

    # Phễu tuyển dụng của một phiếu — thứ tự đúng bằng thứ tự khách đọc bảng:
    #   Tổng CV → CV pass → CV fail → PV → PV pass → PV fail → Nhận việc → Đã tuyển
    #
    # Hai mốc "PV" và "Nhận việc" KHÔNG có trường riêng nên phải suy ra, và suy
    # theo kiểu HỢP (OR) để phễu không bao giờ hụt: nhóm sau luôn nằm trong nhóm
    # trước. Nếu chỉ lấy stage thì ứng viên đã có kết quả PV mà chưa ai kéo thẻ
    # sang bước sau sẽ rơi ra ngoài "PV", thành ra "PV fail" nhiều hơn "PV" —
    # người xem sẽ nghĩ số liệu sai.
    #   PV        = đã sang bước Phỏng vấn (sequence 60) trở đi, HOẶC đã có lịch
    #               hẹn / tình trạng tham gia / kết quả PV.
    #   Nhận việc = đã sang bước Onboarding (sequence 90) trở đi, HOẶC đã điền
    #               ngày nhận việc.
    #   Đã tuyển  = ở bước có cờ hired_stage (Bàn giao nhân sự) — nhân sự đã
    #               hoàn thiện thử việc, cùng con số với cột "Đã tuyển" ngoài bảng.
    # Mốc seed (data/hr_recruitment_stages.xml) — CHỈ dùng làm dự phòng khi bước
    # bị xoá; số thật đọc theo xmlid lúc chạy, xem _stage_seq().
    _STAGE_INTERVIEW_SEQ = 60
    _STAGE_ONBOARD_SEQ = 90

    def _stage_seq(self, ref, fallback):
        """Vị trí (sequence) HIỆN HÀNH của một bước, tra theo xmlid.

        Màn Cấu hình cho thêm bước và kéo-thả, mà action_reorder ghi lại
        sequence 10/20/30… — chèn một bước trước "Phỏng vấn" là mọi bước sau đó
        dịch lên một nấc. Hằng số cứng khi đó đếm nhầm phễu mà không báo gì.

        .sudo() vì trưởng phòng không có ACL đọc `hr.recruitment.stage` — quyền
        của họ đến từ `manager_id`, không phải nhóm tuyển dụng. Thiếu sudo là
        AccessError bay ra thành trang lỗi HTML 403 giữa lúc xem phễu.
        """
        stage = request.env.ref('hocba_recruitments.' + ref,
                                raise_if_not_found=False)
        return stage.sudo().sequence if stage else fallback

    # Nhóm ứng viên khi bấm vào con số ở dòng chi tiết → domain tương ứng.
    # Dùng chung cho cả đếm (_request_stats) và popup danh sách, để con số bấm
    # vào và danh sách hiện ra không bao giờ lệch nhau.
    def _applicant_groups(self):
        """{tên nhóm: domain} — dựng lại mỗi request vì mốc bước đọc lúc chạy."""
        seq_interview = self._stage_seq('hb_stage_interview',
                                        self._STAGE_INTERVIEW_SEQ)
        seq_onboard = self._stage_seq('hb_stage_onboarding',
                                      self._STAGE_ONBOARD_SEQ)
        return {
            'cv':      [],
            'cv_pass': [('cv_filter_result', '=', 'pass')],
            'fail_cv': [('cv_filter_result', '=', 'fail')],
            'pv':      ['|', '|', '|',
                        ('stage_id.sequence', '>=', seq_interview),
                        ('interview_date', '!=', False),
                        ('attendance_status', '!=', False),
                        ('interview_result', '!=', False)],
            'pv_pass': [('interview_result', '=', 'pass')],
            'fail_pv': [('interview_result', '=', 'fail')],
            # Trừ hẳn người đã đánh "Không nhận việc": ngày nhận việc vẫn nằm trên
            # hồ sơ sau khi ứng viên bùng, để nguyên luật cũ là đếm nhầm họ vào đây.
            'onboard': ['&', ('onboard_result', '!=', 'no_show'),
                        '|', '|',
                        ('stage_id.sequence', '>=', seq_onboard),
                        ('start_date', '!=', False),
                        ('onboard_result', '=', 'arrived')],
            'hired':   [('stage_id.hired_stage', '=', True)],
        }

    # Khoá đếm trả về SPA cho từng nhóm. Tách khỏi APPLICANT_GROUPS vì tên khoá
    # JSON theo lối camelCase của SPA, còn khoá nhóm là tham số ?group= của API.
    _STAT_KEYS = {
        'cv': 'cvCount', 'cv_pass': 'cvPass', 'fail_cv': 'failCv',
        'pv': 'pvCount', 'pv_pass': 'pvPass', 'fail_pv': 'failPv',
        'onboard': 'onboard', 'hired': 'hired',
    }

    def _request_stats(self, reqs):
        """{req_id: {cvCount, cvPass, failCv, pvCount, pvPass, failPv, onboard, hired}}.

        Đếm rời từng phiếu là 8×N query; danh sách phiếu đang tuyển của khách đã
        vài chục dòng nên gom một lượt theo phiếu bằng _read_group rồi tra dict.
        """
        if not reqs:
            return {}

        Applicant = self._applicant_env()
        base = [('hb_request_id', 'in', reqs.ids)]

        def by_req(extra):
            return {q.id: n for q, n in Applicant._read_group(
                base + extra, ['hb_request_id'], ['__count'])}

        counts = {g: by_req(dom)
                  for g, dom in self._applicant_groups().items()}
        return {r.id: {key: counts[g].get(r.id, 0)
                       for g, key in self._STAT_KEYS.items()} for r in reqs}

    @http.route('/hocba-hrm/api/recruitment/request/<int:req_id>/applicants',
                auth='user', type='http', methods=['GET'])
    def api_recruitment_request_applicants(self, req_id, group='cv', **kw):
        """Danh sách ứng viên của một phiếu theo nhóm + thông tin JD kèm theo.

        Popup "xem chi tiết số ứng viên": khách cần biết ỨNG VIÊN NÀO chứ không
        chỉ bao nhiêu, và xem luôn JD đang tuyển để đối chiếu.
        """
        r = request.env['hb.recruitment.request'].sudo().browse(req_id)
        if not r.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        if not self._dep_in_scope(r.department_id.id):
            return self._forbidden()
        groups = self._applicant_groups()
        if group not in groups:
            return request.make_json_response(
                {'error': 'bad_request', 'message': 'Nhóm ứng viên không hợp lệ.'},
                status=400)

        apps = self._applicant_env().search(
            [('hb_request_id', '=', r.id)] + groups[group],
            order='date_received desc, id desc')
        rows = [self._cv_row(a) for a in apps]
        return request.make_json_response({
            'group': group,
            'jd': self._request_jd(r),
            'rows': rows,
            # Nhãn kết quả lọc CV / phỏng vấn: popup này không gọi /cv nên phải
            # tự mang nhãn theo, đừng bắt SPA hard-code lại chuỗi tiếng Việt.
            'cvResultLabels': self._sel_labels('hr.applicant', 'cv_filter_result'),
            'interviewResultLabels': self._sel_labels('hr.applicant', 'interview_result'),
        })

    def _request_jd(self, r):
        """Thông tin phiếu + JD hiển thị trên đầu popup ứng viên."""
        labels = {f: self._sel_labels('hb.recruitment.request', f)
                  for f in ('level', 'state', 'education', 'work_type', 'reason')}

        def money(v):
            return '{:,.0f}'.format(v).replace(',', '.') if v else ''

        salary = r.salary_range or ''
        if not salary and (r.salary_from or r.salary_to):
            salary = ('%s – %s VNĐ' % (money(r.salary_from), money(r.salary_to))
                      if r.salary_from and r.salary_to
                      else 'Từ %s VNĐ' % money(r.salary_from or r.salary_to))
        return {
            'id': r.id,
            'code': r.name or '',
            'jobTitle': r.job_title or '',
            'jobId': r.job_id.id or False,
            'jobName': r.job_id.name or '',
            'depName': r.department_id.name or '',
            'state': r.state or '',
            'stateLabel': labels['state'].get(r.state, ''),
            'qty': r.qty_expected or 0,
            'deadline': _d(r.expected_start_date),
            'dateRequest': _d(r.date_request),
            'requester': r.requester_id.name or '',
            'levelLabel': labels['level'].get(r.level, ''),
            'reasonLabel': labels['reason'].get(r.reason, ''),
            'educationLabel': (labels['education'].get(r.education, '')
                               if r.education and r.education != 'none' else ''),
            'workTypeLabel': labels['work_type'].get(r.work_type, ''),
            'experienceYears': r.experience_years or 0,
            'languageRequirement': r.language_requirement or '',
            'skillDescription': r.skill_description or '',
            'salary': salary,
            'jdLink': r.jd_link or '',
            'jdDescription': (r.job_id.description or '') if r.job_id else '',
            'published': self._job_published(r.job_id),
            'websiteUrl': (getattr(r.job_id, 'website_url', '') or '') if r.job_id else '',
        }

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
        # Vị trí mới KHÔNG mang sẵn chỉ tiêu tuyển: default của core hr.job là 1,
        # để nguyên thì JD vừa tạo đã "còn thiếu 1 người" trong khi chưa có phiếu
        # yêu cầu nào được duyệt. Chỉ tiêu ma đó khiến vị trí không bao giờ tự
        # Ngừng đăng khi tuyển đủ (xem hr_applicant._hb_auto_close_if_filled).
        # Form Thêm vị trí vì vậy cũng không còn ô "Số lượng cần tuyển".
        vals.setdefault('no_of_recruitment', 0)
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
        # Cùng luật với _job_meta(): HR thấy mọi phòng, trưởng phòng chỉ thấy
        # phòng mình quản lý (gồm phòng con) và vị trí thuộc các phòng đó.
        # api_recruitment_request_create đã chặn 403 khi lưu phiếu ngoài phạm
        # vi, nhưng liệt kê hết ở ô chọn thì TBP chọn xong mới ăn lỗi — chặn
        # ngay từ ô chọn cho gọn.
        scope = self._dept_scope_ids()
        dep_domain = [] if scope is None else [('id', 'in', scope)]
        job_domain = [] if scope is None else [('department_id', 'in', scope)]
        deps = env['hr.department'].sudo().search(dep_domain, order='name')
        jobs = env['hr.job'].sudo().search(job_domain, order='name')
        return {
            'departments': [{'id': d.id, 'name': d.name} for d in deps],
            # jdLink/status để form phiếu yêu cầu chọn JD thẳng từ kho: chọn xong
            # tự điền tên vị trí + link JD, khỏi copy tay từ tab Kho quản lý JD.
            'jobs': [{'id': j.id, 'name': j.name, 'dep': j.department_id.id,
                      'jdLink': j.jd_google_link or '',
                      'status': j.recruitment_status or ''} for j in jobs],
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

    @http.route('/hocba-hrm/api/recruitment/requests/pending-count',
                auth='user', type='http', methods=['GET'])
    def api_recruitment_requests_pending_count(self, **kw):
        """Số phiếu yêu cầu đang chờ duyệt — badge cạnh menu Tuyển dụng.

        Đếm đúng thứ NGƯỜI ĐANG ĐĂNG NHẬP bấm được: chỉ người duyệt (_is_hr)
        mới có việc. Theo quy trình 7.1, trưởng phòng là người ORDER phiếu chứ
        không duyệt → họ đếm 0 dù nhìn thấy phiếu của phòng mình.

        Không quyền trả 200 {count: 0} chứ không 403 — badge chỉ là trang trí,
        bắt SPA bắt lỗi cho một con số cạnh menu là thừa (khuôn của
        /api/timeoff/pending-count).
        """
        count = 0
        if self._is_hr():
            count = request.env['hb.recruitment.request'].sudo().search_count(
                [('state', '=', 'submitted')])
        return request.make_json_response({'count': count})

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
        """Ứng viên có email để chọn làm người nhận.

        Giới hạn theo phạm vi phòng ban như tab Danh sách CV: trưởng phòng chỉ
        thấy (và chỉ gửi được cho) ứng viên phòng mình. Trước đây search không
        điều kiện nên payload lộ họ tên · email · vị trí · bước của TOÀN BỘ
        ứng viên.
        """
        domain = [('email_from', '!=', False)]
        scope = self._dept_scope_ids()
        if scope is not None:
            domain += ['|', ('department_id', 'in', scope),
                       ('job_id.department_id', 'in', scope)]
        apps = request.env['hr.applicant'].sudo().search(
            domain, order='date_received desc, id desc')
        return [{
            'id': a.id, 'name': a.partner_name or '(Chưa có tên)',
            'email': a.email_from or '', 'jobName': a.job_id.name or '',
            'stage': a.stage_id.name or '',
            'stageRef': self._stage_refs().get(a.stage_id.id, ''),
        } for a in apps]

    @http.route('/hocba-hrm/api/recruitment/mail-templates', auth='user',
                type='http', methods=['GET'])
    def api_recruitment_mail_templates(self, **kw):
        """Danh sách mail mẫu (model hr.applicant) + ứng viên để gửi.

        Chỉ nhóm tuyển dụng (HR hoặc trưởng phòng) — payload kèm danh sách ứng
        viên (họ tên · email) nên user thường không được đọc.
        """
        if not self._is_recruiter():
            return self._forbidden('Chỉ bộ phận tuyển dụng mới xem được mail mẫu.')
        env = request.env
        applicant_model = env.ref('hr_recruitment.model_hr_applicant')
        tmpls = env['mail.template'].sudo().search(
            [('model_id', '=', applicant_model.id)], order='name')
        return request.make_json_response({
            # HAI quyền khác nhau, đừng gộp lại thành một cờ (bug C1 #5, QA 2026-08-07):
            #   canEdit — thêm/sửa/xoá/import mẫu. Mail mẫu là cấu hình email
            #             TOÀN HỆ THỐNG (không theo phòng ban) ⇒ chỉ HR.
            #   canSend — gửi mail cho ứng viên. Trưởng phòng được gửi, nhưng
            #             chỉ tới ứng viên phòng mình vì `recipients` và
            #             /preview đều đã lọc theo _dept_scope_ids().
            # Trước đây cả hai dùng chung khoá 'isRecruiter' = _is_hr(), trong
            # khi /mail/log-sent lại cho _is_recruiter() ⇒ nút "Gửi mail" của
            # trưởng phòng chạy được mà nhìn code không ai biết là cố ý hay lọt.
            'canEdit': self._is_hr(),
            'canSend': self._is_recruiter(),
            'rows': [self._tmpl_row(t) for t in tmpls],
            'recipients': self._applicant_recipients(),
        })

    @http.route('/hocba-hrm/api/recruitment/mail-template/<int:tmpl_id>',
                auth='user', type='http', methods=['GET'])
    def api_recruitment_mail_template(self, tmpl_id, **kw):
        if not self._is_recruiter():
            return self._forbidden('Chỉ bộ phận tuyển dụng mới xem được mail mẫu.')
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
        sent_ids = []
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
                sent_ids.append(aid)
            except (AccessError, ValidationError, UserError):
                skipped += 1
        self._apply_mail_stage_rule(t, Applicant.browse(sent_ids))
        return request.make_json_response({'sent': sent, 'skipped': skipped})

    @http.route('/hocba-hrm/api/recruitment/mail-template/<int:tmpl_id>/preview',
                auth='user', type='http', methods=['POST'], csrf=False)
    def api_recruitment_mail_template_preview(self, tmpl_id, **kw):
        """Render mail mẫu theo 1 ứng viên để XEM TRƯỚC (không gửi) — kiểm tra
        thông tin đã điền đúng chưa, không cần SMTP.

        Bản render chứa dữ liệu cá nhân của ứng viên ⇒ chặn như tab CV: phải là
        nhóm tuyển dụng VÀ ứng viên phải nằm trong phạm vi phòng ban.
        """
        if not self._is_recruiter():
            return self._forbidden('Chỉ bộ phận tuyển dụng mới xem trước được mail.')
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
        if not self._dep_in_scope(self._applicant_dep_id(a)):
            return self._forbidden()
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
        template auto_delete xoá mail.mail sau khi gửi). Trạng thái lấy từ notification.

        Chặn như tab CV: chỉ nhóm tuyển dụng, và trưởng phòng chỉ thấy lịch sử
        của ứng viên thuộc phòng mình (bản ghi kèm họ tên · email ứng viên).
        """
        if not self._is_recruiter():
            return self._forbidden('Chỉ bộ phận tuyển dụng mới xem được lịch sử mail.')
        env = request.env
        tz = self._user_tz()
        domain = [('model', '=', 'hr.applicant'),
                  ('message_type', 'in', ['email', 'email_outgoing'])]
        scope = self._dept_scope_ids()
        if scope is not None:
            in_scope = env['hr.applicant'].sudo().search(
                ['|', ('department_id', 'in', scope),
                 ('job_id.department_id', 'in', scope)])
            domain.append(('res_id', 'in', in_scope.ids))
        msgs = env['mail.message'].sudo().search(
            domain, order='date desc', limit=500)
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
        body: {logs: [{applicantId, subject, templateId}]}. Tạo mail.message
        (message_type='email') để tab Mail logs hiển thị như mail gửi qua server.

        templateId (tuỳ chọn) để áp MAIL_STAGE_RULES: gửi Thư mời phỏng vấn /
        Thư mời nhận việc thì đẩy bước luôn. Thiếu templateId (client cũ) thì chỉ
        ghi lịch sử như trước, không đổi bước.
        """
        if not self._is_recruiter():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        logs = (request.get_json_data() or {}).get('logs') or []
        Applicant = request.env['hr.applicant'].sudo()
        logged = 0
        by_tmpl = {}        # template_id -> ids ứng viên đã ghi nhận gửi
        for item in logs:
            aid = item.get('applicantId')
            if not aid:
                continue
            a = Applicant.browse(int(aid))
            if not a.exists():
                continue
            # Trưởng phòng chỉ ghi lịch sử cho ứng viên phòng mình (ghi chatter
            # lên hồ sơ ứng viên = thao tác ghi, phải cùng phạm vi với tab CV).
            if not self._dep_in_scope(self._applicant_dep_id(a)):
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
            tmpl_id = item.get('templateId')
            if tmpl_id:
                by_tmpl.setdefault(int(tmpl_id), []).append(a.id)
        Template = request.env['mail.template'].sudo()
        for tmpl_id, app_ids in by_tmpl.items():
            self._apply_mail_stage_rule(
                Template.browse(tmpl_id).exists(), Applicant.browse(app_ids))
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

    def _slot_in_scope(self, slot):
        """Slot này có nằm trong phạm vi thao tác của user không.

        HR: mọi slot. Trưởng phòng: slot thuộc phòng mình (department_id của
        slot tính theo phòng của người phỏng vấn). Ngoài ra ai cũng được dọn
        slot do CHÍNH MÌNH đứng tên — người khai lịch rảnh, kể cả nhóm
        Interviewer không quản phòng nào, phải tự xoá được lịch của mình.
        """
        if self._dept_scope_ids() is None:
            return True
        if slot.user_id.id == request.env.user.id:
            return True
        return self._dep_in_scope(slot.department_id.id)

    def _applicants_out_of_scope(self, applicants):
        """Các ứng viên nằm NGOÀI phạm vi phòng ban của user.

        Xếp / gỡ lịch là thao tác GHI lên hồ sơ ứng viên (ngày hẹn, giờ hẹn,
        người PV) và còn đẩy bước kanban, nên phải cùng một phạm vi với tab
        Danh sách CV — không phải cứ quản được slot là đụng được mọi hồ sơ.
        """
        return applicants.filtered(
            lambda a: not self._dep_in_scope(self._applicant_dep_id(a)))

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
            # Nhiều ứng viên có thể cùng phỏng vấn trong 1 slot.
            'applicants': [{'id': a.id,
                            'name': a.partner_name or '',
                            'jobName': a.job_id.name or ''}
                           for a in s.applicant_ids],
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
        # Payload này kèm HỌ TÊN ứng viên + danh bạ nhân viên nên phải cắt theo
        # phạm vi như tab Danh sách CV: HR thấy tất, trưởng phòng thấy phòng
        # mình, ai cũng thấy lịch do chính mình đứng tên (người khai lịch rảnh
        # phải xem lại được lịch của họ). User thường ⇒ scope rỗng ⇒ không thấy gì.
        scope = self._dept_scope_ids()
        domain = [('start_datetime', '>=', start_utc),
                  ('start_datetime', '<=', end_utc)]
        emp_domain = [('user_id', '!=', False)]
        if scope is not None:
            mine = ['|', ('department_id', 'in', scope),
                    ('user_id', '=', env.user.id)]
            domain += mine
            emp_domain += mine
        slots = env['hb.interview.slot'].sudo().search(domain, order='start_datetime')
        # Danh sách người phỏng vấn (nhân viên có tài khoản) để chọn khi tạo slot
        emps = env['hr.employee'].sudo().search(emp_domain, order='name')
        interviewers = [{'id': e.user_id.id, 'name': e.name} for e in emps]
        return request.make_json_response({
            'canManage': self._can_manage_slots(),
            'meId': env.user.id,
            'meName': env.user.name,
            'interviewers': interviewers,
            'rows': [self._slot_row(s) for s in slots],
            # Người khai slot là trưởng bộ phận — KHÔNG có quyền vào màn cấu
            # hình, nên khung giờ phải đi kèm ngay ở payload này.
            'hourOptions': self._slot_hours_payload()['options'],
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
            open_h, close_h, _step = Slot._hb_slot_hour_config()
            for ln in lines:
                day = fields.Date.from_string(ln['date'])
                sh = float(ln['startHour'])
                eh = float(ln['endHour'])
                if eh <= sh:
                    raise UserError('Giờ kết thúc phải sau giờ bắt đầu.')
                # Khung giờ là cấu hình của trung tâm — chặn ở API chứ không chỉ
                # ở dropdown, vì endpoint này nhận float tự do.
                if sh < open_h or eh > close_h:
                    raise UserError(
                        'Khung giờ phỏng vấn của trung tâm là %s–%s. Slot %s–%s '
                        'nằm ngoài khung. Cần khai ngoài giờ thì Admin nới khung '
                        'ở màn Cấu hình tuyển dụng → tab Khung giờ phỏng vấn.'
                        % (_hour_label(open_h), _hour_label(close_h),
                           _hour_label(sh), _hour_label(eh)))
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
        if not self._slot_in_scope(s):
            return self._forbidden('Slot này không thuộc phòng ban bạn quản lý.')
        if self._applicants_out_of_scope(s.applicant_ids):
            return self._forbidden(
                'Slot đang có ứng viên ngoài phòng ban bạn quản lý — xoá slot '
                'sẽ huỷ lịch của họ. Hãy nhờ HR xử lý.')
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
        """Thêm 1 ứng viên vào slot: nối vào applicant_ids (slot -> 'booked'), đồng thời
        điền lịch PV lên hồ sơ ứng viên (ngày/giờ/người PV) để khép vòng với tab
        Danh sách CV và mail Thư mời phỏng vấn (biến interview_date/time).
        Gọi nhiều lần để xếp nhiều ứng viên vào cùng khung giờ."""
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
        if self._applicants_out_of_scope(a):
            return self._forbidden(
                'Ứng viên này không thuộc phòng ban bạn quản lý.')
        if a in s.applicant_ids:
            return request.make_json_response(
                {'error': 'rejected',
                 'message': 'Ứng viên này đã có trong slot.'}, status=400)
        try:
            start_local = pytz.utc.localize(s.start_datetime).astimezone(self._user_tz())
            # ⚠️ THỨ TỰ CÓ Ý NGHĨA — đừng đảo:
            #   1) book slot  → luật "Hẹn & mời phỏng vấn → Phỏng vấn"
            #                   (hb_interview_slot._hb_advance_booked)
            #   2) ghi ngày PV → luật "Lên lịch phỏng vấn → Hẹn & mời phỏng vấn"
            # Nhờ vậy ứng viên đang ở "Lên lịch" chỉ tiến 1 nấc tới "Hẹn & mời"
            # (còn phải gửi thư mời), không nhảy thẳng vào "Phỏng vấn".
            s.write({'applicant_ids': [(4, a.id)]})
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
        """Hủy đặt slot (giữ nguyên lịch PV đã ghi trên hồ sơ ứng viên — chỉ giải
        phóng slot). body {applicantId} = gỡ đúng ứng viên đó; không truyền = gỡ hết."""
        if not self._can_manage_slots():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        s = request.env['hb.interview.slot'].sudo().browse(slot_id)
        if not s.exists():
            return request.make_json_response({'error': 'not_found'}, status=404)
        aid = (request.get_json_data() or {}).get('applicantId')
        # Gỡ 1 người thì kiểm đúng người đó; gỡ hết thì phải trong phạm vi TẤT
        # CẢ — không được mượn nút "gỡ hết" để huỷ lịch của phòng khác.
        targets = (request.env['hr.applicant'].sudo().browse(int(aid)).exists()
                   if aid else s.applicant_ids)
        if self._applicants_out_of_scope(targets):
            return self._forbidden(
                'Slot đang có ứng viên ngoài phòng ban bạn quản lý.')
        try:
            s.write({'applicant_ids': [(3, int(aid))] if aid else [(5, 0, 0)]})
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
        'active': ('active', 'bool'),
    }

    AUTO_CLOSE_LABELS = {
        'full': 'Ngừng đăng tuyển + đóng phiếu yêu cầu (mặc định)',
        'stop': 'Chỉ ngừng đăng tuyển (giữ phiếu đang tuyển)',
        'warn': 'Chỉ cảnh báo trên chatter, không đổi trạng thái',
        'off': 'Tắt — không làm gì khi tuyển đủ chỉ tiêu',
    }
    OVERDUE_NOTIFY_LABELS = {
        'both': 'HR tuyển dụng + Trưởng phòng của vị trí (mặc định)',
        'hr_only': 'Chỉ HR tuyển dụng',
        'manager_only': 'Chỉ Trưởng phòng của vị trí',
        'off': 'Tắt — không gửi thông báo quá hạn cho ai',
    }

    def _stage_config_row(self, s, applicant_counts=None, active_counts=None):
        count = (applicant_counts or {}).get(s.id)
        if count is None:
            count = request.env['hr.applicant'].sudo().with_context(
                active_test=False).search_count([('stage_id', '=', s.id)])
        active_count = (active_counts or {}).get(s.id)
        if active_count is None:
            active_count = request.env['hr.applicant'].sudo().search_count(
                [('stage_id', '=', s.id)])
        return {
            'id': s.id,
            'name': s.name or '',
            'sequence': s.sequence,
            'active': bool(s.active),
            'hiredStage': bool(s.hired_stage),
            'slaDays': s.sla_days or 0,
            'supportPerson': s.support_person or '',
            'requirements': s.requirements or '',
            'successCriteria': s.success_criteria or '',
            'applicantCount': count,
            'activeApplicantCount': active_count,
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
        if not self._can_config():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        env = request.env
        stages = env['hr.recruitment.stage'].sudo().with_context(
            active_test=False).search([], order='sequence, id')
        counts = dict(env['hr.applicant'].sudo().with_context(
            active_test=False)._read_group(
            [('stage_id', 'in', stages.ids)], ['stage_id'], ['__count']))
        counts = {s.id: c for s, c in counts.items()}
        active_counts = {s.id: c for s, c in env['hr.applicant'].sudo()._read_group(
            [('stage_id', 'in', stages.ids)], ['stage_id'], ['__count'])}
        return request.make_json_response({
            'isAdmin': self._is_admin(),   # HR Manager cũng vào được (spec v1.2)
            'canConfig': True,
            'autoCloseMode': env['hr.applicant']._hb_auto_close_mode(),
            'autoCloseLabels': self.AUTO_CLOSE_LABELS,
            'overdueNotifyMode': env['hr.applicant']._hb_overdue_notify_mode(),
            'overdueNotifyLabels': self.OVERDUE_NOTIFY_LABELS,
            'stages': [self._stage_config_row(s, counts, active_counts)
                       for s in stages],
            'slotHours': self._slot_hours_payload(),
        })

    def _slot_hours_payload(self):
        """Khung giờ khai lịch rảnh PV — dùng chung cho màn cấu hình và form khai."""
        Slot = request.env['hb.interview.slot'].sudo()
        open_h, close_h, step = Slot._hb_slot_hour_config()
        return {
            'open': open_h,
            'close': close_h,
            'stepMinutes': step,
            'stepChoices': list(SLOT_STEPS_ALLOWED),
            'options': [[v, lbl] for v, lbl in Slot._hb_hour_slots()],
        }

    @http.route('/hocba-hrm/api/recruitment/config/slot-hours', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_config_slot_hours(self, **kw):
        """Lưu khung giờ phỏng vấn — Admin / HR Manager."""
        if not self._can_config():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data() or {}
        try:
            open_h = float(payload.get('open'))
            close_h = float(payload.get('close'))
            step = int(payload.get('stepMinutes'))
        except (TypeError, ValueError):
            return request.make_json_response(
                {'error': 'invalid', 'message': 'Giá trị khung giờ không hợp lệ.'},
                status=400)
        if step not in SLOT_STEPS_ALLOWED:
            return request.make_json_response(
                {'error': 'invalid',
                 'message': 'Bước nhảy chỉ nhận %s phút.'
                            % ', '.join(str(s) for s in SLOT_STEPS_ALLOWED)},
                status=400)
        if not (0 <= open_h < close_h <= 24):
            return request.make_json_response(
                {'error': 'invalid',
                 'message': 'Giờ mở phải nhỏ hơn giờ đóng và nằm trong 0–24.'},
                status=400)
        # Khung hẹp hơn một bước nhảy ⇒ dropdown chỉ có đúng mốc mở, không khai
        # nổi slot nào (giờ kết thúc luôn phải sau giờ bắt đầu).
        if (close_h - open_h) < (step / 60.0):
            return request.make_json_response(
                {'error': 'invalid',
                 'message': 'Khung giờ %s–%s hẹp hơn một bước nhảy %s phút nên '
                            'không khai được slot nào.'
                            % (_hour_label(open_h), _hour_label(close_h), step)},
                status=400)
        ICP = request.env['ir.config_parameter'].sudo()
        ICP.set_param(P_SLOT_OPEN, str(open_h))
        ICP.set_param(P_SLOT_CLOSE, str(close_h))
        ICP.set_param(P_SLOT_STEP, str(step))
        return request.make_json_response(self._slot_hours_payload())

    @http.route('/hocba-hrm/api/recruitment/config/stages', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_recruitment_config_stage_create(self, **kw):
        """Thêm bước quy trình (vào cuối) — chỉ Admin."""
        if not self._can_config():
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
        if not self._can_config():
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
        if not self._can_config():
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
        if not self._can_config():
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
        """Lưu cấu hình chung — chỉ Admin. Nhận rời từng khoá:
        {autoCloseMode: full|stop|warn|off}
        {overdueNotifyMode: both|hr_only|manager_only|off}
        """
        if not self._can_config():
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data() or {}
        Param = request.env['ir.config_parameter'].sudo()
        for key, labels, param in (
                ('autoCloseMode', self.AUTO_CLOSE_LABELS,
                 'hocba_recruitments.auto_close_mode'),
                ('overdueNotifyMode', self.OVERDUE_NOTIFY_LABELS,
                 'hocba_recruitments.overdue_notify_mode')):
            mode = payload.get(key)
            if mode is None:
                continue
            if mode not in labels:
                return request.make_json_response(
                    {'error': 'bad_request', 'message': 'Chế độ không hợp lệ.'},
                    status=400)
            Param.set_param(param, mode)
        Applicant = request.env['hr.applicant']
        return request.make_json_response(
            {'ok': True,
             'autoCloseMode': Applicant._hb_auto_close_mode(),
             'overdueNotifyMode': Applicant._hb_overdue_notify_mode()})
