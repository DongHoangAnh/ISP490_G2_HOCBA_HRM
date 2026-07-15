/* API Dashboard — KPI + dữ liệu biểu đồ theo tab (Tổng quan/Tuyển dụng/
   Chấm công/Nghỉ phép/Lương). Tab hiển thị theo cờ `tabs` trong stats.
   Spec: docs/superpowers/specs/SPEC_DASHBOARD_HR_OVERVIEW.md */
import { hbGet } from './client';

export const fetchDashboardStats = () => hbGet('/hocba-hrm/api/dashboard/stats');
export const fetchDashboardRecruitment = () => hbGet('/hocba-hrm/api/dashboard/recruitment');
export const fetchDashboardAttendance = () => hbGet('/hocba-hrm/api/dashboard/attendance');
export const fetchDashboardTimeoff = () => hbGet('/hocba-hrm/api/dashboard/timeoff');
export const fetchDashboardPayroll = () => hbGet('/hocba-hrm/api/dashboard/payroll');
