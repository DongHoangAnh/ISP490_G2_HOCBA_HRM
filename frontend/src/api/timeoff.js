/* API domain Nghỉ phép (timeoff) — Nhật Anh. Spec: docs/SPEC_API_TIMEOFF.md */
import { hbGet, hbPost } from './client';

/* Tab "Của tôi": số dư phép + loại nghỉ + đơn của chính mình. */
export const fetchOverview = () => hbGet('/hocba-hrm/api/timeoff/overview');

/* Tab "Chờ duyệt" (officer): đơn đang chờ của đội. */
export const fetchApprovals = () => hbGet('/hocba-hrm/api/timeoff/approvals');

/* Tạo đơn nghỉ cho chính mình. payload:
   { leaveTypeId, dateFrom, dateTo, reason, attachment? }
   attachment = { filename, mimetype, data(base64) } — chỉ cho loại cần chứng từ. */
export const createRequest = (payload) =>
  hbPost('/hocba-hrm/api/timeoff/request', payload);

/* Chủ đơn hủy đơn còn chờ duyệt → trả payload overview mới. */
export const cancelRequest = (id) =>
  hbPost(`/hocba-hrm/api/timeoff/request/${id}/cancel`, {});

/* Duyệt / từ chối đơn (officer). payload:
   { action: 'approve'|'refuse', replacementNote?, medicalOverride?, medicalOverrideReason? }
   → trả payload approvals mới. */
export const decideRequest = (id, payload) =>
  hbPost(`/hocba-hrm/api/timeoff/request/${id}/decision`, payload);

/* Tổng quan (dashboard) — tự đổi view Manager/Nhân viên theo quyền.
   year: số năm; dept: id phòng ban (chỉ Manager dùng để lọc). */
export const fetchDashboard = (year, dept) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/dashboard' + (q ? '?' + q : ''));
};

/* Lịch nghỉ. scope: 'me' (của tôi) | 'all' (cả đội — chỉ officer). */
export const fetchCalendar = (year, scope) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  if (scope) p.set('scope', scope);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/calendar' + (q ? '?' + q : ''));
};

/* Tổng hợp đơn nghỉ (mọi trạng thái) theo phòng ban — chỉ officer.
   year: năm; dept: lọc 1 phòng ban (tùy chọn). */
export const fetchSummary = (year, dept) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/summary' + (q ? '?' + q : ''));
};
