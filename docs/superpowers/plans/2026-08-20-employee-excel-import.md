# Nhập hồ sơ nhân viên từ Excel — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Thêm nút "Nhập từ Excel" trên màn Nhân viên để HR nhập hàng loạt hồ sơ nhân sự cũ từ file Excel có sẵn của trung tâm.

**Architecture:** Parser thuần hàm (`employee_xlsx.py`) đọc bytes → danh sách dòng đã chuẩn hoá, không đụng HTTP/ORM nên test được trực tiếp. Hai route REST tách bạch: `preview` chỉ đọc-kiểm và trả bảng xem trước (không ghi gì), `commit` nhận lại các dòng đã duyệt rồi ghi trong một transaction. SPA mở modal 2 bước. Bám đúng khuôn `hocba_timeoff/controllers/workday_xlsx.py` đã chạy thật.

**Tech Stack:** Odoo 19 (Python 3.12), openpyxl (đã có sẵn trong image Odoo), React 18 + Vite 6, test bằng `odoo.tests.TransactionCase`.

**Spec:** `docs/superpowers/specs/2026-08-20-employee-excel-import-design.md`

## Global Constraints

- Odoo 19: `res.users` dùng `group_ids` (KHÔNG phải `groups_id`); CCCD (`identification_id`) nằm trên `hr.version`, không phải `hr.employee`.
- BR-010: NV `official` phải có CCCD + MST TNCN + số sổ BHXH. Luồng import được miễn qua context `hocba_legacy_import=True`; **mọi luồng khác vẫn phải bị chặn**.
- Context `hocba_no_onb_assign=True` đã tồn tại sẵn trong `hr_employee.py` — dùng để NV nhập vào không bị gán quy trình nhận việc.
- Quyền dùng import: **chỉ** `base.group_system` hoặc `hr.group_hr_manager`.
- Giới hạn file: `.xlsx`, tối đa **10 MB** (`MAX_XLSX_BYTES = 10 * 1024 * 1024`) — file nghiệp vụ thật đã 2,21 MB.
- Route SPA: `type="http"`, trả JSON qua `request.make_json_response`, route ghi đặt `csrf=False`. Khoá JSON dạng camelCase.
- Test bắt buộc chạy bằng lệnh dưới (thiếu `MSYS_NO_PATHCONV=1` trên Git Bash → chạy 0 test mà vẫn báo OK):

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

Kết quả cần thấy: `0 failed, 0 error(s) of N tests` với N > 0.

---

## File Structure

| File | Trách nhiệm |
|---|---|
| `custom-addons/hocba_hrm/controllers/employee_xlsx.py` *(mới)* | Hàm thuần: dò header, ánh xạ cột, chuẩn hoá giá trị, dựng rows/errors. Không import `request`, không đụng ORM. |
| `custom-addons/hocba_hrm/controllers/employee_import.py` *(mới)* | 2 route REST + kiểm quyền + ghi ORM. |
| `custom-addons/hocba_hrm/controllers/__init__.py` | Đăng ký `employee_import`. |
| `custom-addons/hocba_hrm/controllers/main.py` | Thêm `_cap_import_emp()` + khoá `canImport` vào payload `/api/employees`. |
| `custom-addons/hocba_employees/models/hr_employee.py` | Cửa thoát context cho BR-010. |
| `custom-addons/hocba_hrm/tests/test_employee_import.py` *(mới)* | Test parser + controller. |
| `custom-addons/hocba_hrm/tests/__init__.py` | Đăng ký test. |
| `frontend/src/api/employees.js` | 2 hàm gọi API. |
| `frontend/src/features/employees/ImportEmployeesModal.jsx` *(mới)* | Modal 2 bước. |
| `frontend/src/features/employees/Employees.jsx` | Nút "Nhập từ Excel". |

---

### Task 1: Parser — dò header & ánh xạ cột

**Files:**
- Create: `custom-addons/hocba_hrm/controllers/employee_xlsx.py`
- Create: `custom-addons/hocba_hrm/tests/test_employee_import.py`
- Modify: `custom-addons/hocba_hrm/tests/__init__.py`

**Interfaces:**
- Consumes: không có (task đầu tiên).
- Produces:
  - `EmployeeImportError(code, message)` — exception có `.code`, `.message`
  - `norm_header(val) -> str`
  - `HEADER_ALIASES: dict[str, str]`
  - `locate_header(ws) -> (int header_row, dict colmap, list unknown_cols)` — `colmap` là `{khoá: chỉ số cột 0-based}`
  - `MAX_XLSX_BYTES: int`

- [ ] **Step 1: Viết test đỏ**

Tạo `custom-addons/hocba_hrm/tests/test_employee_import.py`:

```python
"""Nhập hồ sơ nhân viên từ Excel (controllers/employee_xlsx.py + employee_import.py).

Trọng tâm: parser là hàm thuần nên test thẳng, không dựng HTTP. Các nhánh danh
mục SAI phải báo lỗi kèm số dòng Excel chứ không âm thầm rơi về mặc định.
"""
import io

import openpyxl
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

from odoo.addons.hocba_hrm.controllers.employee_xlsx import (
    EmployeeImportError, HEADER_ALIASES, locate_header, norm_header,
)


def _sheet(rows):
    """list[list] → worksheet openpyxl (dòng 1 của file = rows[0])."""
    wb = openpyxl.Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    out = io.BytesIO()
    wb.save(out)
    return openpyxl.load_workbook(io.BytesIO(out.getvalue())).worksheets[0]


HDR = ['Mã nhân sự', 'Họ và tên', 'Tình trạng', 'Phòng Ban', 'Chức danh']


@tagged('post_install', '-at_install')
class TestEmployeeXlsxHeader(TransactionCase):

    def test_norm_header_stripped_accents_and_suffix(self):
        self.assertEqual(norm_header('Họ và tên'), 'ho va ten')
        self.assertEqual(norm_header('Họ tên nhân sự_text'), 'ho ten nhan su')
        self.assertEqual(norm_header('  Phòng  Ban '), 'phong ban')
        self.assertEqual(norm_header(None), '')

    def test_locate_header_on_first_row(self):
        ws = _sheet([HDR, ['HB.01', 'Nguyễn A', 'Chính thức', 'Marketing', 'NV']])
        row, colmap, unknown = locate_header(ws)
        self.assertEqual(row, 1)
        self.assertEqual(colmap['code'], 0)
        self.assertEqual(colmap['name'], 1)
        self.assertEqual(colmap['status'], 2)
        self.assertEqual(unknown, [])

    def test_locate_header_below_title_rows(self):
        ws = _sheet([['DANH SÁCH NHÂN SỰ'], [], HDR,
                     ['HB.01', 'Nguyễn A', 'Chính thức', 'Marketing', 'NV']])
        row, colmap, _u = locate_header(ws)
        self.assertEqual(row, 3)
        self.assertEqual(colmap['name'], 1)

    def test_locate_header_missing_raises(self):
        ws = _sheet([['a', 'b'], ['c', 'd']])
        with self.assertRaises(EmployeeImportError) as cm:
            locate_header(ws)
        self.assertEqual(cm.exception.code, 'no_header')

    def test_locate_header_without_name_column_raises(self):
        ws = _sheet([['Mã nhân sự', 'Tình trạng', 'Phòng Ban', 'Chức danh']])
        with self.assertRaises(EmployeeImportError) as cm:
            locate_header(ws)
        self.assertEqual(cm.exception.code, 'no_name_col')

    def test_unknown_columns_collected(self):
        ws = _sheet([HDR + ['Tài khoản Lark', 'Màn máy tính']])
        _row, colmap, unknown = locate_header(ws)
        self.assertNotIn('lark', colmap)
        self.assertEqual(unknown, ['Tài khoản Lark', 'Màn máy tính'])

    def test_company_email_wins_over_personal(self):
        ws = _sheet([['Họ và tên', 'Email cá nhân', 'Email công ty']])
        _row, colmap, _u = locate_header(ws)
        self.assertEqual(colmap['email'], 2)

    def test_personal_email_used_when_no_company_column(self):
        ws = _sheet([['Họ và tên', 'Email cá nhân']])
        _row, colmap, _u = locate_header(ws)
        self.assertEqual(colmap['email'], 1)

    def test_every_alias_maps_to_known_key(self):
        keys = {'code', 'name', 'status', 'workForm', 'posType', 'dep', 'job',
                'probStart', 'bday', 'cccd', 'idIssue', 'idPlace', 'phone',
                'email', 'emailAlt', 'bankAccountNo', 'bankCode', 'pit', 'si',
                'hi', 'hiPlace', 'permStreet', 'currStreet'}
        self.assertEqual(set(HEADER_ALIASES.values()) - keys, set())
```

