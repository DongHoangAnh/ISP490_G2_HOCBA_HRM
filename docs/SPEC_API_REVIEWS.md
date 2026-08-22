# API Đánh giá nhân viên — `/hocba-hrm/api/reviews/*`

Module `hocba_reviews` · Owner: Việt · Controller:
`custom-addons/hocba_reviews/controllers/main.py`

Quy ước chung (theo [QUY_UOC_FRONTEND.md](QUY_UOC_FRONTEND.md)): payload và
response **camelCase**, ngày dạng ISO `YYYY-MM-DD`, lỗi trả
`{"error": "<mã>", "message": "<thông điệp người đọc>"}`.

Mã lỗi dùng chung: `forbidden` (403), `not_found` (404), `bad_request` (400),
`rejected` (400 — nghiệp vụ từ chối, ví dụ chốt phiếu thiếu điểm).

## Phân quyền

| Nhóm | Phạm vi |
|---|---|
| `base.group_system`, `hr.group_hr_manager`, `hr.group_hr_user` | Mọi nhân viên |
| Trưởng phòng (`hr.department.manager_id`) | Phòng mình + phòng con |
| `hocba_employees.group_hocba_giaovu` | Chỉ giáo viên |

Công bố (`publish`) và mở lại (`reset`) chỉ dành cho Admin/HR Manager.
Mở đợt hàng loạt chỉ dành cho HR/Admin.

---

## GET `/hocba-hrm/api/reviews`

Danh sách nhân sự của một nhóm kèm phiếu đánh giá của kỳ đang chọn.

**Query**: `group` = `teacher|office` · `periodType` = `quarter|half|year` ·
`year` (số) · `index` (số, 1..4 tuỳ loại kỳ)

**Response**

```json
{
  "canManage": true,
  "canPublish": true,
  "group": "teacher",
  "periodType": "quarter", "year": 2026, "index": 3,
  "rows": [
    {
      "id": 12, "empId": 45, "empName": "Nguyễn Thị A", "empCode": "HB.GV.045",
      "department": "Giảng viên", "jobTitle": "Giáo viên tiếng Trung",
      "roleGroup": "teacher", "periodLabel": "Quý 3/2026",
      "totalScore": 82.0, "grade": "b", "state": "confirmed",
      "punctualPct": 94.8, "totalUnits": 58
    }
  ],
  "criteria": [
    {"id": 3, "name": "Chất lượng giờ dạy", "code": "t_quality",
     "weight": 25.0, "maxScore": 5, "autoSource": "none", "guideline": "…"}
  ],
  "stats": {"employees": 169, "done": 12, "pending": 157,
            "avgScore": 78.4, "gradeA": 3, "gradeD": 1}
}
```

`state` = `none` (chưa có phiếu) · `draft` · `confirmed` · `published`.
`grade` = `a|b|c|d` (rỗng khi chưa có phiếu).

## GET `/hocba-hrm/api/reviews/<id>`

Chi tiết một phiếu. Ngoài các field ở `rows`, bổ sung:

```json
{
  "periodType": "quarter", "periodYear": 2026, "periodIndex": 3,
  "dateFrom": "2026-07-01", "dateTo": "2026-09-30",
  "selfNote": "", "managerNote": "", "hrNote": "",
  "evaluator": "Test HR Manager",
  "confirmedOn": null, "publishedOn": null,
  "canPublish": true,
  "metrics": {
    "totalUnits": 58, "okUnits": 55, "punctualPct": 94.8, "lateCount": 3,
    "leaveDays": 1.0, "certValid": 2, "certExpiring": 0, "certExpired": 0,
    "computedOn": "2026-07-26T10:12:00"
  },
  "lines": [
    {
      "id": 88, "criteriaId": 3, "name": "Chất lượng giờ dạy",
      "code": "t_quality", "guideline": "…", "weight": 25.0, "maxScore": 5,
      "score": 4.0, "autoScore": 0.0, "isAuto": false, "autoSource": "none",
      "manualOverride": false, "note": ""
    }
  ]
}
```

## POST `/hocba-hrm/api/reviews`

Tạo phiếu cho một nhân viên.

```json
{"employeeId": 45, "periodType": "quarter", "year": 2026, "index": 3}
```

Trả về chi tiết phiếu vừa tạo (đã sinh dòng chấm và tính sẵn chỉ số).
Trùng kỳ → `rejected` kèm thông điệp "Nhân viên đã có phiếu đánh giá cho kỳ này."

## POST `/hocba-hrm/api/reviews/<id>`

