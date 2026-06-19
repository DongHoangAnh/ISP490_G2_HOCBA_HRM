# Attendance — OT/CTV scheduling, time-gated review, and correction requests

**Date:** 2026-06-19
**Module:** `hocba_attendance` (models) + `hocba_hrm` (controllers/API) + `frontend/` (React SPA)
**Status:** Approved design — ready for implementation planning

## Context

The attendance feature is a React SPA (`frontend/src/features/attendance/`) backed by JSON
routes in `custom-addons/hocba_hrm/controllers/main.py`, over four models in
`hocba_attendance`:

- `hocba.work_shift` — OT/CTV shift registration (`employee_id`, `start`, `end`,
  `shift_type` ∈ {ot, ctv}, `ot_level`, `rate`, `state` ∈ {pending, approved, rejected},
  `reviewer_id`, `review_note`, `decision_date`).
- `hocba.shift.attendance` — check-in/out records for an approved shift.
- `hocba.attendance` — daily attendance for official employees, with computed metrics
  (`working_hours`, `expected_check_out`, `late_minutes`, `early_leave_minutes`,
  `missing_minutes`, `morning_credit`, `afternoon_credit`, `work_credit`, `needs_review`).
- `hocba.attendance.request` — correction / "quên chấm công" requests
  (`proposed_check_in`, `proposed_check_out`, `reason`, `state`, `attendance_id`).

CTV vs regular employees are distinguished by `hr.employee.x_employment_status` (value
`'ctv'`). Employee code is `hr.employee.x_employee_code` (unique).

## Goals

1. OT screen shows employee name + đơn type (OT/CTV); managers can filter by OT or CTV.
2. Visibility by shift type: regular employees see all OT shifts; CTV see all CTV shifts;
   managers see everything.
3. OT/CTV registrations remain reviewable/editable/rejectable (even after approval) until a
   time deadline; expired pending registrations are auto-rejected.
4. Managers can add an OT/CTV shift for any employee, found by employee code.
5. "Quên chấm công" correction requests can only be submitted from an existing attendance
   history record; on approval the manager edits check-in/out only and all derived fields
   recompute.
6. Missing-minutes (`phút thiếu`) capped at 240; basis is 4h for a half-day (`công ngày` 0.5),
   else 8h.

## Locked decisions (from brainstorming)

- **Visibility is by shift type** (`shift_type`), not by employee class of the viewer.
- **Deadline = `shift.start − 1 minute`**, purely time-based (unrelated to check-in). A
  pending shift not approved before the deadline is auto-rejected. Approved shifts are locked
  (no edit/reject) once the deadline passes.
- **Correction requests only from existing records** — no arbitrary-date / absent-day
  submission. The standalone date-picker mode of `RequestForm` is removed.
- **Manager edits check-in/out only** on a correction request; every other field recomputes.
- **Auto-reject = Hybrid (approach C)**: lazy-on-read + `ir.cron` backstop + hard server-side
  action guard.

---

## Section 1 — Data model changes

### `hocba.work_shift`

- `deadline` (Datetime, **computed, stored**, `@api.depends('start')`) = `start − timedelta(minutes=1)`.
  Single source of truth for whether the shift is still actionable.
- `is_locked` (Boolean, computed, **not stored**) = `now ≥ deadline`. For UI button enablement.
- New model method `_auto_reject_expired(self, domain=None)`:
  - Builds domain `[('state', '=', 'pending'), ('deadline', '<', now)]` (AND-ed with `domain`
    if provided).
  - Sets `state='rejected'`, `review_note='Tự động từ chối: quá hạn duyệt'`, `decision_date=now`.
  - Returns the recordset rejected (for logging/telemetry).
- New method `_assert_actionable(self)`: raises `UserError("Đã quá hạn thao tác với ca này
  (trước giờ bắt đầu 1 phút).")` if `now >= deadline`. Used by mutating routes.

No change to `state`, `shift_type`, `ot_level`, `rate`, `reviewer_id`, `review_note`,
`decision_date`.

### `hocba.attendance.request`

No schema change. Manager-editable fields stay `proposed_check_in` / `proposed_check_out`.
On approval the target `hocba.attendance` recomputes derived fields (no override columns).

### `hocba.attendance._compute_work_metrics` (logic change only)

Current order computes `missing_minutes` before `work_credit`. Reorder so credits are known
first:

1. Compute `morning_credit`, `afternoon_credit`, then `work_credit = morning + afternoon`.
2. `basis_hours = (std / 2.0) if work_credit == 0.5 else std` (where `std = policy.std_work_hours or 8.0`).
3. `missing_minutes = max(0, min(240, int(round(basis_hours * 60 - worked_min))))`.
4. When `work_credit == 0` (no credit / absent), keep `missing_minutes = 0` as today.

`expected_check_out`, `late_minutes`, `early_leave_minutes`, `afternoon_credit` logic
otherwise unchanged.

---

## Section 2 — Visibility & scoping (backend, `hocba_hrm` controllers)

Shared helper `_shift_scope_domain(env, type_filter=None)`:

- **Manager** (`env.user.has_group('hr.group_hr_manager')`): no `shift_type` restriction.
  If `type_filter` ∈ {'ot', 'ctv'} is passed (filter toggle), AND `[('shift_type', '=', type_filter)]`.
- **CTV** (`env.user.employee_id.x_employment_status == 'ctv'`): force `[('shift_type', '=', 'ctv')]`.
- **Everyone else**: force `[('shift_type', '=', 'ot')]`.

Applied to shift list/read routes (`/shifts/week`, `/shifts/ot`, and any shift detail), replacing
the current per-user `employee_id` scoping on the OT screen. Each serialized row (`_shift_row`)
adds:

- `employeeName` (from `employee_id.name`)
- `shiftTypeLabel` ("OT" / "CTV")
- `mine` (boolean: `shift.employee_id == env.user.employee_id`) for UI highlighting.

`shiftType` filter query param accepted on `/shifts/week` and `/shifts/ot` for managers.

---

## Section 3 — Time-gated approve / edit / reject (backend)

Guard helper `_assert_shift_actionable(shift)` (controller-level wrapper around
`shift._assert_actionable()`): called at the top of every mutating shift route — approve,
reject, edit (start/end/shift_type/ot_level), and the manager OT-level change endpoint.
Applies to both pending and approved shifts.

Lazy pass: before serving any shift list/detail and before any approve action, call
`env['hocba.work_shift'].sudo()._auto_reject_expired(scope_domain)` so expired pendings flip to
rejected immediately for whoever is looking.

Cron backstop: `ir.cron` record "Tự động từ chối ca quá hạn", `interval_number=5`,
`interval_type='minutes'`, model `hocba.work_shift`, calls `model._auto_reject_expired()`
(model-wide, no domain). Defined in `data/` and added to `__manifest__.py`.

---

## Section 4 — Manager adds shift for anyone (by employee code)

- New route `GET /hocba-hrm/api/employees/search?q=` (manager-only; returns `[]` for
  non-managers). Searches `hr.employee` where `x_employee_code ILIKE q OR name ILIKE q`,
  limit ~20, returns `[{id, code, name, employmentStatus}]`.
- `ShiftForm.jsx`: when `canManage`, render an employee autocomplete at the top (search by
  code or name → select). The selected employee id is submitted as the shift owner. The rest
  of the form (start/end, shiftType, otLevel, reason) is identical to self-registration.
- Manager-created shifts: `state='approved'` (existing behavior). `shift_type` is whatever the
  manager selected in the form (consistent with by-shift-type visibility — it is not inferred
  from the target's `x_employment_status`).
- `_shift_create` accepts `employeeId` only from managers; for non-managers it stays pinned to
  `env.user.employee_id` (existing behavior).

---

## Section 5 — Correction request only from history records (frontend + backend)

- `RequestForm.jsx`: remove the standalone "forgot completely / pick any date" mode. The
  component now requires an `attendanceId` + `requestDate` (always supplied by
  `AttendanceDrawer` → "Gửi đơn sửa"). The free date picker and the no-record path are deleted.
- Remove/disable any UI entry point (tab/button) that opened `RequestForm` without an
  `attendanceId`.
- `_request_create` (backend): require a valid `attendance_id` belonging to the caller; reject
  requests without one.
- Manager approval UI in `RequestList.jsx`: editable `proposed_check_in` / `proposed_check_out`
  plus **read-only recomputed previews** of `working_hours` (giờ công), `work_credit` (công ngày),
  `expected_check_out` (giờ ra mong đợi), `early_leave_minutes` (về sớm), `missing_minutes`
  (phút thiếu), `needs_review` (cờ kiểm tra). On approve, backend writes check-in/out to the
  `hocba.attendance` record; compute methods fill the rest. The preview is served by a backend
  dry-run helper — `GET /hocba-hrm/api/attendance/requests/<id>/preview?checkIn=&checkOut=`
  builds a transient `hocba.attendance` (or `new()` record), runs the same compute methods, and
  returns the derived values — so the preview is guaranteed to match what approval will save
  (single source of truth, no duplicated formula on the client).

---

## Testing strategy

- **Model unit tests** (`hocba_attendance/tests/`):
  - `_auto_reject_expired` rejects only pending shifts past deadline; leaves approved/rejected
    and future-pending untouched.
  - `_assert_actionable` raises after deadline, passes before.
  - `deadline` = start − 1 min.
  - `missing_minutes`: full-day basis 8h, half-day (work_credit 0.5) basis 4h, cap 240,
    zero when work_credit 0.
- **Controller/API tests**: `_shift_scope_domain` for manager (all + filter), CTV (ctv only),
  regular (ot only); employee search manager-gated; correction request rejected without
  `attendance_id`; approve/edit/reject blocked after deadline.
- **Manual/SPA**: OT screen shows name + type + filter; manager add-for-anyone flow; correction
  request only reachable from a history record; manager approval preview matches saved values.

## Out of scope

- No change to face/geofence check-in logic.
- No new override columns on `hocba.attendance` (recompute-only per decision #4).
- No change to OT pay (`otpay`) calculations beyond the missing-minutes formula.
