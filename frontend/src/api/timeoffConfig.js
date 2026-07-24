/* API khu Cấu hình Time Off (chỉ Admin). Spec: docs/superpowers/specs/2026-07-22-timeoff-admin-config-center-design.md */
import { hbGet, hbPost } from './client';

const BASE = '/hocba-hrm/api/timeoff/config';

/* Danh sách loại nghỉ do Học Bá quản lý (cả active/inactive). → { leaveTypes: [...] } */
export const fetchLeaveTypes = () => hbGet(`${BASE}/leave-types`);

/* Tạo mới (không id) hoặc cập nhật (có id) một loại nghỉ. → { leaveType: {...} }
   payload: { id?, name, requiresAllocation, unpaid, validationType,
              requestUnit, supportDocument, isEmergency, color } */
export const saveLeaveType = (payload) =>
  hbPost(`${BASE}/leave-types/save`, payload);

/* Bật/tắt (archive) một loại nghỉ. → { leaveType: {...} } */
export const toggleLeaveType = (id, active) =>
  hbPost(`${BASE}/leave-types/toggle-active`, { id, active });

/* Chính sách theo loại NV (6 bản, chỉ sửa). → { policies, leaveTypeChoices, accrualPlanChoices, allocationModes } */
export const fetchPolicies = () => hbGet(`${BASE}/policies`);

/* Cập nhật 1 chính sách. → { policy: {...} }
   payload: { id, name, leaveTypeIds:[...], allocationMode, accrualPlanId, annualDays, notes } */
export const savePolicy = (payload) => hbPost(`${BASE}/policies/save`, payload);
