# Thiết kế: Trang Lộ trình sự nghiệp (dashboard lịch sử) + Bảng vinh danh

- **Ngày**: 2026-08-09
- **Module**: `hocba_employees` (model `hb.honor.entry` + hook) · `hocba_hrm` (API + SPA)
- **Owner**: Tân — nhánh `feature/career-dashboard-honor-board`
- **Nguồn yêu cầu**: họp khách hàng 2026-08-07 (`UpdateISPEmployee.mp4`),
  đoạn **07:47–09:46** (ý C) và **09:46–12:01** (ý D).
- **Phạm vi do người dùng chốt (2026-08-09)**: chỉ làm ý C + ý D.
  **KHÔNG động vào màn Đánh giá** (`frontend/src/features/reviews/*`,
  model `hr.review`) — đó là phần của Việt.

## 1. Nguyên văn yêu cầu

### 1.1 Ý C — trang lịch sử cho từng người

Khách đang xem tab **Thăng tiến** trong drawer hồ sơ (một popup) và phàn nàn:

> "Cái đoạn này anh bảo bọn mày là phải thành một trang, chứ đừng có để thành
> pop-up như thế này nha." (07:50)
>
> "Chỗ này thật ra chị nghĩ cũng nên làm cái bảng to nhìn cho nó… nhìn này,
> [chật] quá." (08:51)
>
> "Phải làm cho anh một cái dashboard. Trong cái dashboard đấy thì phải có đầy
> đủ thông tin, cả nhận xét, các thứ nó phải hiển thị [tường minh] cho người ta
> xem ấy. Chứ không phải là theo kiểu phải click nhiều. Đầy đủ thông tin luôn.
> Từ thăng tiến, từ nhận xét, từ đánh giá, tất cả mọi thứ nó phải hiển thị nó
> giống như kiểu một cái bảng lịch sử." (09:06)
>
> "Phải là một [tab] hẳn hoi, có nghĩa là nó thành một bảng luôn. Nó giống như
> kiểu **dashboard thống kê cho từng người**, giống như kiểu bọn mày xem lại
> **một album của đời** ấy." (09:37)

Và nhân viên phải tự xem được lịch sử của chính mình:

> "Cái này họ vẫn sẽ xem được đúng không? Họ vẫn sẽ xem được cái đánh giá của
> họ, lịch sử của họ là họ được đánh giá như thế nào, thăng tiến như thế nào."
> (08:13)

### 1.2 Ý D — bảng vinh danh

> "Một cái bảng leadership của việc thống kê của những người được vinh danh,
> hiển thị lên **trang dashboard chung của tất cả mọi người**." (09:56)
>
> "Ví dụ một bạn được lên một vị trí mới thì nó sẽ hiển thị ở đấy bao lâu?" —
> "**Đến lúc mà lần bầu tiếp theo.**" (10:05)
>
> "Hiển thị lên dashboard chung của tất cả mọi người… người ta vào đấy, người
> ta sẽ **nhìn thấy cái đấy đầu tiên**. Mình sẽ có một cái khung ở trên cùng
> kiểu vinh danh." (10:33)
>
> "Ranking sales, ranking marketing… mỗi cái bên em cứ nghĩ ra 1 đến 2 cái gì
> đấy để nó thành ranking, hoặc xếp hạng." (10:49)
>
> "Vinh danh **chung cả công ty**, không phải theo từng phòng… có cái vinh danh
> gì thì mình sẽ cho nó lên đấy thôi." (11:13)

**Khách tự loại một hạng mục ra khỏi phạm vi HRM.** Khi bàn tới ranking doanh
thu real-time:

> "Không, cái đấy nó sẽ trên CRM chứ… sales nó không mở cái này để nó xem đâu."
> (11:43)

→ Ranking doanh thu/chốt sale **không làm** ở HRM. Ranking trong phạm vi này chỉ
lấy dữ liệu HRM thật sự sở hữu.

## 2. Bối cảnh code hiện tại

