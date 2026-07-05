# Hợp nhất chuông: copy hb.leave.notification -> hb.notification rồi bỏ bảng cũ.
# Chạy TRƯỚC khi load model mới (bảng hb_notification đã tồn tại vì hocba_notify
# là dependency, được cài/nâng cấp trước hocba_timeoff).


def migrate(cr, version):
    cr.execute("""SELECT 1 FROM information_schema.tables
                  WHERE table_name = 'hb_leave_notification'""")
    if not cr.fetchone():
        return
    cr.execute("""SELECT 1 FROM information_schema.tables
                  WHERE table_name = 'hb_notification'""")
    if not cr.fetchone():
        return
    cr.execute("""
        INSERT INTO hb_notification
            (recipient_id, category, kind, level, title, body,
             target_view, target_ref, target_tab, is_read,
             create_date, write_date, create_uid, write_uid)
        SELECT n.recipient_id, 'timeoff', n.kind,
               CASE WHEN n.kind IN ('pending','withdraw_pending','sub_request','sub_returned') THEN 'warning'
                    WHEN n.kind IN ('approved','sub_accepted','withdraw_approved') THEN 'success'
                    WHEN n.kind IN ('refused','sub_declined','sub_cancelled','withdraw_refused') THEN 'danger'
                    ELSE 'info' END,
               n.title, n.body, 'timeoff', n.leave_id,
               CASE WHEN n.kind LIKE 'sub_%' THEN 'sub' ELSE NULL END,
               n.is_read, n.create_date, n.write_date, n.create_uid, n.write_uid
        FROM hb_leave_notification n
    """)
    cr.execute("DROP TABLE hb_leave_notification CASCADE")
