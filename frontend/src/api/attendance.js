/* API domain Attendance — Hoàng Anh.
   Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md */
import { hbGet, hbPost } from './client';

export const fetchMyAttendance = () => hbGet('/hocba-hrm/api/attendance/me');
export const fetchAttendanceDay = (date) =>
  hbGet(`/hocba-hrm/api/attendance?date=${date}`);
export const fetchMyHistory = (month) =>
  hbGet(`/hocba-hrm/api/attendance/me/history?month=${month}`);
export const fetchMyHistoryFull = (month, type) =>
  hbGet(`/hocba-hrm/api/attendance/me/history-full?month=${month}&type=${type}`);
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

export const fetchOtTable = (month) =>
  hbGet(`/hocba-hrm/api/shifts/ot?month=${month}`);
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

export const fetchManagerSummary = (month) =>
  hbGet(`/hocba-hrm/api/attendance/manager-summary?month=${month}`);
export const fetchEmpHistory = (empId, month, type) =>
  hbGet(`/hocba-hrm/api/attendance/emp-history?empId=${empId}&month=${month}&type=${type}`);

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
