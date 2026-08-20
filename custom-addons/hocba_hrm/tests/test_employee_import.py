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
        ws = _sheet([['Họ và tên', 'Email cá nhân', 'Số điện thoại']])
        _row, colmap, _u = locate_header(ws)
        self.assertEqual(colmap['email'], 1)

    def test_every_alias_maps_to_known_key(self):
        keys = {'code', 'name', 'status', 'workForm', 'posType', 'dep', 'job',
                'probStart', 'bday', 'cccd', 'idIssue', 'idPlace', 'phone',
                'email', 'emailAlt', 'bankAccountNo', 'bankCode', 'pit', 'si',
                'hi', 'hiPlace', 'permStreet', 'currStreet'}
        self.assertEqual(set(HEADER_ALIASES.values()) - keys, set())


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


# Khoá dựng y hệt cách controller làm (_catalogs dùng norm_header trên tên
# thật) — đặt khoá thô ở đây là fixture nói dối, che mất lỗi ánh xạ bí danh.
CATALOGS = {
    'departments': {norm_header('Marketing'): 11,
                    norm_header('Sản phẩm (R&D_SP)'): 12,
                    norm_header('Kế toán_HCNS'): 13},
    'jobs': {norm_header('Nhân viên R&D'): 21},
}


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
        self.assertEqual(res['errors'], [])
        self.assertEqual(res['rows'][0]['values']['department_id'], 12)

    def test_department_alias_ke_toan(self):
        res = self._parse([_row(dep='Kế Toán')])
        self.assertEqual(res['rows'][0]['values']['department_id'], 13)

    def test_department_matched_case_insensitively(self):
        res = self._parse([_row(dep='kinh doanh')])
        self.assertEqual(res['errors'][0]['code'], 'bad_department')
        res = self._parse([_row(dep='MARKETING')])
        self.assertEqual(res['rows'][0]['values']['department_id'], 11)

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
