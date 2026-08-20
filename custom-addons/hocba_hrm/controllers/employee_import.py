# ============================================================
# Nhập hồ sơ nhân viên từ Excel — 2 route REST.
# Owner: Việt. Spec: docs/superpowers/specs/2026-08-20-employee-excel-import-design.md
#
# preview: đọc-kiểm, KHÔNG ghi gì.  commit: ghi trong MỘT transaction.
# Tách khỏi main.py (đã hơn 4.400 dòng) cho dễ đọc.
# ============================================================
from odoo import http
from odoo.http import request

from .employee_xlsx import (
    EmployeeImportError, MAX_XLSX_BYTES, norm_header, parse_employees_xlsx,
)
from .main import SPA_ENABLED, _cap_import_emp


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
