# 🏛️ HOCBA HRM — UNIVERSAL AI AGENT RULES

> **Mục đích:** File này định nghĩa quy tắc bắt buộc cho MỌI AI model (Gemini, Claude, GPT, v.v.)
> khi làm việc trên dự án ISP490_G2_HOCBA_HRM. Dù user hỏi gì, AI phải đi qua đúng
> quy trình 7 pha bên dưới trước khi trả lời hoặc thực hiện thay đổi.
>
> **Phạm vi:** Áp dụng cho mọi request liên quan đến code, spec, feature, fix bug, refactor.
> Những câu hỏi đơn giản không liên quan đến code (ví dụ: "giờ mấy giờ?") thì bỏ qua quy trình.

---

## ⚙️ NGUYÊN TẮC CHUNG

1. **Spec là code trên giấy** — Mọi thay đổi code PHẢI phản ánh ngược lại spec. Spec và code luôn đồng nhất.
2. **Knowledge trước, Code sau** — Không bao giờ code khi chưa hiểu nghiệp vụ.
3. **Chuẩn Senior** — Output phải ở cấp độ senior engineer: rõ ràng, có lý do, có edge cases.
4. **Docker là bước cuối** — Mọi task kết thúc bằng việc build lại Docker để user test được ngay.
5. **Tự động Build & Deploy Docker** — Mỗi lần code xong hoặc sửa/thêm/bớt bất kỳ file/DB/model nào, AI PHẢI tự động chạy `npm run build` (nếu FE đổi) và tự động thực thi lệnh build Docker bản ONLINE (`docker compose -f docker-compose.yml -f docker-compose.onl.yml up -d --build`) để áp dụng ngay lên môi trường chạy thực tế mà không bắt user phải thao tác thủ công.

---

## 🔄 QUY TRÌNH 7 PHA BẮT BUỘC

Mọi request của user PHẢI đi qua 7 pha theo thứ tự. Không được bỏ pha, không được đảo thứ tự.

### ═══════════════════════════════════════════════════
### PHA 1: 📚 ĐỌC KNOWLEDGE (Kiến thức chuyên môn)
### ═══════════════════════════════════════════════════

**Mục đích:** Nắm kiến thức nghiệp vụ và kỹ thuật cấp senior trước khi động tay vào code.

**Thư mục Knowledge:** `D:\FPT\DO_an\code\ISP490_G2_HOCBA_HRM\Knowledge\`

Cấu trúc Knowledge Base:
```
Knowledge/
├── BE/           → Backend architecture, Odoo patterns
├── FE/           → Frontend (React, JS/TS, UI/UX, Performance, a11y)
│   ├── 01-core-web/
│   ├── 02-javascript/
│   ├── 03-typescript/
│   ├── 04-react-ecosystem/
│   ├── 05-architecture/
│   ├── 06-performance/
│   ├── 07-accessibility/
│   └── 08-ui-ux/
├── DA/           → Data Architecture, SQL, dbt, Visualization
├── PM/           → Product Strategy, Estimation, Execution
├── QA/           → Testing Strategy, Test Design, Unit Testing
├── DevOps_SRE/   → Docker, K8s, IaC, Cloud Architecture
├── SECURITY/     → Security Foundations, Web Vulns, Secure Design
└── financial_app_best_practices.md
```

**Hành động:**
- Xác định request của user thuộc domain nào (BE, FE, DA, PM, QA, DevOps, Security).
- Đọc các file knowledge liên quan trong thư mục tương ứng.
- Nếu request cross-domain (ví dụ: feature mới cần cả BE + FE), đọc cả 2 domain.
- Ghi nhớ best practices, patterns, anti-patterns từ knowledge để áp dụng khi code.

**Output pha này:** AI hiểu rõ nghiệp vụ + kỹ thuật liên quan, sẵn sàng phân tích dự án.

---

### ═══════════════════════════════════════════════════
### PHA 2: 📖 ĐỌC DOCS DỰ ÁN (Hiểu project hiện tại)
### ═══════════════════════════════════════════════════

**Mục đích:** Hiểu dự án HOCBA HRM trước khi sửa — biết cái gì đã có, cái gì đã quyết định.

**Thư mục Docs:** `D:\FPT\DO_an\code\ISP490_G2_HOCBA_HRM\docs\`

Cấu trúc Docs:
```
docs/
├── README.md                        → Tổng quan dự án
├── DB_SCHEMA_VA_MIGRATION.md        → Schema database & migration
├── QUY_UOC_FRONTEND.md              → Quy ước coding frontend
├── QUY_TRINH_TUYEN_DUNG.md          → Quy trình tuyển dụng (nghiệp vụ)
├── SPEC_EMPLOYEES_DAC_TA_v2.1.md    → Spec employees (đặc tả chi tiết)
├── SPEC_API_RECRUITMENT.md          → Spec API tuyển dụng
├── SPEC_API_TIMEOFF.md              → Spec API nghỉ phép
├── SPEC_USERS_AUTH.md               → Spec xác thực users
├── SPEC_HRM_SPA_API.md              → Spec HRM SPA API
├── DEV_LOCAL.md                     → Hướng dẫn dev local
├── DEMO_FLOW_EMPLOYEES.md           → Flow demo employees
├── DB_TEST_DATA.md                  → Test data cho database
├── MANUAL_TEST_GUIDE.md             → Hướng dẫn test thủ công
├── CUSTOMER_VERIFY_QUESTIONS.md     → Câu hỏi verify với khách hàng
├── specs/                           → Functional Specs chi tiết
│   └── payroll/                     → Specs payroll (FS-PAY-001 → 005)
└── superpowers/
    ├── specs/                       → 35+ design specs cho từng feature
    └── plans/                       → Implementation plans
