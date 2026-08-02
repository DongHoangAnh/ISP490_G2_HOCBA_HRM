/* ============================================================
   API domain Dịch vụ nhân sự (service) — Nhật Anh.
   Spec: docs/superpowers/specs/2026-07-26-hr-service-request-design.md §6
   Backend: custom-addons/hocba_service/controllers/main.py
   ============================================================ */
import { hbGet, hbPost } from './client';

const BASE = '/hocba-hrm/api/service';

const qs = (params) => {
  const p = new URLSearchParams();
  Object.entries(params || {}).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== '' && v !== false) p.set(k, v);
  });
  const s = p.toString();
  return s ? '?' + s : '';
};

/* Dữ liệu khởi tạo màn: danh mục loại + cờ vai trò + thông tin phòng.
   → { isHr, isHrManager, isDeptManager, canHandle, canSend,
       types: [{id, code, name, defaultRecipient, forceHrOnly, allowAnonymous,
                allowAttachment, hasRating, slaDays, description}],
       myDepartment: {id, name, headcount, hasManager, iAmManager} | null,
       minAnonDeptSize, anonDailyLimit, anonUsedToday }
   3 field cuối + myDepartment.headcount để form CHẶN TẠI CHỖ các luật ẩn danh
   (§7.3) thay vì để người dùng viết xong đơn mới ăn 400. */
export const fetchMeta = () => hbGet(`${BASE}/meta`);

/* Gửi đơn. payload:
   { typeId, subject, body, recipientScope: 'hr'|'manager'|'both',
     isAnonymous, rating?: '1'..'5', priority?: 'normal'|'urgent',
     attachments?: [{ name, mimetype, data(base64) }] }
   ⚠️ KHÔNG có `attachmentIds` — BE cố tình không nhận id attachment do client
   chọn (§6.1: gắn file của người khác vào đơn của mình là lỗ hổng). Gửi nội
   dung base64, BE tự tạo record. Giới hạn PDF/JPG/PNG · ≤5MB · ≤3 tệp.
   Đơn ẩn danh KHÔNG được đính kèm (BR-SVC-02).
   → payload chi tiết của đơn vừa tạo (kèm messages).
   Mã lỗi hay gặp (e.code): anon_not_allowed · anon_scope_both ·
   anon_dept_too_small · anon_daily_limit · attachment_not_allowed ·
   bad_mimetype · file_too_large · too_many_files · no_employee. */
export const createRequest = (payload) => hbPost(`${BASE}/request`, payload);

/* Tab "Đơn của tôi". state: '' | 'open' (new+in_progress) | state thật;
   year: lọc theo năm gửi. → { requests: [...], years: [2026, …] } */
export const fetchMyRequests = (state, year) =>
  hbGet(`${BASE}/my-requests${qs({ state, year })}`);

/* Chi tiết 1 đơn + hội thoại. Người gửi không thấy tin nội bộ (BR-SVC-07).
   → { …đơn, messages: [{id, authorRole, authorName, body, isInternal, createdAt}] } */
export const fetchRequest = (id) => hbGet(`${BASE}/request/${id}`);

/* Trả lời trong hội thoại. isInternal chỉ có tác dụng với người xử lý —
   BE tự ép false cho người gửi (BR-SVC-07), SPA không cần tự chốt. */
export const replyRequest = (id, body, isInternal = false) =>
  hbPost(`${BASE}/request/${id}/reply`, { body, isInternal });

/* Người gửi rút đơn — chỉ khi đơn còn ở trạng thái 'Mới'. */
export const cancelRequest = (id) => hbPost(`${BASE}/request/${id}/cancel`, {});

/* ---- Phía người xử lý (dùng từ P4/P5) ---------------------------------- */

/* Hộp thư cần xử lý (HR / Trưởng phòng). BR-SVC-13: HR Manager KHÔNG thấy đơn
   gửi riêng cho Trưởng phòng ⇒ không có filter "Tất cả". */
export const fetchInbox = ({ state, overdue, typeId, q } = {}) =>
  hbGet(`${BASE}/inbox${qs({ state, overdue: overdue ? 1 : '', typeId, q })}`);

export const claimRequest = (id) => hbPost(`${BASE}/request/${id}/claim`, {});
export const answerRequest = (id) => hbPost(`${BASE}/request/${id}/answer`, {});
export const closeRequest = (id, closedReason) =>
  hbPost(`${BASE}/request/${id}/close`, { closedReason });

/* KPI hộp thư của CHÍNH người xử lý (không phải toàn hệ thống — BR-SVC-13). */
export const fetchStats = () => hbGet(`${BASE}/stats`);

/* ---- Cấu hình (P6) — chỉ HR Manager/Admin (meta.canConfig) -------------- */

/* → { canConfig, params: { minAnonDeptSize, anonDailyLimit },
       types: [{ …như meta.types…, sequence, active, usageCount, openCount }] }
   Khác meta.types: có CẢ loại đã tắt + số đơn đang dùng. HR User gọi → 403. */
export const fetchServiceConfig = () => hbGet(`${BASE}/config/types`);

/* Thêm (không có id) hoặc sửa (có id) một loại. Chỉ gửi key nào muốn đổi —
   BE patch từng phần. → nguyên payload cấu hình mới (khỏi gọi lại).
   Mã lỗi: name_required · code_required · code_invalid · code_duplicate ·
   sla_invalid · scope_invalid · type_invalid; riêng BR-SVC-09 (ẩn danh +
   đính kèm) và BR-SVC-01 về từ @api.constrains nên chỉ có `message`. */
export const saveRequestType = (payload) =>
  hbPost(`${BASE}/config/types/save`, payload);

/* Bật/tắt loại. Tắt = ẩn khỏi form gửi, KHÔNG đụng đơn đang chạy.
   Lỗi last_active_type khi cố tắt loại cuối cùng còn bật. */
export const toggleRequestType = (id, active) =>
  hbPost(`${BASE}/config/types/toggle-active`, { id, active });

/* 2 ngưỡng ẩn danh (BR-SVC-03 / BR-SVC-12), 1..999. Lỗi: param_invalid. */
export const saveServiceParams = (params) =>
  hbPost(`${BASE}/config/params`, params);
