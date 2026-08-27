# Sửa lỗi 500 khi Đăng tuyển (`hr.job.is_published`) — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nút "Đăng tuyển / Ngừng đăng" và nút "Chép link" phải chạy đúng trên MỌI database, kể cả database không cài `website_hr_recruitment`.

**Architecture:** Module `hocba_recruitments` không depends `website_hr_recruitment` nên phải **suy biến êm** (graceful degradation), không phải bắt buộc cài thêm. Cụ thể: controller chỉ ghi cờ nội bộ `x_published`, để `hr_job.write()` tự soi gương sang `is_published` khi field đó tồn tại; mọi chỗ ĐỌC dùng chung một helper có fallback. Song song, stack deploy nginx được bổ sung `website_hr_recruitment` vào danh sách cài để trang tuyển dụng công khai `/jobs` hoạt động thật.

**Tech Stack:** Odoo 19 (custom-addons), Python, `odoo.tests` (TransactionCase/HttpCase), Docker Compose.

**Spec:** `custom-addons/hocba_recruitments/SPEC.md` §11.1 (Link tuyển dụng công khai) + §15 (TODO). Chẩn đoán gốc và bằng chứng: mục "P1" trong phiên rà soát 2026-08-26; tiền lệ đã ghi ở `docs/DB_TEST_DATA.md:223` (DB demo 17/08 dính đúng lỗi này).

## Global Constraints

- Odoo 19: `res.users` dùng `group_ids` (không phải `groups_id`).
- KHÔNG thêm `website_hr_recruitment` vào `__manifest__.py` `depends` — nó kéo theo `website`, `website_mail`, `website_sms`; module phải cài được độc lập. Ràng buộc này là lý do tồn tại của toàn bộ kế hoạch, đừng "sửa" bằng cách thêm depends.
- Chạy test trên Git Bash BẮT BUỘC có `MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`; thiếu nó ra "0 tests" mà vẫn báo OK.
- Kết quả test cần thấy: `0 failed, 0 error(s) of N tests` với **N ≥ 193**.
- DB test local hiện hỏng (volume PG18 vs image postgres:15). Dùng container tạm đã dựng: `hbtestdb` (network `hbtest`, alias `db`, user/pass `odoo`/`odoo_password`, db `hocba_hrm`). Container này **không** cài `website_hr_recruitment` — đó chính là môi trường tái hiện lỗi.
- Commit trên nhánh `Viet/Recruitment`, commit nhỏ theo từng task.

---

### Task 1: Controller ngừng ghi thẳng `is_published`

**Files:**
- Modify: `custom-addons/hocba_recruitments/controllers/main.py:823-827` (`_job_vals`)
- Test: `custom-addons/hocba_recruitments/tests/test_job_publish.py` (tạo mới)
- Modify: `custom-addons/hocba_recruitments/tests/__init__.py` (đăng ký file test mới)

**Interfaces:**
- Consumes: `JOB_FORM_FIELDS` (đã map sẵn `'published' → ('x_published', 'bool')`), `HbJob.write()` tại `models/hr_job.py:59` (đã có guard `if 'is_published' in self._fields`).
- Produces: `_job_vals(payload) -> dict` — sau task này dict trả về **không bao giờ** chứa khoá `is_published`; luôn chứa `x_published` (bool) và `recruitment_status` khi payload có `published`.

- [ ] **Step 1: Viết test đỏ**

Tạo `custom-addons/hocba_recruitments/tests/test_job_publish.py`:

```python
"""Đăng tuyển / Ngừng đăng phải chạy trên DB KHÔNG cài website_hr_recruitment.

`is_published` là field của `website_hr_recruitment`, không phải của
`hr_recruitment`. Manifest của module này không depends nó, nên controller
tuyệt đối không được ghi thẳng field đó: DB thiếu module → ORM ném ValueError
→ controller không bắt (chỉ bắt AccessError/ValidationError/UserError) → HTTP
500 trần, nút Đăng tuyển chết. Ghi `x_published` thì hr_job.write() tự soi
gương sang `is_published` KHI field tồn tại.
"""
from odoo.tests import TransactionCase, tagged

from odoo.addons.hocba_recruitments.controllers.main import HocBaTuyenDung


@tagged('post_install', '-at_install', 'hocba')
class TestJobPublishVals(TransactionCase):
    """_job_vals() là hàm thuần (chỉ đọc payload) nên gọi thẳng được."""

    def test_01_publish_true_khong_ghi_is_published(self):
        vals = HocBaTuyenDung()._job_vals({'published': True})
        self.assertNotIn(
            'is_published', vals,
            'Controller không được ghi field của website_hr_recruitment')
        self.assertTrue(vals['x_published'])
        self.assertEqual(vals['recruitment_status'], 'recruiting')

    def test_02_publish_false_khong_ghi_is_published(self):
        vals = HocBaTuyenDung()._job_vals({'published': False})
        self.assertNotIn('is_published', vals)
        self.assertFalse(vals['x_published'])
        self.assertEqual(vals['recruitment_status'], 'stopped')

    def test_03_khong_gui_published_thi_khong_dung_toi_hai_co(self):
        vals = HocBaTuyenDung()._job_vals({'name': 'Trợ giảng'})
        self.assertNotIn('is_published', vals)
        self.assertNotIn('x_published', vals)
        self.assertNotIn('recruitment_status', vals)
```

Thêm vào `custom-addons/hocba_recruitments/tests/__init__.py`:

```python
from . import test_job_publish
```

- [ ] **Step 2: Chạy test để chắc chắn nó ĐỎ**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker run --rm --network hbtest -v "$PWD/custom-addons:/mnt/extra-addons" -v "$PWD/odoo.local.conf:/etc/odoo/odoo.conf" -e HOST=db -e PORT=5432 -e USER=odoo -e PASSWORD=odoo_password hocba_onl-odoo odoo -d hocba_hrm -u hocba_recruitments --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_recruitments:TestJobPublishVals --stop-after-init --log-level=test
```

Expected: `test_01` và `test_02` FAIL với `AssertionError: 'is_published' unexpectedly found in ...`; `test_03` PASS.

- [ ] **Step 3: Sửa `_job_vals`**

Trong `custom-addons/hocba_recruitments/controllers/main.py`, thay khối cuối của `_job_vals`:

```python
        # "published" là cờ nghiệp vụ của SPA. CHỈ ghi x_published (cờ nội bộ,
        # luôn tồn tại); hr_job.write() tự soi gương sang is_published KHI
        # website_hr_recruitment có cài. Ghi thẳng is_published ở đây thì DB
        # không cài module đó sẽ ném ValueError → HTTP 500 (xem test_job_publish).
        if 'published' in payload:
            pub = bool(payload['published'])
            vals['x_published'] = pub
            vals['recruitment_status'] = 'recruiting' if pub else 'stopped'
        return vals
```

- [ ] **Step 4: Chạy lại test — phải XANH**

Chạy đúng lệnh Step 2. Expected: `0 failed, 0 error(s) of 3 tests`.

- [ ] **Step 5: Commit**

```bash
git add custom-addons/hocba_recruitments/controllers/main.py custom-addons/hocba_recruitments/tests/test_job_publish.py custom-addons/hocba_recruitments/tests/__init__.py
git commit -m "fix(recruitment): dung ghi thang is_published, tranh 500 khi thieu website_hr_recruitment"
```

---

### Task 2: Đọc cờ `published` thống nhất qua một helper

**Files:**
- Modify: `custom-addons/hocba_recruitments/controllers/main.py` — thêm helper cạnh `_job_row` (khoảng dòng 669), sửa 3 chỗ đọc: dòng ~679 (`_job_row`), ~868 (tab Theo dõi tuyển dụng), ~1033 (`_request_jd`)
- Test: `custom-addons/hocba_recruitments/tests/test_job_publish.py` (bổ sung class thứ hai)

**Interfaces:**
- Consumes: `HbJob.x_published`, `HbJob.write()` (mirror hai cờ).
- Produces: `_job_published(job) -> bool` — dùng chung cho mọi payload trả về SPA. Trả `False` khi `job` rỗng.

- [ ] **Step 1: Viết test đỏ**

Thêm vào cuối `custom-addons/hocba_recruitments/tests/test_job_publish.py`:

```python
@tagged('post_install', '-at_install', 'hocba')
class TestJobPublishRead(TransactionCase):
    """Đọc cờ published phải ra cùng một kết quả trên mọi DB.

    Trước đây _job_row fallback về x_published còn tab Theo dõi và popup JD
    fallback về False ⇒ trên DB không có website, JD nào cũng hiện "chưa đăng"
    và nút Chép link không bao giờ xuất hiện.
    """

    def setUp(self):
        super().setUp()
        self.ctrl = HocBaTuyenDung()
        self.job = self.env['hr.job'].create({'name': 'Trợ giảng (test publish)'})

    def test_10_job_rong_tra_false(self):
        self.assertFalse(self.ctrl._job_published(self.env['hr.job']))

    def test_11_dang_tuyen_tra_true(self):
        self.job.write({'x_published': True})
        self.assertTrue(self.ctrl._job_published(self.job))

    def test_12_ngung_dang_tra_false(self):
        self.job.write({'x_published': True})
        self.job.write({'x_published': False})
        self.assertFalse(self.ctrl._job_published(self.job))