| Thứ | Ở đâu | Vấn đề |
|---|---|---|
| Lịch sử thăng tiến | `EmployeeDrawer.jsx` → `PromoTab`, trong `<Modal lg>` | Popup, vùng nội dung `maxHeight: 72vh` → đúng chỗ khách kêu chật |
| Kết quả đánh giá | `PromoTab` gọi `fetchEvaluations` **chỉ khi `canAct`** | `Profile.jsx:120` truyền `<PromoTab det isMgr />` — không có `onUpdated` → `canAct=false` → **nhân viên không hề thấy đánh giá của chính mình** (đúng thứ khách hỏi ở 08:13) |
| Nhận xét bước thử việc | `hb.onboarding.step.result_note` | Chỉ hiện trong tab Thử việc, không gộp vào dòng thời gian |
| Dashboard chung | `features/dashboard/Dashboard.jsx`, nav `need: 'manage'` | **Nhân viên thường không thấy Dashboard**; `defaultView` của họ là `profile` |

Dữ liệu đã có sẵn, không cần model mới cho ý C:
`hr.promotion.history` (mốc thăng tiến + lương), `hr.promotion.evaluation` +
`.line` (điểm, kết luận, nhận xét), `hb.onboarding.step` (kết quả + nhận xét
từng bước thử việc).

## 3. Quyết định thiết kế

| Quyết định | Phương án chọn | Vì sao không chọn phương án kia |
|---|---|---|
| Chỗ đặt trang lịch sử | **View SPA riêng `career`**, có mặt trong nav | Nhét thêm tab vào drawer thì vẫn là popup — đúng cái khách bảo bỏ. Trang riêng còn deep-link được (`allowedViews` + `localStorage`) |
| Đường vào cho quản lý | Nav "Lộ trình sự nghiệp" (`need: manage`) + nút "Mở trang đầy đủ" trong tab Thăng tiến | Chỉ để nút trong drawer thì không tìm thấy trang khi chưa mở hồ sơ ai |
| Đường vào cho nhân viên | Nav "Lộ trình của tôi" (`need: self`), tự ghim vào bản thân | Nhân viên thường **không** thấy Dashboard, nếu chỉ gắn ở Dashboard thì họ mất luôn tính năng |
| Model cho ý C | **Không thêm model** | 3 nguồn dữ liệu đã có; thêm bảng tổng hợp là nhân bản sự thật |
| Model cho ý D | **Thêm `hb.honor.entry`** | Vinh danh là quyết định của HR ("có cái vinh danh gì thì mình cho lên"), không suy ra được hết từ dữ liệu; nhưng vẫn tự sinh cho bổ nhiệm |
| "Hiển thị bao lâu" | **Kỳ = tháng dương lịch**; hết tháng thì rơi khỏi bảng | Khách nói "đến lần bầu tiếp theo" nhưng hệ thống chưa có khái niệm "lần bầu"; tháng là chu kỳ có sẵn, không cần HR mở/đóng kỳ bằng tay |
| Kỳ hiện tại rỗng | **Lùi về kỳ gần nhất còn dữ liệu**, gắn cờ `isCurrent=false` | Bảng trống ngay đầu tháng làm khung vinh danh thành ô chết — nó là thứ "nhìn thấy đầu tiên" |
| Ranking | **Top điểm đánh giá thăng tiến đã xác nhận trong kỳ** | Doanh thu/chốt sale khách đã tự loại (§1.2); chuyên cần nằm ở `hocba_attendance` — ranh giới đã chốt 2026-08-06 là không đụng vào |
| Điểm số trên bảng công khai | Chỉ `canManage` thấy **số điểm**; mọi người thấy tên + danh hiệu | Bêu điểm đánh giá cá nhân cho toàn công ty là chuyện khác hẳn với vinh danh |
| Nút "Đánh giá mới" / "Tạo thăng tiến" trong drawer | **Giữ nguyên** | Bỏ chúng là ý B — phải chuyển chỗ nhập liệu sang màn Đánh giá của Việt, mà màn đó ngoài phạm vi lần này. Gỡ trước khi có chỗ thay thế = mất chức năng |

**Ngoài phạm vi**: ý B (gom nhập liệu đánh giá về màn Đánh giá, biến tab Thăng
tiến thành chỉ-hiển-thị); thông báo `hb.notification` khi được vinh danh;
ranking doanh thu (khách đã chuyển sang CRM).

## 4. Phần 1 — Trang Lộ trình sự nghiệp (ý C)

### 4.1 API

