#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seed dữ liệu NGHỈ PHÉP cho DB demo Học Bá HRM (chạy TRONG container Odoo).

    docker compose -f docker-compose.yml -f docker-compose.local.yml \
        run --rm --no-deps -v "$PWD/tools:/tools" odoo python3 /tools/seed_demo_timeoff.py

Tuỳ chọn (env):
    SEED_DB    tên database (mặc định hocba_demo)
    SEED_WIPE  1 = xoá TOÀN BỘ hr.leave + hr.leave.allocation cũ rồi dựng lại
               (mặc định 1 — script idempotent, chạy bao nhiêu lần cũng ra
               cùng một bộ dữ liệu)

Sinh ra (mọi tab của màn Nghỉ phép đều có dữ liệu):
  · Cấp phép năm 2026 trên loại nghỉ Học Bá "Nghỉ Phép Năm" (chính thức 12
    ngày · thử việc 6 ngày · CTV không cấp)
  · ~60 đơn ĐÃ DUYỆT trong quá khứ (tháng 6 & nửa đầu tháng 8) → tab "Đơn đã
    duyệt", biểu đồ Tổng quan, và màn "Theo dõi nghỉ phép" (burnout)
  · Đơn CHỜ DUYỆT ngày tương lai (có đơn khẩn cấp, nửa ngày, đơn nghỉ bù)
  · Đơn QUÁ HẠN DUYỆT (ngày nghỉ đã qua mà còn chờ) đủ 3 nhóm đề xuất:
    "nên duyệt" · "nên từ chối" (đối chiếu chấm công thấy vẫn đi làm) ·
    "cần xem xét" → tab "Kiểm duyệt phát sinh"
  · Yêu cầu RÚT ĐƠN đang chờ + vài đơn BỊ TỪ CHỐI (KPI Tổng quan)

⚠️ Tháng 7/2026 đã có chấm công từng ngày (seed_demo_full). Vì vậy:
   - đơn ĐÃ DUYỆT chỉ đặt ở tháng 6 và tháng 8 (không có chấm công) để dữ
     liệu chấm công ↔ nghỉ phép không mâu thuẫn;
   - đơn QUÁ HẠN cố ý đặt ở tháng 7 để màn "Kiểm duyệt phát sinh" có nhóm
     "vẫn đi làm trong ngày xin nghỉ → đề xuất từ chối".
