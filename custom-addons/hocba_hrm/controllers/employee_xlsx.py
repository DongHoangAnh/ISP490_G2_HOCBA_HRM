# ============================================================
# Nhập hồ sơ nhân viên từ Excel — parser thuần hàm.
# Owner: Việt. Spec: docs/superpowers/specs/2026-08-20-employee-excel-import-design.md
#
# Tách khỏi controller để test thẳng bằng hàm: dựng worksheet → dò header →
# chuẩn hoá từng ô → kiểm từng nhánh lỗi, không cần dựng HTTP request.
#
# Nguyên tắc: danh mục lạ (Tình trạng, Phòng ban) là LỖI DÒNG, không âm thầm
# rơi về mặc định — file thật có 52 dòng ghi "Online" ở cột Tình trạng, để rơi
# về 'probation' là 52 người bị gán nhầm quy trình nhận việc.
# ============================================================
import re
import unicodedata

MAX_XLSX_BYTES = 2 * 1024 * 1024
MAX_HEADER_SCAN = 10        # chỉ dò header trong ngần này dòng đầu
MIN_HEADER_HITS = 3         # dòng phải khớp ngần này tiêu đề mới coi là header


class EmployeeImportError(Exception):
    """Lỗi cả file — controller đổi thẳng ra JSON 400."""

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def strip_accents(txt):
    txt = txt.replace('đ', 'd').replace('Đ', 'D')
    return ''.join(c for c in unicodedata.normalize('NFD', txt)
                   if unicodedata.category(c) != 'Mn')


def norm_header(val):
    """Tên cột → khoá so sánh: bỏ dấu, hạ hoa-thường, gộp khoảng trắng, bỏ
    hậu tố "_text" mà file nghiệp vụ hay gắn ("Họ tên nhân sự_text")."""
    if val is None:
        return ''
    txt = strip_accents(str(val)).lower().replace('_', ' ')
    txt = re.sub(r'\s+', ' ', txt).strip()
    return re.sub(r'\s*text$', '', txt).strip()


# Bí danh cột → khoá nội bộ. Khoá 'emailAlt' là email cá nhân: chỉ dùng khi
# file KHÔNG có cột email công ty.
HEADER_ALIASES = {
    'ma nhan su': 'code', 'ma nhan vien': 'code', 'ma nv': 'code',
    'ho va ten': 'name', 'ho ten': 'name', 'ho ten nhan su': 'name',
    'ho va ten nhan vien': 'name',
    'tinh trang': 'status', 'trang thai': 'status',
    'hinh thuc': 'workForm', 'hinh thuc lam viec': 'workForm',
    'loai vi tri': 'posType',
    'phong ban': 'dep', 'phong': 'dep',
    'chuc danh': 'job', 'vi tri': 'job',
    'ngay thu viec': 'probStart',
    'ngay thang nam sinh': 'bday', 'ngay sinh': 'bday',
    'so can cuoc cong dan': 'cccd', 'cccd': 'cccd', 'so cccd': 'cccd',
    'ngay cap': 'idIssue', 'noi cap': 'idPlace',
    'so dien thoai': 'phone', 'sdt': 'phone',
    'email cong ty': 'email', 'email': 'email', 'email ca nhan': 'emailAlt',
    'so tai khoan': 'bankAccountNo', 'ngan hang': 'bankCode',
    'ma so thue tncn': 'pit', 'mst': 'pit',
    'so so bhxh': 'si',
    'so the bhyt': 'hi', 'noi dang ky bhyt': 'hiPlace',
    # "thường chú" là lỗi chính tả có thật trong file nghiệp vụ của trung tâm.
    'dia chi thuong tru': 'permStreet', 'dia chi thuong chu': 'permStreet',
    'dia chi hien tai': 'currStreet',
}


def _map_row(cells):
    """Một dòng ô → (colmap, unknown_cols). Cột trùng khoá thì cột TRÁI thắng."""
    colmap, unknown = {}, []
    for idx, val in enumerate(cells):
        if val is None or not str(val).strip():
            continue
        key = HEADER_ALIASES.get(norm_header(val))
        if not key:
            unknown.append(str(val).strip())
        elif key not in colmap:
            colmap[key] = idx
    return colmap, unknown


def locate_header(ws):
    """Tìm dòng tiêu đề trong MAX_HEADER_SCAN dòng đầu.

    Trả (số dòng 1-based, colmap, danh sách cột không nhận diện được).
    """
    for row_idx, cells in enumerate(
            ws.iter_rows(min_row=1, max_row=MAX_HEADER_SCAN, values_only=True), 1):
        colmap, unknown = _map_row(cells)
        if len(colmap) < MIN_HEADER_HITS:
            continue
        # Email cá nhân chỉ được dùng khi không có cột email công ty.
        if 'email' not in colmap and 'emailAlt' in colmap:
            colmap['email'] = colmap['emailAlt']
        colmap.pop('emailAlt', None)
        if 'name' not in colmap:
            raise EmployeeImportError(
                'no_name_col',
                'File không có cột "Họ và tên" — không xác định được nhân viên. '
                'Đổi tên cột thành "Họ và tên" rồi tải lên lại.')
        return row_idx, colmap, unknown
    raise EmployeeImportError(
        'no_header',
        'Không tìm thấy dòng tiêu đề trong %d dòng đầu. File cần một dòng ghi '
        'tên cột (Mã nhân sự, Họ và tên, Tình trạng, Phòng ban…).' % MAX_HEADER_SCAN)
