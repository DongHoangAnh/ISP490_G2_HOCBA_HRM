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
export const createEmployee = (payload) => hbPost('/hocba-hrm/api/employees', payload);
export const updateEmployee = (id, payload) =>
  hbPost(`/hocba-hrm/api/employee/${id}`, payload);
