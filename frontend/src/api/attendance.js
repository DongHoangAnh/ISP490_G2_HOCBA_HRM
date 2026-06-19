/* API domain Attendance — Hoàng Anh.
   Spec: docs/superpowers/specs/2026-06-13-attendance-spa-screen-design.md */
import { hbGet, hbPost } from './client';

export const fetchMyAttendance = () => hbGet('/hocba-hrm/api/attendance/me');
export const fetchAttendanceDay = (date) =>
  hbGet(`/hocba-hrm/api/attendance?date=${date}`);
export const fetchMyHistory = (month) =>
  hbGet(`/hocba-hrm/api/attendance/me/history?month=${month}`);
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

export const fetchWeekShifts = (monday) =>
  hbGet(`/hocba-hrm/api/shifts/week?monday=${monday}`);
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
