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
