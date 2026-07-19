# Bỏ mô hình "GV thay trả lại buổi" (spec 2026-06-26 §12, bản sửa 2026-07-17).
# State 'returned' bị gỡ khỏi selection của hocba.leave.session.resolution → dữ liệu
# cũ còn dòng state='returned' sẽ thành giá trị không hợp lệ khi nạp model mới.
# Đổi 'returned' -> 'declined' bằng SQL trước khi model mới nạp: cả hai đều nghĩa
# "GV thay không còn giữ buổi", và 'declined' đã được _revert_teaching_changes bỏ qua
# đúng như 'returned' trước đây nên chuỗi revert không đổi hành vi.


def migrate(cr, version):
    cr.execute("""SELECT 1 FROM information_schema.tables
                  WHERE table_name = 'hocba_leave_session_resolution'""")
    if not cr.fetchone():
        return
    cr.execute("""UPDATE hocba_leave_session_resolution
                  SET state = 'declined'
                  WHERE state = 'returned'""")