```

**Hành động:**
- Đọc `docs/README.md` để nắm tổng quan.
- Đọc các SPEC liên quan đến request (ví dụ: nếu user hỏi về payroll → đọc `docs/specs/payroll/`).
- Đọc các design specs trong `docs/superpowers/specs/` nếu liên quan.
- Đọc `docs/QUY_UOC_FRONTEND.md` nếu task liên quan FE.
- Đọc `docs/DB_SCHEMA_VA_MIGRATION.md` nếu task liên quan DB.

**Output pha này:** AI hiểu project scope, architecture hiện tại, các quyết định đã có.

---

### ═══════════════════════════════════════════════════
### PHA 3: 📐 ĐỌC & CẬP NHẬT SPEC (Code trên giấy)
### ═══════════════════════════════════════════════════

**Mục đích:** Spec = code trên giấy. PHẢI đọc spec liên quan, đánh giá và cải tiến trước khi code.

**Vị trí specs:**
- `docs/SPEC_*.md` — Spec API & nghiệp vụ chính
- `docs/specs/payroll/FS-PAY-*.md` — Spec payroll chi tiết (BPMN + EARS)
- `docs/superpowers/specs/*.md` — Design specs cho từng feature

**Hành động:**
- Tìm spec liên quan đến request. Nếu chưa có spec → tạo mới theo EARS format.
- Đọc spec hiện tại, đánh giá:
  - Có đầy đủ edge cases không?
  - Có thiếu error handling (Unwanted behaviors) không?
  - Data model có đồng bộ với DB hiện tại không?
  - Non-functional requirements có SỐ ĐO cụ thể không?
- Cải tiến spec ở cấp senior: thêm edge cases, error flows, security considerations.
- Đảm bảo spec phản ánh đúng trạng thái project hiện tại + cải tiến tương lai.

**EARS Format tham chiếu** (từ `CLAUDE_WORKING_GUIDE.md`):
```
Ubiquitous:  THE <system> SHALL <action>
Event:       WHEN <event>, THE <system> SHALL <action>
State:       WHILE <state>, THE <system> SHALL <action>
Optional:    WHERE <feature> IS ENABLED, THE <system> SHALL <action>
Unwanted ★:  WHERE <error>, THE <system> SHALL <response>
```

**Output pha này:** Spec được review/cập nhật/tạo mới, sẵn sàng làm blueprint cho code.

---

### ═══════════════════════════════════════════════════
### PHA 4: 🔍 RESEARCH (Khảo sát thêm nếu cần)
### ═══════════════════════════════════════════════════

**Mục đích:** Bổ sung thông tin từ bên ngoài nếu Knowledge + Docs chưa đủ.

**Khi nào cần research:**
- API/library chưa từng dùng trong project.
- Best practices mới cho domain cụ thể (ví dụ: payroll compliance, labor law).
- Patterns giải quyết vấn đề mà Knowledge chưa cover.
- Odoo 19 API changes hoặc breaking changes.
- Tham khảo cách các hệ thống HRM khác giải quyết vấn đề tương tự.

**Hành động:**
- Dùng web search để tìm thông tin.
- Đọc documentation chính thức (Odoo docs, React docs, v.v.).
- Ghi chú lại findings để bổ sung vào spec nếu cần.

**Khi nào KHÔNG cần research:**
- Knowledge + Docs đã đủ thông tin.
- Task đơn giản, đã có pattern sẵn trong codebase.

**Output pha này:** Có đủ thông tin và tư liệu để bắt đầu code.

---

### ═══════════════════════════════════════════════════
### PHA 5: 💻 CODE (Thực hiện code)
### ═══════════════════════════════════════════════════

**Mục đích:** Implement solution dựa trên spec đã review + knowledge đã đọc.

**Nguyên tắc code:**
- Code PHẢI tuân theo spec (Pha 3). Nếu phát hiện spec sai khi code → quay lại sửa spec trước.
- Tuân thủ `docs/QUY_UOC_FRONTEND.md` cho code frontend.
- Tuân thủ patterns trong `Knowledge/BE/` cho code backend (Odoo).
- Security considerations từ `Knowledge/SECURITY/`.
- Error handling đầy đủ theo Unwanted behaviors trong spec.
- Có comments giải thích WHY, không chỉ WHAT.

**Cấu trúc code project:**
```
custom-addons/          → Backend Odoo modules
├── hocba_employees/    → Module quản lý nhân viên
├── hocba_attendance/   → Module chấm công
├── hocba_users/        → Module quản lý tài khoản
├── hocba_recruitments/ → Module tuyển dụng
├── hocba_payroll/      → Module bảng lương
├── hocba_hrm/          → Module HRM tổng hợp
├── hr_holidays_modern/ → Module nghỉ phép
└── hb_timeoff_*/       → Các module timeoff extensions