```

- [ ] **Step 2: Chạy test để chắc chắn nó ĐỎ**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker run --rm --network hbtest -v "$PWD/custom-addons:/mnt/extra-addons" -v "$PWD/odoo.local.conf:/etc/odoo/odoo.conf" -e HOST=db -e PORT=5432 -e USER=odoo -e PASSWORD=odoo_password hocba_onl-odoo odoo -d hocba_hrm -u hocba_recruitments --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_recruitments:TestJobPublishRead --stop-after-init --log-level=test
```

Expected: cả 3 test ERROR với `AttributeError: 'HocBaTuyenDung' object has no attribute '_job_published'`.

- [ ] **Step 3: Thêm helper + thay 3 chỗ đọc**

Thêm ngay TRƯỚC `def _job_row(self, j, detail=False):` trong `controllers/main.py`:

```python
    def _job_published(self, job):
        """Vị trí này có đang đăng tuyển công khai không.

        is_published (website_hr_recruitment) là nguồn sự thật khi có website;
        DB không cài module đó thì lùi về cờ nội bộ x_published. Ba chỗ trả
        payload cho SPA phải dùng CHUNG hàm này, đừng getattr rời rạc — trước
        đây mỗi chỗ fallback một kiểu nên tab Theo dõi luôn báo "chưa đăng".
        """
        if not job:
            return False
        if 'is_published' in job._fields:
            return bool(job.is_published)
        return bool(job.x_published)
```

Trong `_job_row`, thay dòng `'published': bool(getattr(j, 'is_published', j.x_published)),` bằng:

```python
            'published': self._job_published(j),
```

Trong `api_recruitment_jobs` (khối `data['requests']`) và trong `_request_jd`, thay cả hai dòng
`'published': bool(getattr(r.job_id, 'is_published', False)) if r.job_id else False,` bằng:

```python
            'published': self._job_published(r.job_id),
```

- [ ] **Step 4: Chạy lại test — phải XANH**

Chạy đúng lệnh Step 2. Expected: `0 failed, 0 error(s) of 3 tests`.

- [ ] **Step 5: Chạy TOÀN BỘ suite tuyển dụng**

```bash
MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*' docker run --rm --network hbtest -v "$PWD/custom-addons:/mnt/extra-addons" -v "$PWD/odoo.local.conf:/etc/odoo/odoo.conf" -e HOST=db -e PORT=5432 -e USER=odoo -e PASSWORD=odoo_password hocba_onl-odoo odoo -d hocba_hrm -u hocba_recruitments --addons-path=/mnt/extra-addons --test-enable --test-tags /hocba_recruitments --stop-after-init --log-level=test 2>&1 | tail -30
```

Expected: `0 failed, 0 error(s) of 199 tests` (193 cũ + 6 mới). Hai test `TestRequestTracking.test_31_publish_toggle_flips_recruitment_status` và `test_32_publish_toggle_shows_on_tracking_tab` — vốn đỏ từ 10/08 — nay phải XANH. Nếu chúng vẫn đỏ thì Task 2 chưa xong, đừng đi tiếp.

- [ ] **Step 6: Commit**

