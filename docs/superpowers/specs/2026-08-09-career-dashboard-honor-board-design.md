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

`_order = 'date_awarded desc, id desc'` — **cố tình không có `rank`**: rank 0
nghĩa là "không xếp hạng", sắp tăng dần thì nó leo lên trên cả hạng 1. Việc xếp
hạng làm ở tầng payload (`(rank == 0, rank, -ngày, -id)`).

> **Odoo 19**: `_sql_constraints` đã bị bỏ và **im lặng không có tác dụng** —
> phải dùng `models.Constraint`. Test `test_unique_auto_entry_per_promotion`
> bắt được đúng cái bẫy này.

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

`frontend/src/components/HonorBoard.jsx` — khung ngang, đặt **trên cùng màn
`career`** (xem §5.5).

Nội dung: nhãn kỳ, danh sách thẻ vinh danh (avatar + tên + danh hiệu + phòng ban
+ mô tả), cột ranking bên phải. HR có nút "Thêm vinh danh" (modal nhỏ ngay trong
khung, không thêm màn hình mới) và nút gỡ trên từng thẻ. Bảng rỗng hoàn toàn →
ẩn khung với nhân viên thường; với HR thu về **một dải mỏng** kèm nút thêm, chứ
không để nguyên khung cao chiếm chỗ đắt nhất của trang.

### 5.5 Gộp về MỘT màn (quyết định 2026-08-09, sau bản dựng đầu)

Bản đầu đặt bảng vinh danh ở `Dashboard.jsx` + `Profile.jsx`, tách khỏi trang
lộ trình. Người dùng yêu cầu **gộp cả hai vào một màn** và làm nó ra dáng
dashboard. Đã bỏ khung khỏi hai chỗ cũ; toàn bộ nằm trong view `career`:

| Khối | Nội dung |
|---|---|
| Dải vinh danh | Bảng vinh danh toàn công ty (dữ liệu chung, hiện cả khi chưa chọn ai) |
| Thẻ nhân sự + KPI | avatar/chức danh/phòng ban + 6 ô: thâm niên, lần thăng chức, tháng từ thăng tiến, đợt đánh giá, điểm gần nhất (kèm TB), số lần vinh danh |
| Insight | 3–5 câu tự sinh từ chính dữ liệu (§4.3) |
| 5 biểu đồ | radar năng lực (2 đợt), đường xu hướng điểm (có mốc 80% "Đủ điều kiện"), thanh ngang chênh lệch từng tiêu chí, donut tiến độ nhận việc, vùng bậc thang lộ trình lương |
| Bảng lịch sử | dòng thời gian gọn + chip điểm từng tiêu chí, lọc theo nhóm |

**Đánh đổi đã biết**: khách muốn khung vinh danh nằm trên dashboard chung để
"vào là nhìn thấy đầu tiên" (10:33). Gộp về một màn thì mất tính đó — người
dùng đã chọn phương án gộp.

### 4.3 Insight tự sinh (`_career_insights`)

Rút thẳng từ dữ liệu đã có trên trang, **không nhắc tới lương** (insight hiện
cho cả vai trò không được xem lương):

- chưa có đợt đánh giá nào được xác nhận;
- điểm tăng / giảm / đi ngang bao nhiêu so với đợt trước;
- tiêu chí thấp nhất và cao nhất của đợt gần nhất (theo tỉ lệ điểm/thang);
- cảnh báo khi đã ≥ `STALE_PROMO_MONTHS` (12) tháng chưa đổi chức vụ;
- tiến độ quy trình nhận việc khi còn bước chưa xong.

`criteriaRadar` ghép đợt gần nhất với đợt liền trước **theo TÊN tiêu chí** (bộ
tiêu chí có thể đổi giữa hai đợt); tiêu chí đợt trước không có → `previous =
None`, **không quy về 0** — "0 điểm" và "chưa từng chấm" là hai chuyện khác nhau.

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

## 8. Phát sinh trong lúc làm (đã sửa, có test chặn)

Bốn thứ chỉ lộ ra khi chạy thật, không có trong thiết kế ban đầu:

1. **Mốc "Vào làm việc" bị nhân đôi.** `hr.employee.create` đã tự ghi snapshot
   `x_change_type='join'` vào `hr.promotion.history`, nên mốc tổng hợp dựng từ
   `x_probation_start` là dòng thứ hai cùng nội dung. → Chỉ dựng mốc tổng hợp
   khi **không có** snapshot `join`.
2. **`promoCount` và `monthsSincePromo` đếm cả snapshot `join`.** Hệ quả trên
   màn hình: một người chưa từng thăng chức vẫn hiện "Từ lần thăng tiến: 1.7"
   ngay cạnh ô "Lần thăng chức: 0". → Cả hai chỉ tính bản ghi
   `x_change_type='promotion'`.
