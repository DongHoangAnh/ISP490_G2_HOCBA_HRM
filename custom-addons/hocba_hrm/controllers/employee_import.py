# ============================================================
# Nhập hồ sơ nhân viên từ Excel — 2 route REST.
# Owner: Việt. Spec: docs/superpowers/specs/2026-08-20-employee-excel-import-design.md
#
# preview: đọc-kiểm, KHÔNG ghi gì.  commit: ghi trong MỘT transaction.
# Tách khỏi main.py (đã hơn 4.400 dòng) cho dễ đọc.
# ============================================================
from psycopg2 import IntegrityError

from odoo import http
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.http import request

from .employee_xlsx import (
    EmployeeImportError, MAX_XLSX_BYTES, norm_header, parse_employees_xlsx,
)
from .main import SPA_ENABLED, _cap_import_emp

# Field được phép ghi từ file import. KHÔNG có wage — lương không nhập qua
# đường này (spec §10), và không tin payload client gửi field ngoài danh sách.
IMPORT_EMP_FIELDS = {
    'name', 'x_employee_code', 'department_id', 'job_id', 'job_title',
    'x_employment_status', 'x_work_form', 'x_position_type',
    'x_probation_start', 'birthday', 'x_id_date_issue', 'x_id_place_issue',
    'work_phone', 'work_email', 'x_bank_account_no', 'x_bank_code',
    'x_pit_code', 'x_social_insurance_no', 'x_health_insurance_no',
    'x_health_care_place', 'x_permanent_street', 'x_current_street',
}


class HocBaEmployeeImport(http.Controller):

    # ------------------------------------------------------------- helpers
    def _catalogs(self):
        """Danh mục phòng ban / chức danh, khoá đã chuẩn hoá để so tên."""
        Dep = request.env['hr.department'].sudo()
        Job = request.env['hr.job'].sudo()
        return {
            'departments': {norm_header(d.name): d.id for d in Dep.search([])},
            'jobs': {norm_header(j.name): j.id for j in Job.search([])},
        }

    def _existing(self):
        """Mã NV + CCCD đã có, để bỏ qua dòng trùng.

        active_test=False: hồ sơ đã lưu trữ vẫn giữ mã và CCCD, nhập đè lên là
        sinh bản sao của cùng một người.
        """
        Emp = request.env['hr.employee'].sudo().with_context(active_test=False)
        emps = Emp.search([])
        return {
            'codes': {c for c in emps.mapped('x_employee_code') if c},
            'cccds': {c for c in emps.mapped('version_id.identification_id') if c},
        }

    def _preview_payload(self, upload, sheet):
        """Kiểm file rồi trả bảng xem trước. Tách khỏi route để test thuần."""
        filename = getattr(upload, 'filename', '') or ''
        if not upload or not filename:
            raise EmployeeImportError('no_file', 'Chưa chọn file để tải lên.')
        if not filename.lower().endswith('.xlsx'):
            raise EmployeeImportError(
                'bad_ext',
                'Chỉ nhận file Excel .xlsx (file bạn chọn: "%s"). Nếu đang dùng '
                '.xls hoặc .csv, hãy mở bằng Excel rồi "Lưu dưới dạng" .xlsx.'
                % filename)
        content = upload.read()
        if len(content) > MAX_XLSX_BYTES:
            raise EmployeeImportError(
                'too_large',
                'File nặng quá %d MB.' % (MAX_XLSX_BYTES // (1024 * 1024)))
        res = parse_employees_xlsx(content, sheet, self._catalogs(), self._existing())
        res['filename'] = filename
        return res

    # -------------------------------------------------------------- routes
    @http.route('/hocba-hrm/api/employees/import/preview', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_employee_import_preview(self, **kw):
        """Đọc + KIỂM file, KHÔNG ghi gì — SPA xem trước rồi mới bấm Nhập."""
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        if not _cap_import_emp(request.env):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        try:
            payload = self._preview_payload(kw.get('file'), kw.get('sheet') or None)
        except EmployeeImportError as ex:
            return request.make_json_response(
                {'error': ex.code, 'message': ex.message}, status=400)
        return request.make_json_response(payload)

    # --------------------------------------------------------------- ghi
    def _commit_rows(self, rows):
        """Ghi các dòng đã duyệt. Trọn gói: lỗi bất kỳ → raise, caller rollback.

        Kiểm LẠI toàn bộ ở đây — payload đi vòng qua trình duyệt nên không tin
        được, kể cả khi bước xem trước đã lọc sạch.
        """
        existing = self._existing()
        codes, cccds = existing['codes'], existing['cccds']
        Emp = request.env['hr.employee'].sudo().with_context(
            hocba_legacy_import=True, hocba_no_onb_assign=True)

        created, need_completion = [], 0
        for row in rows or []:
            excel_row = row.get('excelRow') or 0
            raw = row.get('values') or {}
            vals = {k: v for k, v in raw.items() if k in IMPORT_EMP_FIELDS}
            cccd = raw.get('cccd') or ''
            if not (vals.get('name') or '').strip():
                raise EmployeeImportError(
                    'empty_name', 'Dòng %d: thiếu Họ và tên.' % excel_row)
            code = vals.get('x_employee_code')
            if code and code in codes:
                raise EmployeeImportError(
                    'code_exists',
                    'Dòng %d: mã nhân sự "%s" đã tồn tại.' % (excel_row, code))
            if cccd and cccd in cccds:
                raise EmployeeImportError(
                    'cccd_exists',
                    'Dòng %d: CCCD "%s" đã tồn tại.' % (excel_row, cccd))
            try:
                emp = Emp.create(vals)
                if cccd:
                    emp.version_id.sudo().with_context(
                        hocba_legacy_import=True).write(
                            {'identification_id': cccd})
            except IntegrityError as ex:
                raise EmployeeImportError(
                    'rejected', 'Dòng %d: %s' % (excel_row, ex))
            except (AccessError, ValidationError, UserError) as ex:
                raise EmployeeImportError(
                    'rejected', 'Dòng %d: %s' % (excel_row, ex))
            if code:
                codes.add(code)
            if cccd:
                cccds.add(cccd)
            if row.get('missingOfficial'):
                need_completion += 1
            created.append(emp.id)

        return {'created': len(created), 'needCompletion': need_completion,
                'employeeIds': created}

    @http.route('/hocba-hrm/api/employees/import/commit', auth='user',
                type='http', methods=['POST'], csrf=False)
    def api_employee_import_commit(self, **kw):
        """Ghi các dòng SPA gửi lại từ bảng xem trước. Lỗi → rollback cả mẻ.

        Không bắn thông báo: hồ sơ thiếu giấy tờ được đánh dấu thường trực bằng
        badge trên menu Nhân viên + icon trên dòng NV (xem employee_flags).
        """
        if not SPA_ENABLED:
            return request.make_json_response({'error': 'spa_disabled'}, status=410)
        if not _cap_import_emp(request.env):
            return request.make_json_response({'error': 'forbidden'}, status=403)
        payload = request.get_json_data() or {}
        try:
            res = self._commit_rows(payload.get('rows') or [])
        except EmployeeImportError as ex:
            request.env.cr.rollback()
            return request.make_json_response(
                {'error': ex.code, 'message': ex.message}, status=400)
        return request.make_json_response(res)
