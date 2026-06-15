/* API domain Employees — Tân. Spec: docs/SPEC_HRM_SPA_API.md §3 */
import { hbGet, hbPost } from './client';

export const fetchEmployees = () => hbGet('/hocba-hrm/api/employees');
export const fetchEmployee = (id) => hbGet(`/hocba-hrm/api/employee/${id}`);
export const fetchCertAlerts = () => hbGet('/hocba-hrm/api/employees/cert-alerts');
export const fetchOnboarding = () => hbGet('/hocba-hrm/api/employees/onboarding');
export const fetchMe = () => hbGet('/hocba-hrm/api/me');
/* Nhân viên tự cập nhật liên hệ + địa chỉ của chính mình. */
export const updateMe = (payload) => hbPost('/hocba-hrm/api/me', payload);

/* Đánh giá cổng thử việc (F-004/005). gate: '2w'|'2m', result: 'pass'|'fail'.
   Trả về hồ sơ chi tiết đã cập nhật (status có thể đổi sang official/exiting). */
export const postGate = (id, payload) =>
  hbPost(`/hocba-hrm/api/employee/${id}/gate`, payload);

/* Form Thêm/Sửa nhân viên (chỉ HR). */
export const fetchFormMeta = () => hbGet('/hocba-hrm/api/form/meta');

/* Người phụ thuộc (F-003) — CRUD inline, chỉ HR. Mỗi thao tác trả hồ sơ mới. */
export const createDependent = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/dependent`, payload);
export const updateDependent = (depId, payload) =>
  hbPost(`/hocba-hrm/api/dependent/${depId}`, payload);
export const deleteDependent = (depId) =>
  hbPost(`/hocba-hrm/api/dependent/${depId}/delete`, {});
export const createEmployee = (payload) => hbPost('/hocba-hrm/api/employees', payload);
export const updateEmployee = (id, payload) =>
  hbPost(`/hocba-hrm/api/employee/${id}`, payload);

/* Tài sản (F-006) — cấp / thu hồi / chuyển giao inline (chỉ HR). */
export const createAsset = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/asset`, payload);
export const returnAsset = (assetId, payload) =>
  hbPost(`/hocba-hrm/api/asset/${assetId}/return`, payload);
export const transferAsset = (assetId, payload) =>
  hbPost(`/hocba-hrm/api/asset/${assetId}/transfer`, payload);

/* Thăng tiến (F-007) — thêm mốc thăng tiến inline (chỉ HR Manager). */
export const createPromotion = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/promotion`, payload);
