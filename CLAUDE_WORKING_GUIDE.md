# 🤖 CLAUDE WORKING GUIDE
## Tài liệu làm việc tối ưu hóa riêng cho Claude Sonnet 4.6
### Kế thừa & phát triển từ Matrix Green Playbook của LinhNDM
**Version:** 2.0.0 | **Cập nhật:** Tháng 5/2026 | **Dùng cho:** claude.ai, API, Claude Code

---

> **Cách dùng tài liệu này:** Paste toàn bộ (hoặc section liên quan) vào đầu cuộc trò chuyện với Claude. Mỗi khi bắt đầu task mới, kiểm tra section "Quick Start" và chọn mode phù hợp.

---

## 🧠 HIỂU CLAUDE ĐỂ DÙNG ĐÚNG

### Điều Claude làm TỐT NHẤT
- **Spec Review:** Phát hiện logic gaps, contradictions, missing edge cases trong tài liệu
- **Multi-file reasoning:** Hiểu kiến trúc tổng thể khi có đủ context (1M token window)
- **Extended Thinking:** Phân tích sâu trước khi trả lời — dùng cho task phức tạp
- **Self-correction:** Tự phát hiện và fix lỗi dựa trên feedback từ environment (test results, errors)
- **EARS compliance:** Giỏi viết và verify spec theo EARS notation
- **Constitution enforcement:** Tự check output theo rules đã định

### Điều Claude CÓ THỂ SAI
- **API hallucination:** Bịa method/parameter không tồn tại — luôn chạy code sau khi nhận
- **Context Cliff:** Sau ~150K–200K tokens, có thể "quên" constraints từ đầu session
- **Tacit knowledge gap:** Không biết "convention ngầm" của team — phải viết tường minh
- **Over-engineering:** Có xu hướng thêm feature "helpful" nếu không có Out of Scope rõ ràng
- **Loop Trapping:** Khi bị stuck >3 lần, cần human interrupt và clarify root cause

### Claude làm việc tốt nhất khi
1. Context được cung cấp TRƯỚC khi hỏi (không phải trong khi chat)
2. Yêu cầu WHAT + DoD, không phải HOW
3. Có EARS spec → output nhất quán và đúng hơn nhiều
4. Mỗi task chạy trong session sạch (tránh context pollution)
5. Human review tại điểm rủi ro cao, không micromanage từng bước

---

## ⚡ QUICK START — Chọn Mode Làm Việc

### MODE 1: Vibe Mode (task đơn giản, <30 phút)
*Khi nào dùng:* CSS tweak, utility function, câu hỏi nhanh, prototype throw-away
```
Prompt trực tiếp. Không cần setup. Accept output.
```

### MODE 2: Spec Mode (task medium, 2-8 giờ)
*Khi nào dùng:* Feature mới, API endpoint, business logic có 3-10 rules
```
1. Dán [CONTEXT BLOCK] bên dưới vào đầu conversation
2. Mô tả WHAT + DoD (không mô tả HOW)
3. Yêu cầu Claude viết Shadow Plan trước khi code
4. Approve plan → Execute → Validate Gate
```

### MODE 3: Agentic Mode (task phức tạp, >1 ngày, dùng Claude Code)
*Khi nào dùng:* Multi-file refactor, greenfield module, migration
```
1. Setup AGENTS.md + CLAUDE.md trong project
2. Dán [CONSTITUTION BLOCK] vào AGENTS.md
3. Mô tả Intent + DoD
4. Claude tự Plan → Code → Test → Fix loop
5. Human gate tại: approve plan, approve risky file changes
```

---

## 📋 CONTEXT BLOCK (Copy vào đầu conversation)

Điền vào các `[...]` theo dự án của bạn:

```
=== PROJECT CONTEXT ===
Dự án: [Tên dự án]
Mục tiêu: [1-2 câu mô tả]
Tech stack: [VD: FastAPI, PostgreSQL 16, React 18, Redis 7]
Kiến trúc: [VD: Clean Architecture — domain/usecase/interface/infra]
Conventions:
  - File naming: [VD: snake_case cho Python, kebab-case cho TS]
  - Error handling: [VD: luôn wrap với fmt.Errorf("context: %w", err)]
  - Test framework: [VD: pytest + testify]

Constraints không được vi phạm:
  - [VD: Không dùng raw SQL — dùng SQLAlchemy 2.0]
  - [VD: Soft delete bắt buộc cho business entities]
  - [VD: Mọi endpoint mutating phải có JWT auth]

Current task: [Mô tả task ngắn gọn]
Spec file: [Link hoặc paste SPEC.md nếu có]
=== END CONTEXT ===
```