Đăng ký test — thêm vào cuối `custom-addons/hocba_hrm/tests/__init__.py`:

```python
from . import test_employee_import
```

- [ ] **Step 2: Chạy test cho chắc là ĐỎ**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

Kỳ vọng: FAIL với `ModuleNotFoundError: No module named 'odoo.addons.hocba_hrm.controllers.employee_xlsx'`.

- [ ] **Step 3: Viết implementation tối thiểu**

Tạo `custom-addons/hocba_hrm/controllers/employee_xlsx.py`:

```python
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

MAX_XLSX_BYTES = 10 * 1024 * 1024
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
```

- [ ] **Step 4: Chạy test cho chắc là XANH**

Lệnh như Step 2. Kỳ vọng: `0 failed, 0 error(s)`, 9 test của `TestEmployeeXlsxHeader` chạy.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/employee_xlsx.py custom-addons/hocba_hrm/tests/test_employee_import.py custom-addons/hocba_hrm/tests/__init__.py
git commit -m "feat(emp-import): parser do dong tieu de va anh xa cot Excel"
```

---

### Task 2: Parser — chuẩn hoá giá trị & dựng rows

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/employee_xlsx.py`
- Modify: `custom-addons/hocba_hrm/tests/test_employee_import.py`

**Interfaces:**
- Consumes: `locate_header`, `norm_header`, `EmployeeImportError` (Task 1).
- Produces:
  - `parse_employees_xlsx(content, sheet=None, catalogs=None, existing=None) -> dict` với các khoá `sheets, sheet, headerRow, rows, skipped, errors, unknownCols, summary`
  - Mỗi phần tử `rows`: `{'excelRow': int, 'name': str, 'code': str|None, 'depId': int|None, 'depName': str, 'jobId': int|None, 'jobName': str, 'status': str|None, 'warnings': list[str], 'missingOfficial': list[str], 'values': dict}` — `values` dùng **tên field hr.employee**, riêng khoá `cccd` là của `hr.version`.
  - `catalogs` = `{'departments': {norm_name: id}, 'jobs': {norm_name: id}}`; `existing` = `{'codes': set[str], 'cccds': set[str]}`.

- [ ] **Step 1: Viết test đỏ**

Thêm vào `custom-addons/hocba_hrm/tests/test_employee_import.py`:

```python
from odoo.addons.hocba_hrm.controllers.employee_xlsx import parse_employees_xlsx


def _book(rows, sheet_title='2.1. Quản lý nhân sự'):
    """list[list] → bytes .xlsx."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = sheet_title
    for r in rows:
        ws.append(r)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


FULL_HDR = ['Mã nhân sự', 'Họ và tên', 'Tình trạng', 'Hình thức', 'Loại vị trí',
            'Phòng Ban', 'Chức danh', 'Ngày thử việc', 'Số căn cước công dân',
            'Số điện thoại', 'Email công ty', 'Mã số thuế TNCN', 'Số sổ BHXH']


def _row(code='HB.01', name='Nguyễn Văn A', status='Chính thức', form='Offline',
         pos='Nhân viên', dep='Marketing', job='Nhân viên R&D', prob='01/06/2024',
         cccd='038098029187', phone='0325252626', email='a@hocba.vn',
         pit=None, si=None):
    return [code, name, status, form, pos, dep, job, prob, cccd, phone, email, pit, si]


CATALOGS = {'departments': {'marketing': 11, 'san pham (r&d_sp)': 12},
            'jobs': {'nhan vien r&d': 21}}


@tagged('post_install', '-at_install')
class TestEmployeeXlsxParse(TransactionCase):

    def _parse(self, rows, existing=None, hdr=None):
        return parse_employees_xlsx(_book([hdr or FULL_HDR] + rows),
                                    catalogs=CATALOGS, existing=existing)

    def test_happy_row(self):
        res = self._parse([_row()])
        self.assertEqual(res['summary']['ok'], 1)
        r = res['rows'][0]
        self.assertEqual(r['excelRow'], 2)
        self.assertEqual(r['values']['name'], 'Nguyễn Văn A')
        self.assertEqual(r['values']['x_employment_status'], 'official')
        self.assertEqual(r['values']['x_work_form'], 'offline')
        self.assertEqual(r['values']['x_position_type'], 'staff')
        self.assertEqual(r['values']['department_id'], 11)
        self.assertEqual(r['values']['job_id'], 21)
        self.assertEqual(r['values']['cccd'], '038098029187')

    def test_cccd_keeps_leading_zero(self):
        res = self._parse([_row(cccd='038098029187')])
        self.assertEqual(res['rows'][0]['values']['cccd'], '038098029187')

    def test_cccd_wrong_length_warns_and_blanks(self):
        res = self._parse([_row(cccd='12345')])
        r = res['rows'][0]
        self.assertNotIn('cccd', r['values'])
        self.assertTrue(any('CCCD' in w for w in r['warnings']))

    def test_status_online_is_row_error(self):
        res = self._parse([_row(status='Online')])
        self.assertEqual(res['rows'], [])
        self.assertEqual(res['errors'][0]['code'], 'bad_status')
        self.assertEqual(res['errors'][0]['excelRow'], 2)

    def test_department_alias_matched(self):
        res = self._parse([_row(dep='Phòng R&D_SP')])
        self.assertEqual(res['rows'][0]['values']['department_id'], 12)

    def test_unknown_department_is_row_error(self):
        res = self._parse([_row(dep='Phòng ma')])
        self.assertEqual(res['errors'][0]['code'], 'bad_department')

    def test_unknown_job_kept_as_text(self):
        res = self._parse([_row(job='Nhân viên tư vấn tuyển sinh thử việc')])
        vals = res['rows'][0]['values']
        self.assertNotIn('job_id', vals)
        self.assertEqual(vals['job_title'], 'Nhân viên tư vấn tuyển sinh thử việc')

    def test_dates_accept_three_string_formats(self):
        for txt in ('01/06/2024', '2024-06-01', '01-06-2024'):
            res = self._parse([_row(prob=txt)])
            self.assertEqual(str(res['rows'][0]['values']['x_probation_start']),
                             '2024-06-01', txt)

    def test_bad_date_warns_and_blanks(self):
        res = self._parse([_row(prob='Cần ngay')])
        r = res['rows'][0]
        self.assertNotIn('x_probation_start', r['values'])
        self.assertTrue(r['warnings'])

    def test_bad_email_warns_and_blanks(self):
        res = self._parse([_row(email='khong-phai-email')])
        self.assertNotIn('work_email', res['rows'][0]['values'])

    def test_empty_name_is_row_error(self):
        res = self._parse([_row(name='   ')])
        self.assertEqual(res['errors'][0]['code'], 'empty_name')

    def test_blank_rows_ignored_not_errors(self):
        res = self._parse([_row(), [None] * len(FULL_HDR)])
        self.assertEqual(res['summary']['total'], 1)
        self.assertEqual(res['errors'], [])

    def test_existing_code_skipped(self):
        res = self._parse([_row(code='HB.01')],
                          existing={'codes': {'HB.01'}, 'cccds': set()})
        self.assertEqual(res['rows'], [])
        self.assertEqual(res['skipped'][0]['reason'], 'code_exists')

    def test_existing_cccd_skipped(self):
        res = self._parse([_row(code='HB.99')],
                          existing={'codes': set(), 'cccds': {'038098029187'}})
        self.assertEqual(res['skipped'][0]['reason'], 'cccd_exists')

    def test_duplicate_code_inside_file_skipped_second(self):
        res = self._parse([_row(code='HB.07'), _row(code='HB.07', cccd='038098029188')])
        self.assertEqual(len(res['rows']), 1)
        self.assertEqual(res['skipped'][0]['reason'], 'code_exists')

    def test_missing_official_fields_reported(self):
        res = self._parse([_row(pit=None, si=None)])
        self.assertEqual(res['rows'][0]['missingOfficial'], ['MST TNCN', 'Số sổ BHXH'])
        self.assertEqual(res['summary']['needCompletion'], 1)

    def test_probation_row_has_no_missing_official(self):
        res = self._parse([_row(status='Thử việc', pit=None, si=None)])
        self.assertEqual(res['rows'][0]['missingOfficial'], [])

    def test_sheet_list_and_chosen_sheet(self):
        res = self._parse([_row()])
        self.assertEqual(res['sheet'], '2.1. Quản lý nhân sự')
        self.assertIn('2.1. Quản lý nhân sự', res['sheets'])
```

- [ ] **Step 2: Chạy test cho chắc là ĐỎ**

Lệnh như Task 1 Step 2. Kỳ vọng: FAIL với `ImportError: cannot import name 'parse_employees_xlsx'`.

- [ ] **Step 3: Viết implementation tối thiểu**

Thêm vào cuối `custom-addons/hocba_hrm/controllers/employee_xlsx.py`:

```python
import io
from datetime import date, datetime

import openpyxl

# Nhãn trong file nghiệp vụ → mã Selection của model. Khoá đã qua norm_header.
STATUS_MAP = {
    'chinh thuc': 'official', 'thu viec': 'probation', 'tts': 'intern',
    'parttime': 'parttime', 'part time': 'parttime', 'part-time': 'parttime',
    'ctv': 'ctv', 'co van': 'advisor', 'nghi viec': 'resigned',
    'dang offboarding': 'exiting',
}
WORK_FORM_MAP = {'offline': 'offline', 'online': 'online'}
POS_TYPE_MAP = {'quan ly': 'manager', 'nhan vien': 'staff', 'ctv': 'ctv',
                'freelancer': 'freelancer', 'co van': 'advisor'}

# Bí danh phòng ban: tên trong file → tên trong danh mục (đã norm_header).
# "Phòng Nhân sự" CỐ Ý không có ở đây — chưa hỏi được Học Bá nó thuộc đơn vị
# nào, nên để rơi vào bad_department thay vì đoán (xem spec §7.3).
DEPT_ALIASES = {
    'phong r&d sp': 'san pham (r&d_sp)',
    'phong r&d_sp': 'san pham (r&d_sp)',
    'ke toan': 'ke toan_hcns',
}

DATE_FORMATS = ('%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%d/%m/%y')
EMAIL_RE = re.compile(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')

# Khoá parser → field hr.employee. 'cccd' xử lý riêng (nằm trên hr.version).
TEXT_FIELDS = {
    'code': 'x_employee_code', 'phone': 'work_phone',
    'idPlace': 'x_id_place_issue', 'bankAccountNo': 'x_bank_account_no',
    'bankCode': 'x_bank_code', 'pit': 'x_pit_code',
    'si': 'x_social_insurance_no', 'hi': 'x_health_insurance_no',
    'hiPlace': 'x_health_care_place', 'permStreet': 'x_permanent_street',
    'currStreet': 'x_current_street',
}
DATE_FIELDS = {'probStart': 'x_probation_start', 'bday': 'birthday',
               'idIssue': 'x_id_date_issue'}


def _text(val):
    if val is None:
        return ''
    if isinstance(val, float) and val.is_integer():
        return str(int(val))
    return str(val).strip()


def to_date(val):
    """Ô Excel → date. Nhận ô kiểu ngày lẫn chuỗi dd/mm/yyyy | yyyy-mm-dd."""
    if isinstance(val, datetime):
        return val.date()
    if isinstance(val, date):
        return val
    txt = _text(val)
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(txt, fmt).date()
        except ValueError:
            continue
    return None


def clean_cccd(val):
    """Chuỗi CCCD → 12 chữ số, hoặc None. Giữ số 0 đầu (ô Excel là text)."""
    digits = re.sub(r'\D', '', _text(val))
    return digits if len(digits) == 12 else None


def _parse_row(cells, colmap, excel_row, catalogs):
    """Một dòng dữ liệu → (row dict, error dict). Đúng một trong hai khác None."""
    def cell(key):
        idx = colmap.get(key)
        return cells[idx] if idx is not None and idx < len(cells) else None

    def err(code, message):
        return None, {'excelRow': excel_row, 'code': code, 'message': message}

    name = _text(cell('name'))
    if not name:
        return err('empty_name', 'Dòng %d: thiếu Họ và tên.' % excel_row)

    vals, warnings = {'name': name}, []

    raw_status = _text(cell('status'))
    if raw_status:
        status = STATUS_MAP.get(norm_header(raw_status))
        if not status:
            return err('bad_status',
                       'Dòng %d: Tình trạng "%s" không thuộc danh mục '
                       '(Chính thức / Thử việc / TTS / Part-time / CTV / '
                       'Cố vấn / Nghỉ việc).' % (excel_row, raw_status))
        vals['x_employment_status'] = status

    raw_dep = _text(cell('dep'))
    if raw_dep:
        key = norm_header(raw_dep)
        key = DEPT_ALIASES.get(key, key)
        dep_id = (catalogs.get('departments') or {}).get(key)
        if not dep_id:
            return err('bad_department',
                       'Dòng %d: Phòng ban "%s" không khớp danh mục. Sửa lại '
                       'trong file hoặc thêm phòng ban vào hệ thống rồi tải '
                       'lên lại.' % (excel_row, raw_dep))
        vals['department_id'] = dep_id

    raw_job = _text(cell('job'))
    if raw_job:
        job_id = (catalogs.get('jobs') or {}).get(norm_header(raw_job))
        if job_id:
            vals['job_id'] = job_id
        # Luôn giữ nguyên văn: danh mục hệ thống ~16 vị trí, file có 48.
        vals['job_title'] = raw_job

    for key, code in (('workForm', 'x_work_form'), ('posType', 'x_position_type')):
        raw = _text(cell(key))
        if not raw:
            continue
        table = WORK_FORM_MAP if key == 'workForm' else POS_TYPE_MAP
        mapped = table.get(norm_header(raw))
        if mapped:
            vals[code] = mapped
        else:
            warnings.append('%s "%s" không thuộc danh mục — để trống.'
                            % ('Hình thức' if key == 'workForm' else 'Loại vị trí', raw))

    for key, field in DATE_FIELDS.items():
        raw = cell(key)
        if raw in (None, ''):
            continue
        parsed = to_date(raw)
        if parsed:
            vals[field] = parsed
        else:
            warnings.append('Không đọc được ngày "%s" — để trống.' % _text(raw))

    for key, field in TEXT_FIELDS.items():
        raw = _text(cell(key))
        if raw:
            vals[field] = raw

    raw_email = _text(cell('email'))
    if raw_email:
        if EMAIL_RE.match(raw_email):
            vals['work_email'] = raw_email
        else:
            warnings.append('Email "%s" sai định dạng — để trống.' % raw_email)

    raw_cccd = cell('cccd')
    if _text(raw_cccd):
        cccd = clean_cccd(raw_cccd)
        if cccd:
            vals['cccd'] = cccd
        else:
            warnings.append('CCCD "%s" không đủ 12 chữ số — để trống.'
                            % _text(raw_cccd))

    missing = []
    if vals.get('x_employment_status') == 'official':
        if not vals.get('cccd'):
            missing.append('CCCD')
        if not vals.get('x_pit_code'):
            missing.append('MST TNCN')
        if not vals.get('x_social_insurance_no'):
            missing.append('Số sổ BHXH')

    return {
        'excelRow': excel_row,
        'name': name,
        'code': vals.get('x_employee_code') or '',
        'depName': raw_dep,
        'jobName': raw_job,
        'status': vals.get('x_employment_status') or '',
        'warnings': warnings,
        'missingOfficial': missing,
        'values': vals,
    }, None


def parse_employees_xlsx(content, sheet=None, catalogs=None, existing=None):
    """Đọc + KIỂM file, KHÔNG ghi gì. Trả bảng xem trước cho SPA."""
    if len(content) > MAX_XLSX_BYTES:
        raise EmployeeImportError(
            'too_large', 'File nặng quá %d MB.' % (MAX_XLSX_BYTES // (1024 * 1024)))
    try:
        wb = openpyxl.load_workbook(io.BytesIO(content), read_only=True, data_only=True)
    except Exception:
        raise EmployeeImportError(
            'bad_file', 'Không mở được file. Hãy mở bằng Excel rồi "Lưu dưới '
                        'dạng" .xlsx và tải lên lại.')

    catalogs = catalogs or {}
    existing = existing or {}
    codes = set(existing.get('codes') or ())
    cccds = set(existing.get('cccds') or ())

    ws = wb[sheet] if sheet and sheet in wb.sheetnames else wb.worksheets[0]
    header_row, colmap, unknown = locate_header(ws)

    rows, errors, skipped = [], [], []
    for offset, cells in enumerate(
            ws.iter_rows(min_row=header_row + 1, values_only=True)):
        if not any(_text(c) for c in cells):
            continue
        excel_row = header_row + 1 + offset
        row, error = _parse_row(cells, colmap, excel_row, catalogs)
        if error:
            errors.append(error)
            continue
        code, cccd = row['values'].get('x_employee_code'), row['values'].get('cccd')
        if code and code in codes:
            skipped.append({'excelRow': excel_row, 'code': code,
                            'name': row['name'], 'reason': 'code_exists'})
            continue
        if cccd and cccd in cccds:
            skipped.append({'excelRow': excel_row, 'code': code or '',
                            'name': row['name'], 'reason': 'cccd_exists'})
            continue
        if code:
            codes.add(code)
        if cccd:
            cccds.add(cccd)
        rows.append(row)

    return {
        'sheets': list(wb.sheetnames),
        'sheet': ws.title,
        'headerRow': header_row,
        'rows': rows,
        'skipped': skipped,
        'errors': errors,
        'unknownCols': unknown,
        'summary': {
            'total': len(rows) + len(skipped) + len(errors),
            'ok': len(rows),
            'skipped': len(skipped),
            'error': len(errors),
            'needCompletion': sum(1 for r in rows if r['missingOfficial']),
        },
    }
```

- [ ] **Step 4: Chạy test cho chắc là XANH**

Lệnh như Task 1 Step 2. Kỳ vọng: `0 failed, 0 error(s)`, cả `TestEmployeeXlsxHeader` lẫn `TestEmployeeXlsxParse` xanh.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/employee_xlsx.py custom-addons/hocba_hrm/tests/test_employee_import.py
git commit -m "feat(emp-import): chuan hoa gia tri va dung bang xem truoc"
```

---

### Task 3: Cửa thoát BR-010 cho luồng import

**Files:**
- Modify: `custom-addons/hocba_employees/models/hr_employee.py:471-479`
- Modify: `custom-addons/hocba_hrm/tests/test_employee_import.py`

**Interfaces:**
- Consumes: không có.
- Produces: context key `hocba_legacy_import=True` bỏ qua `_check_official_required_fields`. Không có API mới.

- [ ] **Step 1: Viết test đỏ**

Thêm vào `custom-addons/hocba_hrm/tests/test_employee_import.py`:

```python
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestLegacyImportEscapeHatch(TransactionCase):
    """BR-010 phải MỞ cho luồng import và ĐÓNG cho mọi luồng khác."""

    VALS = {'name': 'NV Cũ', 'x_employment_status': 'official'}

    def test_official_without_pit_still_blocked_normally(self):
        with self.assertRaises(ValidationError):
            self.env['hr.employee'].create(dict(self.VALS))

    def test_official_without_pit_allowed_under_import_context(self):
        emp = self.env['hr.employee'].with_context(
            hocba_legacy_import=True).create(dict(self.VALS))
        self.assertEqual(emp.x_employment_status, 'official')
        self.assertEqual(
            set(emp._hocba_missing_official_fields()),
            {'CCCD', 'MST TNCN', 'Số sổ BHXH'})

    def test_editing_imported_record_later_is_still_blocked(self):
        emp = self.env['hr.employee'].with_context(
            hocba_legacy_import=True).create(dict(self.VALS))
        with self.assertRaises(ValidationError):
            emp.write({'work_phone': '0900000000',
                       'x_employment_status': 'official'})