`GET /hocba-hrm/api/career/<int:emp_id>` — `emp_id = 0` nghĩa là **chính mình**.

Helper thuần để test được không qua HTTP (theo lối `_account_*` đã có):

```python
_career_payload(env, emp_id)   # emp_id 0 → env.user.employee_id
```

**Quyền**:

```
emp là chính mình                       → cho (isSelf=True)
_emp_in_scope(env, emp)                 → cho
còn lại                                 → AccessError
```

`canSeeSalary = isSelf or _cap_see_salary(env)` — tự xem lương của mình vốn đã
mở ở `/api/me` (`_employee_detail(..., is_mgr=True)`), giữ nhất quán.

**Payload**:

```jsonc
{
  "employee": {"id","name","code","jobTitle","depName","hasImg","start",
               "status","statusKey"},
  "isSelf": true, "canSeeSalary": true, "canManage": false,
  "stats": {"tenureMonths","monthsSincePromo","promoCount","evalCount",
            "avgScore","lastScore","honorCount"},
  "timeline": [{"kind","date","title","detail","badge","badgeKind","meta"}],
  "salaryJourney": [{"date","wage","label"}],     // [] khi !canSeeSalary
  "scoreTrend": [{"date","score","verdict"}],
  "evaluations": [{"id","date","evaluator","state","totalScore","verdictFinal",
                   "note","lines":[…]}],
  "honors": [{"id","date","category","title","description"}]
}
```

`timeline.kind` ∈ `join | promotion | evaluation | onboarding | honor`, sắp xếp
**ngày giảm dần** (mới nhất trên cùng), tie-break theo thứ tự kind rồi id để
kết quả ổn định.

- `join` — 1 dòng từ `employee.start` ("Vào làm việc").
- `promotion` — mọi `hr.promotion.history`; `detail` gộp lý do + số quyết định;
  chênh lệch lương chỉ đưa vào khi `canSeeSalary`.
- `evaluation` — `hr.promotion.evaluation`; `detail = conclusion_note`;
  `badge` = nhãn `verdict_final`. Bản `draft` chỉ hiện với người quản lý.
- `onboarding` — `hb.onboarding.step` ở `done`/`skipped`; `detail = result_note`
  — đây chính là "nhận xét" khách đòi phải nhìn thấy.
- `honor` — `hb.honor.entry` của NV đó.

### 4.2 SPA

`frontend/src/features/employees/Career.jsx` — view mới `career`:

- **Đầu trang**: thẻ nhân sự (avatar, tên, mã, chức danh, phòng ban, trạng thái)
  + hàng KPI 6 ô (thâm niên, tháng từ lần thăng tiến, số mốc, số đợt đánh giá,
  điểm TB, điểm gần nhất).
- **Hai biểu đồ**: lộ trình lương/chức vụ (chỉ khi `canSeeSalary`) và xu hướng
  điểm đánh giá.
- **Dòng thời gian đầy đủ** — mọi mốc, mở sẵn, không phải bấm để xem chi tiết
  ("chứ không phải là theo kiểu phải click nhiều"). Đợt đánh giá hiện luôn bảng
  điểm từng tiêu chí + nhận xét.
- **Bộ lọc kind** dạng chip (Tất cả / Thăng tiến / Đánh giá / Thử việc /
  Vinh danh) — lọc client-side, không thêm round-trip.
- Với quản lý: ô chọn nhân viên ở đầu trang (`EmployeePicker`).

`Shell.jsx` (file CHUNG): thêm nav item `career` ở **cả hai** mục — "Lộ trình sự
nghiệp" (`need: manage`) và "Lộ trình của tôi" (`need: self`) — cùng một view id,
đúng lối `attendance` / `timeoff` đang dùng; thêm `PAGE_META.career`.

`EmployeeDrawer.jsx` → `PromoTab`: thêm nút **"Mở trang đầy đủ"** gọi
`onOpenCareer(det.id)`; prop truyền từ `App → Employees → EmployeeDrawer →
PromoTab`. Khi không có prop (Profile self-view) thì không hiện nút.

`Profile.jsx`: sửa `<PromoTab det isMgr />` → truyền thêm `showEvaluations` để
nhân viên xem được đánh giá của mình ngay tại tab Thăng tiến (§2, hàng 2).
Dữ liệu lấy từ `/api/career/0`, **không** từ `/api/promotion/eval/<id>` (route đó
gác `_can_eval_emp` — nhân viên thường không qua được).

