/* API domain Phòng ban (chỉ HR/Admin) — Owner: Tân.
   Spec: docs/superpowers/specs/2026-06-22-department-management-design.md */
import { hbGet, hbPost } from './client';

export const fetchDepartments = (archived = false) =>
  hbGet(`/hocba-hrm/api/departments${archived ? '?archived=1' : ''}`);
export const createDepartment = (payload) =>
  hbPost('/hocba-hrm/api/department', payload);
export const updateDepartment = (id, payload) =>
  hbPost(`/hocba-hrm/api/department/${id}`, payload);
export const archiveDepartment = (id, active) =>
  hbPost(`/hocba-hrm/api/department/${id}/archive`, { active });
