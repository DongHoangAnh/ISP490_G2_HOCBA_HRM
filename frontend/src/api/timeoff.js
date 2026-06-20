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

/* Báo cáo cá nhân (tab "Tổng hợp" — chỉ role Nhân viên): thống kê nghỉ phép
   của chính user trong năm (quỹ phép năm, KPI, theo loại/tháng, danh sách đơn). */
export const fetchSummary = (year) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/summary' + (q ? '?' + q : ''));
};

/* Lịch làm việc: các ngày đi làm thêm (ngoài Thứ 2–Thứ 6). Mọi user xem được;
   chỉ HR/Admin (canEdit) mới thêm/xoá. */
export const fetchWorkdays = (year) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/workdays' + (q ? '?' + q : ''));
};

/* Thêm 1 hoặc nhiều ngày đi làm (HR). dates: mảng 'YYYY-MM-DD'. */
export const addWorkdays = (dates, name, year) =>
  hbPost('/hocba-hrm/api/timeoff/workdays/add', { dates, name, year });

/* Xoá 1 ngày đi làm (HR). */
export const deleteWorkday = (id, year) =>
  hbPost(`/hocba-hrm/api/timeoff/workdays/${id}/delete`, { year });

/* Danh sách đơn nghỉ ĐÃ DUYỆT (trang quản lý — chỉ officer).
   HR/Admin xem mọi phòng ban, Trưởng phòng chỉ phòng mình.
   year: năm; dept: lọc 1 phòng ban (tùy chọn). */
export const fetchApproved = (year, dept) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/approved' + (q ? '?' + q : ''));
};