---

## 📐 EARS SPEC TEMPLATE (Dùng cho task medium-complex)

```markdown
# SPEC: [Feature Name]
# Version: 1.0.0 | Owner: @[name] | Status: DRAFT → APPROVED

## 1. Context & Goal
**Business problem:** [Vấn đề thực tế]
**Feature goal:** [Mục tiêu cụ thể]
**Success metric:** [Đo thành công bằng gì]
**Tech context:** [Stack liên quan]

## 2. Actors & Roles
| Actor | Mô tả | Permissions |
|-------|--------|-------------|
| [Actor 1] | [mô tả] | [quyền] |

**NOT trong scope:** [Actors không liên quan]

## 3. Functional Requirements (EARS)
<!-- Ubiquitous: THE <sys> SHALL <action> -->
<!-- Event: WHEN <event>, THE <sys> SHALL <action> -->
<!-- State: WHILE <state>, THE <sys> SHALL <action> -->
<!-- Optional: WHERE <feature> IS ENABLED, THE <sys> SHALL <action> -->
<!-- Unwanted ★: WHERE <error>, THE <sys> SHALL <response> -->

THE system SHALL ...
WHEN user ..., THE system SHALL ...
WHERE [error condition], THE system SHALL ... <!-- Thêm nhiều Unwanted nhất có thể -->

## 4. Non-functional Requirements
<!-- Phải có SỐ ĐO. "Nhanh" là vô nghĩa -->
- Response time: P95 < [Xms]
- Throughput: [N] requests/second
- Availability: [X]%

## 5. Data Model
```sql
-- Chỉ list tables/fields liên quan
-- Align với schema thực tế
```

## 6. Error Handling (Unwanted Patterns)
WHERE [input invalid] → [HTTP status + error_code + message]
WHERE [resource not found] → [404 + "resource_not_found"]
WHERE [concurrent access] → [409 + idempotency handling]

## 7. Acceptance Criteria
- [ ] GIVEN [context] WHEN [action] THEN [outcome]
- [ ] [Mỗi criterion một dòng, testable]

## 8. Out of Scope (QUAN TRỌNG — Claude sẽ "nhiệt tình" thêm nếu thiếu)
- Không có [feature X] trong sprint này
- Không thay đổi [schema Y]
- Không implement [Z]
```

---

## 🎯 PROMPT TEMPLATES

### Template 1: New Feature
```
Đọc SPEC.md + AGENTS.md + CLAUDE.md trước khi làm gì.

Task: Implement [feature name] theo SPEC.md §3.

TRƯỚC KHI CODE — viết Shadow Plan:
1. Tôi hiểu task này là: [1 câu]
2. Files sẽ CREATE: [list]
3. Files sẽ MODIFY: [list]
4. Files KHÔNG thay đổi: [list]
5. Test strategy: [brief]
6. Risks & Assumptions: [list]

DỪNG và hiển thị Shadow Plan. Chờ "proceed" trước khi code.

Definition of Done:
- [ ] Tests pass: [lệnh test]
- [ ] No lint errors: [lệnh lint]
- [ ] Constitution self-check: PASS
- [ ] Mọi SHALL trong spec có implementation
- [ ] Mọi Unwanted pattern có error handler
- [ ] Không code Out of Scope
```

### Template 2: Bug Fix
```
Bug: [behavior hiện tại]
Expected: [behavior đúng]
Reproduce: [bước reproduce]

QUAN TRỌNG: Tìm root cause TRƯỚC khi fix.
"Add null check" không acceptable nếu không giải thích tại sao null.

Investigation:
1. Đọc error logs/stack trace
2. Tìm root cause (không chỉ fix symptom)
3. Xác định minimal fix

DoD:
- Root cause documented
- Fix không introduce regression
- Test case thêm vào để prevent recurrence
```

