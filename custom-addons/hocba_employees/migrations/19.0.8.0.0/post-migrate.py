"""Gỡ nhóm Giáo vụ khỏi mọi tài khoản nhân viên thật.

Nối tiếp 19.0.7.0.0 (đã gỡ manager_id): giáo vụ ngang hàng trưởng phòng — quản
lý giảng viên — nên cũng phải là TÀI KHOẢN VAI TRÒ riêng, HR tạo lại qua form
phòng ban. Chốt với khách 2026-08-27.

Bản ghi tài khoản vai trò (x_is_role_account) được CHỪA LẠI: nếu ai đó đã kịp
tạo giáo vụ đúng mô hình mới thì không có lý do gì gỡ quyền của họ. Trên DB
hiện tại chưa có bản ghi nào như vậy nên trong thực tế mệnh đề này chưa lọc gì,
nhưng để đó thì chạy lại migration ở môi trường khác vẫn an toàn.

Sau bản này mọi tài khoản giáo vụ cũ MẤT quyền cho tới khi HR tạo lại — đây là
hệ quả cố ý, giống hệt đợt gỡ 6 trưởng phòng kiêm nhiệm.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        DELETE FROM res_groups_users_rel r
        USING ir_model_data d
        WHERE r.gid = d.res_id
          AND d.module = 'hocba_employees'
          AND d.name = 'group_hocba_giaovu'
          AND d.model = 'res.groups'
          AND NOT EXISTS (
              SELECT 1 FROM hr_employee e
              WHERE e.user_id = r.uid
                AND e.x_is_role_account IS TRUE
          )
    """)
