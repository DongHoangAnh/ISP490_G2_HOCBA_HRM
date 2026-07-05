/* API domain Nghỉ việc (offboarding) — Vu/Tan.
   Spec: docs/superpowers/specs/2026-07-05-offboarding-spa-design.md */
import { hbGet, hbPost } from './client';

/* { isOfficer, isEmployee, mine:[...], managed:[...] } */
export const fetchOffboarding = () => hbGet('/hocba-hrm/api/offboarding/list');

/* NV tự nộp đơn. payload: { reasonType, reason, expectedLeaveDate } */
export const submitOffboarding = (payload) =>
  hbPost('/hocba-hrm/api/offboarding/submit', payload);

/* action ∈ mgr_approve | hr_approve | done | refuse | cancel */
export const offboardingAction = (id, action) =>
  hbPost('/hocba-hrm/api/offboarding/action', { id, action });
