/* API chuông thông báo hợp nhất (hb.notification — module hocba_notify).
   Dùng chung mọi domain: timeoff, offboarding, onboarding, nhắc hạn. */
import { hbGet, hbPost } from './client';

/* → { items: [{id, category, kind, level, title, body, targetView, targetRef,
     targetTab, isRead, createdAt}], unread } */
export const fetchNotifications = (limit = 20) =>
  hbGet(`/hocba-hrm/api/notifications?limit=${limit}`);

/* Đánh dấu 1 thông báo đã đọc → trả { items, unread } mới. */
export const markNotificationRead = (id) =>
  hbPost(`/hocba-hrm/api/notifications/${id}/read`, {});

/* Đánh dấu tất cả thông báo đã đọc → trả { items, unread } mới. */
export const markAllNotificationsRead = () =>
  hbPost('/hocba-hrm/api/notifications/read-all', {});