### Template 3: Spec Review (dùng trước khi lock spec)
```
Review spec này với tư cách Senior Engineer. ĐỪNG viết code.

Trả lời 4 câu hỏi:
1. LOGIC GAPS: Trạng thái/kịch bản chưa được xử lý? Format: "Nếu [X], system làm gì?"
2. CONTRADICTIONS: Yêu cầu nào mâu thuẫn? Trích dẫn cụ thể.
3. MISSING EDGE CASES: 5 edge cases quan trọng nhất chưa đề cập (ưu tiên: security, concurrency, data integrity).
4. AMBIGUOUS: Yêu cầu nào có thể hiểu theo >1 cách?

Format: numbered list, 1-3 câu/issue. Không suggest giải pháp — chỉ chỉ ra vấn đề.
DỪNG sau khi liệt kê. Chờ tôi trả lời trước khi tiếp tục.

--- SPEC ---
[paste SPEC.md]
```

### Template 4: Adversarial Spec Test
```
Đóng vai developer muốn implement ĐÚNG spec nhưng tạo code SAI nhất có thể.

Liệt kê:
1. 5 cách implement "đúng spec" nhưng SAI business intent
2. 3 edge cases spec không cover, cho phép behavior tùy ý
3. 2 invariants bị thiếu có thể gây security issue

Với mỗi item: chỉ ra line/section trong spec cần update.

--- SPEC ---
[paste SPEC.md]
```

### Template 5: Validation Gate
```
Chạy Validation Gate cho code vừa được implement.

L1 — Automated Quality:
- [ ] [test command] → ALL PASS?
- [ ] [lint command] → ZERO errors?
- [ ] [type check] → CLEAN?

L2 — Spec Compliance:
- [ ] Mỗi SHALL trong SPEC.md có implementation (list from-to)?
- [ ] EARS tags trong code (search "# EARS[")?
- [ ] Không có code Out of Scope?
- [ ] Mọi WHERE error condition có handler?

L3 — Constitution:
- [ ] Không có hardcoded secrets?
- [ ] Auth middleware có trên endpoints mutating?
- [ ] Input validation present?
- [ ] [Thêm rules từ CONSTITUTION.md của dự án]

L4 — Acceptance:
- [ ] Chạy qua từng checkbox trong SPEC §7?

Format: ✅ PASS / ❌ FAIL + details cho từng item.
Nếu có FAIL: list ra cụ thể, đừng auto-fix — để tôi quyết định.
```

---

## 🏗️ CONSTITUTION.md TEMPLATE

*File này đặt trong `.sdd/constitution.md` hoặc root project. Claude sẽ tự check trước khi submit code.*

```markdown
# PROJECT CONSTITUTION
# Version: 1.0.0 | Owner: @[name] | Status: LOCKED
# Áp dụng cho: Mọi AI agent, mọi developer, mọi PR

## LAYER 1 — Hard Rules (CI fail ngay nếu vi phạm)

### SEC-01: No Secrets in Code
THE system SHALL NOT lưu bất kỳ secret nào dưới dạng plaintext
trong source code, config files, hoặc logs.
Áp dụng cho: API keys, passwords, tokens, PII.
Enforcement: git-secrets pre-commit hook.

### SEC-02: Authentication Required
THE system SHALL yêu cầu xác thực cho mọi endpoint mutating
(POST, PUT, PATCH, DELETE).
Exception: public endpoints phải có comment // PUBLIC ENDPOINT + lý do.

### SEC-03: Input Validation
THE system SHALL validate và sanitize tất cả user input
trước khi xử lý hoặc lưu vào database.
Không raw SQL với user input chưa được parameterize.

### DATA-01: Soft Delete
THE system SHALL dùng soft-delete (deleted_at) thay vì hard-delete
cho mọi entity business-critical.

## LAYER 2 — Architectural Constraints (cần approved exception)

### ARCH-01: Service Boundary
Services SHALL giao tiếp qua API contracts.
Direct DB access từ service khác là PROHIBITED.

### ARCH-02: Async Operations
Operations >2 giây SHALL được xử lý asynchronously
qua message queue (Celery/Kafka/Bull).

### ARCH-03: Idempotency
Mọi mutating API endpoint SHALL có idempotency mechanism.

## LAYER 3 — Engineering Standards (non-blocking, document deviation)

### ENG-01: Test Coverage
Minimum 80% cho business logic modules.
Exception: proof-of-concept (phải xóa trước merge main).

### ENG-02: API Documentation
Mọi public API endpoint SHALL có OpenAPI documentation.
Cập nhật openapi.yaml TRƯỚC KHI implement endpoint.

### ENG-03: Error Response Format
{ "error_code": "...", "message": "...", "request_id": "..." }
Stack trace KHÔNG expose ra client.

## AI AGENT SELF-CHECK PROTOCOL

Trước khi submit bất kỳ output nào, Claude chạy checklist:

CHECKLIST SEC:
  [ ] Không có hardcoded secrets (grep: password=, key=, token=, secret=)
  [ ] Mọi endpoint mutating có auth middleware
  [ ] Input validation present trước DB operations

CHECKLIST ARCH:
  [ ] Không cross-service DB access
  [ ] Async operations >2s dùng queue
  [ ] Mutating endpoints có idempotency

CHECKLIST ENG:
  [ ] Unit tests cover happy path + error cases
  [ ] EARS tags trong code comments
  [ ] Error responses không chứa stack trace

CONSTITUTION SELF-CHECK REPORT FORMAT:
=== SELF-CHECK ===
Layer 1 (Hard Rules): ✅ PASS / ❌ VIOLATION: [details]
Layer 2 (Arch):       ✅ PASS / ⚠ EXCEPTION NEEDED: [details]
Layer 3 (Standards):  ✅ PASS / ⚠ DEVIATION: [reason]
=================
```

