/* API domain Nghỉ phép (timeoff) — Nhật Anh. Spec: docs/SPEC_API_TIMEOFF.md */
import { hbGet, hbPost, hbUploadFields } from './client';

/* Tab "Của tôi": số dư phép + loại nghỉ + đơn của chính mình. */
export const fetchOverview = () => hbGet('/hocba-hrm/api/timeoff/overview');

/* Tab "Chờ duyệt" (officer): đơn đang chờ của đội. */
export const fetchApprovals = () => hbGet('/hocba-hrm/api/timeoff/approvals');

/* Số đơn cần duyệt — cho badge cạnh "Nghỉ phép" ở thanh menu. Endpoint chỉ
   đếm (rẻ hơn fetchApprovals) và trả {canApprove:false, count:0} thay vì 403
   khi user không có quyền duyệt. */
export const fetchPendingCount = () =>
  hbGet('/hocba-hrm/api/timeoff/pending-count');

/* Tạo đơn nghỉ cho chính mình. payload:
   { leaveTypeId, dateFrom, dateTo, period?, reason, attachment?, resolutions? }
   period = 'am'|'pm' cho nghỉ NỬA NGÀY (chỉ loại requestUnit='half_day'); bỏ trống = cả ngày.
   attachment = { filename, mimetype, data(base64) } — chỉ cho loại cần chứng từ.
   resolutions = [{ sessionId, type:'class_off'|'substitute', substituteId? }] — GV nghỉ
   trùng buổi dạy phải xử lý từng buổi (xem fetchTeachingConflicts). */
export const createRequest = (payload) =>
  hbPost('/hocba-hrm/api/timeoff/request', payload);

/* Dò buổi dạy trùng khoảng nghỉ (chỉ giáo viên). dateFrom/dateTo 'YYYY-MM-DD'.
   → { conflicts: [{sessionId, className, date, startTime, endTime}],
       substitutes: [{id, name}] } (DS giáo viên để chọn dạy thay). */
export const fetchTeachingConflicts = (dateFrom, dateTo) =>
  hbPost('/hocba-hrm/api/timeoff/teaching-conflicts', { dateFrom, dateTo });

/* Buổi dạy sắp tới của chính GV (cho form nghỉ-theo-buổi, chế độ A).
   → { sessions: [{sessionId, className, date, startTime, endTime}], substitutes: [{id,name}] }. */
export const fetchMyTeachingSessions = () =>
  hbGet('/hocba-hrm/api/timeoff/my-teaching-sessions');

/* Yêu cầu dạy thay gửi tới chính mình (giáo viên thay). → { items: [...] }. */
export const fetchSubstitutions = () =>
  hbGet('/hocba-hrm/api/timeoff/substitutions');

/* GV thay đồng ý/từ chối 1 yêu cầu dạy thay. accept=bool; reason chỉ khi từ chối.
   → { items: [...] } (danh sách yêu cầu mới). */
export const decideSubstitution = (id, accept, reason) =>
  hbPost(`/hocba-hrm/api/timeoff/substitutions/${id}/decide`, { accept, reason });

/* Chủ đơn hủy đơn còn chờ duyệt → trả payload overview mới. */
export const cancelRequest = (id) =>
  hbPost(`/hocba-hrm/api/timeoff/request/${id}/cancel`, {});

/* Duyệt / từ chối đơn (officer). payload:
   { action: 'approve'|'refuse', medicalOverride?, medicalOverrideReason? }
   → trả payload approvals mới. */
export const decideRequest = (id, payload) =>
  hbPost(`/hocba-hrm/api/timeoff/request/${id}/decision`, payload);

/* Phase 7 — chủ đơn gửi yêu cầu rút đơn đã duyệt. payload: { reason }
   → trả payload overview mới (đơn vào state "chờ duyệt rút"). */
export const withdrawRequest = (id, reason) =>
  hbPost(`/hocba-hrm/api/timeoff/request/${id}/withdraw`, { reason });

/* Phase 7 — người duyệt phạm vi duyệt/từ chối yêu cầu rút. payload: { approve, note }
   approve=true → đơn về 'refuse' + hoàn quỹ; false → đơn giữ 'validate'.
   → trả payload approvals mới. */
export const decideWithdraw = (id, payload) =>
  hbPost(`/hocba-hrm/api/timeoff/request/${id}/withdraw/decide`, payload);

/* Tổng quan (dashboard) — tự đổi view Manager/Nhân viên theo quyền.
   year: số năm; dept: id phòng ban (chỉ Manager dùng để lọc). */
export const fetchDashboard = (year, dept) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/dashboard' + (q ? '?' + q : ''));
};

/* Lịch nghỉ. Phạm vi theo vai trò (NV/GV: cá nhân · trưởng phòng: cả phòng ·
   HR: mọi phòng). dept = id phòng ban để HR lọc 1 phòng (vai trò khác bỏ qua). */
