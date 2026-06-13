/* API domain Employees — Tân. Spec: docs/SPEC_HRM_SPA_API.md §3 */
import { hbGet } from './client';

export const fetchEmployees = () => hbGet('/hocba-hrm/api/employees');
export const fetchEmployee = (id) => hbGet(`/hocba-hrm/api/employee/${id}`);
export const fetchCertAlerts = () => hbGet('/hocba-hrm/api/employees/cert-alerts');
export const fetchOnboarding = () => hbGet('/hocba-hrm/api/employees/onboarding');
