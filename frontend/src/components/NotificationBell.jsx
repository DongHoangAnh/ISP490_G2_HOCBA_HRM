/* Chuông thông báo hợp nhất — đặt ở góc phải Topbar (file CHUNG). Dùng chung
   MỌI module (timeoff/offboarding/onboarding/nhắc hạn): poll /api/notifications
   mỗi 60s; mở dropdown xem danh sách, đánh dấu đã đọc, bấm 1 thông báo →
   điều hướng view đích (onOpenNotification). */
import { useState, useEffect, useRef } from 'react';
import Icon from './Icon';
import {
  fetchNotifications, markNotificationRead, markAllNotificationsRead,
} from '../api/notifications';

const POLL_MS = 60000;

/* Mức thông báo → màu chấm (level do BE quyết, không phụ thuộc kind).
   'lapsed' của timeoff dùng level='danger' (đỏ) — xem _KIND_LEVEL ở BE. */
const LEVEL_DOT = {
  info: 'var(--blue,#3b82f6)', success: 'var(--green,#10b981)',
  warning: 'var(--amber,#f59e0b)', danger: 'var(--red-600,#dc2626)',
};

function timeAgo(s) {
  if (!s) return '';
  const d = new Date(s);
  if (isNaN(d)) return '';
  const sec = Math.floor((Date.now() - d.getTime()) / 1000);
  if (sec < 60) return 'vừa xong';
  if (sec < 3600) return Math.floor(sec / 60) + ' phút trước';
  if (sec < 86400) return Math.floor(sec / 3600) + ' giờ trước';
  return Math.floor(sec / 86400) + ' ngày trước';
}

export default function NotificationBell({ onOpenNotification }) {
  const [open, setOpen] = useState(false);
  const [data, setData] = useState({ items: [], unread: 0 });
  const wrapRef = useRef(null);

  // Poll badge (số chưa đọc) định kỳ; không cần realtime.
  const refresh = () => fetchNotifications(20).then(setData).catch(() => {});
  useEffect(() => {
    refresh();
    const t = setInterval(refresh, POLL_MS);
    return () => clearInterval(t);
  }, []);

  // Đóng dropdown khi bấm ra ngoài.
  useEffect(() => {
    if (!open) return undefined;
    const h = (e) => { if (wrapRef.current && !wrapRef.current.contains(e.target)) setOpen(false); };
    window.addEventListener('mousedown', h);
    return () => window.removeEventListener('mousedown', h);
  }, [open]);

  const onItem = (n) => {
    setOpen(false);
    if (!n.isRead) markNotificationRead(n.id).then(setData).catch(() => {});
    if (onOpenNotification) onOpenNotification(n);
  };

  const onReadAll = () => { markAllNotificationsRead().then(setData).catch(() => {}); };

  const unread = data.unread || 0;

  return (
    <div ref={wrapRef} style={{ position: 'relative' }}>
      <button className="icon-btn" title="Thông báo" onClick={() => { setOpen((o) => !o); if (!open) refresh(); }}
        style={{ position: 'relative' }}>
        <Icon name="bell" size={20} />
        {unread > 0 && (
          <span style={{ position: 'absolute', top: 2, right: 2, minWidth: 16, height: 16, padding: '0 4px', borderRadius: 9, background: 'var(--red-600,#dc2626)', color: '#fff', fontSize: 10, fontWeight: 700, display: 'grid', placeItems: 'center', lineHeight: 1 }}>
            {unread > 99 ? '99+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div style={{ position: 'absolute', top: 'calc(100% + 8px)', right: 0, width: 340, maxHeight: 440, overflow: 'auto', background: '#fff', border: '1px solid var(--border)', borderRadius: 12, boxShadow: '0 12px 32px rgba(0,0,0,.14)', zIndex: 50 }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 14px', borderBottom: '1px solid var(--border)', position: 'sticky', top: 0, background: '#fff' }}>
            <strong style={{ fontSize: 14 }}>Thông báo{unread > 0 ? ` (${unread})` : ''}</strong>
            {unread > 0 && (
              <button className="btn btn-ghost btn-sm" onClick={onReadAll}>Đánh dấu tất cả đã đọc</button>
            )}
          </div>
          {data.items.length === 0 ? (
            <div className="muted" style={{ padding: '24px 14px', textAlign: 'center', fontSize: 13 }}>
              Không có thông báo nào.
            </div>
          ) : (
            <ul style={{ listStyle: 'none', margin: 0, padding: 0 }}>
              {data.items.map((n) => (
                <li key={n.id}>
                  <button onClick={() => onItem(n)}
                    style={{ width: '100%', textAlign: 'left', display: 'flex', gap: 10, padding: '11px 14px', border: 'none', borderBottom: '1px solid var(--border)', background: n.isRead ? '#fff' : 'var(--red-50,#fef2f2)', cursor: 'pointer' }}>
                    <span style={{ width: 8, height: 8, borderRadius: '50%', marginTop: 5, flexShrink: 0, background: LEVEL_DOT[n.level] || 'var(--muted)' }}></span>
                    <span style={{ flex: 1, minWidth: 0 }}>
                      <span style={{ display: 'block', fontSize: 13, fontWeight: n.isRead ? 500 : 700, color: 'var(--ink)' }}>{n.title}</span>
                      <span style={{ display: 'block', fontSize: 12, color: 'var(--muted)', marginTop: 1, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{n.body}</span>
                      <span style={{ display: 'block', fontSize: 11, color: 'var(--muted)', marginTop: 2 }}>{timeAgo(n.createdAt)}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}
