/* API domain Employees — Tân. Spec: docs/SPEC_HRM_SPA_API.md §3 */
import { hbGet, hbPost } from './client';

export const fetchEmployees = () => hbGet('/hocba-hrm/api/employees');
export const fetchEmployee = (id) => hbGet(`/hocba-hrm/api/employee/${id}`);
export const fetchCertAlerts = () => hbGet('/hocba-hrm/api/employees/cert-alerts');
export const fetchOnboarding = () => hbGet('/hocba-hrm/api/employees/onboarding');
export const fetchMe = () => hbGet('/hocba-hrm/api/me');
/* Danh tính + cờ vai trò (nhẹ) để dựng nav theo vai trò (tách tài khoản — họp #2). */
export const fetchRoles = () => hbGet('/hocba-hrm/api/me/roles');
/* Nhân viên tự cập nhật liên hệ + địa chỉ của chính mình. */
export const updateMe = (payload) => hbPost('/hocba-hrm/api/me', payload);
/* Nhân viên tự cập nhật ảnh đại diện của mình (base64). */
export const updateMyPhoto = (image) => hbPost('/hocba-hrm/api/me/photo', { image });

/* (postGate/postTrial cũ đã gỡ — đánh giá thử việc chuyển sang bước động,
   xem api/onboarding.js.) */

/* Form Thêm/Sửa nhân viên (chỉ HR). */
export const fetchFormMeta = () => hbGet('/hocba-hrm/api/form/meta');
export const fetchDependentMeta = () => hbGet('/hocba-hrm/api/dependent/meta');

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

/* Tài sản (F-006 rút gọn) — cấp / gỡ inline (chỉ HR). Không còn thu hồi/chuyển giao. */
export const createAsset = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/asset`, payload);
export const deleteAsset = (assetId) =>
  hbPost(`/hocba-hrm/api/asset/${assetId}/delete`, {});

/* Thăng tiến (F-007) — thêm mốc thăng tiến inline (chỉ HR Manager). */
export const createPromotion = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/promotion`, payload);

/* Chứng chỉ (F-008) — thêm/sửa/xác minh/xoá inline (chỉ HR). */
export const createCert = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/cert`, payload);
export const updateCert = (certId, payload) =>
  hbPost(`/hocba-hrm/api/cert/${certId}`, payload);
export const verifyCert = (certId, verified) =>
  hbPost(`/hocba-hrm/api/cert/${certId}/verify`, { verified });
export const deleteCert = (certId) =>
  hbPost(`/hocba-hrm/api/cert/${certId}/delete`, {});

/* Tài khoản đăng nhập (chỉ HR/Admin). createAccount/resetAccountPassword trả
   khối account đã cập nhật; fetchAccounts trả { accounts, departments }. */
export const createAccount = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/account`, payload);
export const resetAccountPassword = (empId, payload) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/account/reset`, payload);
export const fetchAccounts = () => hbGet('/hocba-hrm/api/accounts');
/* active PHẢI là boolean thật — BE từ chối chuỗi vì bool('false') là true. */
export const setAccountActive = (empId, active) =>
  hbPost(`/hocba-hrm/api/employee/${empId}/account/active`, { active: !!active });

/* Dashboard đánh giá thăng tiến — lấy danh sách đánh giá của NV + lưu đánh giá mới. */
export const fetchEvaluations = (empId) => hbGet(`/hocba-hrm/api/promotion/eval/${empId}`);
export const saveEvaluation = (payload) => hbPost('/hocba-hrm/api/promotion/eval/save', payload);