---

## 📁 PROJECT STRUCTURE TEMPLATE

```
my-project/
├── .sdd/
│   ├── constitution.md          # ← Claude self-check rules
│   ├── shared_context.md        # ← Multi-agent sync point
│   ├── constraints/
│   │   ├── global.md            # Stack, naming, approved packages
│   │   ├── business.md          # Auth rules, domain glossary, PII
│   │   └── safety.md            # Forbidden actions, mandatory actions
│   ├── specs/
│   │   └── feat-{name}/
│   │       ├── SPEC.md          # Locked khi approved
│   │       ├── PLAN.md          # AI-generated arch plan
│   │       ├── TASKS.md         # Atomic task breakdown
│   │       └── CHANGELOG.md
│   └── skills/
│       └── *.md                 # Domain expertise (SQL, Security, etc.)
├── AGENTS.md                    # Agent persona + allowed/forbidden
├── CLAUDE.md                    # Project DNA + lesson learned
├── plan.md                      # Plan-Act-Check tracking (per session)
└── src/
```

---

## 📝 AGENTS.md TEMPLATE

```markdown
# AGENTS.md
# Version: 1.0.0 | Owner: @[name]
# Claude đọc file này trước mỗi session

## PERSONA
Bạn là Senior [Stack] Developer với [N]+ năm kinh nghiệm.
Philosophy: correctness > performance > readability > terseness.
Câu hỏi trước khi code: "Có cách đơn giản hơn không?"

## EXPERTISE
- Primary: [main stack]
- Secondary: [secondary tools]

## TECH STACK (immutable trừ khi có RFC)
[Liệt kê cụ thể — ví dụ:]
Language: Python 3.12+
HTTP: FastAPI 0.111+
Database: PostgreSQL 16 + SQLAlchemy 2.0 (KHÔNG dùng raw SQL)
Cache: Redis 7 + redis-py
Testing: pytest + pytest-asyncio

## NAMING CONVENTIONS
[VD:]
Files: snake_case (user_service.py)
Classes: PascalCase (UserService)
Functions: snake_case (get_user_by_id)
Constants: SCREAMING_SNAKE

## APPROVED PACKAGES
[List packages được phép dùng]

## BANNED PACKAGES (với lý do)
[List packages bị cấm + lý do cụ thể]

## DECISION RULES
- Không chắc về architecture → hỏi, không assume
- Thấy violation constitution → báo cáo, không workaround
- Spec không cover edge case → dừng lại và hỏi

## TOOLS BẠN ĐƯỢC PHÉP
Read/write: src/, tests/, docs/, .sdd/
Execute: [pytest/jest/go test], [ruff/eslint], git status, git diff
KHÔNG: delete files, push main, thêm dependency

## KHÔNG ĐƯỢC PHÉP (cần human confirm)
- Xóa bất kỳ file nào
- Thêm dependency vào package.json/requirements.txt
- Modify .github/workflows/
- Commit vào main/production
- DROP TABLE, TRUNCATE trong migrations

## PHẢI LÀM (mandatory)
- Chạy Constitution Self-Check trước khi submit code
- Update plan.md sau mỗi completed step
- Shadow Plan trước khi execute task mới
- Báo cáo edge case không có trong spec
- "Tôi không chắc về X. Bạn muốn xử lý thế nào?" khi ambiguous
```