```bash
git add custom-addons/hocba_recruitments/controllers/main.py custom-addons/hocba_recruitments/tests/test_job_publish.py
git commit -m "fix(recruitment): doc co published qua mot helper co fallback x_published"
```

---

### Task 3: Stack deploy nginx cài `website_hr_recruitment`

**Files:**
- Modify: `docker-compose.nginx.yml:66-68` (`--init` và `--update`)

**Interfaces:**
- Consumes: không.
- Produces: DB dựng bằng stack nginx có field `hr.job.is_published` và route công khai `/jobs/detail/...`.

Task 1+2 làm nút hết vỡ; task này làm trang tuyển dụng công khai **tồn tại thật** trên bản deploy — thiếu nó thì nút Chép link vẫn không hiện (SPA chỉ render khi `published` true, mà không có website thì chẳng ai đăng lên đâu để mà chép).

- [ ] **Step 1: Sửa compose**

Trong `docker-compose.nginx.yml`, thêm `website_hr_recruitment` vào CẢ HAI danh sách và ghi chú lý do:

```yaml
    # ⚠️ website_hr_recruitment BẮT BUỘC (kéo theo website/website_mail/website_sms):
    #    field `hr.job.is_published` và trang công khai /jobs/detail/... là của
    #    module này. Thiếu nó: badge PUBLISHED không bật, nút "Chép link" không
    #    hiện, link công khai 404. Xem docs/DB_TEST_DATA.md:223 (DB demo 17/08).
    command: >
      bash -c "python3 /fix_stale_assets.py; exec odoo
      --database=hocba_hrm
      --init=hocba_employees,hocba_attendance,hocba_users,hocba_recruitments,hocba_payroll,hocba_hrm,hocba_finance,hocba_service,hocba_reviews,hocba_notify,hocba_timeoff,website_hr_recruitment
      --update=hocba_employees,hocba_attendance,hocba_users,hocba_recruitments,hocba_payroll,hocba_hrm,hocba_finance,hocba_service,hocba_reviews,hocba_notify,hocba_timeoff,website_hr_recruitment
      --addons-path=/mnt/extra-addons
      --dev=xml"
```

- [ ] **Step 2: Kiểm tra cú pháp compose**

```bash
docker compose -f docker-compose.nginx.yml config --quiet
```

Expected: không in ra gì (thoát 0).

- [ ] **Step 3: Commit**

```bash
git add docker-compose.nginx.yml
git commit -m "chore(deploy): stack nginx cai website_hr_recruitment cho trang tuyen dung cong khai"
```

---

### Task 4: Xác minh trên app đang chạy + cập nhật SPEC

**Files:**
- Modify: `custom-addons/hocba_recruitments/SPEC.md` §15 (bảng "Còn lại")

- [ ] **Step 1: Verify không hồi quy trên Neon (DB CÓ website)**

Stack Neon đang chạy ở cổng 8070, SPA dev ở 5173. Restart Odoo để nạp code Python mới (Odoo không hot-reload controller):

```bash
docker restart hocba_onl-odoo-1
```

Rồi trên `http://localhost:5173/hocba_hrm/static/spa/` → tab **Theo dõi tuyển dụng**: bấm **Ngừng đăng** một vị trí đang đăng → badge PUBLISHED tắt, cột trạng thái thành "Dừng tuyển"; bấm **Đăng tuyển** lại → badge bật, nút **Chép link** hiện, mở link ra đúng trang `/jobs/detail/...`. Không được có request 500 nào trong console.

- [ ] **Step 2: Ghi nhận vào SPEC**

Trong `custom-addons/hocba_recruitments/SPEC.md` §15, thêm một dòng vào bảng "Đã xử lý":

```markdown
| ✅ Nút Đăng tuyển vỡ 500 khi thiếu `website_hr_recruitment` | Controller chỉ ghi `x_published`, model tự mirror; 3 chỗ đọc dùng chung `_job_published()`; stack nginx cài thêm module. Test: `test_job_publish.py` |
```

- [ ] **Step 3: Commit**

```bash
git add custom-addons/hocba_recruitments/SPEC.md
git commit -m "docs(recruitment): ghi nhan da xu ly loi 500 nut Dang tuyen"
```
