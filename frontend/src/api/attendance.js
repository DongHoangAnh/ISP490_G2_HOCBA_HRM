/* API domain Attendance — Hoàng Anh.
   Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md */
import { hbGet, hbPost } from './client';

export const fetchMyAttendance = () => hbGet('/hocba-hrm/api/attendance/me');
export const fetchAttendanceDay = (date) =>
  hbGet(`/hocba-hrm/api/attendance?date=${date}`);
export const fetchMyHistory = (month, from, to) => {
  let url = `/hocba-hrm/api/attendance/me/history?`;
  if (from && to) url += `dateFrom=${from}&dateTo=${to}`;
  else url += `month=${month}`;
  return hbGet(url);
};
export const fetchMyHistoryFull = (month, type, from, to) => {
  let url = `/hocba-hrm/api/attendance/me/history-full?type=${type}&`;
  if (from && to) url += `dateFrom=${from}&dateTo=${to}`;
  else url += `month=${month}`;
  return hbGet(url);
};
export const enrollFace = (photo, descriptor) =>
  hbPost('/hocba-hrm/api/attendance/enroll', { photo, descriptor });
export const checkIn = (payload) =>
  hbPost('/hocba-hrm/api/attendance/check-in', payload);
export const checkOut = (payload) =>
  hbPost('/hocba-hrm/api/attendance/check-out', payload);
export const editAttendance = (id, body) =>
  hbPost(`/hocba-hrm/api/attendance/${id}`, body);
export const deleteAttendance = (id) =>
  hbPost(`/hocba-hrm/api/attendance/${id}/delete`, {});

export const createRequest = (body) =>
  hbPost('/hocba-hrm/api/attendance/requests', body);
export const fetchMyRequests = () =>
  hbGet('/hocba-hrm/api/attendance/requests/mine');
export const fetchPendingRequests = () =>
  hbGet('/hocba-hrm/api/attendance/requests/pending');
export const fetchAttendancePendingCount = () =>
  hbGet('/hocba-hrm/api/attendance/pending-count');
export const approveRequest = (id, body) =>
  hbPost(`/hocba-hrm/api/attendance/requests/${id}/approve`, body);
export const rejectRequest = (id, body) =>
  hbPost(`/hocba-hrm/api/attendance/requests/${id}/reject`, body);

export const fetchWeekShifts = (monday, type) =>
  hbGet(`/hocba-hrm/api/shifts/week?monday=${monday}${type ? `&type=${type}` : ''}`);
export const createShift = (body) =>
  hbPost('/hocba-hrm/api/shifts', body);
export const approveShift = (id, body) =>
  hbPost(`/hocba-hrm/api/shifts/${id}/approve`, body);
export const rejectShift = (id, body) =>
  hbPost(`/hocba-hrm/api/shifts/${id}/reject`, body);
export const cancelShift = (id) =>
  hbPost(`/hocba-hrm/api/shifts/${id}/cancel`, {});

export const fetchOtTable = (month, from, to) => {
  let url = `/hocba-hrm/api/shifts/ot?`;
  if (from && to) url += `dateFrom=${from}&dateTo=${to}`;
  else url += `month=${month}`;
  return hbGet(url);
};
export const setShiftLevel = (id, otLevel) =>
  hbPost(`/hocba-hrm/api/shifts/${id}/level`, { otLevel });

export const shiftCheckIn = (shiftId, payload) =>
  hbPost(`/hocba-hrm/api/attendance/shift/${shiftId}/check-in`, payload);
export const shiftCheckOut = (shiftId, payload) =>
  hbPost(`/hocba-hrm/api/attendance/shift/${shiftId}/check-out`, payload);

export const searchEmployees = (q) =>
  hbGet(`/hocba-hrm/api/employees/search?q=${encodeURIComponent(q)}`);
export const previewRequest = (id, body) =>
  hbPost(`/hocba-hrm/api/attendance/requests/${id}/preview`, body);

export const fetchManagerSummary = (month, from, to, role) => {
  let url = `/hocba-hrm/api/attendance/manager-summary?`;
  if (role) url += `role=${role}&`;
  if (from && to) url += `dateFrom=${from}&dateTo=${to}`;
  else url += `month=${month}`;
  return hbGet(url);
};
export const fetchEmpHistory = (empId, month, type, from, to) => {
  let url = `/hocba-hrm/api/attendance/emp-history?empId=${empId}&type=${type}&`;
  if (from && to) url += `dateFrom=${from}&dateTo=${to}`;
  else url += `month=${month}`;
  return hbGet(url);
};

export const fetchAttendanceConfig = () => hbGet('/hocba-hrm/api/attendance/config');
export const saveAttendanceConfig = (body) => hbPost('/hocba-hrm/api/attendance/config', body);

// Teaching schedule (giáo viên — lịch từ CMS)
export const fetchTeachingSchedule = (date) =>
  hbGet(`/hocba-hrm/api/teaching/schedule?date=${date}`);
export const fetchTeachingWeek = (monday) =>
  hbGet(`/hocba-hrm/api/teaching/schedule?monday=${monday}`);
// Các ngày có lịch dạy trong khoảng [from, to] (đánh dấu trên tab "Lịch").
export const fetchTeachingDays = (from, to) =>
  hbGet(`/hocba-hrm/api/teaching/days?from=${from}&to=${to}`);
export const teachingCheckIn = (sessionId, payload) =>
  hbPost(`/hocba-hrm/api/teaching/sessions/${sessionId}/check-in`, payload);
export const teachingCheckOut = (sessionId, payload) =>
  hbPost(`/hocba-hrm/api/teaching/sessions/${sessionId}/check-out`, payload);