frontend/               → Frontend React SPA
└── src/
    └── features/       → Feature-based folder structure
```

**Output pha này:** Code hoàn chỉnh, tuân thủ spec, ready for test.

---

### ═══════════════════════════════════════════════════
### PHA 6: 📝 CẬP NHẬT SPEC (Đồng bộ spec với code)
### ═══════════════════════════════════════════════════

**Mục đích:** Đảm bảo spec và code LUÔN ĐỒNG NHẤT. Spec phản ánh chính xác code hiện tại.

**Hành động:**
- Sau khi code xong, review lại spec tương ứng.
- Cập nhật spec nếu có bất kỳ thay đổi nào so với bản spec trước khi code:
  - Data model changes.
  - API endpoint changes.
  - New edge cases phát hiện khi code.
  - Error handling thực tế khác với spec ban đầu.
- Cập nhật version number của spec (ví dụ: v1.0 → v1.1).
- Thêm changelog entry vào cuối spec nếu có.

**Output pha này:** Spec đồng bộ 100% với code hiện tại.

---

### ═══════════════════════════════════════════════════
### PHA 7: 🐳 BUILD DOCKER (Bản ONLINE Neon Cloud)
### ═══════════════════════════════════════════════════

**Mục đích:** Build lại Docker (môi trường Online Neon) để user test được ngay.

> ⚠️ **PORT VÀ PROJECT NAME CHÍNH XÁC (KHÔNG ĐƯỢC SAI):**
>
> | Stack | Project name | Port host | URL | DB |
> |---|---|---|---|---|
> | **ONLINE** | `hocba_onl` | **8070** | http://localhost:8070 | Neon cloud DB |
>
> **Tập trung hoàn toàn vào môi trường Online Neon.** Không cần chạy bản local nữa.

> ⚠️ **BẮT BUỘC BUILD FE TRƯỚC KHI BUILD DOCKER:**
> Nếu task có thay đổi bất kỳ file nào trong `frontend/src/`, AI PHẢI chạy
> `npm run build` trong thư mục `frontend/` TRƯỚC khi build Docker.
> FE dùng Vite — source code trong `src/` KHÔNG được serve trực tiếp;
> phải compile ra `custom-addons/hocba_hrm/static/spa/` thì Odoo mới nhận.

**Bước 0 (bắt buộc nếu FE thay đổi) — Build Frontend:**
```bash
# Chạy trong thư mục frontend/
npm run build
```

**Build bản ONLINE** (Neon cloud DB, project `hocba_onl`, port **8070**):
```bash
docker compose -f docker-compose.yml -f docker-compose.onl.yml up -d --build
```

**Working directory:** `D:\FPT\DO_an\code\ISP490_G2_HOCBA_HRM`

**Hành động (theo thứ tự):**
1. Nếu FE thay đổi → `cd frontend && npm run build` trước.
2. Chạy build bản ONLINE.
3. Kiểm tra output build, báo lỗi nếu có.
4. Báo user URL để test:
   - **Online (Neon, `hocba_onl`):** http://localhost:8070

**Output pha này:** Stack Docker ONLINE đã build với code mới nhất, user có thể test ngay.

---

## 📋 CHECKLIST TÓM TẮT (AI tự kiểm tra mỗi task)

```
□ Pha 1: Đã đọc Knowledge liên quan?
□ Pha 2: Đã đọc Docs dự án liên quan?
□ Pha 3: Đã đọc/cập nhật/tạo Spec?
□ Pha 4: Đã research thêm (nếu cần)?
□ Pha 5: Đã code theo spec + knowledge?
□ Pha 6: Đã cập nhật spec khớp code?
□ Pha 7: Đã build Docker (local + online)?
```

---

## 🚫 NGOẠI LỆ — Khi nào KHÔNG cần đi qua 7 pha

Các trường hợp sau được phép bỏ qua hoặc rút gọn quy trình:

1. **Câu hỏi đơn giản** (không liên quan code): "Giải thích cái này", "Giờ mấy giờ?" → Trả lời trực tiếp.
2. **Fix typo / CSS nhỏ**: Chỉ cần Pha 5 (code) + Pha 7 (build Docker).
3. **Chỉ hỏi review/giải thích code**: Pha 1 + 2 + 3 (đọc context), trả lời, không cần build.
4. **Chỉ yêu cầu build Docker**: Chỉ cần Pha 7.
5. **Chỉ yêu cầu update spec**: Pha 1 + 2 + 3 + 6 (không code, không build).

---

## 📁 CẤU TRÚC FILE QUAN TRỌNG

| File/Folder | Mô tả |
|---|---|
| `Knowledge/` | Kiến thức senior (BE, FE, DA, PM, QA, DevOps, Security) |
| `docs/` | Tài liệu dự án (specs, guides, test plans) |
| `docs/specs/` | Functional Specs chi tiết (payroll) |
| `docs/superpowers/specs/` | Design specs cho từng feature (35+ files) |
| `custom-addons/` | Backend Odoo modules |
| `frontend/` | Frontend React SPA |
| `docker-compose.yml` | Docker base config |
| `docker-compose.local.yml` | LOCAL stack: project `isp490_g2_hocba_hrm`, **port 8069** → http://localhost:8069, DB Postgres |
| `docker-compose.onl.yml` | ONLINE stack: project `hocba_onl`, **port 8070** → http://localhost:8070, DB Neon. Volume TÁCH BIỆT |
| `CLAUDE_WORKING_GUIDE.md` | Guide riêng cho Claude (EARS format, modes) |
| `.agents/AGENTS.md` | **FILE NÀY** — Rules cho mọi AI model |

---

## 🔑 LƯU Ý CUỐI

- **Quy trình này là BẮT BUỘC.** AI phải tường minh liệt kê đang ở pha nào khi làm việc.
- **Nếu thiếu thông tin** → hỏi user, KHÔNG bịa.
- **Nếu Knowledge chưa đủ** → research web (Pha 4), KHÔNG đoán.
- **Mọi output phải ở cấp senior** — không chấp nhận code/spec ở mức junior.
- **Spec và code LUÔN đồng nhất** — đây là nguyên tắc sống còn.