Lưu điểm và nhận xét. Chỉ chấp nhận khi phiếu ở trạng thái `draft`.

```json
{
  "lines": [{"id": 88, "score": 4, "note": "Giáo án tốt"}],
  "selfNote": "…", "managerNote": "…", "hrNote": "…"
}
```

Sửa điểm khác `autoScore` trên dòng tự động → backend tự bật `manualOverride`.
Trả về chi tiết phiếu sau khi lưu.

## POST `/hocba-hrm/api/reviews/<id>/action`

```json
{"action": "compute"}
```

| `action` | Tác dụng | Điều kiện |
|---|---|---|
| `compute` | Tính lại chỉ số + điểm đề xuất | Phiếu `draft` |
| `confirm` | Chốt phiếu | Có điểm > 0 và có `managerNote` |
| `publish` | Công bố + thông báo nhân viên | Phiếu `confirmed`, người dùng là HR/Admin |
| `reset` | Mở lại về `draft` | HR/Admin |

Trả về chi tiết phiếu sau hành động.

## POST `/hocba-hrm/api/reviews/bulk-open`

Mở đợt cho cả nhóm (idempotent — bỏ qua người đã có phiếu).

```json
{"group": "teacher", "periodType": "quarter", "year": 2026, "index": 3}
```

**Response**: `{"created": 165, "skipped": 4}`

---

# Cấu hình đánh giá — `/hocba-hrm/api/reviews/config*`

Màn **Cấu hình đánh giá** (SPA view `reviewsConfig`). Chỉ
`base.group_system` / `hr.group_hr_manager`; trưởng phòng và giáo vụ chấm điểm
được nhưng **không** đổi được bộ tiêu chí → `403 forbidden`.
Thiết kế: [spec](superpowers/specs/2026-08-21-reviews-config-design.md).

## GET `/hocba-hrm/api/reviews/config`

```json
{
  "canEdit": true,
  "groups": {
    "teacher": [{"id": 12, "name": "Chất lượng giờ dạy", "code": "t_quality",
                 "weight": 25.0, "maxScore": 5, "autoSource": "none",
                 "guideline": "…", "anchorTop": "…", "anchorMid": "…",
                 "anchorLow": "…", "active": true, "sequence": 10}],
    "office": []
  },
  "weightSum": {"teacher": 100.0, "office": 100.0},
  "draftCount": {"teacher": 3, "office": 0},
  "grades": {"a": 85.0, "b": 70.0, "c": 55.0},
  "params": {"sessionsTarget": 60.0},
  "autoSources": [{"key": "none", "label": "Chấm tay"}],
  "maxScoreMin": 1, "maxScoreMax": 10
}
```

`groups` gồm cả tiêu chí đã tắt (`active: false`); `weightSum` chỉ cộng phần
đang bật. `draftCount` = số phiếu Nháp đang dùng cấu hình cũ.

## POST `/hocba-hrm/api/reviews/config/criteria`

Lưu **cả bộ** câu hỏi của một nhóm; thứ tự trong mảng thành `sequence`.

```json
{"group": "teacher", "criteria": [
  {"id": 12, "name": "Chất lượng giờ dạy", "weight": 30, "maxScore": 10,
   "autoSource": "none", "guideline": "…", "anchorTop": "…",
   "anchorMid": "…", "anchorLow": "…", "active": true},
  {"id": 0, "name": "Câu hỏi mới", "weight": 10, "maxScore": 5,
   "autoSource": "none", "active": true}
]}
```

- `id: 0` = câu hỏi mới, `code` do hệ thống sinh (`t_*` / `o_*`).
- Bỏ câu hỏi = `active: false` (không xoá cứng — phiếu cũ còn tham chiếu).
- Câu hỏi không có trong payload thì giữ nguyên.
- **Tổng trọng số phần đang bật phải bằng 100**, lệch → `400 rejected` và
  **rollback cả lô**. `maxScore` ngoài 1–10 hoặc `weight` ngoài 0–100 → `rejected`.

**Response**: y hệt `GET /config` sau khi lưu.

## POST `/hocba-hrm/api/reviews/config/grading`

```json
{"gradeA": 85, "gradeB": 70, "gradeC": 55, "sessionsTarget": 60}
```

Ràng buộc `0 < C < B < A ≤ 100` và `sessionsTarget > 0`, sai → `400 rejected`.
Ngưỡng không snapshot vào phiếu: phiếu **Nháp** được tính lại ngay, phiếu đã
chốt/công bố giữ nguyên kết quả.

**Response**: y hệt `GET /config`.
