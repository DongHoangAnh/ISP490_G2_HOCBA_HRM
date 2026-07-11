# Design: Màn hình Lịch sử chấm công của tôi

**Ngày:** 2026-06-19  
**Trạng thái:** Approved

---

## Tổng quan

Tách `MyHistory` ra khỏi tab "Chấm công của tôi" và nâng lên thành tab riêng **"Lịch sử chấm công"** trong `Attendance.jsx`. Tab mới có bộ lọc theo loại công (Thường / OT / Tất cả cho nhân viên chính thức; Công CTV cho CTV).

---

## Kiến trúc

### Thay đổi tab trong `Attendance.jsx`

**Nhân viên thường (non-manager), sau khi thêm:**
```
['me', 'Chấm công của tôi']
['history', 'Lịch sử chấm công']   ← MỚI
['shift', shiftTabLabel]
['requests', 'Đơn của tôi']
['ot', 'Ca làm việc (CTV/OT)']
```

**Tab `'me'` sau khi tách:**  
Giữ nguyên `CheckInPanel` + `MyHistory` (công thường tháng hiện tại, không có filter). `MyHistory` trong tab này không thay đổi — chỉ bổ sung tab `'history'` riêng.

### Component mới: `AttendanceHistory.jsx`

Thay thế vai trò của `MyHistory` khi cần xem đầy đủ với filter. Render bên trong tab `'history'`.

```
AttendanceHistory
├── FilterTabs (Thường / OT / Tất cả | Công CTV)
├── SummaryBar (tính theo filter đang chọn)
└── HistoryTable (9 cột, dùng lại AttendanceDrawer khi click)
```

---

## API

### Endpoint mới

```
GET /hocba-hrm/api/attendance/me/history-full
    ?month=YYYY-MM
    &type=all|regular|ot|ctv
```

### Nguồn dữ liệu theo `type`

| type | Nguồn | Ai dùng |
|---|---|---|
| `regular` | `hocba.attendance` | Chính thức |
| `ot` | `hocba.work_shift` (shift_type='ot') + `hocba.shift.attendance` | Chính thức |
| `all` | Gộp regular + ot, sort theo ngày desc | Chính thức |
| `ctv` | `hocba.work_shift` (shift_type='ctv') + `hocba.shift.attendance` | CTV |

### Cấu trúc 1 dòng trả về (thống nhất)

```json
{
  "id": 123,
  "date": "2026-06-19",
  "checkIn": "2026-06-19T08:00:00",
  "checkOut": "2026-06-19T17:00:00",
  "workingHours": 9.0,
  "lateMinutes": 0,
  "earlyLeaveMinutes": 0,
  "missingMinutes": 0,
  "workCredit": 1.0,
  "statusKey": "on_time",
  "rowType": "regular|ot|ctv",
  "shiftLabel": null
}
```

**Lưu ý:**
- Dòng OT/CTV: `lateMinutes`, `earlyLeaveMinutes`, `missingMinutes` so sánh với `shift.start` / `shift.end` (không phải 9:30 / 8h chuẩn)
- `shiftLabel`: tên ca hiển thị khi hover, ví dụ `"OT 150% · 18:00–22:00"`
- `rowType`: dùng để hiện badge phân biệt khi filter `all`

### Hàm backend mới

```python
# controllers/main.py
def _att_me_history_full(env, month_str, att_type):
    emp = env.user.employee_id
    rows = []
    if att_type in ('regular', 'all'):
        rows += [_att_row(r, policy) | {'rowType': 'regular', 'shiftLabel': None}
                 for r in hocba.attendance.search(...)]
    if att_type in ('ot', 'all'):
        rows += [_shift_att_row(s, att) | {'rowType': 'ot'}
                 for s in hocba.work_shift.search([..., ('shift_type','=','ot')])]
    if att_type == 'ctv':
        rows += [_shift_att_row(s, att) | {'rowType': 'ctv'}
                 for s in hocba.work_shift.search([..., ('shift_type','=','ctv')])]
    rows.sort(key=lambda r: r['date'], reverse=True)
    return {'month': month_str, 'summary': _summarize(rows), 'rows': rows}
```

---

## UI

### Filter tabs

```
Chính thức:  [ Tất cả ]  [ Thường ]  [ OT ]
CTV:         [ Công CTV ]   ← không có filter, chỉ 1 tab
```

- Detect loại nhân viên từ `me.employmentStatus` (đã có trong API `/me`)
- Mặc định chọn `Tất cả` (chính thức) hoặc `Công CTV` (CTV) khi vào trang

### Bảng — 9 cột giữ nguyên

| Ngày | Check-in | Check-out | Giờ công | Đi trễ | Về sớm | Thiếu | Ngày công | Trạng thái |
|---|---|---|---|---|---|---|---|---|

- Khi filter `Tất cả`: badge nhỏ trên cột Ngày phân biệt `Thường` / `OT`
- Hover vào Ngày của dòng OT/CTV: tooltip hiện `shiftLabel`
- Click dòng → mở `AttendanceDrawer` (dùng lại, không thay đổi)

### Summary bar

Tính lại theo filter đang chọn:
- Filter `Thường`: tổng công thường, công thiếu
- Filter `OT`: tổng giờ OT, công OT
- Filter `Tất cả`: gộp cả hai
- Filter `Công CTV`: tổng giờ CTV, công CTV

---

## Các file thay đổi

### Frontend
| File | Thay đổi |
|---|---|
| `frontend/src/features/attendance/Attendance.jsx` | Thêm tab `'history'`, render `AttendanceHistory` |
| `frontend/src/features/attendance/AttendanceHistory.jsx` | **Tạo mới** — filter tabs + bảng |
| `frontend/src/api/attendance.js` | Thêm `fetchMyHistoryFull(month, type)` |

### Backend
| File | Thay đổi |
|---|---|
| `custom-addons/hocba_hrm/controllers/main.py` | Thêm `_att_me_history_full()` và route `history-full` |

---

## Không thay đổi

- `MyHistory.jsx` — giữ nguyên trong tab `'me'` (công thường, không filter)
- `AttendanceDrawer.jsx` — dùng lại không sửa
- `hocba.attendance` model — không sửa
- `hocba.work_shift` / `hocba.shift.attendance` model — không sửa