```

- [ ] **Step 2: Chạy test cho chắc là ĐỎ**

Lệnh như Task 1 Step 2 nhưng thêm module employees:

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker compose -f docker-compose.yml -f docker-compose.local.yml run --rm odoo odoo -d hocba_hrm -u hocba_hrm,hocba_employees --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_hrm --stop-after-init --log-level=test
```

Kỳ vọng: `test_official_without_pit_allowed_under_import_context` FAIL với `ValidationError: Nhân viên chính thức cần khai: CCCD, MST TNCN, Số sổ BHXH (BR-010).`

- [ ] **Step 3: Viết implementation tối thiểu**

Sửa `custom-addons/hocba_employees/models/hr_employee.py`, hàm `_check_official_required_fields`:

```python
    @api.constrains('x_employment_status', 'x_pit_code', 'x_social_insurance_no')
    def _check_official_required_fields(self):
        # Di cư dữ liệu cũ: file nhân sự của trung tâm không có MST/BHXH, nên
        # luồng nhập Excel được miễn BR-010 (spec 2026-08-20-employee-excel-import).
        # Hồ sơ nhập vào thiếu mục nào thì lần SỬA sau vẫn bị chặn ở đây —
        # đó là chủ đích: ép hoàn thiện dần chứ không bỏ luật.
        if self.env.context.get('hocba_legacy_import'):
            return
        # BR-010 (mở rộng họp #2): chính thức bắt buộc CCCD + MST + BHXH
        for emp in self.sudo():
            if emp.x_employment_status == 'official':
                missing = emp._hocba_missing_official_fields()
                if missing:
                    raise ValidationError(_(
                        'Nhân viên chính thức cần khai: %s (BR-010).') % ', '.join(missing))
```

- [ ] **Step 4: Chạy test cho chắc là XANH**

Lệnh như Step 2. Kỳ vọng: 3 test của `TestLegacyImportEscapeHatch` xanh, các test BR-010 sẵn có trong `hocba_employees` **không đỏ thêm cái nào**.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_employees/models/hr_employee.py custom-addons/hocba_hrm/tests/test_employee_import.py
git commit -m "feat(employees): mien BR-010 cho luong nhap du lieu cu"
```

---

### Task 4: Route preview + quyền

**Files:**
- Create: `custom-addons/hocba_hrm/controllers/employee_import.py`
- Modify: `custom-addons/hocba_hrm/controllers/__init__.py`
- Modify: `custom-addons/hocba_hrm/controllers/main.py` (thêm `_cap_import_emp`, thêm `canImport` vào payload `/api/employees`)
- Modify: `custom-addons/hocba_hrm/tests/test_employee_import.py`

**Interfaces:**
- Consumes: `parse_employees_xlsx`, `EmployeeImportError`, `MAX_XLSX_BYTES`, `norm_header` (Task 1-2).
- Produces:
  - `_cap_import_emp(env) -> bool` (trong `main.py`)
  - class `HocBaEmployeeImport` với `_catalogs()`, `_existing()`, `api_employee_import_preview()`
  - Route `POST /hocba-hrm/api/employees/import/preview`

- [ ] **Step 1: Viết test đỏ**

Thêm vào `custom-addons/hocba_hrm/tests/test_employee_import.py`:

```python
from odoo import http
from odoo.addons.hocba_hrm.controllers.employee_import import HocBaEmployeeImport
from odoo.addons.hocba_hrm.controllers.main import _cap_import_emp


class _FakeUpload:
    """Stand-in cho werkzeug FileStorage: đủ .filename và .read()."""

    def __init__(self, content, filename='ns.xlsx'):
        self._content = content
        self.filename = filename

    def read(self):
        return self._content


class _FakeRequest:
    def __init__(self, env):
        self.env = env


@tagged('post_install', '-at_install')
class TestEmployeeImportPermission(TransactionCase):

    def _user(self, login, groups):
        return self.env['res.users'].create({
            'name': login, 'login': login,
            'group_ids': [(6, 0, [self.env.ref(g).id for g in groups])]})

    def test_hr_manager_can_import(self):
        u = self._user('imp_mgr@test.vn', ['hr.group_hr_manager'])
        self.assertTrue(_cap_import_emp(self.env(user=u)))

    def test_admin_can_import(self):
        u = self._user('imp_admin@test.vn', ['base.group_system'])
        self.assertTrue(_cap_import_emp(self.env(user=u)))

    def test_hr_officer_cannot_import(self):
        u = self._user('imp_hr@test.vn', ['hr.group_hr_user'])
        self.assertFalse(_cap_import_emp(self.env(user=u)))

    def test_giaovu_cannot_import(self):
        u = self._user('imp_gv@test.vn', ['hocba_employees.group_hocba_giaovu'])
        self.assertFalse(_cap_import_emp(self.env(user=u)))


