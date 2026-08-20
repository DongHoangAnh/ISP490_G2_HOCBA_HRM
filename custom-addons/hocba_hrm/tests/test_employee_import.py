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
