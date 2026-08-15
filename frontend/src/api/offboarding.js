/* API domain Nghỉ việc (offboarding) — Vu/Tan.
   Spec: docs/superpowers/specs/2026-07-05-offboarding-spa-design.md */
import { hbGet, hbPost } from './client';

/* { isOfficer, isEmployee, mine:[...], managed:[...] } */
export const fetchOffboarding = () => hbGet('/hocba-hrm/api/offboarding/list');

/* Số đơn chính mình bấm được (duyệt / hoàn tất) — badge cạnh "Nghỉ việc" ở
   thanh menu. Chỉ đếm, và trả {canAct:false, count:0} thay vì 403. */
export const fetchOffbPendingCount = () =>
  hbGet('/hocba-hrm/api/offboarding/pending-count');

/* NV tự nộp đơn. payload: { reasonType, reason, expectedLeaveDate } */
export const submitOffboarding = (payload) =>
  hbPost('/hocba-hrm/api/offboarding/submit', payload);

/* action ∈ mgr_approve | hr_approve | done | refuse | cancel */
export const offboardingAction = (id, action) =>
  hbPost('/hocba-hrm/api/offboarding/action', { id, action });