@tagged('post_install', '-at_install')
class TestEmployeeImportPreview(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaEmployeeImport()
        http._request_stack.push(_FakeRequest(self.env))
        self.addCleanup(http._request_stack.pop)
        self.dep = self.env['hr.department'].create({'name': 'Phòng Test Import'})

    def test_catalogs_use_normalized_names(self):
        cat = self.ctrl._catalogs()
        self.assertEqual(cat['departments'].get('phong test import'), self.dep.id)

    def test_existing_collects_codes_and_cccds(self):
        emp = self.env['hr.employee'].create({'name': 'Đã có', 'x_employee_code': 'HB.XX'})
        emp.version_id.identification_id = '012345678901'
        found = self.ctrl._existing()
        self.assertIn('HB.XX', found['codes'])
        self.assertIn('012345678901', found['cccds'])

    def test_preview_creates_nothing(self):
        content = _book([FULL_HDR, _row(dep='Phòng Test Import')])
        before = self.env['hr.employee'].search_count([])
        res = self.ctrl._preview_payload(_FakeUpload(content), None)
        self.assertEqual(res['summary']['ok'], 1)
        self.assertEqual(self.env['hr.employee'].search_count([]), before)

    def test_preview_rejects_non_xlsx(self):
        with self.assertRaises(EmployeeImportError) as cm:
            self.ctrl._preview_payload(_FakeUpload(b'x', filename='ns.csv'), None)
        self.assertEqual(cm.exception.code, 'bad_ext')

    def test_preview_rejects_missing_file(self):
        with self.assertRaises(EmployeeImportError) as cm:
            self.ctrl._preview_payload(None, None)
        self.assertEqual(cm.exception.code, 'no_file')
```

- [ ] **Step 2: Chạy test cho chắc là ĐỎ**

Lệnh như Task 3 Step 2. Kỳ vọng: FAIL với `ModuleNotFoundError: ... employee_import` và `ImportError: cannot import name '_cap_import_emp'`.

- [ ] **Step 3: Viết implementation tối thiểu**

Thêm vào `custom-addons/hocba_hrm/controllers/main.py`, ngay dưới `_cap_manage_account` (khoảng dòng 1591):

```python
def _cap_import_emp(env):
    """Nhập hồ sơ hàng loạt từ Excel: chỉ Admin | HR-Mgr.

    Chặt hơn _cap_edit_emp có chủ đích — Trưởng phòng/Giáo vụ có phạm vi hẹp,
    nhập cả file sẽ đẻ hồ sơ ngoài phạm vi rồi bị _emp_in_scope chặn giữa chừng.
    """
    user = env.user
    return (user.has_group('base.group_system')
            or user.has_group('hr.group_hr_manager'))
```

Trong `api_employees` (payload danh sách, khoảng dòng 3056), thêm một khoá:

```python
            'canManageAccount': _cap_manage_account(request.env),
            'canImport': _cap_import_emp(request.env),
```

Tạo `custom-addons/hocba_hrm/controllers/employee_import.py`:

```python
# ============================================================
# Nhập hồ sơ nhân viên từ Excel — 2 route REST.
# Owner: Việt. Spec: docs/superpowers/specs/2026-08-20-employee-excel-import-design.md
#
# preview: đọc-kiểm, KHÔNG ghi gì.  commit: ghi trong MỘT transaction.
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
        """Mã NV + CCCD đã có, để bỏ qua dòng trùng (gồm cả hồ sơ đã lưu trữ)."""
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
```

Sửa `custom-addons/hocba_hrm/controllers/__init__.py`:

```python
from . import main
from . import employee_import
```

- [ ] **Step 4: Chạy test cho chắc là XANH**

Lệnh như Task 3 Step 2. Kỳ vọng: `TestEmployeeImportPermission` (4 test) + `TestEmployeeImportPreview` (5 test) xanh.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/employee_import.py custom-addons/hocba_hrm/controllers/__init__.py custom-addons/hocba_hrm/controllers/main.py custom-addons/hocba_hrm/tests/test_employee_import.py
git commit -m "feat(emp-import): route xem truoc + quyen HR Manager/Admin"
```

---

### Task 5: Route commit — ghi hồ sơ

**Files:**
- Modify: `custom-addons/hocba_hrm/controllers/employee_import.py`
- Modify: `custom-addons/hocba_hrm/tests/test_employee_import.py`

**Interfaces:**
- Consumes: `_catalogs()`, `_existing()` (Task 4); context `hocba_legacy_import` (Task 3).
- Produces:
  - `HocBaEmployeeImport._commit_rows(rows) -> dict` với khoá `created`, `needCompletion`, `employeeIds`
  - Route `POST /hocba-hrm/api/employees/import/commit`

- [ ] **Step 1: Viết test đỏ**

Thêm vào `custom-addons/hocba_hrm/tests/test_employee_import.py`:

```python
@tagged('post_install', '-at_install')
class TestEmployeeImportCommit(TransactionCase):

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaEmployeeImport()
        http._request_stack.push(_FakeRequest(self.env))
        self.addCleanup(http._request_stack.pop)
        self.dep = self.env['hr.department'].create({'name': 'Phòng Test Import'})

    def _preview(self, data_rows):
        return self.ctrl._preview_payload(
            _FakeUpload(_book([FULL_HDR] + data_rows)), None)

    def test_commit_creates_employees_with_cccd_on_version(self):
        prev = self._preview([_row(code='HB.C1', dep='Phòng Test Import')])
        res = self.ctrl._commit_rows(prev['rows'])
        self.assertEqual(res['created'], 1)
        emp = self.env['hr.employee'].browse(res['employeeIds'][0])
        self.assertEqual(emp.x_employee_code, 'HB.C1')
        self.assertEqual(emp.department_id, self.dep)
        self.assertEqual(emp.version_id.identification_id, '038098029187')

    def test_commit_allows_official_missing_pit(self):
        prev = self._preview([_row(code='HB.C2', dep='Phòng Test Import')])
        res = self.ctrl._commit_rows(prev['rows'])
        emp = self.env['hr.employee'].browse(res['employeeIds'][0])
        self.assertEqual(emp.x_employment_status, 'official')
        self.assertEqual(res['needCompletion'], 1)

    def test_commit_skips_row_whose_code_now_exists(self):
        self.env['hr.employee'].create({'name': 'Có rồi', 'x_employee_code': 'HB.C3'})
        prev = self._preview([_row(code='HB.C3', dep='Phòng Test Import')])
        # preview đã lọc, nhưng commit phải tự kiểm lại — giả lập client gửi bừa.
        rows = [{'excelRow': 2, 'name': 'Nguyễn Văn A',
                 'values': {'name': 'Nguyễn Văn A', 'x_employee_code': 'HB.C3'},
                 'missingOfficial': []}]
        with self.assertRaises(EmployeeImportError) as cm:
            self.ctrl._commit_rows(rows)
        self.assertEqual(cm.exception.code, 'code_exists')

    def test_commit_rejects_field_outside_whitelist(self):
        rows = [{'excelRow': 2, 'name': 'X',
                 'values': {'name': 'X', 'wage': 99999999},
                 'missingOfficial': []}]
        res = self.ctrl._commit_rows(rows)
        emp = self.env['hr.employee'].browse(res['employeeIds'][0])
        self.assertNotEqual(emp.version_id.wage, 99999999)

    def test_commit_rejects_empty_name(self):
        rows = [{'excelRow': 5, 'name': '', 'values': {'name': '  '},
                 'missingOfficial': []}]
        with self.assertRaises(EmployeeImportError) as cm:
            self.ctrl._commit_rows(rows)
        self.assertEqual(cm.exception.code, 'empty_name')

    def test_probation_row_gets_no_onboarding_steps(self):
        prev = self._preview([_row(code='HB.C4', status='Thử việc',
                                   dep='Phòng Test Import', prob='01/06/2024')])
        res = self.ctrl._commit_rows(prev['rows'])
        emp = self.env['hr.employee'].browse(res['employeeIds'][0])
        self.assertEqual(emp.x_employment_status, 'probation')
        self.assertFalse(emp.x_onboarding_step_ids)

    def test_commit_is_all_or_nothing(self):
        good = {'excelRow': 2, 'name': 'Tốt',
                'values': {'name': 'Tốt', 'x_employee_code': 'HB.C5'},
                'missingOfficial': []}
        bad = {'excelRow': 3, 'name': '', 'values': {'name': ''},
               'missingOfficial': []}
        before = self.env['hr.employee'].search_count([])
        with self.assertRaises(EmployeeImportError):
            self.ctrl._commit_rows([good, bad])
        self.assertEqual(self.env['hr.employee'].search_count([]), before)
```

- [ ] **Step 2: Chạy test cho chắc là ĐỎ**

Lệnh như Task 3 Step 2. Kỳ vọng: FAIL với `AttributeError: 'HocBaEmployeeImport' object has no attribute '_commit_rows'`.

- [ ] **Step 3: Viết implementation tối thiểu**

Thêm vào `custom-addons/hocba_hrm/controllers/employee_import.py`:

```python
import json

from odoo.exceptions import AccessError, UserError, ValidationError
from psycopg2 import IntegrityError

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
```

và 2 phương thức trong class `HocBaEmployeeImport`:

```python
    def _commit_rows(self, rows):
        """Ghi các dòng đã duyệt. Trọn gói: lỗi bất kỳ → raise, caller rollback.

        Kiểm LẠI toàn bộ ở đây — payload đi qua trình duyệt nên không tin được.
        """
        existing = self._existing()
        codes, cccds = existing['codes'], existing['cccds']
        Emp = request.env['hr.employee'].sudo().with_context(
            hocba_legacy_import=True, hocba_no_onb_assign=True)

        created, need_completion = [], 0
        for row in rows or []:
            excel_row = row.get('excelRow') or 0
            vals = {k: v for k, v in (row.get('values') or {}).items()
                    if k in IMPORT_EMP_FIELDS}
            cccd = (row.get('values') or {}).get('cccd') or ''
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
                        hocba_legacy_import=True).write({'identification_id': cccd})
            except IntegrityError as ex:
                raise EmployeeImportError(
                    'rejected', 'Dòng %d: %s' % (excel_row, ex))
            except (AccessError, ValidationError, UserError) as ex:
                raise EmployeeImportError('rejected', 'Dòng %d: %s' % (excel_row, ex))
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
        """Ghi các dòng SPA gửi lại từ bảng xem trước. Lỗi → rollback cả mẻ."""
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
        self._notify_done(res)
        return request.make_json_response(res)

    def _notify_done(self, res):
        """MỘT thông báo tổng kết cho người import — không bắn theo từng hồ sơ."""
        if 'hb.notification' not in request.env:
            return
        body = 'Đã nhập %d hồ sơ nhân viên.' % res['created']
        if res['needCompletion']:
            body += (' %d hồ sơ thiếu MST/BHXH — cần hoàn thiện trước khi sửa '
                     'lại hồ sơ.' % res['needCompletion'])
        request.env['hb.notification'].sudo().create({
            'user_id': request.env.user.id,
            'title': 'Nhập hồ sơ nhân viên từ Excel',
            'body': body,
            'kind': 'info',
            'target_view': 'employees',
        })
```

**Lưu ý cho người thực hiện:** kiểm tên field thật của `hb.notification` trước khi
viết `_notify_done` — mở `custom-addons/hocba_notify/models/hb_notification.py` và
dùng đúng tên (`user_id`/`title`/`body`/`kind`/`target_view` là tên dự kiến). Nếu
lệch thì sửa cho khớp model, đừng sửa model.

- [ ] **Step 4: Chạy test cho chắc là XANH**

Lệnh như Task 3 Step 2. Kỳ vọng: 7 test của `TestEmployeeImportCommit` xanh, tổng cả file `0 failed, 0 error(s)`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_hrm/controllers/employee_import.py custom-addons/hocba_hrm/tests/test_employee_import.py
git commit -m "feat(emp-import): route ghi ho so, tron goi va bo qua dong trung"
```

---

### Task 6: SPA — nút và modal 2 bước

**Files:**
- Modify: `frontend/src/api/employees.js`
- Create: `frontend/src/features/employees/ImportEmployeesModal.jsx`
- Modify: `frontend/src/features/employees/Employees.jsx:141-143`

**Interfaces:**
- Consumes: 2 route của Task 4-5; khoá `canImport` trong payload `/api/employees`.
- Produces: component `<ImportEmployeesModal onClose={fn} onDone={fn} />`.

- [ ] **Step 1: Thêm 2 hàm gọi API**

Thêm vào `frontend/src/api/employees.js` (sửa dòng import đầu file cho đủ):

```javascript
import { hbGet, hbPost, hbUploadFields } from './client';

/* Nhập hồ sơ từ Excel (chỉ HR Manager/Admin). preview KHÔNG ghi gì; commit mới ghi. */
export const previewEmployeeImport = (file, sheet) =>
  hbUploadFields('/hocba-hrm/api/employees/import/preview', file,
    sheet ? { sheet } : {});
export const commitEmployeeImport = (rows) =>
  hbPost('/hocba-hrm/api/employees/import/commit', { rows });
```

- [ ] **Step 2: Viết modal**

Tạo `frontend/src/features/employees/ImportEmployeesModal.jsx`:

```jsx
/* Nhập hồ sơ nhân viên từ Excel — modal 2 bước.
   Bước 1 chọn file → gọi preview (backend KHÔNG ghi gì).
   Bước 2 xem trước → bấm Nhập mới gọi commit.
   Spec: docs/superpowers/specs/2026-08-20-employee-excel-import-design.md */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { previewEmployeeImport, commitEmployeeImport } from '../../api/employees';

const REASON_TXT = {
  code_exists: 'Mã nhân sự đã có trong hệ thống',
  cccd_exists: 'CCCD đã có trong hệ thống',
};

export default function ImportEmployeesModal({ onClose, onDone }) {
  const [file, setFile] = useState(null);
  const [prev, setPrev] = useState(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  async function doPreview(f, sheet) {
    setBusy(true); setErr(null);
    try {
      setPrev(await previewEmployeeImport(f, sheet));
    } catch (e) {
      setErr(e.message || 'Không đọc được file.');
      setPrev(null);
    } finally { setBusy(false); }
  }

  async function doCommit() {
    setBusy(true); setErr(null);
    try {
      const res = await commitEmployeeImport(prev.rows);
      onDone(res);
    } catch (e) {
      setErr(e.message || 'Không nhập được.');
    } finally { setBusy(false); }
  }

  const s = prev?.summary;
  return (
    <Modal title="Nhập hồ sơ nhân viên từ Excel" onClose={onClose} wide>
      {!prev && (
        <div className="form-row">
          <label className="lbl">Chọn file .xlsx (tối đa 10MB)</label>
          <input type="file" accept=".xlsx" disabled={busy}
            onChange={(e) => {
              const f = e.target.files?.[0];
              setFile(f);
              if (f) doPreview(f, null);
            }} />
          <p className="faint">Hệ thống tự dò cột theo tên tiêu đề — không cần
            sửa file về mẫu riêng.</p>
        </div>
      )}

      {err && <div className="alert alert-error">{err}</div>}
      {busy && <p className="faint">Đang xử lý…</p>}

      {prev && (
        <>
          {prev.sheets?.length > 1 && (
            <div className="form-row">
              <label className="lbl">Sheet</label>
              <select className="sel" value={prev.sheet} disabled={busy}
                onChange={(e) => doPreview(file, e.target.value)}>
                {prev.sheets.map((n) => <option key={n}>{n}</option>)}
              </select>
            </div>
          )}

          <p>
            <b>{s.ok}</b> hồ sơ sẽ nhập · <b>{s.skipped}</b> bỏ qua vì đã có ·{' '}
            <b>{s.error}</b> lỗi phải sửa
            {s.needCompletion > 0 &&
              ` · ${s.needCompletion} hồ sơ thiếu MST/BHXH, cần hoàn thiện sau`}
          </p>

          {prev.errors.length > 0 && (
            <div className="alert alert-warn">
              <b>Dòng phải sửa trong file:</b>
              <ul>{prev.errors.slice(0, 15).map((e) => (
                <li key={e.excelRow}>{e.message}</li>))}</ul>
              {prev.errors.length > 15 && <p>… và {prev.errors.length - 15} dòng nữa.</p>}
            </div>
          )}

          <div className="tbl-wrap" style={{ maxHeight: 320 }}>
            <table className="tbl">
              <thead><tr>
                <th>Dòng</th><th>Họ và tên</th><th>Mã NV</th><th>Phòng ban</th>
                <th>Chức danh</th><th>Cảnh báo</th>
              </tr></thead>
              <tbody>
                {prev.rows.map((r) => (
                  <tr key={r.excelRow}>
                    <td>{r.excelRow}</td><td>{r.name}</td><td>{r.code}</td>
                    <td>{r.depName}</td><td>{r.jobName}</td>
                    <td className="faint">{r.warnings.join(' ')}</td>
                  </tr>
                ))}
                {prev.skipped.map((r) => (
                  <tr key={`s${r.excelRow}`} className="faint">
                    <td>{r.excelRow}</td><td>{r.name}</td><td>{r.code}</td>
                    <td colSpan={3}>Bỏ qua — {REASON_TXT[r.reason] || r.reason}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {prev.unknownCols?.length > 0 && (
            <p className="faint">Cột không nhận diện được (bỏ qua):{' '}
              {prev.unknownCols.join(', ')}</p>
          )}

          <div className="modal-actions">
            <button className="btn" onClick={onClose} disabled={busy}>Huỷ</button>
            <button className="btn btn-primary" onClick={doCommit}
              disabled={busy || !s.ok}>
              <Icon name="plus" size={16} />Nhập {s.ok} hồ sơ
            </button>
          </div>
        </>
      )}
    </Modal>
  );
}
```

**Lưu ý cho người thực hiện:** mở `frontend/src/components/Modal.jsx` kiểm prop thật
(`title`/`onClose`/`wide`) và class CSS đang dùng ở các modal khác (`alert-warn`,
`modal-actions`); dùng đúng khuôn có sẵn thay vì tự đặt tên class mới.

- [ ] **Step 3: Gắn nút vào màn Nhân viên**

Trong `frontend/src/features/employees/Employees.jsx`, thêm import + state:

```jsx
import ImportEmployeesModal from './ImportEmployeesModal';
```

```jsx
  const [importing, setImporting] = useState(false);
```

Sửa khối nút (dòng ~141):

```jsx
          {data.canImport && (
            <button className="btn" onClick={() => setImporting(true)}>
              <Icon name="upload" size={16} />Nhập từ Excel</button>
          )}
          {data.canEditEmp && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Thêm nhân viên</button>
          )}
```

Và render modal cạnh `EmployeeForm` (cuối component):

```jsx
      {importing && (
        <ImportEmployeesModal
          onClose={() => setImporting(false)}
          onDone={() => { setImporting(false); load(); }} />
      )}
```

**Lưu ý:** kiểm tên hàm nạp lại danh sách trong `Employees.jsx` (chỗ `useEffect` gọi
`fetchEmployees`) và dùng đúng tên đó thay cho `load()`. Kiểm `Icon` có tên
`upload` chưa — chưa có thì dùng tên đã tồn tại trong `components/Icon.jsx`.

- [ ] **Step 4: Build SPA và kiểm bằng preview**

```bash
cd frontend && npm run build
```

Rồi `docker restart hocba_onl-odoo-1`, mở `http://localhost:5173/hocba_hrm/static/spa/`,
đăng nhập bằng tài khoản HR Manager, vào màn Nhân viên: nút "Nhập từ Excel" phải hiện.
Tải file `C:\Users\ADMIN\Downloads\Học bá  education.xlsx` (chọn sheet
"2.1. Quản lý nhân sự") và đối chiếu với số liệu khảo sát trong spec §1.1: phải thấy
~52 dòng lỗi `bad_status` ("Online") và 3 dòng `bad_department` ("Phòng Nhân sự").
Bấm Huỷ — kiểm `hr.employee` không tăng thêm bản ghi nào.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/employees.js frontend/src/features/employees/ImportEmployeesModal.jsx frontend/src/features/employees/Employees.jsx custom-addons/hocba_hrm/static/spa
git commit -m "feat(emp-import): nut Nhap tu Excel va modal xem truoc tren man Nhan vien"
```

---

## Self-Review

**Spec coverage:**

| Mục spec | Task |
|---|---|
| §4 luồng 2 bước | 6 |
| §5 kiến trúc file | 1, 2, 4, 5, 6 |
| §6.1 route preview + quyền | 4 |
| §6.2 route commit, rollback, 1 thông báo | 5 |
| §6.3 mã lỗi | 1 (`no_header`, `no_name_col`), 2 (`empty_name`, `bad_status`, `bad_department`, `code_exists`, `cccd_exists`, `too_large`), 4 (`no_file`, `bad_ext`) |
| §7.1 dò header | 1 |
| §7.2 bảng bí danh 22 cột | 1 |
| §7.3 chuẩn hoá giá trị | 2 |
| §8 cửa thoát BR-010 | 3 |
| §9 test 1-18 | 1 (t1-4, 10), 2 (t5-9), 3 (t15, 16), 4 (t11, 12), 5 (t13, 14, 17, 18) |
| §10 ngoài phạm vi | không có task nào chạm tới (`wage` bị loại khỏi `IMPORT_EMP_FIELDS`) |

**Type consistency:** `parse_employees_xlsx` trả khoá `rows/skipped/errors/unknownCols/summary` — dùng nguyên tên đó ở Task 4 (`_preview_payload`), Task 5 (`_commit_rows(prev['rows'])`) và Task 6 (`prev.rows`, `prev.summary.ok`). `values` luôn là dict tên field `hr.employee` + khoá `cccd` riêng, được `IMPORT_EMP_FIELDS` lọc ở Task 5. `_cap_import_emp` khai ở `main.py` (Task 4), import vào `employee_import.py` cùng task.

**Điểm còn treo (đã ghi trong spec §7.3, không chặn thi công):** `Phòng Nhân sự` chưa có ánh xạ — 3 dòng sẽ báo `bad_department` cho tới khi hỏi được Học Bá.