## 5. Phần 2 — Bảng vinh danh (ý D)

### 5.1 Model `hb.honor.entry` (`hocba_employees`)

| Field | Kiểu | Ghi chú |
|---|---|---|
| `employee_id` | M2o `hr.employee`, required, `ondelete='cascade'`, index | |
| `category` | Selection `promotion` / `achievement` / `tenure` / `other` | mặc định `achievement` |
| `title` | Char, required | "Bổ nhiệm Trưởng phòng Đào tạo" |
| `description` | Text | |
| `date_awarded` | Date, required, mặc định hôm nay | |
| `period_key` | Char, compute **store**, index | `'YYYY-MM'` từ `date_awarded` |
| `rank` | Integer | 0 = không xếp hạng |
| `source` | Selection `auto` / `manual`, mặc định `manual` | |
| `promotion_id` | M2o `hr.promotion.history`, `ondelete='set null'` | khoá chống trùng bản tự sinh |
| `active` | Boolean, mặc định True | HR gỡ khỏi bảng = archive, **không xoá** |

Ràng buộc:

- `UNIQUE(promotion_id)` — SQL constraint. Postgres cho phép nhiều NULL nên bản
  ghi HR nhập tay (không gắn promotion) không bị chặn.
- `rank >= 0` (`@api.constrains`).
- `title` không được rỗng/toàn khoảng trắng.

`_order = 'date_awarded desc, rank, id desc'` — mới nhất trước; trong cùng ngày
thì hạng nhỏ đứng trên (rank 0 = không xếp hạng lại đứng đầu, nên **rank 0 được
đẩy xuống cuối** bằng cách sắp ở tầng payload, không dựa vào `_order`).

### 5.2 Tự sinh khi bổ nhiệm

Trong `hr.promotion.history.create()`, sau khi tạo bản ghi: nếu
`x_change_type == 'promotion'` **và** `to_job_id` **và** `to_job_id != from_job_id`
→ tạo `hb.honor.entry` (`source='auto'`, `category='promotion'`,
`title = 'Bổ nhiệm ' + to_job_id.name`, `date_awarded = date_effective`,
`promotion_id = rec.id`).

Không sinh cho `join` / `probation` / `salary` / `other` — đó là biến động hồ sơ,
không phải chuyện đem ra vinh danh trước toàn công ty.

### 5.3 API

| Route | Quyền | Việc |
|---|---|---|
| `GET /hocba-hrm/api/honor/board` | mọi user đăng nhập | Trả kỳ + entries + ranking |
| `POST /hocba-hrm/api/honor/entry` | `_is_hr(env)` | HR thêm mục vinh danh |
| `POST /hocba-hrm/api/honor/entry/<id>/archive` | `_is_hr(env)` | Gỡ khỏi bảng |

Helper thuần: `_honor_board(env)`, `_honor_create(env, payload)`,
`_honor_archive(env, entry_id)` — cả ba trả về payload bảng để SPA render lại
bằng một lượt.

**Chọn kỳ**: kỳ hiện tại `YYYY-MM` của hôm nay. Nếu kỳ đó không có entry nào →
lấy `period_key` lớn nhất còn entry, trả `isCurrent=false` để SPA ghi rõ
"Kỳ tháng M/YYYY". Không có entry nào cả → `entries=[]`, `period` = kỳ hiện tại.

**Ranking**: `hr.promotion.evaluation` `state='confirmed'`,
`verdict_final='qualified'`, `eval_date` trong kỳ đã chọn, sắp `total_score` DESC,
lấy tối đa 5. Trường `score` **chỉ có trong payload khi `_user_can_manage(env)`**.

Payload:

```jsonc
{
  "period": "2026-08", "periodLabel": "Tháng 8/2026", "isCurrent": true,
  "canManage": false,
  "entries": [{"id","empId","empName","empCode","dep","hasImg","category",
               "categoryLabel","title","description","date","rank","source"}],
  "ranking": [{"empId","empName","dep","hasImg","score"?}]
}
```

### 5.4 SPA

`frontend/src/components/HonorBoard.jsx` — khung ngang, đặt **trên cùng**:

