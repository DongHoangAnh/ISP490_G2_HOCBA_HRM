/* API quy trình nhận việc bước động — Tân.
   Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md */
import { hbGet, hbPost } from './client';

/* Config template (chỉ HR Manager — 403 với vai trò khác). */
export const fetchOnbTemplates = () => hbGet('/hocba-hrm/api/onboarding/templates');
export const createOnbTemplate = (payload) =>
  hbPost('/hocba-hrm/api/onboarding/templates', payload);
export const updateOnbTemplate = (id, payload) =>
  hbPost(`/hocba-hrm/api/onboarding/templates/${id}`, payload);
export const assignPendingOnb = () =>
  hbPost('/hocba-hrm/api/onboarding/templates/assign-pending', {});

/* Vận hành bước — mỗi call trả item NV đã refresh (steps + progress). */
export const completeOnbStep = (stepId, payload = {}) =>
  hbPost(`/hocba-hrm/api/onboarding/steps/${stepId}/complete`, payload);
export const evaluateOnbStep = (stepId, payload) =>
  hbPost(`/hocba-hrm/api/onboarding/steps/${stepId}/evaluate`, payload);
export const setOnbStepDue = (stepId, dueDate) =>
  hbPost(`/hocba-hrm/api/onboarding/steps/${stepId}/due`, { dueDate });
export const assignOnbTemplate = (empId, templateId) =>
  hbPost(`/hocba-hrm/api/employees/${empId}/onboarding/assign`, { templateId });