---

## 📝 CLAUDE.md TEMPLATE

```markdown
# CLAUDE.md — Project Memory
# Version: 1.0.0 | Updated: [date]

## TL;DR (30 giây đọc)
[Dự án là gì, làm gì, cho ai]
Stack: [brief]
Kiến trúc: [brief]
Sprint hiện tại: [focus]

## KIẾN TRÚC
[Describe architecture in text — no need for diagrams]

Pattern: [Clean Architecture / Hexagonal / MVC / etc.]
Data flow: [brief description]

## ARCHITECTURE DECISION RECORDS (ADR)
### ADR-001: [Tên quyết định]
**Quyết định:** [Chọn X thay vì Y]
**Lý do:** [Tại sao X]
**Không chọn:** [Y vì ...]

## PATTERNS & CONVENTIONS
```[language]
# Ví dụ code pattern chuẩn của project
# VD: cách handle error
# VD: cách viết service method
# VD: cách structure test
```

## ANTI-PATTERNS (đừng làm)
- [Anti-pattern 1 + lý do]
- [Anti-pattern 2 + lý do]

## KNOWN ISSUES & WORKAROUNDS
- [Issue 1]: [workaround + lý do không fix thẳng]

## LESSON LEARNED (từ incidents)
- [Date] [Module]: [Vấn đề] → [Giải pháp]

## CURRENT SPRINT FOCUS
[Những gì đang được build, task nào in-progress]
```

---

## 🔄 SESSION MANAGEMENT

### Bắt đầu session mới
```bash
# Script chuẩn bị context cho session mới
echo "=== AGENT CONTEXT ==="
echo "## Project Identity"
head -30 AGENTS.md
echo "## Current State"
cat plan.md | grep -A5 "IN PROGRESS"
echo "## Recent commits"
git log --oneline -5
echo "## Test status"
[pytest/go test/npm test] --no-header -q 2>&1 | tail -5
```

### plan.md format (Plan-Act-Check)
```markdown
# [Task ID]: [Task Name]
# Status: IN PROGRESS | Session: [date-time]

## Shadow Plan (approved [time])
- [x] Step 1: Read spec §3
- [x] Step 2: Create [file]
- [ ] Step 3: Write tests
- [ ] Step 4: Run tests + fix

## Current Status
Completed: Steps 1-2. [file] created.
Next: Write unit tests.

## Issues Encountered
- [Issue]: [Resolution/Assumption made]

## Failed Attempts (giữ lại để học)
- Attempt: [approach]
- Result: [outcome]
- Decision: [why discarded]

## Rollback Point
git commit: [hash] ([message])
```

### Khi context window sắp đầy (>150K tokens)
```
Tóm tắt session này trong 500 tokens:
1. Task đang làm là gì
2. Files đã thay đổi (list)
3. Constraints quan trọng nhất (list)
4. Step tiếp theo cần làm
5. Assumptions đã dùng

[Paste summary này vào session mới]
```

---

## 📊 THÔNG TIN MODEL CẬP NHẬT (Tháng 5/2026)

### Models hiện tại (để chọn đúng cho task)

| Model | Context | Input | Output | Best for |
|-------|---------|-------|--------|----------|
| **Claude Sonnet 4.6** | 1M tokens (beta) | $3/MTok | $15/MTok | Daily coding, spec, reasoning — **best value** |
| Claude Opus 4.6 | 1M tokens | $5/MTok | $25/MTok | Complex architecture, deep analysis |
| Claude Opus 4.7 | 1M tokens | $5/MTok | $25/MTok | Hardest tasks, formal verification |
| Claude Opus 4.8 | 1M tokens | $10/MTok (fast) | $50/MTok (fast) | Tốc độ cao, production-critical |
| Claude Haiku 4.5 | 200K tokens | $0.80/MTok | $4/MTok | Boilerplate, routing, simple tasks |

