/* API Lộ trình sự nghiệp + Bảng vinh danh (họp khách 2026-08-07, ý C & D).
   Spec: docs/superpowers/specs/2026-08-09-career-dashboard-honor-board-design.md */
import { hbGet, hbPost } from './client';

/* empId = 0 → lộ trình của chính mình. */
export const fetchCareer = (empId = 0) =>
  hbGet(`/hocba-hrm/api/career/${empId || 0}`);

export const fetchHonorBoard = () => hbGet('/hocba-hrm/api/honor/board');

export const createHonorEntry = (payload) =>
  hbPost('/hocba-hrm/api/honor/entry', payload);

export const archiveHonorEntry = (entryId) =>
  hbPost(`/hocba-hrm/api/honor/entry/${entryId}/archive`, {});
