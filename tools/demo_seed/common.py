# -*- coding: utf-8 -*-
"""Hằng số + tiện ích dùng chung cho bộ script seed dữ liệu demo.

Chạy trong `odoo shell` (biến `env` có sẵn), KHÔNG import được từ ngoài:
    exec(open('/tmp/demo_seed/common.py').read())
"""
import datetime
import random

random.seed(490)                      # seed cố định → chạy lại ra cùng dữ liệu

TODAY = datetime.date(2026, 8, 16)    # mốc "hôm nay" của bản demo
YEAR = TODAY.year

DEPTS = ['BOD', 'Kế toán_HCNS', 'Kinh doanh', 'Marketing',
         'Sản phẩm (R&D_SP)', 'Vận hành']

PWD = 'Hocba@2026'


def D(y, m, d):
    return datetime.date(y, m, d)


def dt(d, h, m=0):
    """date + giờ local (GMT+7) → datetime UTC để lưu vào Odoo."""
    return datetime.datetime(d.year, d.month, d.day, h, m) - datetime.timedelta(hours=7)


def dept(name):
    return env['hr.department'].sudo().search([('name', '=', name)], limit=1)


def emp(code):
    return env['hr.employee'].sudo().with_context(active_test=False).search(
        [('x_employee_code', '=', code)], limit=1)


def job(name, dep=None):
    J = env['hr.job'].sudo()
    j = J.search([('name', '=', name)], limit=1)
    if not j:
        j = J.create({'name': name, 'department_id': dep and dep.id})
    return j


def workdays(d_from, d_to, saturday=False):
    """Các ngày làm việc trong khoảng (T2–T6, tuỳ chọn thêm T7)."""
    out, d = [], d_from
    while d <= d_to:
        if d.weekday() < 5 or (saturday and d.weekday() == 5):
            out.append(d)
        d += datetime.timedelta(days=1)
    return out


def say(*a):
    print('   ', *a)