> **Thay đổi quan trọng 2026:**
> - **1M token context window** (beta) — đủ chứa ~600K dòng code
> - **Context compaction:** Claude Code tự summarize khi context đầy
> - **Sonnet 4.6 > Opus 4.5** trong 59% coding tests — không cần trả Opus price cho daily work

### Multi-model strategy tối ưu chi phí
```
Haiku 4.5   → Boilerplate, CRUD generation, routing, simple classification
Sonnet 4.6  → Business logic, spec review, debugging, architecture (80% tasks)
Opus 4.7    → Payment flows, security audit, formal spec, complex refactor
```

### Claude Code (2026) — Tính năng mới cần biết
- `/loop` — Recurring tasks chạy tự động lặp lại
- `/voice` — Push-to-talk (spacebar)
- `/context` — Analyze context health, optimization tips
- `/effort xhigh` — Tăng thinking budget cho hardest tasks
- `ultrathink` — Maximum reasoning mode
- **Dynamic workflows:** Một task có thể orchestrate hàng chục sub-agents
- **Named sub-agents:** Đặt tên và track từng agent trong team
- **MCP OAuth 9728:** Chuẩn auth mới cho MCP servers
- **Self-hosted sandboxes (beta):** Agent chạy trong infrastructure của bạn

---

## 💰 BUDGET ESTIMATION

### Chi phí thực tế per task (Sonnet 4.6)
```
Normal feature task:    ~28K tokens = ~$0.17
Loop task (stuck):      ~280K tokens = ~$1.70 (tránh!)
Complex refactor:       50-200K tokens = $0.30-$1.20
Full spec review:       ~15K tokens = ~$0.09

Sprint (20 features, 2 devs): ~$7-15/sprint
```

### Tối ưu chi phí
1. **Prompt caching:** System prompt >1024 tokens → dùng cache_control → tiết kiệm 90%
2. **Haiku cho simple tasks:** 75% cheaper, chất lượng OK cho boilerplate
3. **Hard token limit:** `maxTokensPerTask: 50000` trong Cline
4. **1 task = 1 session:** Tránh context pollution → tránh loop → tiết kiệm token
5. **Selective file reads:** Chỉ đọc files liên quan — không dump toàn codebase

---

## ⚠️ ANTI-PATTERNS & RED FLAGS

### Anti-pattern 1: Over-Specification
**Dấu hiệu:** SPEC.md >200 dòng cho task đơn giản, mô tả HOW thay vì WHAT
**Fix:** Chạy Risk × Complexity Matrix trước khi viết spec

### Anti-pattern 2: Blind Trust
**Dấu hiệu:** Merge code vì "tests pass" mà không qua Validation Gate 4 lớp
**Fix:** "Agent says done" = bắt đầu kiểm định, không phải kết thúc

### Anti-pattern 3: Context Amnesia
**Dấu hiệu:** Claude lặp lại pattern đã deprecated (VD: dùng bcrypt sau khi team switch sang argon2id)
**Fix:** Update AGENTS.md ngay khi có quyết định thay đổi

### Anti-pattern 4: Micromanagement
**Dấu hiệu:** Interrupt Claude sau mỗi dòng code để "guide"
**Fix:** Approve plan → let it run → review output. Interrupt chỉ khi vi phạm constitution hoặc loop >3 lần.

### Red Flags trong Claude Output
| Dấu hiệu | Ý nghĩa | Action |
|----------|---------|--------|
| Confident answer khi spec mơ hồ | Có thể hallucinate | Clarify trước khi proceed |
| Không hỏi gì khi spec phức tạp | Đang assume — nguy hiểm | Chạy Clarification Trigger |
| Cùng error sau 3 lần fix | Loop trap | Interrupt + clarify root cause |
| Thêm feature không có trong spec | "Nhiệt tình quá mức" | Kiểm tra Out of Scope |
| Method tên lạ không có docs | API hallucination | Verify ngay trước khi dùng |

---

## 🎓 DECISION FRAMEWORK

