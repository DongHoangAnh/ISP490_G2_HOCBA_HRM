"""Kết nối CMS MySQL để lấy lịch dạy giáo viên.

Đọc thông tin kết nối từ biến môi trường (CMS_MYSQL_*).
Dùng pymysql — đã cài trong Dockerfile.
"""
import logging
import os
from contextlib import contextmanager
from datetime import date, timedelta

_logger = logging.getLogger(__name__)

_CMS_HOST = os.environ.get('CMS_MYSQL_HOST', '14.232.211.255')
_CMS_PORT = int(os.environ.get('CMS_MYSQL_PORT', '58008'))
_CMS_USER = os.environ.get('CMS_MYSQL_USER', 'root')
_CMS_PASS = os.environ.get('CMS_MYSQL_PASSWORD', '123456')
_CMS_DB = os.environ.get('CMS_MYSQL_DB', 'erp_database')


@contextmanager
def _cms_conn():
    """Context manager trả về pymysql cursor. Tự đóng connection."""
    import pymysql
    conn = pymysql.connect(
        host=_CMS_HOST, port=_CMS_PORT,
        user=_CMS_USER, password=_CMS_PASS,
        database=_CMS_DB, charset='utf8mb4',
        connect_timeout=5, read_timeout=10,
    )
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        yield cursor
    finally:
        conn.close()


def get_sessions_for_tutor(cms_tutor_id: str, target_date: date) -> list[dict]:
    """Lấy danh sách buổi dạy của 1 giáo viên trong 1 ngày.

    Trả về list dict:
        id, class_id, class_name, date, start_time, end_time, status, role_type
    Giáo viên có thể là main_tutor của class hoặc được assign riêng vào session.
    """
    if not cms_tutor_id:
        return []
    try:
        with _cms_conn() as cur:
            cur.execute("""
                SELECT
                    cs.id,
                    cs.class_id,
                    COALESCE(c.name, '') AS class_name,
                    cs.date,
                    cs.start_time,
                    cs.end_time,
                    COALESCE(cs.status, 'PLANING') AS status,
                    CASE
                        WHEN cs.tutor_id = %(tid)s THEN 'TEACHER'
                        WHEN c.main_tutor_id = %(tid)s THEN 'MAIN_TEACHER'
                        WHEN c.assistant_id = %(tid)s THEN 'ASSISTANT'
                        ELSE 'TEACHER'
                    END AS role_type
                FROM class_session cs
                LEFT JOIN class c ON cs.class_id = c.id
                WHERE cs.date = %(date)s
                  AND (cs.deleted IS NULL OR cs.deleted = 0)
                  AND (
                      cs.tutor_id = %(tid)s
                      OR c.main_tutor_id = %(tid)s
                      OR c.assistant_id = %(tid)s
                  )
                ORDER BY cs.start_time
            """, {'tid': cms_tutor_id, 'date': target_date.isoformat()})
            rows = cur.fetchall()
        return list(rows)
    except Exception as exc:
        _logger.warning('CMS MySQL error (get_sessions): %s', exc)
        return []


def get_sessions_for_week(cms_tutor_id: str, monday: date) -> list[dict]:
    """Lấy buổi dạy của 1 giáo viên trong tuần (7 ngày từ monday)."""
    if not cms_tutor_id:
        return []
    sunday = monday + timedelta(days=6)
    try:
        with _cms_conn() as cur:
            cur.execute("""
                SELECT
                    cs.id,
                    cs.class_id,
                    COALESCE(c.name, '') AS class_name,
                    cs.date,
                    cs.start_time,
                    cs.end_time,
                    COALESCE(cs.status, 'PLANING') AS status,
                    CASE
                        WHEN cs.tutor_id = %(tid)s THEN 'TEACHER'
                        WHEN c.main_tutor_id = %(tid)s THEN 'MAIN_TEACHER'
                        WHEN c.assistant_id = %(tid)s THEN 'ASSISTANT'
                        ELSE 'TEACHER'
                    END AS role_type
                FROM class_session cs
                LEFT JOIN class c ON cs.class_id = c.id
                WHERE cs.date BETWEEN %(mon)s AND %(sun)s
                  AND (cs.deleted IS NULL OR cs.deleted = 0)
                  AND (
                      cs.tutor_id = %(tid)s
                      OR c.main_tutor_id = %(tid)s
                      OR c.assistant_id = %(tid)s
                  )
                ORDER BY cs.date, cs.start_time
            """, {'tid': cms_tutor_id, 'mon': monday.isoformat(), 'sun': sunday.isoformat()})
            rows = cur.fetchall()
        return list(rows)
    except Exception as exc:
        _logger.warning('CMS MySQL error (get_sessions_week): %s', exc)
        return []


def _fmt_time(t) -> str:
    """Chuyển timedelta (MySQL TIME) hoặc string 'HH:MM:SS' sang 'HH:MM'."""
    if t is None:
        return ''
    if isinstance(t, timedelta):
        total_s = int(t.total_seconds())
        h, rem = divmod(total_s, 3600)
        m = rem // 60
        return f'{h:02d}:{m:02d}'
    parts = str(t).split(':')
    return f'{int(parts[0]):02d}:{int(parts[1]):02d}'


def session_to_dict(row: dict) -> dict:
    """Chuẩn hóa 1 row từ MySQL thành dict trả về API."""
    return {
        'id': row['id'],
        'classId': row['class_id'],
        'className': row['class_name'] or '',
        'date': str(row['date']),
        'startTime': _fmt_time(row['start_time']),
        'endTime': _fmt_time(row['end_time']),
        'status': (row['status'] or 'PLANING').upper(),
        'roleType': row.get('role_type', 'TEACHER'),
        # raw timedelta còn giữ để tính window check-in
        '_start_raw': row['start_time'],
        '_end_raw': row['end_time'],
        '_date_raw': row['date'],
    }