3. **Snapshot `join` hiển thị tiêu đề "— → —"** (chưa có chức vụ trước/sau).
   → Dòng đó lấy tiêu đề "Vào làm việc".
4. **Trang `career` thành ngõ cụt với tài khoản vai trò quản lý.** Các tài
   khoản HR/Admin/Giáo vụ **không gắn hồ sơ nhân viên** (tách tài khoản quản lý
   ↔ cá nhân, họp #2), nên `emp_id=0` chắc chắn lỗi — mà `ErrorState` lại thay
   cả trang, nuốt luôn ô chọn nhân viên: không còn cách nào thoát. → Header
   (gồm ô chọn) **luôn render**; với `canManage` mặc định là "chờ chọn người",
   không tự nạp bản thân.

Ngoài ra `_honor_board` đọc **toàn bộ** bảng nên test của nó phải tự dọn dữ
liệu sẵn có trong `setUp` (trong phạm vi transaction) — nếu không, mọi khẳng
định về kỳ / thứ tự / bảng-rỗng sẽ vỡ ngay khi DB có mục vinh danh thật.

## 8b. Đợt tự kiểm 2026-08-10 (trên DB thật, 200 NV)

Chạy lại toàn bộ tính năng trên Neon với 3 vai (`test_hrmanager`,
`test_truongphong`, `test_employee`). Bốn thứ nữa lộ ra — đều đã sửa, mỗi cái
có test chặn:

5. **Điểm đánh giá rò ra ngoài phạm vi.** `score` trong `ranking` gác bằng
   `_user_can_manage` (mọi vai trò quản lý), nên trưởng phòng đọc được điểm
   của người **phòng khác** — trong khi `/api/career/<id>` của đúng người đó
   trả **403** cho họ. → Điều kiện đổi thành `_is_hr(env) or
   _emp_in_scope(env, emp)`: HR thấy hết, quản lý chỉ thấy điểm người
   trong phạm vi mình, còn lại chỉ thấy tên như nhân viên thường.
6. **Nút HR bày cho vai trò không có quyền.** `HonorBoard` bật "Thêm vinh
   danh" / "Gỡ khỏi bảng" theo `canManage`, mà `_honor_create` /
   `_honor_archive` lại đòi `_is_hr` ⇒ trưởng phòng bấm là chắc chắn 403.
   → Payload thêm cờ **`canEdit = _is_hr(env)`**, FE bày nút theo cờ đó
   (kể cả nhánh "bảng rỗng thu về dải mỏng").
7. **Snapshot `join` vẫn mang `kind='promotion'`.** Đã sửa ở tầng thống kê
   (§8.2) nhưng còn sót ở dòng thời gian: chip lọc đếm theo `kind` nên
   người chưa từng thăng chức vẫn thấy **"Thăng tiến (1)"** cạnh ô
   "Lần thăng chức: 0". → Dòng đó nhận `kind='join'`, `sort=0`.
8. **Tab Thăng tiến trong hồ sơ vẫn in "— → —".** Trang lộ trình đã bỏ
   (§8.3) nhưng `PromoTab` (drawer + "Hồ sơ của tôi") tự ghép
   `fromJob → toJob` nên hồ sơ nào cũng mở đầu bằng dòng vô nghĩa đó.
   → `_employee_detail` trả thêm `changeType` + **`title`** dựng sẵn, FE
   dùng `p.title` (vẫn fallback về mũi tên cho payload cũ).

**Cải thiện kèm theo**: ô chọn nhân viên trên trang `career` từ `<select>`
phẳng đổi thành **ô tìm kiếm gõ-để-lọc** (`PeoplePicker` trong `Career.jsx`).
Trên DB thật danh sách đã 199 người — thẻ `<select>` bắt HR cuộn tay qua từng
dòng. Lọc theo tên **không dấu** lẫn mã HB, hiển thị tối đa 30 dòng kèm nhắc
"còn N người nữa — gõ thêm để lọc".

## 9. Rủi ro đã cân nhắc

- **`Dashboard.jsx` và `Shell.jsx` là file CHUNG.** Chỉ chèn thêm, không sửa
  logic sẵn có: 1 dòng render `HonorBoard` + 2 nav item + 1 `PAGE_META`.
- **Bảng vinh danh là dữ liệu công khai toàn công ty.** Không đưa lương, không
  đưa điểm số cho người không quản lý, không có bảng xếp hạng ngược.
- **`hb.honor.entry` không xoá cứng** — HR gỡ bằng `active=False`, giữ vết.
- **Trang `career` phải chịu được NV chưa có dữ liệu gì** (mới vào, chưa đánh
  giá): timeline vẫn có mốc `join`, các biểu đồ hiện trạng thái rỗng.