### Khi nào dùng gì?

```
Task là gì?
│
├─ Hackathon/Prototype/Chưa biết mình muốn gì
│  → Vibe Mode (không cần spec, prompt trực tiếp)
│
├─ Landing page/CSS/UI tweak nhỏ
│  → Vibe Mode
│
├─ Utility function (<20 lines, rõ ràng)
│  → Sketch: 5-10 dòng spec + prompt
│
├─ Feature có 3-10 business rules, risk vừa
│  → Spec Mode: EARS đầy đủ + Clarification Trigger
│
└─ Payment/Auth/Compliance/Legacy refactor
   → Agentic Mode: Full Spec + State Diagram + Constitution

Luôn làm (bất kể level):
✅ Clarification Trigger nếu >5 business rules
✅ EARS notation cho requirements
✅ Out of Scope rõ ràng
✅ Shadow Plan trước khi execute
✅ Validation Gate trước khi merge
```

### Core (cần Full Spec) vs Shell (Agent-first OK)

| Core (SDD) | Shell (ADD) |
|-----------|-------------|
| DB schema, migrations | UI components |
| API contracts | CRUD operations |
| Authentication/Authorization | Form validation |
| Payment flows | Email templates |
| Security policies | Boilerplate |
| Data model invariants | Tests từ accepted spec |

**3 câu hỏi phân biệt:**
1. Sai có sửa được mà không migration? (NO → Core)
2. Có consumer ngoài module? (YES → Core)
3. Liên quan security/compliance? (YES → Core)

---

## 🔑 10 QUY TẮC VÀNG

1. **"Fix the Spec, not the Code"** — Khi AI sai, sửa spec rồi re-generate. Đừng sửa tay code.

2. **Spec trước, code sau** — Nếu AI phải đoán → bạn đã thất bại. *"If AI has to guess, you have already failed."*

3. **Bad Spec + Good AI = Perfect execution of wrong thing** — Nguy hiểm hơn không có spec.

4. **1 task = 1 session mới** — Context pollution làm Claude "ngáo". Fresh context = better output.

5. **WHAT + DoD, không phải HOW** — Mô tả outcome và điều kiện xong, để Claude tự chọn HOW trong constraints.

6. **Unwanted patterns là quan trọng nhất** — 40-60% production code là error handling, nhưng spec thường chỉ có 5-10% error cases.

7. **Constitution enforce trước, không phải sau** — Rules phải vào AGENTS.md trước khi Claude bắt đầu làm, không phải nhắc nhở sau khi nó sai.

8. **Validation Gate 4 lớp là bắt buộc** — "Tests pass" ≠ "đúng spec". Claude tự test thường viết test theo implementation sai.

9. **Clarification Trigger trước task phức tạp** — Bắt Claude liệt kê điểm chưa rõ TRƯỚC khi làm. 1 phút clarify = tiết kiệm 10 phút debug.

10. **Update AGENTS.md khi quyết định thay đổi** — Context Amnesia là lý do Claude lặp lại pattern cũ đã deprecated.

---

## 📌 CHECKLIST TRƯỚC KHI BẮT ĐẦU MỌI TASK

```
□ Đã chọn đúng Mode (Vibe/Spec/Agentic)?
□ Context block đã được paste vào đầu conversation?
□ Đây là CORE hay SHELL? (CORE → bắt buộc Full Spec)
□ Out of Scope đã được viết rõ?
□ EARS Unwanted patterns đủ chưa? (mục tiêu: 30-40% total requirements)
□ Definition of Done rõ ràng và testable?
□ Nếu >5 business rules: Clarification Trigger đã chạy?
□ Shadow Plan đã được approve trước khi execute?
□ plan.md đã được tạo/cập nhật?
□ Token budget estimate hợp lý (<50K tokens per task)?
```

---

*Tài liệu này được tạo bởi Claude Sonnet 4.6, kế thừa từ Matrix Green Playbook của LinhNDM (linhndm.io.vn), với các cập nhật về model capabilities, pricing và tooling tính đến tháng 5/2026.*

*Phiên bản ngắn hơn: Giữ lại CONTEXT BLOCK + SPEC TEMPLATE + PROMPT TEMPLATES + 10 QUY TẮC VÀNG là đủ cho 90% use cases.*