"""
import logging
import os
import random
import sys
from collections import defaultdict
from datetime import date, timedelta

import odoo
from odoo.api import Environment, SUPERUSER_ID
from odoo.modules.registry import Registry

_log = logging.getLogger('seed_timeoff')
logging.basicConfig(level=logging.INFO, format='%(message)s', stream=sys.stdout)

DB = os.environ.get('SEED_DB', 'hocba_demo')
WIPE = os.environ.get('SEED_WIPE', '1') == '1'

# Mốc thời gian: lấy theo ngày chạy thật để cửa sổ "3 tháng gần nhất" của màn
# Theo dõi nghỉ phép (SQL view: CURRENT_DATE - 90 days) luôn phủ dữ liệu seed.
TODAY = date.today()

# Nhãn ir.model.data để lần chạy sau nhận ra và dọn đúng dữ liệu của script này.
TAG_MODULE = 'seed_demo_timeoff'

random.seed(20260817)

# ══════════════════════════════════════════════════════════════════════════
# Loại nghỉ Học Bá (tra theo xml_id của module hocba_timeoff)
# ══════════════════════════════════════════════════════════════════════════
LEAVE_TYPE_XMLID = {
    'annual':    'hocba_timeoff.hb_leave_type_annual',       # Nghỉ Phép Năm (cần quỹ)
    'sick':      'hocba_timeoff.hb_leave_type_sick',         # Nghỉ Ốm (có chứng từ)
    'unpaid':    'hocba_timeoff.hb_leave_type_unpaid',       # Nghỉ Không Lương
    'personal':  'hocba_timeoff.hb_leave_type_personal',     # Nghỉ Việc Riêng
    'emergency': 'hocba_timeoff.hb_leave_type_emergency',    # Nghỉ Khẩn Cấp
    'comp':      'hocba_timeoff.hb_leave_type_compensatory',  # Nghỉ Bù
    'maternity': 'hocba_timeoff.hb_leave_type_maternity',    # Nghỉ Thai Sản
}

# Quỹ phép năm 2026 theo tình trạng lao động.
ALLOC_DAYS = {'official': 12.0, 'probation': 6.0}   # 'ctv' → không cấp

# ══════════════════════════════════════════════════════════════════════════
# Bộ dữ liệu — viết tay để mỗi tab có đúng "câu chuyện" cần demo.
# Mỗi dòng: (tên nhân viên, loại nghỉ, từ ngày, đến ngày, [ghi chú])
# ══════════════════════════════════════════════════════════════════════════

# ── A. ĐÃ DUYỆT — nhóm "nghỉ ốm thường xuyên" (≥3 lần/3 tháng) ────────────
#     → màn Theo dõi nghỉ phép, KPI "Nghỉ ốm thường xuyên"
APPROVED_SICK_FREQUENT = [
    ('Phùng Minh Anh',  'sick', date(2026, 6, 25), date(2026, 6, 25), 'Sốt virus'),
    ('Phùng Minh Anh',  'sick', date(2026, 8, 3),  date(2026, 8, 3),  'Đau dạ dày'),
    ('Phùng Minh Anh',  'sick', date(2026, 8, 7),  date(2026, 8, 7),  'Tái khám dạ dày'),
    ('Phùng Minh Anh',  'sick', date(2026, 8, 13), date(2026, 8, 13), 'Cảm cúm'),
    ('Lê Thị Dung',     'sick', date(2026, 6, 10), date(2026, 6, 10), 'Viêm họng'),
    ('Lê Thị Dung',     'sick', date(2026, 8, 5),  date(2026, 8, 5),  'Sốt cao'),
    ('Lê Thị Dung',     'sick', date(2026, 8, 11), date(2026, 8, 11), 'Đau đầu kéo dài'),
    ('Nguyễn Bình An',  'sick', date(2026, 6, 23), date(2026, 6, 23), 'Ngộ độc thực phẩm'),
    ('Nguyễn Bình An',  'sick', date(2026, 8, 6),  date(2026, 8, 6),  'Sốt siêu vi'),
    ('Nguyễn Bình An',  'sick', date(2026, 8, 14), date(2026, 8, 14), 'Đau lưng'),
    ('Nguyễn Thị Mai',  'sick', date(2026, 6, 24), date(2026, 6, 24), 'Viêm xoang'),
    ('Nguyễn Thị Mai',  'sick', date(2026, 8, 4),  date(2026, 8, 4),  'Cảm cúm'),
    ('Nguyễn Thị Mai',  'sick', date(2026, 8, 10), date(2026, 8, 10), 'Tái khám xoang'),
]

# ── B. ĐÃ DUYỆT — nhóm "vắng nhiều" (>10 ngày/3 tháng) ───────────────────
APPROVED_HIGH_ABSENCE = [
    ('Đinh Hoàng Mai Phương', 'annual',   date(2026, 6, 22), date(2026, 6, 26), 'Về quê'),
    ('Đinh Hoàng Mai Phương', 'unpaid',   date(2026, 8, 3),  date(2026, 8, 7),  'Việc gia đình'),
    ('Đinh Hoàng Mai Phương', 'personal', date(2026, 8, 10), date(2026, 8, 11), 'Thu xếp việc riêng'),
    ('Nguyễn Thị Thanh Thuý', 'annual',   date(2026, 6, 8),  date(2026, 6, 12), 'Nghỉ mát cùng gia đình'),
    ('Nguyễn Thị Thanh Thuý', 'annual',   date(2026, 6, 15), date(2026, 6, 17), 'Nghỉ mát (đợt 2)'),
    ('Nguyễn Thị Thanh Thuý', 'unpaid',   date(2026, 8, 10), date(2026, 8, 12), 'Chăm người nhà ốm'),
    ('Lô Đức Thịnh',          'annual',   date(2026, 6, 15), date(2026, 6, 19), 'Du lịch Đà Nẵng'),
    ('Lô Đức Thịnh',          'unpaid',   date(2026, 8, 3),  date(2026, 8, 6),  'Việc gia đình'),
    ('Lô Đức Thịnh',          'personal', date(2026, 8, 12), date(2026, 8, 13), 'Chuyển nhà'),
]

# ── C. ĐÃ DUYỆT — nhóm "sắp hết quỹ phép" (<2 ngày còn lại) ──────────────
#     NV thử việc chỉ được cấp 6 ngày → dùng 5 ngày là còn 1.
APPROVED_LOW_BALANCE = [
    ('Trần Khánh Linh', 'annual', date(2026, 8, 3),  date(2026, 8, 7),  'Nghỉ phép hè'),
    ('Võ Lê Duy Hoàng', 'annual', date(2026, 8, 10), date(2026, 8, 14), 'Về quê'),
    ('Đặng Vũ Thu Hà',  'annual', date(2026, 8, 4),  date(2026, 8, 7),  'Việc gia đình'),
    ('Đặng Vũ Thu Hà',  'personal', date(2026, 8, 12), date(2026, 8, 12), 'Khám sức khoẻ'),
]

# ── D. ĐÃ DUYỆT — dựng lại 6 đơn tháng 7 của seed gốc trên loại nghỉ Học Bá
#     (chấm công tháng 7 đã chừa sẵn đúng những ngày này).
APPROVED_JULY_LEGACY = [
    ('Bùi Thị Trang',      'annual', date(2026, 7, 6),  date(2026, 7, 6),  'Nghỉ phép cá nhân'),
    ('Cao Việt Khánh',     'annual', date(2026, 7, 9),  date(2026, 7, 9),  'Nghỉ phép cá nhân'),
    ('Hoàng Thị Ngọc Anh', 'annual', date(2026, 7, 13), date(2026, 7, 13), 'Nghỉ phép cá nhân'),
    ('Hán Vũ Tú Ngọc',     'annual', date(2026, 7, 15), date(2026, 7, 15), 'Nghỉ phép cá nhân'),
    ('Lê Thu Thảo',        'annual', date(2026, 7, 20), date(2026, 7, 20), 'Nghỉ phép cá nhân'),
    ('Lê Thị Dung',        'annual', date(2026, 7, 21), date(2026, 7, 21), 'Nghỉ phép cá nhân'),
]

# ── D2. ĐÃ DUYỆT — đang nghỉ NGAY HÔM NAY (KPI "Đang nghỉ hôm nay") ─────
#     (tên, loại, lệch ngày bắt đầu, lệch ngày kết thúc so với hôm nay, lý do)
APPROVED_ONGOING = [
    ('Lê Thị Thùy',           'annual',   -1, 1, 'Nghỉ phép năm'),
    ('Nguyễn Thị Phương Nga', 'personal',  0, 0, 'Việc gia đình'),
    ('Đỗ Thị Hải Ngọc',       'annual',    0, 2, 'Nghỉ phép năm'),
]

# ── E. CHỜ DUYỆT — ngày nghỉ ở TƯƠNG LAI (tab "Đơn chờ duyệt") ───────────
#     (tên, loại, từ, đến, lý do, nửa ngày?)
PENDING_FUTURE = [
    ('Phạm Thanh Hoa',        'emergency', 0,  0,  'Người nhà nhập viện gấp', False),
    ('Nguyễn Thị Thương',     'annual',    7,  9,  'Nghỉ phép cùng gia đình', False),
    ('Đỗ Thị Hải Ngọc',       'personal',  3,  3,  'Giải quyết việc riêng', False),
    ('Lô Đức Thịnh',          'annual',    1,  4,  'Nghỉ phép năm', False),
    ('Nguyễn Thị Mai',        'sick',      2,  2,  'Khám định kỳ theo lịch bác sĩ', False),
    ('Ngô Thị Minh Tuyết',    'annual',    14, 18, 'Nghỉ phép dài ngày cuối tháng', False),
    ('Nguyễn Bình An',        'personal',  8,  8,  'Đưa con đi nhập học (nửa ngày chiều)', True),
    ('Lê Thu Thảo',           'annual',    3,  4,  'Nghỉ phép năm', False),
    ('Nguyễn Thị Phương Nga', 'annual',    9,  11, 'Nghỉ phép năm', False),
    ('Trần Khánh Linh',       'unpaid',    10, 11, 'Việc gia đình (thử việc, xin không lương)', False),
    ('Nguyễn Minh Trung',     'unpaid',    7,  7,  'CTV xin nghỉ buổi làm', False),
    ('Bùi Thị Tú',            'unpaid',    4,  4,  'CTV bận lịch cá nhân', False),
    ('Trương Thị Trang',      'personal',  5,  5,  'Đám cưới người thân (nửa ngày sáng)', True),
]

# ── F. CHỜ DUYỆT — ĐƠN NGHỈ BÙ (ngày đã qua nhưng KHÔNG tính quá hạn) ────
PENDING_MAKEUP = [
    ('Nguyễn Thị Len',   'comp', date(2026, 8, 6),  date(2026, 8, 6),  'Nộp bù cho ngày đã nghỉ'),
    ('Phan Quỳnh Giang', 'comp', date(2026, 8, 11), date(2026, 8, 11), 'Nộp bù — quên nộp đơn'),
]

# ── G. CHỜ DUYỆT + QUÁ HẠN (tab "Kiểm duyệt phát sinh") ─────────────────
#     · tháng 7 → có chấm công trong ngày xin nghỉ ⇒ đề xuất "Từ chối"
#     · tháng 8 → không có chấm công             ⇒ đề xuất "Duyệt"
#     · vắt qua 31/7–đầu 8 → nửa có nửa không    ⇒ "Cần xem xét"
LAPSED = [
    ('Đỗ Thu Giang',      'sick',     date(2026, 7, 20), date(2026, 7, 21), 'Ốm, báo miệng chưa duyệt'),
    ('Vũ Hoàng Minh',     'annual',   date(2026, 7, 22), date(2026, 7, 23), 'Nghỉ phép năm'),
    ('Trương Thị Trang',  'personal', date(2026, 7, 27), date(2026, 7, 27), 'Việc riêng'),
    ('Nguyễn Trung Kiên', 'annual',   date(2026, 7, 30), date(2026, 8, 4),  'Nghỉ phép dài ngày'),
    ('Mai Hoài Tâm',      'unpaid',   date(2026, 7, 29), date(2026, 8, 3),  'Việc gia đình'),
    ('Đặng Thị Thu Hà',   'annual',   date(2026, 8, 5),  date(2026, 8, 7),  'Nghỉ phép năm'),
    ('Lê Thị Phương',     'sick',     date(2026, 8, 10), date(2026, 8, 11), 'Ốm dài ngày'),
    ('Ngô Thị Minh Tuyết', 'personal', date(2026, 8, 13), date(2026, 8, 13), 'Việc riêng'),
    ('Nguyễn Vũ Bình Dương', 'unpaid', date(2026, 8, 12), date(2026, 8, 12), 'CTV xin nghỉ'),
    ('Bùi Thị Trang',     'emergency', date(2026, 8, 14), date(2026, 8, 14), 'Sự cố gia đình'),
]

# ── H. ĐÃ DUYỆT + ĐANG XIN RÚT (hiện ở tab "Đơn chờ duyệt", badge riêng) ─
WITHDRAW_PENDING = [
    ('Lê Thị Phương',  'annual', 6,  7,  'Kế hoạch gia đình thay đổi'),
    ('Vũ Hoàng Minh',  'annual', 12, 13, 'Dự án gấp, xin đi làm lại'),
    ('Nguyễn Thị Len', 'personal', 4, 4, 'Đã xử lý xong việc riêng'),
]

# ── I. BỊ TỪ CHỐI (KPI "Đã từ chối" ở Tổng quan) ─────────────────────────
REFUSED = [
    ('Nguyễn Phương Thảo', 'unpaid',   date(2026, 8, 5),  date(2026, 8, 7),  'Trùng đợt cao điểm'),
    ('Đỗ Thị Minh Tuyết',  'personal', date(2026, 8, 11), date(2026, 8, 12), 'Không bố trí được người thay'),
    ('Lê Thị Ngọc Trang',  'annual',   date(2026, 8, 12), date(2026, 8, 14), 'Chưa đủ điều kiện quỹ phép'),
    ('Phùng Minh Anh',     'unpaid',   date(2026, 6, 29), date(2026, 6, 30), 'Nộp sát ngày, không kịp bố trí'),
]

# Nhân viên đã có "kịch bản riêng" ở trên → không rải thêm đơn ngẫu nhiên
# để các con số cảnh báo (burnout) đúng như thiết kế.
SCRIPTED = {
    'Phùng Minh Anh', 'Lê Thị Dung', 'Nguyễn Bình An', 'Nguyễn Thị Mai',
    'Đinh Hoàng Mai Phương', 'Nguyễn Thị Thanh Thuý', 'Lô Đức Thịnh',
    'Trần Khánh Linh', 'Võ Lê Duy Hoàng', 'Đặng Vũ Thu Hà',
    'Nguyễn Trung Kiên', 'Mai Hoài Tâm', 'Đỗ Thu Giang', 'Vũ Hoàng Minh',
    'Trương Thị Trang', 'Đặng Thị Thu Hà', 'Lê Thị Phương',
    'Ngô Thị Minh Tuyết', 'Bùi Thị Trang', 'Nguyễn Vũ Bình Dương',
    'Nguyễn Phương Thảo', 'Đỗ Thị Minh Tuyết', 'Lê Thị Ngọc Trang',
    'Nguyễn Thị Len', 'Phan Quỳnh Giang',
}

# Lý do cho các đơn rải ngẫu nhiên (nhóm J).
BULK_REASONS = {
    'personal': ['Giải quyết việc gia đình', 'Đi khám sức khoẻ',
                 'Việc cá nhân đột xuất', 'Về quê giỗ chạp'],
    'unpaid': ['Việc riêng, xin không lương', 'Bận việc gia đình'],
    'sick': ['Cảm sốt', 'Đau bụng', 'Viêm họng'],
    'annual': ['Nghỉ phép năm', 'Nghỉ ngơi sau đợt cao điểm'],
}


def workdays_between(d0, d1):
    """Số ngày T2–T6 trong [d0, d1] — dùng để ước lượng khi rải đơn."""
    n, cur = 0, d0
    while cur <= d1:
        if cur.weekday() < 5:
            n += 1
        cur += timedelta(days=1)
    return n


def next_workday(d):
    while d.weekday() >= 5:
        d += timedelta(days=1)
    return d


class TimeoffSeeder:
    def __init__(self, env, registry):
        self.env = env
        self.registry = registry
        self.stats = defaultdict(int)
        self.warnings = []
        self.emp = {}          # tên → hr.employee
        self.ltype = {}        # key → hr.leave.type
        self.tag_seq = 0

    # ── tiện ích ────────────────────────────────────────────────────────
    def step(self, title):
        _log.info('\n── %s', title)

    def warn(self, msg):
        self.warnings.append(msg)
        _log.warning('    ! %s', msg)

    def tag(self, record):
        """Gắn ir.model.data để lần chạy sau dọn đúng dữ liệu của script."""
        self.tag_seq += 1
        self.env['ir.model.data'].sudo().create({
            'module': TAG_MODULE,
            'name': '%s_%d' % (record._name.replace('.', '_'), self.tag_seq),
            'model': record._name,
            'res_id': record.id,
            'noupdate': True,
        })

    # ── 0. Nạp danh mục ─────────────────────────────────────────────────
    def load(self):
        self.step('0. Nạp nhân viên & loại nghỉ')
        for emp in self.env['hr.employee'].sudo().search([]):
            self.emp[emp.name] = emp
        for key, xmlid in LEAVE_TYPE_XMLID.items():
            lt = self.env.ref(xmlid, raise_if_not_found=False)
            if not lt:
                raise SystemExit('Thiếu loại nghỉ %s (%s) — DB chưa cài '
                                 'hocba_timeoff?' % (key, xmlid))
            self.ltype[key] = lt.sudo()
        _log.info('    %d nhân viên · %d loại nghỉ Học Bá',
                  len(self.emp), len(self.ltype))

    # ── 1. Dọn dữ liệu nghỉ phép cũ ─────────────────────────────────────
    def wipe(self):
        self.step('1. Dọn dữ liệu nghỉ phép cũ (đơn + quỹ phép)')
        env = self.env
        Leave = env['hr.leave'].sudo()
        Alloc = env['hr.leave.allocation'].sudo()

        leaves = Leave.search([])
        n_leave = len(leaves)
        for leave in leaves:
            try:
                with env.cr.savepoint():
                    if leave.state == 'validate':
                        leave.action_refuse()
                    leave.unlink()
            except Exception as ex:                       # noqa: BLE001
                self.warn('không xoá được đơn #%d: %s'
                          % (leave.id, str(ex).strip()[:100]))

        allocs = Alloc.search([])
        n_alloc = len(allocs)
        for alloc in allocs:
            try:
                with env.cr.savepoint():
                    if alloc.state == 'validate':
                        alloc.action_refuse()
                    alloc.unlink()
            except Exception as ex:                       # noqa: BLE001
                self.warn('không xoá được quỹ phép #%d: %s'
                          % (alloc.id, str(ex).strip()[:100]))

        # Bẫy đã biết (xem seed_demo_full): dòng resource_calendar_leaves sinh
        # ra khi duyệt đơn mà còn sót lại sẽ khiến CẢ CÔNG TY bị coi là không
        # làm việc ngày đó ⇒ đơn nghỉ mới ra 0 ngày, không duyệt được.
        env.cr.execute("""
            DELETE FROM resource_calendar_leaves l
             WHERE NOT EXISTS (SELECT 1 FROM ir_model_data d
                                WHERE d.model = 'resource.calendar.leaves'
                                  AND d.res_id = l.id)
        """)
        n_cal = env.cr.rowcount

        # Nhãn mồ côi của lần chạy trước (nếu bản ghi đã bị xoá bằng đường khác)
        env['ir.model.data'].sudo().search(
            [('module', '=', TAG_MODULE)]).unlink()

        _log.info('    xoá %d đơn · %d quỹ phép · %d dòng lịch nghỉ phát sinh',
                  n_leave, n_alloc, n_cal)
        env.cr.commit()

    # ── 2. Loại nhân viên (phục vụ chính sách nghỉ phép) ────────────────
    def set_emp_types(self):
        self.step('2. Gán "Loại nhân viên" cho chính sách nghỉ phép')
        n = 0
        for emp in self.env['hr.employee'].sudo().search([]):
            if emp.x_employment_status == 'ctv':
                emp_type = 'ctv'
            elif (emp.job_title or '').lower().startswith('giáo viên'):
                emp_type = 'teacher'
            else:
                emp_type = 'fulltime'
            if emp.x_hb_leave_emp_type == emp_type:
                continue
            # x_policy_override=True ghi CÙNG lệnh write: engine chính sách chỉ
            # tự tạo allocation khi cờ này tắt. Quỹ phép ở bước 3 do script cấp
            # tay với số ngày cố định — để cron tích luỹ (accrual) chen vào thì
            # số dư demo sẽ trôi, phá luôn cảnh báo "sắp hết phép".
            emp.write({'x_hb_leave_emp_type': emp_type,
                       'x_policy_override': True})
            n += 1
        self.stats['emp_types'] = n
        _log.info('    gán %d nhân viên', n)
        self.env.cr.commit()

    # ── 3. Cấp quỹ phép năm 2026 ───────────────────────────────────────
    def seed_allocations(self):
        self.step('3. Cấp quỹ phép năm 2026 (Nghỉ Phép Năm)')
        env = self.env
        annual = self.ltype['annual']
        n = 0
        for emp in env['hr.employee'].sudo().search([], order='name'):
            days = ALLOC_DAYS.get(emp.x_employment_status)
            if not days:                       # CTV không có quỹ phép năm
                continue
            try:
                with env.cr.savepoint():
                    alloc = env['hr.leave.allocation'].sudo().create({
                        'name': 'Phép năm 2026 — %s' % emp.name,
                        'holiday_status_id': annual.id,
                        'employee_id': emp.id,
                        'number_of_days': days,
                        'allocation_type': 'regular',
                        'date_from': date(2026, 1, 1),
                        'date_to': date(2026, 12, 31),
                    })
                    if alloc.state != 'validate':
                        alloc.action_approve()
                    self.tag(alloc)
                    n += 1
            except Exception as ex:                       # noqa: BLE001
                self.warn('cấp phép %s: %s' % (emp.name, str(ex).strip()[:120]))
        self.stats['allocations'] = n
        _log.info('    %d phiếu cấp phép (chính thức 12 ngày · thử việc 6 ngày)', n)
        env.cr.commit()

    # ── tạo 1 đơn nghỉ ──────────────────────────────────────────────────
    def make_leave(self, env, emp_name, type_key, d0, d1, reason,
                   state='validate', half=False, makeup=False,
                   approver=None):
        """Tạo 1 đơn nghỉ và đưa về đúng trạng thái. Trả record hoặc None."""
        emp = self.emp.get(emp_name)
        if not emp:
            self.warn('không có nhân viên "%s"' % emp_name)
            return None
        start = emp.x_probation_start or date(2026, 1, 1)
        if d0 < start:
            self.warn('%s vào làm %s — bỏ đơn %s' % (emp_name, start, d0))
            return None
        vals = {
            'name': reason,
            'holiday_status_id': self.ltype[type_key].id,
            'employee_id': emp.id,
            'request_date_from': d0,
            'request_date_to': d1,
        }
        if half:
            vals.update({'request_unit_half': True,
                         'request_date_to': d0,
                         'request_date_from_period': 'pm'})
        if makeup:
            vals['x_is_makeup'] = True
        try:
            with env.cr.savepoint():
                leave = env['hr.leave'].sudo().create(vals)
                if state == 'validate':
                    if leave.state in ('draft', 'confirm', 'validate1'):
                        leave.action_approve()
                    if leave.state == 'validate1':
                        leave.action_validate()
                    if approver:
                        leave.write({'first_approver_id': approver.id})
                elif state == 'refuse':
                    leave.action_refuse()
                    if approver:
                        leave.write({'first_approver_id': approver.id})
                # state 'confirm' → giữ nguyên sau create
                self.tag(leave)
                return leave
        except Exception as ex:                           # noqa: BLE001
            self.warn('%s %s→%s (%s): %s' % (emp_name, d0, d1, type_key,
                                             str(ex).strip()[:140]))
            return None

    # ── 4. Đơn đã duyệt trong quá khứ ───────────────────────────────────
    def seed_approved(self):
        self.step('4. Đơn ĐÃ DUYỆT trong quá khứ (tháng 6 & 8) ')
        # Cursor mới: number_of_days là compute-store tính qua lịch làm việc;
        # đọc trên transaction đã commit mới ra đúng số ngày (bẫy seed gốc).
        with self.registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, dict(self.env.context))
            approver = self.emp.get('Hoàng Thị Ngọc Anh')  # HR Manager
            approver = approver and env['hr.employee'].sudo().browse(approver.id)
            rows = (APPROVED_JULY_LEGACY + APPROVED_SICK_FREQUENT
                    + APPROVED_HIGH_ABSENCE + APPROVED_LOW_BALANCE)
            n = 0
            for name, key, d0, d1, reason in rows:
                if self.make_leave(env, name, key, d0, d1, reason,
                                   state='validate', approver=approver):
                    n += 1
            # Đơn đang nghỉ vắt qua hôm nay → KPI "Đang nghỉ hôm nay" khác 0.
            for name, key, off0, off1, reason in APPROVED_ONGOING:
                d0 = next_workday(TODAY + timedelta(days=off0))
                d1 = next_workday(TODAY + timedelta(days=off1))
                if self.make_leave(env, name, key, d0, max(d0, d1), reason,
                                   state='validate', approver=approver):
                    n += 1
            n += self.seed_bulk_approved(env, approver)
            cr.commit()
        self.stats['approved'] = n
        _log.info('    %d đơn đã duyệt', n)

    def seed_bulk_approved(self, env, approver):
        """Rải 1–2 đơn đã duyệt cho các nhân viên chưa có kịch bản riêng —
        để biểu đồ Tổng quan / tab Đơn đã duyệt phủ hết phòng ban.

        Chỉ dùng loại nghỉ KHÔNG trừ quỹ (việc riêng / không lương / ốm) và
        tối đa 3 ngày/người: giữ nguyên các ngưỡng cảnh báo đã thiết kế
        (>10 ngày vắng, <2 ngày quỹ phép) cho đúng nhóm nhân viên ở trên.

        BỎ QUA CTV: họ không được cấp quỹ phép (chính sách BR-021) nên chỉ cần
        một đơn đã duyệt là số dư âm ⇒ lọt vào cảnh báo "sắp hết phép" ở màn
        Theo dõi nghỉ phép — nhiễu, không phải rủi ro thật. CTV vẫn có đơn chờ
        duyệt / quá hạn / bị từ chối ở các nhóm khác.
        """
        n = 0
        # Khoảng an toàn: tháng 6 (từ 8/6) và 3–14/8 — không đụng chấm công T7.
        windows = [(date(2026, 6, 8), date(2026, 6, 30)),
                   (date(2026, 8, 3), date(2026, 8, 14))]
        for name in sorted(self.emp):
            if name in SCRIPTED:
                continue
            emp = self.emp[name]
            if emp.x_employment_status == 'ctv':
                continue
            rnd = random.Random(emp.id * 31 + 7)
            start = emp.x_probation_start or date(2026, 1, 1)
            picks = rnd.randint(1, 2)
            used = []
            for _i in range(picks):
                w0, w1 = windows[rnd.randrange(len(windows))]
                if w1 < start:
                    continue
                span = rnd.choice([1, 1, 1, 2])
                d0 = next_workday(max(w0, start)
                                  + timedelta(days=rnd.randrange(0, 12)))
                d1 = d0 + timedelta(days=span - 1)
                if d1 > w1 or any(not (d1 < a or d0 > b) for a, b in used):
                    continue
                key = rnd.choice(['personal', 'personal', 'unpaid', 'sick'])
                reason = rnd.choice(BULK_REASONS[key])
                if self.make_leave(env, name, key, d0, d1, reason,
                                   state='validate', approver=approver):
                    used.append((d0, d1))
                    n += 1
        return n

    # ── 5. Đơn chờ duyệt (tương lai) + nghỉ bù ─────────────────────────
    def seed_pending(self):
        self.step('5. Đơn CHỜ DUYỆT (ngày nghỉ tương lai) + đơn nghỉ bù')
        with self.registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, dict(self.env.context))
            n = 0
            for name, key, off0, off1, reason, half in PENDING_FUTURE:
                d0 = next_workday(TODAY + timedelta(days=off0))
                d1 = next_workday(TODAY + timedelta(days=off1))
                if d1 < d0:
                    d1 = d0
                if self.make_leave(env, name, key, d0, d1, reason,
                                   state='confirm', half=half):
                    n += 1
            self.stats['pending_future'] = n

            n_mk = 0
            for name, key, d0, d1, reason in PENDING_MAKEUP:
                if self.make_leave(env, name, key, d0, d1, reason,
                                   state='confirm', makeup=True):
                    n_mk += 1
            self.stats['pending_makeup'] = n_mk
            cr.commit()
        _log.info('    %d đơn chờ duyệt · %d đơn nghỉ bù (không tính quá hạn)',
                  self.stats['pending_future'], self.stats['pending_makeup'])

    # ── 6. Đơn quá hạn duyệt ───────────────────────────────────────────
    def seed_lapsed(self):
        self.step('6. Đơn QUÁ HẠN DUYỆT (tab Kiểm duyệt phát sinh)')
        with self.registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, dict(self.env.context))
            n = 0
            for name, key, d0, d1, reason in LAPSED:
                leave = self.make_leave(env, name, key, d0, d1, reason,
                                        state='confirm')
                if leave:
                    # Lùi ngày nộp về trước ngày nghỉ → cột "Ngày nộp" hợp lý
                    # (đơn nộp trước, người duyệt để trôi), không phải hôm nay.
                    cr.execute(
                        "UPDATE hr_leave SET create_date = %s WHERE id = %s",
                        (d0 - timedelta(days=3), leave.id))
                    n += 1
            cr.commit()
        self.stats['lapsed'] = n
        _log.info('    %d đơn quá hạn', n)

    # ── 7. Yêu cầu rút đơn + đơn bị từ chối ────────────────────────────
    def seed_withdraw_and_refused(self):
        self.step('7. Yêu cầu RÚT ĐƠN đang chờ + đơn BỊ TỪ CHỐI')
        with self.registry.cursor() as cr:
            env = Environment(cr, SUPERUSER_ID, dict(self.env.context))
            approver = self.emp.get('Hoàng Thị Ngọc Anh')
            approver = approver and env['hr.employee'].sudo().browse(approver.id)

            n_wd = 0
            for name, key, off0, off1, reason in WITHDRAW_PENDING:
                d0 = next_workday(TODAY + timedelta(days=off0))
                d1 = next_workday(TODAY + timedelta(days=off1))
                leave = self.make_leave(env, name, key, d0, max(d0, d1),
                                        'Nghỉ phép năm', state='validate',
                                        approver=approver)
                if leave:
                    leave.write({'x_withdraw_state': 'pending',
                                 'x_withdraw_reason': reason})
                    n_wd += 1
            self.stats['withdraw'] = n_wd

            n_rf = 0
            for name, key, d0, d1, reason in REFUSED:
                if self.make_leave(env, name, key, d0, d1, reason,
                                   state='refuse', approver=approver):
                    n_rf += 1
            self.stats['refused'] = n_rf
            cr.commit()
        _log.info('    %d yêu cầu rút đơn · %d đơn bị từ chối',
                  self.stats['withdraw'], self.stats['refused'])

    # ── 8. Kiểm chứng ──────────────────────────────────────────────────
    def report(self):
        self.step('8. Kiểm chứng dữ liệu vừa seed')
        env = self.env
        env.invalidate_all()
        env.registry.clear_cache()
        Leave = env['hr.leave'].sudo()

        pending = Leave.search_count([('state', 'in', ('confirm', 'validate1')),
                                      ('x_withdraw_state', '=', 'none')])
        withdraw = Leave.search_count([('state', '=', 'validate'),
                                       ('x_withdraw_state', '=', 'pending')])
        approved = Leave.search_count([('state', '=', 'validate')])
        refused = Leave.search_count([('state', '=', 'refuse')])

        # Quá hạn: còn chờ duyệt mà ngày bắt đầu đã qua, trừ đơn nghỉ bù.
        lapsed = Leave.search([('state', 'in', ('confirm', 'validate1')),
                               ('request_date_from', '<', TODAY),
                               ('x_is_makeup', '=', False)])
        burnout = env['hb.timeoff.burnout.line'].sudo().search(
            [('burnout_risk', '=', True)])
        by_reason = defaultdict(int)
        for line in burnout:
            by_reason[(line.risk_reason or '')[:30]] += 1

        _log.info('    Đơn chờ duyệt (tab Đơn chờ duyệt) : %d', pending)
        _log.info('    Yêu cầu rút đơn đang chờ          : %d', withdraw)
        _log.info('    Đơn quá hạn (Kiểm duyệt phát sinh): %d', len(lapsed))
        _log.info('    Đơn đã duyệt                      : %d', approved)
        _log.info('    Đơn bị từ chối                    : %d', refused)
        _log.info('    Nhân viên bị cảnh báo (Theo dõi nghỉ phép): %d',
                  len(burnout))
        for reason, cnt in sorted(by_reason.items(), key=lambda x: -x[1]):
            _log.info('      · %-32s %d', reason or '(không rõ)', cnt)

        if self.warnings:
            _log.info('\n    ⚠ %d cảnh báo trong lúc seed:', len(self.warnings))
            for w in self.warnings[:20]:
                _log.info('      - %s', w)

    def run(self):
        self.load()
        if WIPE:
            self.wipe()
        self.set_emp_types()
        self.seed_allocations()
        self.seed_approved()
        self.seed_pending()
        self.seed_lapsed()
        self.seed_withdraw_and_refused()
        self.env.cr.commit()
        self.report()


def main():
    # BẮT BUỘC có --addons-path: thiếu nó registry nạp không có custom-addons →
    # hr.employee mất sạch field x_* (AttributeError giữa chừng).
    odoo.tools.config.parse_config([
        '-c', '/etc/odoo/odoo.conf', '-d', DB,
        '--addons-path=/mnt/extra-addons',
        '--db_host=%s' % os.environ.get('HOST', 'db'),
        '--db_port=%s' % os.environ.get('PORT', '5432'),
        '--db_user=%s' % os.environ.get('USER', 'odoo'),
        '--db_password=%s' % os.environ.get('PASSWORD', 'odoo_password'),
    ])
    registry = Registry(DB)
    with registry.cursor() as cr:
        env = Environment(cr, SUPERUSER_ID, {
            'tz': 'Asia/Ho_Chi_Minh',
            'lang': 'en_US',
            'tracking_disable': True,
            'mail_create_nolog': True,
            'mail_notrack': True,
        })
        _log.info('╔══════════════════════════════════════════════════════════╗')
        _log.info('║  SEED NGHỈ PHÉP — DB %-35s ║', DB)
        _log.info('║  Hôm nay: %-46s ║', TODAY.isoformat())
        _log.info('╚══════════════════════════════════════════════════════════╝')
        seeder = TimeoffSeeder(env, registry)
        seeder.run()
        cr.commit()
    _log.info('\n✔ Xong.')


if __name__ == '__main__':
    main()