export const fetchCalendar = (year, dept) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  if (dept) p.set('dept', dept);
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

/* Thêm 1 hoặc nhiều ngày đi làm (HR). items: [{date:'YYYY-MM-DD', name?}] —
   ngày nào không có `name` thì dùng chung ghi chú `name` của cả lô.
   Chỉ nhận ngày CHƯA ĐẾN (>= minDate); ngày đã qua → 400 'past_workday'. */
export const addWorkdays = (items, name, year) =>
  hbPost('/hocba-hrm/api/timeoff/workdays/add', { items, name, year });

/* URL tải file .xlsx mẫu (chỉ HR/Admin) — liệt kê sẵn Thứ 7/Chủ nhật CHƯA ĐẾN
   của năm, HR chỉ điền 'x'. Dùng làm href cho thẻ <a download>. */
export const workdayTemplateUrl = (year) =>
  `/hocba-hrm/api/timeoff/workdays/template?year=${year}`;

/* Tải file mẫu đã điền lên để KIỂM (chưa ghi gì). OK → {rows, skipped};
   sai định dạng → ApiError có .message + .details (từng dòng sai). */
export const importWorkdays = (file, year) =>
  hbUploadFields('/hocba-hrm/api/timeoff/workdays/import', file, { year });

/* Sửa 1 ngày đi làm (HR): đổi ngày và/hoặc ghi chú. Chỉ ngày CHƯA ĐẾN;
   ngày đã diễn ra → 400 'locked_workday'. */
export const updateWorkday = (id, { date, name }, year) =>
  hbPost(`/hocba-hrm/api/timeoff/workdays/${id}/update`, { date, name, year });

/* Xoá 1 ngày đi làm (HR). Chỉ ngày CHƯA ĐẾN — ngày đã diễn ra bị chặn (400)
   vì chấm công/lương của ngày đó đã tính theo lịch này. */
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

/* Bảng "Quỹ phép" toàn nhân viên (Phase 1/3 — chỉ officer).
   HR/Admin xem mọi phòng ban, Trưởng phòng chỉ phòng mình.
   year; dept (lọc phòng ban); type (lọc loại nghỉ); filter='expiring'
   (chỉ NV còn nhiều phép năm — sắp mất phép). Tham số tùy chọn. */
export const fetchBalances = (year, dept, type, filter) => {
  const p = new URLSearchParams();
  if (year) p.set('year', year);
  if (dept) p.set('dept', dept);
  if (type) p.set('type', type);
  if (filter) p.set('filter', filter);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/balances' + (q ? '?' + q : ''));
};

/* Điều chỉnh quỹ phép thủ công (Phase 2 — chỉ HR Manager).
   payload: { employeeId, leaveTypeId, deltaDays, reason }
   deltaDays > 0 = cấp thêm, < 0 = trừ bớt. → trả { row } (dòng số dư mới của NV). */
export const adjustQuota = (payload) =>
  hbPost('/hocba-hrm/api/timeoff/balances/adjust', payload);

/* Mức độ trùng lịch nghỉ theo ngày (Phase 4 — chỉ officer). Trả các ngày có
   người nghỉ (đã duyệt) trong khoảng + KPI ngày 'quá tải' (>= overlapWarn).
   from/to: 'YYYY-MM-DD' (thiếu → cả năm hiện tại); dept: lọc 1 phòng ban. */
export const fetchCoverage = (from, to, dept) => {
  const p = new URLSearchParams();
  if (from) p.set('from', from);
  if (to) p.set('to', to);
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/coverage' + (q ? '?' + q : ''));
};

/* Nhật ký điều chỉnh quỹ. Lọc theo NV / loại nghỉ (tùy chọn). → { history: [...] } */
export const fetchAdjustHistory = (employeeId, leaveTypeId) => {
  const p = new URLSearchParams();
  if (employeeId) p.set('employeeId', employeeId);
  if (leaveTypeId) p.set('leaveTypeId', leaveTypeId);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/balances/history' + (q ? '?' + q : ''));
};

/* Nhật ký thao tác (audit) của 1 đơn nghỉ. → { history: [{date, author, body, type}] } */
export const fetchRequestHistory = (id) =>
  hbGet(`/hocba-hrm/api/timeoff/request/${id}/history`);

/* Phase 12 — màn "Giám sát duyệt đơn": đơn lỡ hạn (qua ngày bắt đầu nghỉ mà
   vẫn chờ duyệt) + đối chiếu chấm công + KPI. Chỉ officer; dept: lọc 1 phòng. */
export const fetchLapsedDashboard = (dept) => {
  const p = new URLSearchParams();
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/lapsed-dashboard' + (q ? '?' + q : ''));
};

export const fetchBurnout = (dept) => {
  const p = new URLSearchParams();
  if (dept) p.set('dept', dept);
  const q = p.toString();
  return hbGet('/hocba-hrm/api/timeoff/burnout' + (q ? '?' + q : ''));
};