- `Dashboard.jsx` tab Tổng quan, trước `KpiRow` (file CHUNG — chèn đúng 1 dòng).
- `Profile.jsx`, trước thẻ hồ sơ — vì nhân viên thường vào thẳng Profile, đây
  mới là "cái nhìn thấy đầu tiên" của họ.

Nội dung: nhãn kỳ, danh sách thẻ vinh danh (avatar + tên + danh hiệu + phòng ban
+ mô tả), cột ranking bên phải. HR có nút "Thêm vinh danh" (modal nhỏ ngay trong
khung, không thêm màn hình mới) và nút gỡ trên từng thẻ. Bảng rỗng hoàn toàn →
ẩn khung với nhân viên thường, hiện gợi ý thêm với HR.

## 6. Test

`custom-addons/hocba_employees/tests/test_honor.py`

1. `test_promotion_creates_honor_entry` — đổi chức vụ → 1 entry `auto/promotion`, gắn `promotion_id`.
2. `test_salary_change_no_honor` — `x_change_type='salary'` → 0 entry.
3. `test_join_snapshot_no_honor` — `x_change_type='join'` → 0 entry.
4. `test_promotion_same_job_no_honor` — `promotion` nhưng chỉ đổi lương → 0 entry.
5. `test_period_key_from_date` — `date_awarded` 2026-08-09 → `'2026-08'`; đổi ngày → đổi kỳ.
6. `test_unique_auto_entry_per_promotion` — entry thứ 2 cùng `promotion_id` → `IntegrityError`.
7. `test_negative_rank_rejected` / `test_blank_title_rejected`.

`custom-addons/hocba_hrm/tests/test_career.py`

8. `test_career_self_by_zero` — `emp_id=0` trả đúng NV của user, `isSelf`.
9. `test_career_forbidden_out_of_scope` — NV thường xem người khác → `AccessError`.
10. `test_career_manager_in_scope_allowed`.
11. `test_career_hides_salary_when_not_allowed` — `salaryJourney == []` và mốc thăng tiến không lộ lương.
12. `test_career_timeline_sorted_desc`.
13. `test_career_timeline_includes_onboarding_note` — nhận xét bước thử việc có mặt.
14. `test_career_timeline_includes_evaluation_and_honor`.
15. `test_career_draft_evaluation_hidden_from_self`.
16. `test_career_stats_counts`.

`custom-addons/hocba_hrm/tests/test_honor_board.py`

17. `test_board_current_period`.
18. `test_board_falls_back_to_previous_period` — `isCurrent False` + đúng `period`.
19. `test_board_empty_when_no_entries`.
20. `test_ranking_hides_score_from_plain_user` / `test_ranking_shows_score_to_manager`.
21. `test_ranking_only_qualified_confirmed_in_period`.
22. `test_honor_create_requires_hr` — NV thường → `AccessError`.
23. `test_honor_archive_removes_from_board`.

## 7. Migration

`hocba_employees` `19.0.4.0.0` → **`19.0.5.0.0`** (model mới + ACL).

`migrations/19.0.5.0.0/post-migrate.py`: bù entry `auto` cho các
`hr.promotion.history` có `x_change_type='promotion'`, đổi chức vụ thật, hiệu lực
trong **90 ngày** gần nhất và chưa có entry — để bảng vinh danh trên DB đang chạy
không trống trơn sau khi upgrade. Idempotent (lọc theo `promotion_id` chưa tồn
tại), an toàn khi chạy lại.

## 8. Rủi ro đã cân nhắc

- **`Dashboard.jsx` và `Shell.jsx` là file CHUNG.** Chỉ chèn thêm, không sửa
  logic sẵn có: 1 dòng render `HonorBoard` + 2 nav item + 1 `PAGE_META`.
- **Bảng vinh danh là dữ liệu công khai toàn công ty.** Không đưa lương, không
  đưa điểm số cho người không quản lý, không có bảng xếp hạng ngược.
- **`hb.honor.entry` không xoá cứng** — HR gỡ bằng `active=False`, giữ vết.
- **Trang `career` phải chịu được NV chưa có dữ liệu gì** (mới vào, chưa đánh
  giá): timeline vẫn có mốc `join`, các biểu đồ hiện trạng thái rỗng.
