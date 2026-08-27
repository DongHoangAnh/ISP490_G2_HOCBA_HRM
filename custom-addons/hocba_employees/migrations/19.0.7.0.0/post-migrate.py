"""Gỡ manager_id của mọi phòng ban — chuẩn bị cho tài khoản vai trò.

Spec: docs/superpowers/specs/2026-08-27-tai-khoan-vai-tro-truong-phong-design.md

Trước bản này, trưởng phòng là một NV THẬT kiêm nhiệm, nên tài khoản cá nhân của
người đó mang luôn quyền quản lý phòng. Chốt với khách 2026-08-27: quyền quản lý
phải nằm ở một tài khoản vai trò riêng, HR tạo lại qua form "Thêm phòng ban".

CỐ TÌNH không đánh dấu x_is_role_account cho bản ghi cũ: không heuristic nào
phân biệt được "NV thật kiêm trưởng phòng" với "tài khoản vai trò" mà không có
nguy cơ bắt nhầm một NV thật rồi làm họ biến mất khỏi lương và chấm công.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("UPDATE hr_department SET manager_id = NULL "
               "WHERE manager_id IS NOT NULL")
