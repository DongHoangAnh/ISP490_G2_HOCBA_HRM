# Time Off Frontend Cleanup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dọn trùng lặp + fix bug badge + đồng nhất UX cho SPA màn Nghỉ phép theo spec `docs/superpowers/specs/2026-07-07-timeoff-frontend-cleanup-design.md`.

**Architecture:** 3 lớp tuần tự — (1) nền móng: hook `useFetch` (stale-while-revalidate) + 5 component chung; (2) migrate 10 file timeoff sang nền móng, hành vi giữ nguyên; (3) fix hành vi: badge Chờ duyệt, ConfirmModal thay `window.confirm`, lift filter năm/phòng ban lên `TimeOff`, gộp KPI, hint search, a11y bàn phím.

**Tech Stack:** React 18 + Vite 6, **không** TypeScript, **không** test framework (kiểm chứng = `npm run build` + checklist thủ công qua preview `/hocba-hrm`). Làm trên nhánh `NhatAnh/TimeOff`.

**Quy ước chung cho MỌI task:**
- Build: `cd /Users/nguyenanh/odoo19/frontend && npm run build` — kỳ vọng kết thúc `✓ built in …s`, KHÔNG có lỗi/warning mới.
- Commit: chỉ add file **source** (`frontend/src/...`); bundle `custom-addons/hocba_hrm/static/spa/` chỉ commit ở Task 22. KHÔNG thêm dòng `Co-Authored-By` vào commit message.
- Mọi file đều là JSX thuần, inline style theo văn phong hiện có của repo.

---

## Lớp 1 — Nền móng

### Task 1: Hook `useFetch`

**Files:**
- Create: `frontend/src/hooks/useFetch.js` (thư mục `hooks/` chưa tồn tại — tạo mới)

- [ ] **Step 1: Viết hook**

```js
/* Hook fetch dùng chung cho các panel Nghỉ phép (và về sau: toàn SPA).
   Stale-while-revalidate: có cache theo cacheKey → hiện data cũ ngay và fetch
   ngầm cập nhật; chưa có cache → loading=true (skeleton). Thay cho pattern
   data/err/tick lặp ở từng panel. Owner: Nhật Anh.
   Spec: docs/superpowers/specs/2026-07-07-timeoff-frontend-cleanup-design.md */
import { useState, useEffect, useRef, useCallback } from 'react';

/* Cache cấp module: sống trong phiên SPA, mất khi F5 (chấp nhận). */
const cache = new Map();

/* fetcher: () => Promise<payload>.
   deps: mảng dependency — đổi là fetch lại (truyền thẳng cho useEffect).
   cacheKey: chuỗi định danh cache (vd `timeoff:dashboard:2026:5`); null = không cache. */
export default function useFetch(fetcher, deps, cacheKey) {
  const [state, setState] = useState(() => {
    const hit = cacheKey != null && cache.has(cacheKey);
    return { data: hit ? cache.get(cacheKey) : null, err: null, loading: !hit };
  });
  const runId = useRef(0);           // chống race: chỉ nhận response của lần gọi mới nhất
  const fetcherRef = useRef(fetcher);
  fetcherRef.current = fetcher;
  const keyRef = useRef(cacheKey);
  keyRef.current = cacheKey;

  const load = useCallback(() => {
    const id = ++runId.current;
    const key = keyRef.current;
    const hit = key != null && cache.has(key);
    // Có cache → hiện ngay (stale) rồi revalidate ngầm; chưa có → loading.
    setState({ data: hit ? cache.get(key) : null, err: null, loading: !hit });
    fetcherRef.current()
      .then((payload) => {
        if (id !== runId.current) return; // deps đã đổi — bỏ response cũ
        if (key != null) cache.set(key, payload);
        setState({ data: payload, err: null, loading: false });
      })
      .catch((e) => {
        if (id !== runId.current) return;
        if (hit) {
          // Đang hiện data cũ → không đè màn hình lỗi, chỉ ghi log.
          console.warn('useFetch revalidate failed:', e);
          setState((s) => ({ ...s, loading: false }));
        } else {
          setState({ data: null, err: e.message, loading: false });
        }
      });
  }, []);

  useEffect(load, deps);

  /* Action (duyệt/hủy/điều chỉnh…) ghi thẳng payload server trả về. */
  const setData = useCallback((payload) => {
    if (keyRef.current != null) cache.set(keyRef.current, payload);
    setState({ data: payload, err: null, loading: false });
  }, []);

  return { data: state.data, err: state.err, loading: state.loading, reload: load, setData };
}
```

- [ ] **Step 2: Build** — chạy lệnh build ở Quy ước chung, kỳ vọng PASS (hook chưa được import ở đâu, chỉ cần parse OK).

- [ ] **Step 3: Commit**

```bash
git add frontend/src/hooks/useFetch.js
git commit -m "feat(timeoff-ui): hook useFetch dùng chung — stale-while-revalidate + setData"
```

### Task 2: `YearNav` + `DeptSelect`

**Files:**
- Create: `frontend/src/features/timeoff/YearNav.jsx`
- Create: `frontend/src/features/timeoff/DeptSelect.jsx`

- [ ] **Step 1: Viết `YearNav.jsx`** (gói khối `◀ năm ▶ · Năm nay` đang lặp ở 5 file)

```jsx
/* Thanh chọn năm dùng chung cho các tab Nghỉ phép. Owner: Nhật Anh. */
import Icon from '../../components/Icon';

const THIS_YEAR = new Date().getFullYear();

export default function YearNav({ year, onChange }) {
  return (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <button className="icon-btn" onClick={() => onChange(year - 1)}>
        <span style={{ display: 'inline-flex', transform: 'rotate(180deg)' }}><Icon name="chevR" size={16} /></span></button>
      <span className="mono" style={{ fontWeight: 700, minWidth: 48, textAlign: 'center' }}>{year}</span>
      <button className="icon-btn" onClick={() => onChange(year + 1)}><Icon name="chevR" size={16} /></button>
      <button className="btn btn-ghost btn-sm" onClick={() => onChange(THIS_YEAR)}>Năm nay</button>
    </div>
  );
}
```

- [ ] **Step 2: Viết `DeptSelect.jsx`** (gói dropdown "Mọi phòng ban" đang lặp ở 6 chỗ)

```jsx
/* Dropdown lọc phòng ban dùng chung cho các tab Nghỉ phép. Owner: Nhật Anh. */
export default function DeptSelect({ value, onChange, departments, style }) {
  return (
    <select className="sel" style={style} value={value} onChange={(e) => onChange(e.target.value)}>
      <option value="">Mọi phòng ban</option>
      {(departments || []).map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
    </select>
  );
}
```

- [ ] **Step 3: Build** — kỳ vọng PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/timeoff/YearNav.jsx frontend/src/features/timeoff/DeptSelect.jsx
git commit -m "feat(timeoff-ui): component YearNav + DeptSelect dùng chung"
```

### Task 3: `ModalHeader`

**Files:**
- Create: `frontend/src/components/ModalHeader.jsx` (dùng chung toàn app — khối `drawer-head` lặp 11 chỗ)

- [ ] **Step 1: Viết component.** Codebase có 2 cỡ header: mặc định (icon-box 44px, icon 20, title 18) và lớn `lg` (48px, icon 22, title 20, letterSpacing -.3px). `iconBg` cho DetailModal của ApprovedPanel (nền theo màu loại nghỉ). `children` render cạnh title (chỗ chèn Badge).

```jsx
/* Header chuẩn cho modal: gradient đỏ + ô icon + tiêu đề + nút đóng.
   lg: cỡ lớn (icon-box 48, title 20). iconBg: đổi màu nền ô icon.
   children: node chèn cạnh title (vd Badge). Owner: Nhật Anh. */
import Icon from './Icon';

export default function ModalHeader({ icon, title, sub, onClose, lg, iconBg, children }) {
  const box = lg ? 48 : 44;
  return (
    <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
      <div style={{ width: box, height: box, borderRadius: 12, background: iconBg || 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
        <Icon name={icon} size={lg ? 22 : 20} />
      </div>
      <div style={{ flex: 1 }}>
        <h2 style={{
          margin: 0, fontSize: lg ? 20 : 18, fontWeight: 800,
          letterSpacing: lg ? '-.3px' : undefined,
          display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap',
        }}>{title}{children}</h2>
        {sub && <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>{sub}</div>}
      </div>
      <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
    </div>
  );
}
```

- [ ] **Step 2: Build** — kỳ vọng PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ModalHeader.jsx
git commit -m "feat(ui): component ModalHeader dùng chung — thay khối drawer-head lặp 11 chỗ"
```

### Task 4: `ConfirmModal`

**Files:**
- Create: `frontend/src/components/ConfirmModal.jsx`

- [ ] **Step 1: Viết component.** `onConfirm` trả Promise; modal tự quản `busy` + hiện lỗi trong modal (khối đỏ nhạt như WithdrawModal). Thành công thì **phía gọi** đóng modal (trong `.then` của chính nó). `btn-primary` của theme đã là đỏ nên dùng luôn cho hành động nguy hiểm.

```jsx
/* Modal xác nhận dùng chung — thay window.confirm/alert. onConfirm trả
   Promise; lỗi hiện ngay trong modal, thành công thì phía gọi tự đóng.
   Owner: Nhật Anh. */
import { useState } from 'react';
import Modal from './Modal';
import ModalHeader from './ModalHeader';

export default function ConfirmModal({ title, message, confirmLabel = 'Xác nhận', icon = 'alertCircle', onConfirm, onClose }) {
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const run = () => {
    setBusy(true); setErr(null);
    Promise.resolve(onConfirm()).catch((e) => { setErr(e.message); setBusy(false); });
  };

  return (
    <Modal onClose={onClose}>
      <ModalHeader icon={icon} title={title} onClose={onClose} />
      <div style={{ padding: '18px 24px', display: 'grid', gap: 12 }}>
        <div style={{ fontSize: 13.5, color: 'var(--ink)' }}>{message}</div>
        {err && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Đóng</button>
        <button className="btn btn-primary" onClick={run} disabled={busy}>
          {busy ? 'Đang xử lý…' : confirmLabel}
        </button>
      </div>
    </Modal>
  );
}
```

- [ ] **Step 2: Build** — kỳ vọng PASS.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/ConfirmModal.jsx
git commit -m "feat(ui): component ConfirmModal — xác nhận có Promise, lỗi hiện trong modal"
```

### Task 5: `TableSkeleton` + CSS

**Files:**
- Modify: `frontend/src/components/states.jsx`
- Modify: `frontend/src/styles/base.css` (cuối file)

- [ ] **Step 1: Thêm export vào cuối `states.jsx`**

```jsx
/* Skeleton giả hàng bảng — dùng cho lần tải đầu của các panel (useFetch.loading). */
export function TableSkeleton({ rows = 6 }) {
  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '6px 0' }}>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton" style={{ height: 38, borderRadius: 10 }}></div>
      ))}
    </div>
  );
}
```

- [ ] **Step 2: Thêm CSS vào cuối `base.css`**

```css
/* Skeleton loading (timeoff cleanup 2026-07-07) */
.skeleton {
  background: linear-gradient(90deg, var(--surface-2) 25%, var(--border) 50%, var(--surface-2) 75%);
  background-size: 200% 100%;
  animation: skeleton-shimmer 1.2s ease-in-out infinite;
}
@keyframes skeleton-shimmer {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}
```

- [ ] **Step 3: Build** — kỳ vọng PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/states.jsx frontend/src/styles/base.css
git commit -m "feat(ui): TableSkeleton — skeleton loading cho bảng"
```

---

## Lớp 2 — Migrate từng file (hành vi giữ nguyên, mỗi file 1 commit)

Pattern chung cho các task 6–14: thay `data/err/tick + useEffect` bằng `useFetch`; thay `LoadingState` đầu trang bằng `TableSkeleton`; thay khối năm/phòng ban bằng `YearNav`/`DeptSelect`; thay khối `drawer-head` bằng `ModalHeader`. Sau mỗi task: build PASS + mở preview đảo qua tab tương ứng thấy render đúng.

### Task 6: Migrate `BurnoutPanel.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/BurnoutPanel.jsx`

- [ ] **Step 1: Sửa imports** — thay 2 dòng:

```js
// CŨ:
import { useState, useEffect } from 'react';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
// MỚI:
import { useState } from 'react';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import DeptSelect from './DeptSelect';
```

- [ ] **Step 2: Thay khối state + effect** (các dòng `const [data…]` → hết `if (!data) return…`):

```js
// CŨ:
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [dept, setDept] = useState('');
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setData(null);
    fetchBurnout(dept || undefined).then(setData).catch((e) => setErr(e.message));
  }, [dept, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải cảnh báo sức khỏe nhân viên…" />;
// MỚI:
  const [dept, setDept] = useState('');
  const { data, err, loading, reload } = useFetch(
    () => fetchBurnout(dept || undefined), [dept], `timeoff:burnout:${dept}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;
```

- [ ] **Step 3: Thay dropdown phòng ban trong filterbar**

```jsx
// CŨ:
            <select className="sel" value={dept} onChange={(e) => setDept(e.target.value)}>
              <option value="">Mọi phòng ban</option>
              {data.allDepartments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
// MỚI:
            <DeptSelect value={dept} onChange={setDept} departments={data.allDepartments} />
```

- [ ] **Step 4: Build PASS; preview tab "Sức khỏe NV" (login `hr.manager`) hiện đúng KPI + bảng.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/timeoff/BurnoutPanel.jsx
git commit -m "refactor(timeoff-ui): BurnoutPanel dùng useFetch + DeptSelect + skeleton"
```

### Task 7: Migrate `LapsedPanel.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/LapsedPanel.jsx`

- [ ] **Step 1: Sửa imports** — như Task 6 Step 1 (`useState` giữ vì còn `busy`; thêm `useFetch`, `DeptSelect`, `TableSkeleton`; bỏ `LoadingState`).

```js
// CŨ:
import { useState, useEffect } from 'react';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
// MỚI:
import { useState } from 'react';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import DeptSelect from './DeptSelect';
```

- [ ] **Step 2: Thay khối state + effect**

```js
// CŨ:
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [dept, setDept] = useState('');
  const [busy, setBusy] = useState(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setData(null);
    fetchLapsedDashboard(dept || undefined).then(setData).catch((e) => setErr(e.message));
  }, [dept, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải giám sát duyệt đơn…" />;
// MỚI:
  const [dept, setDept] = useState('');
  const [busy, setBusy] = useState(null);
  const { data, err, loading, reload } = useFetch(
    () => fetchLapsedDashboard(dept || undefined), [dept], `timeoff:lapsed:${dept}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;
```

- [ ] **Step 3: Trong `quickDecide`, thay `setTick((t) => t + 1)` bằng `reload()`** (giữ nguyên `window.confirm`/`alert` — sẽ thay ở Task 17):

```js
    decideRequest(row.requestId, { action: row.suggestion })
      .then(() => reload())
      .catch((e) => alert('Không xử lý được đơn: ' + e.message))
      .finally(() => setBusy(null));
```

- [ ] **Step 4: Thay dropdown phòng ban** (khối trong `data.seeAll &&`):

```jsx
            <DeptSelect value={dept} onChange={setDept} departments={data.allDepartments} />
```

- [ ] **Step 5: Build PASS; preview tab "Giám sát duyệt".**

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/timeoff/LapsedPanel.jsx
git commit -m "refactor(timeoff-ui): LapsedPanel dùng useFetch + DeptSelect + skeleton"
```

### Task 8: Migrate `SummaryPanel.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/SummaryPanel.jsx`

- [ ] **Step 1: Sửa imports**

```js
// CŨ:
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
// MỚI:
import { useState } from 'react';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';
```

(`Icon` chỉ dùng trong khối nav cũ — sau khi thay `YearNav` thì bỏ import. Xóa luôn hằng `THIS_YEAR` đầu file.)

- [ ] **Step 2: Thay khối state + effect + nav**

```js
// CŨ:
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [year, setYear] = useState(THIS_YEAR);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setData(null);
    fetchSummary(year).then(setData).catch((e) => setErr(e.message));
  }, [year, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải báo cáo nghỉ phép…" />;

  const nav = (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <button className="icon-btn" onClick={() => setYear((y) => y - 1)}>
        <span style={{ display: 'inline-flex', transform: 'rotate(180deg)' }}><Icon name="chevR" size={16} /></span></button>
      <span className="mono" style={{ fontWeight: 700, minWidth: 48, textAlign: 'center' }}>{year}</span>
      <button className="icon-btn" onClick={() => setYear((y) => y + 1)}><Icon name="chevR" size={16} /></button>
      <button className="btn btn-ghost btn-sm" onClick={() => setYear(THIS_YEAR)}>Năm nay</button>
    </div>
  );
// MỚI:
  const [year, setYear] = useState(new Date().getFullYear());
  const { data, err, loading, reload } = useFetch(
    () => fetchSummary(year), [year], `timeoff:summary:${year}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;

  const nav = <YearNav year={year} onChange={setYear} />;
```

- [ ] **Step 3: Build PASS; preview tab "Tổng hợp" (login `nv.test`).**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/timeoff/SummaryPanel.jsx
git commit -m "refactor(timeoff-ui): SummaryPanel dùng useFetch + YearNav + skeleton"
```

### Task 9: Migrate `ApprovedPanel.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/ApprovedPanel.jsx`

- [ ] **Step 1: Sửa imports** — bỏ `useEffect`, `LoadingState`; thêm `TableSkeleton`, `useFetch`, `YearNav`, `DeptSelect`, `ModalHeader`. Xóa hằng `THIS_YEAR`.

```js
// CŨ:
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
// MỚI:
import { useState } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';
import DeptSelect from './DeptSelect';
```

(`Icon` giữ — còn dùng cho nút Xuất Excel + DetailModal.)

- [ ] **Step 2: Thay khối state + effect**

```js
// CŨ:
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [year, setYear] = useState(THIS_YEAR);
  const [dept, setDept] = useState('');
  const [tick, setTick] = useState(0);
  const [detail, setDetail] = useState(null); // đơn đang xem chi tiết
  const [sort, setSort] = useState({ key: 'from', dir: 'desc' });

  useEffect(() => {
    setErr(null); setData(null);
    fetchApproved(year, dept || undefined).then(setData).catch((e) => setErr(e.message));
  }, [year, dept, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải đơn đã duyệt…" />;
// MỚI:
  const [year, setYear] = useState(new Date().getFullYear());
  const [dept, setDept] = useState('');
  const [detail, setDetail] = useState(null); // đơn đang xem chi tiết
  const [sort, setSort] = useState({ key: 'from', dir: 'desc' });
  const { data, err, loading, reload } = useFetch(
    () => fetchApproved(year, dept || undefined), [year, dept],
    `timeoff:approved:${year}:${dept}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;
```

- [ ] **Step 3: Thay filterbar** (cả khối năm + select):

```jsx
      <div className="filterbar">
        <YearNav year={year} onChange={setYear} />
        <div style={{ marginLeft: 'auto' }}>
          <DeptSelect value={dept} onChange={setDept} departments={data.allDepartments} />
        </div>
      </div>
```

- [ ] **Step 4: Thay header của `DetailModal`** (khối `drawer-head` → hết nút X):

```jsx
      <ModalHeader lg icon="calendar" iconBg={req.color}
        title={req.employee} sub={req.department} onClose={onClose} />
```

- [ ] **Step 5: Build PASS; preview tab "Đơn đã duyệt": lọc năm/phòng, mở chi tiết 1 đơn.**

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/timeoff/ApprovedPanel.jsx
git commit -m "refactor(timeoff-ui): ApprovedPanel dùng useFetch + YearNav/DeptSelect/ModalHeader"
```

### Task 10: Migrate `DashboardPanel.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/DashboardPanel.jsx`

- [ ] **Step 1: Sửa imports** — bỏ `useEffect`, `LoadingState`; `Icon` chỉ dùng trong nav cũ và EmployeeView (icon calendar ở "Nghỉ sắp tới") → **giữ** `Icon`. Xóa hằng `THIS_YEAR`.

```js
// CŨ:
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
// MỚI:
import { useState } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';
import DeptSelect from './DeptSelect';
```

- [ ] **Step 2: Thay khối state + effect + nav trong `DashboardPanel`**

```js
// CŨ:
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [year, setYear] = useState(THIS_YEAR);
  const [dept, setDept] = useState('');
  const [tick, setTick] = useState(0); // ép tải lại (nút Thử lại)

  useEffect(() => {
    setErr(null); setData(null);
    fetchDashboard(year, dept || undefined).then(setData).catch((e) => setErr(e.message));
  }, [year, dept, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải tổng quan nghỉ phép…" />;

  const nav = (
    <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
      <button className="icon-btn" onClick={() => setYear((y) => y - 1)}>
        <span style={{ display: 'inline-flex', transform: 'rotate(180deg)' }}><Icon name="chevR" size={16} /></span></button>
      <span className="mono" style={{ fontWeight: 700, minWidth: 48, textAlign: 'center' }}>{year}</span>
      <button className="icon-btn" onClick={() => setYear((y) => y + 1)}><Icon name="chevR" size={16} /></button>
      <button className="btn btn-ghost btn-sm" onClick={() => setYear(THIS_YEAR)}>Năm nay</button>
    </div>
  );
// MỚI:
  const [year, setYear] = useState(new Date().getFullYear());
  const [dept, setDept] = useState('');
  const { data, err, loading, reload } = useFetch(
    () => fetchDashboard(year, dept || undefined), [year, dept],
    `timeoff:dashboard:${year}:${dept}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;

  const nav = <YearNav year={year} onChange={setYear} />;
```

- [ ] **Step 3: Thay dropdown trong `ManagerView`**

```jsx
        <div style={{ marginLeft: 'auto' }}>
          <DeptSelect value={dept} onChange={setDept} departments={data.departments} />
        </div>
```

Lưu ý: `ManagerView` nhận `dept`/`setDept` qua props — giữ nguyên chữ ký `function ManagerView({ data, dept, setDept, nav })`.

- [ ] **Step 4: Build PASS; preview tab "Tổng quan" cả 2 view (login `hr.manager` và `nv.test`).**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/timeoff/DashboardPanel.jsx
git commit -m "refactor(timeoff-ui): DashboardPanel dùng useFetch + YearNav/DeptSelect"
```

### Task 11: Migrate `BalancesPanel.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/BalancesPanel.jsx`

- [ ] **Step 1: Sửa imports** — bỏ `useEffect` khỏi import react của component chính (LƯU Ý: `HistoryModal` bên trong vẫn dùng `useState`+`useEffect` + `LoadingState` — GIỮ `useEffect` và `LoadingState` trong import). Thêm `useFetch`, `YearNav`, `DeptSelect`, `ModalHeader`, `TableSkeleton`. Xóa hằng `THIS_YEAR`.

```js
// CŨ:
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
// MỚI:
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import { LoadingState, ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';
import DeptSelect from './DeptSelect';
```

- [ ] **Step 2: Thay khối state + effect của `BalancesPanel`**

```js
// CŨ:
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [year, setYear] = useState(THIS_YEAR);
  const [dept, setDept] = useState('');
  const [tick, setTick] = useState(0);
  const [sort, setSort] = useState({ key: 'totalRemaining', dir: 'asc' });
  const [adjust, setAdjust] = useState(null);   // dòng đang điều chỉnh
  const [history, setHistory] = useState(null); // dòng đang xem lịch sử
  const [expiring, setExpiring] = useState(false); // lọc "sắp mất phép"

  useEffect(() => {
    setErr(null); setData(null);
    fetchBalances(year, dept || undefined, undefined, expiring ? 'expiring' : undefined)
      .then(setData).catch((e) => setErr(e.message));
  }, [year, dept, expiring, tick]);

  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải quỹ phép…" />;
// MỚI:
  const [year, setYear] = useState(new Date().getFullYear());
  const [dept, setDept] = useState('');
  const [sort, setSort] = useState({ key: 'totalRemaining', dir: 'asc' });
  const [adjust, setAdjust] = useState(null);   // dòng đang điều chỉnh
  const [history, setHistory] = useState(null); // dòng đang xem lịch sử
  const [expiring, setExpiring] = useState(false); // lọc "sắp mất phép"
  const { data, err, loading, reload } = useFetch(
    () => fetchBalances(year, dept || undefined, undefined, expiring ? 'expiring' : undefined),
    [year, dept, expiring], `timeoff:balances:${year}:${dept}:${expiring ? 1 : 0}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;
```

- [ ] **Step 3: Thay filterbar** (khối năm + select; nút "Sắp mất phép" giữ nguyên giữa hai khối):

```jsx
      <div className="filterbar">
        <YearNav year={year} onChange={setYear} />
        <button className={'btn btn-sm ' + (expiring ? 'btn-primary' : 'btn-soft')}
          onClick={() => setExpiring((v) => !v)} title={`Còn ≥ ${data.atRiskDays ?? 5} ngày phép năm chưa dùng`}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 6, marginLeft: 12 }}>
          <Icon name="bell" size={15} />Sắp mất phép{(k.atRisk ?? 0) > 0 ? ` (${k.atRisk})` : ''}
        </button>
        <div style={{ marginLeft: 'auto' }}>
          <DeptSelect value={dept} onChange={setDept} departments={data.allDepartments} />
        </div>
      </div>
```

LƯU Ý: `k` được khai báo SAU return sớm — khối filterbar nằm trong JSX nên `k` đã có (`const k = data.kpi || {}` giữ nguyên vị trí hiện tại).

- [ ] **Step 4: `AdjustQuotaModal` onDone: thay `setTick((t) => t + 1)` bằng `reload()`**

```jsx
      {adjust && (
        <AdjustQuotaModal row={adjust} leaveTypes={types}
          onClose={() => setAdjust(null)}
          onDone={() => { setAdjust(null); reload(); }} />
      )}
```

- [ ] **Step 5: Thay 2 header modal bằng `ModalHeader`**

Trong `AdjustQuotaModal`:
```jsx
      <ModalHeader lg icon="calendar" title="Điều chỉnh quỹ phép"
        sub={`${row.employee} · ${row.department}`} onClose={onClose} />
```

Trong `HistoryModal`:
```jsx
      <ModalHeader lg icon="file" title="Lịch sử điều chỉnh"
        sub={`${row.employee} · ${row.department}`} onClose={onClose} />
```

- [ ] **Step 6: Build PASS; preview tab "Quỹ phép": lọc, mở Điều chỉnh + Lịch sử (login `hr.manager`).**

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/timeoff/BalancesPanel.jsx
git commit -m "refactor(timeoff-ui): BalancesPanel dùng useFetch + YearNav/DeptSelect/ModalHeader"
```

### Task 12: Migrate `CalendarPanel.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/CalendarPanel.jsx`

Lịch có nav riêng (năm/tháng + "Hôm nay") — KHÔNG dùng `YearNav`. Chỉ thay fetch + select phòng ban.

- [ ] **Step 1: Sửa imports**

```js
// CŨ:
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
// MỚI:
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import DeptSelect from './DeptSelect';
```

(`useState, useEffect, useMemo` giữ nguyên — còn dùng cho `active`, `teaching`.)

- [ ] **Step 2: Thay khối fetch.** Side-effect `setActive` sau fetch chuyển thành effect theo `data`:

```js
// CŨ:
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [year, setYear] = useState(NOW.getFullYear());
  const [month, setMonth] = useState(NOW.getMonth());
  const [mode, setMode] = useState('year');   // 'year' | 'month'
  const [dept, setDept] = useState('');         // HR lọc 1 phòng ban ('' = tất cả)
  const [active, setActive] = useState(null);   // Set id loại đang bật (null = tất cả)
  const [teaching, setTeaching] = useState(new Map()); // ngày dạy → số buổi (GV)
  const [tick, setTick] = useState(0);

  useEffect(() => {
    setErr(null); setData(null);
    fetchCalendar(year, seeAll ? (dept || undefined) : undefined).then((d) => {
      setData(d);
      setActive(new Set(d.leaveTypes.map((t) => t.id))); // bật tất cả loại
    }).catch((e) => setErr(e.message));
  }, [year, dept, seeAll, tick]);
// MỚI:
  const [year, setYear] = useState(NOW.getFullYear());
  const [month, setMonth] = useState(NOW.getMonth());
  const [mode, setMode] = useState('year');   // 'year' | 'month'
  const [dept, setDept] = useState('');         // HR lọc 1 phòng ban ('' = tất cả)
  const [active, setActive] = useState(null);   // Set id loại đang bật (null = tất cả)
  const [teaching, setTeaching] = useState(new Map()); // ngày dạy → số buổi (GV)
  const { data, err, loading, reload } = useFetch(
    () => fetchCalendar(year, seeAll ? (dept || undefined) : undefined),
    [year, dept, seeAll], `timeoff:calendar:${year}:${seeAll ? dept : 'mine'}`);

  // Data (mới hoặc từ cache) về → bật tất cả loại nghỉ.
  useEffect(() => {
    if (data) setActive(new Set(data.leaveTypes.map((t) => t.id)));
  }, [data]);
```

- [ ] **Step 3: Thay 2 dòng return sớm** (nằm SAU các useMemo — giữ vị trí):

```js
// CŨ:
  if (err) return <ErrorState message={err} onRetry={() => setTick((t) => t + 1)} />;
  if (!data) return <LoadingState label="Đang tải lịch nghỉ phép…" />;
// MỚI:
  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton rows={8} />;
```

- [ ] **Step 4: Thay select phòng ban ở cột phải** (trong `seeAll &&`, card "Phòng ban"):

```jsx
            <DeptSelect value={dept} onChange={setDept} style={{ width: '100%' }}
              departments={data.allDepartments} />
```

(Nhãn option đầu đổi từ "Tất cả phòng ban" → "Mọi phòng ban" — thống nhất toàn màn, chấp nhận.)

- [ ] **Step 5: Build PASS; preview tab "Lịch": đổi Năm/Tháng, tick loại nghỉ, đổi phòng ban.**

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/timeoff/CalendarPanel.jsx
git commit -m "refactor(timeoff-ui): CalendarPanel dùng useFetch + DeptSelect + skeleton"
```

### Task 13: Migrate `ApprovalPanel.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/ApprovalPanel.jsx`

- [ ] **Step 1: Sửa imports**

```js
// CŨ:
import { useState, useEffect } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
// MỚI:
import { useState, useEffect } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import ModalHeader from '../../components/ModalHeader';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
```

(`useEffect` giữ — còn dùng cho deep-link focus.)

- [ ] **Step 2: Thay khối state + effect fetch** (giữ nguyên effect deep-link phía dưới):

```js
// CŨ:
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [decision, setDecision] = useState(null); // đơn đang mở modal duyệt
  const [withdrawDecision, setWithdrawDecision] = useState(null); // yêu cầu rút đang xử lý
  const [sort, setSort] = useState({ key: 'from', dir: 'asc' });
  const [dept, setDept] = useState(''); // lọc phòng ban (chỉ role HR, khi sắp xếp theo phòng ban)

  const load = () => {
    setErr(null); setData(null);
    fetchApprovals().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
// MỚI:
  const [decision, setDecision] = useState(null); // đơn đang mở modal duyệt
  const [withdrawDecision, setWithdrawDecision] = useState(null); // yêu cầu rút đang xử lý
  const [sort, setSort] = useState({ key: 'from', dir: 'asc' });
  const [dept, setDept] = useState(''); // lọc phòng ban (chỉ role HR, khi sắp xếp theo phòng ban)
  const { data, err, loading, reload, setData } = useFetch(
    () => fetchApprovals(), [], 'timeoff:approvals');
```

- [ ] **Step 3: Thay 2 dòng return sớm**

```js
// CŨ:
  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải đơn chờ duyệt…" />;
// MỚI:
  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;
```

(`onDone` của 2 modal gọi `setData(payload)` — giữ nguyên, giờ là `setData` của hook nên cache cũng được cập nhật.)

- [ ] **Step 4: Thay 2 header modal**

Trong `WithdrawDecisionModal`:
```jsx
      <ModalHeader lg icon="alertCircle" title="Xử lý yêu cầu rút đơn"
        sub={`${req.employee} · ${req.leaveType} · ${fmtDate(req.from)} → ${fmtDate(req.to)} (${req.days} ngày)`}
        onClose={onClose} />
```

Trong `DecisionModal`:
```jsx
      <ModalHeader lg icon="checkCircle" title="Xử lý đơn nghỉ"
        sub={`${req.employee} · ${req.leaveType} · ${fmtDate(req.from)} → ${fmtDate(req.to)} (${req.days} ngày)`}
        onClose={onClose} />
```

- [ ] **Step 5: Build PASS; preview tab "Chờ duyệt": mở modal Xử lý, duyệt thử 1 đơn thấy danh sách cập nhật.**

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/timeoff/ApprovalPanel.jsx
git commit -m "refactor(timeoff-ui): ApprovalPanel dùng useFetch + ModalHeader + skeleton"
```

### Task 14: Migrate `WorkScheduleModal.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/WorkScheduleModal.jsx`

Year giữ CỤC BỘ (modal độc lập, không phải tab — spec §3.3). Lỗi fetch và lỗi action gộp hiển thị cùng một chỗ như hiện tại.

- [ ] **Step 1: Sửa imports** — thêm `ModalHeader`, `useFetch`, `YearNav`; `LoadingState` giữ (dùng cho vùng danh sách trong modal). Xóa hằng `THIS_YEAR`.

```js
// CŨ:
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState } from '../../components/states';
// MỚI:
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import ModalHeader from '../../components/ModalHeader';
import { LoadingState } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';
```

- [ ] **Step 2: Thay khối state + load**

```js
// CŨ:
  const [year, setYear] = useState(THIS_YEAR);
  const [data, setData] = useState(null);
  const [staging, setStaging] = useState([]);   // các ngày chờ lưu
  const [pick, setPick] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const load = (y) => { setData(null); fetchWorkdays(y).then(setData).catch((e) => setErr(e.message)); };
  useEffect(() => { load(year); setStaging([]); }, [year]);
// MỚI:
  const [year, setYear] = useState(new Date().getFullYear());
  const [staging, setStaging] = useState([]);   // các ngày chờ lưu
  const [pick, setPick] = useState('');
  const [note, setNote] = useState('');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);         // lỗi action (thêm/xoá)
  const { data, err: loadErr, loading, setData } = useFetch(
    () => fetchWorkdays(year), [year], `timeoff:workdays:${year}`);

  useEffect(() => { setStaging([]); }, [year]);
```

- [ ] **Step 3: Gộp hiển thị lỗi** — khối err hiện tại đổi điều kiện:

```jsx
        {(err || loadErr) && (
          <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err || loadErr}</div>
        )}
```

- [ ] **Step 4: Vùng danh sách:** thay `{!data ? <LoadingState label="Đang tải…" /> : (` bằng `{loading || !data ? <LoadingState label="Đang tải…" /> : (`.

- [ ] **Step 5: Thay header + khối năm**

Header:
```jsx
      <ModalHeader lg icon="calendar" title="Thêm lịch làm việc"
        sub="Công ty làm Thứ 2 – Thứ 6 · thêm các ngày Thứ 7 đi làm" onClose={onClose} />
```

Khối năm (4 nút hiện tại) → `<YearNav year={year} onChange={setYear} />`.

- [ ] **Step 6: Build PASS; preview: mở "Thêm lịch làm việc" (login `hr.manager`), thêm/xoá 1 ngày thử.**

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/timeoff/WorkScheduleModal.jsx
git commit -m "refactor(timeoff-ui): WorkScheduleModal dùng useFetch + YearNav/ModalHeader"
```

### Task 15: `ModalHeader` cho `TimeOff.jsx`, `SubstitutionsPanel.jsx`, `LeaveForm.jsx`

**Files:**
- Modify: `frontend/src/features/timeoff/TimeOff.jsx` (3 header)
- Modify: `frontend/src/features/timeoff/SubstitutionsPanel.jsx` (1 header)
- Modify: `frontend/src/features/timeoff/LeaveForm.jsx` (1 header)

- [ ] **Step 1: `TimeOff.jsx`** — thêm `import ModalHeader from '../../components/ModalHeader';` rồi thay 3 khối:

Modal lịch sử (`historyReq`):
```jsx
          <ModalHeader icon="clock" title="Lịch sử xử lý đơn"
            sub="Dòng thời gian thao tác của đơn nghỉ" onClose={() => setHistoryReq(null)} />
```

`LeaveDetailModal` (badges thành children):
```jsx
      <ModalHeader icon="calendar" title={req.leaveType} sub="Chi tiết đơn nghỉ" onClose={onClose}>
        {req.halfDay && <Badge kind="blue">{req.halfDay}</Badge>}
        {req.isEmergency && <Badge kind="red">Khẩn cấp</Badge>}
      </ModalHeader>
```

`WithdrawModal`:
```jsx
      <ModalHeader icon="alertCircle" title="Rút đơn nghỉ đã duyệt"
        sub={`${req.leaveType} · ${fmtDate(req.from)} → ${fmtDate(req.to)} (${req.days} ngày)`}
        onClose={onClose} />
```

- [ ] **Step 2: `SubstitutionsPanel.jsx`** — thêm import, thay header modal từ chối:

```jsx
      <ModalHeader icon="alertCircle" title="Từ chối dạy thay"
        sub={`${req.requester} · ${req.className} · ${fmtDate(req.date)} ${req.startTime}`}
        onClose={onClose} />
```

- [ ] **Step 3: `LeaveForm.jsx`** — thêm import, thay header:

```jsx
      <ModalHeader lg icon="calendar" title="Tạo đơn nghỉ"
        sub={isTeacher && mode === 'sessions'
          ? 'Chọn buổi dạy bạn muốn nghỉ — xử lý lớp cho từng buổi'
          : 'Gửi đơn xin nghỉ để quản lý phê duyệt'}
        onClose={onClose} />
```

- [ ] **Step 4: Grep xác nhận hết trùng lặp:** `grep -rn "drawer-head" frontend/src/features/timeoff/` → kỳ vọng 0 kết quả (chỉ còn trong `components/ModalHeader.jsx`).

- [ ] **Step 5: Build PASS; preview: mở modal chi tiết đơn, rút đơn, tạo đơn, từ chối dạy thay.**

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/timeoff/TimeOff.jsx frontend/src/features/timeoff/SubstitutionsPanel.jsx frontend/src/features/timeoff/LeaveForm.jsx
git commit -m "refactor(timeoff-ui): 5 modal còn lại dùng ModalHeader chung"
```

---

## Lớp 3 — Fix hành vi

### Task 16: Badge "Chờ duyệt" cập nhật sau khi xử lý đơn (BUG)

**Files:**
- Modify: `frontend/src/features/timeoff/ApprovalPanel.jsx`
- Modify: `frontend/src/features/timeoff/TimeOff.jsx`

- [ ] **Step 1: `ApprovalPanel` nhận + gọi `onChanged`**

```jsx
// CŨ:
export default function ApprovalPanel({ isHrManager, focusRequestId, onFocusConsumed }) {
// MỚI:
export default function ApprovalPanel({ isHrManager, focusRequestId, onFocusConsumed, onChanged }) {
```

2 chỗ `onDone` (API trả sẵn danh sách mới — không tốn request thêm):

```jsx
      {decision && (
        <DecisionModal req={decision} isHrManager={isHrManager}
          onClose={() => setDecision(null)}
          onDone={(payload) => {
            setDecision(null); setData(payload);
            onChanged && onChanged((payload.requests || []).length);
          }} />
      )}

      {withdrawDecision && (
        <WithdrawDecisionModal req={withdrawDecision}
          onClose={() => setWithdrawDecision(null)}
          onDone={(payload) => {
            setWithdrawDecision(null); setData(payload);
            onChanged && onChanged((payload.requests || []).length);
          }} />
      )}
```

- [ ] **Step 2: `TimeOff.jsx` truyền `onChanged`**

```jsx
      {activeTab === 'approvals' && data.isOfficer && (
        <ApprovalPanel isHrManager={data.isHrManager}
          focusRequestId={approvalFocus}
          onFocusConsumed={() => setApprovalFocus(null)}
          onChanged={setPendingCount} />
      )}
```

- [ ] **Step 3: Build PASS. Preview (login `hr.manager`): tab Chờ duyệt đang badge N → duyệt 1 đơn → badge thành N−1 ngay, không cần F5.**

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/timeoff/ApprovalPanel.jsx frontend/src/features/timeoff/TimeOff.jsx
git commit -m "fix(timeoff-ui): badge tab Chờ duyệt cập nhật ngay sau khi xử lý đơn"
```

### Task 17: Thay `window.confirm`/`alert` bằng `ConfirmModal`

**Files:**
- Modify: `frontend/src/features/timeoff/TimeOff.jsx` (hủy đơn — spec §3.2)
- Modify: `frontend/src/features/timeoff/LapsedPanel.jsx` (quickDecide — mở rộng nhẹ cùng mục tiêu UX, đã có sẵn pattern)
- Modify: `frontend/src/features/timeoff/ApprovalPanel.jsx` (nút "xử lý theo đề xuất" trong DecisionModal)

- [ ] **Step 1: `TimeOff.jsx` — hủy đơn.** Thêm `import ConfirmModal from '../../components/ConfirmModal';`. Thay state `busy` + hàm `onCancel`:

```js
// CŨ:
  const [busy, setBusy] = useState(null); // id đơn đang hủy
  ...
  const onCancel = (id) => {
    if (!window.confirm('Hủy đơn nghỉ này?')) return;
    setBusy(id);
    cancelRequest(id)
      .then(setData)
      .catch((e) => alert('Không hủy được đơn: ' + e.message))
      .finally(() => setBusy(null));
  };
// MỚI:
  const [cancelling, setCancelling] = useState(null); // đơn đang chờ xác nhận hủy
```

Render `ConfirmModal` cạnh các modal cuối component `TimeOff`:

```jsx
      {cancelling && (
        <ConfirmModal title="Hủy đơn nghỉ" confirmLabel="Hủy đơn"
          message={`Hủy đơn "${cancelling.leaveType}" (${fmtDate(cancelling.from)} → ${fmtDate(cancelling.to)})? Hành động không hoàn tác được.`}
          onClose={() => setCancelling(null)}
          onConfirm={() => cancelRequest(cancelling.id).then((payload) => {
            setData(payload); setCancelling(null);
          })} />
      )}
```

Cập nhật `MyTimeOff`: đổi props `busy, onCancel` → `onCancel` (nhận nguyên object `r`):

```jsx
// Chỗ gọi trong TimeOff:
        <MyTimeOff data={data} search={search}
          onCancel={setCancelling} onUpdated={setData} />
// Chữ ký:
function MyTimeOff({ data, search, onCancel, onUpdated }) {
// Nút trong bảng (bỏ disabled/busy):
                    {r.canCancel && (
                      <button className="btn btn-ghost btn-sm"
                        onClick={(e) => { e.stopPropagation(); onCancel(r); }}>Hủy</button>
                    )}
```

- [ ] **Step 2: `LapsedPanel.jsx` — quickDecide.** Thêm `import ConfirmModal from '../../components/ConfirmModal';`. Thay `busy` + `quickDecide` bằng state `confirming`:

```js
// CŨ (đã sửa ở Task 7):
  const [busy, setBusy] = useState(null);
  ...
  const quickDecide = (row) => {
    const label = row.suggestion === 'approve'
      ? 'Duyệt trễ' : 'Từ chối (nhân viên vẫn đi làm)';
    if (!window.confirm(`${label} đơn của ${row.employee}?`)) return;
    setBusy(row.requestId);
    decideRequest(row.requestId, { action: row.suggestion })
      .then(() => reload())
      .catch((e) => alert('Không xử lý được đơn: ' + e.message))
      .finally(() => setBusy(null));
  };
// MỚI:
  const [confirming, setConfirming] = useState(null); // dòng chờ xác nhận xử lý nhanh
```

Nút trong bảng: `onClick={() => setConfirming(r)}`, bỏ `disabled={busy === r.requestId}` và nhãn động (nhãn cố định "Xử lý theo đề xuất"). Render cuối component:

```jsx
      {confirming && (
        <ConfirmModal
          title={confirming.suggestion === 'approve' ? 'Duyệt trễ theo đề xuất' : 'Từ chối theo đề xuất'}
          confirmLabel={confirming.suggestion === 'approve' ? 'Duyệt trễ' : 'Từ chối'}
          message={`${confirming.suggestion === 'approve'
            ? 'Duyệt trễ' : 'Từ chối (nhân viên vẫn đi làm)'} đơn của ${confirming.employee}?`}
          onClose={() => setConfirming(null)}
          onConfirm={() => decideRequest(confirming.requestId, { action: confirming.suggestion })
            .then(() => { setConfirming(null); reload(); })} />
      )}
```

- [ ] **Step 3: `ApprovalPanel.jsx` — DecisionModal nút đề xuất.** Trong `DecisionModal`, nút "Duyệt trễ theo đề xuất / Từ chối theo đề xuất" đang dùng `window.confirm` — bỏ confirm lồng (đã ở TRONG modal xử lý, người duyệt đã chủ động mở):

```jsx
            onClick={() => decide(req.lapsed.suggestion)}>
```

(Xóa khối `const label = ...; if (window.confirm(...)) {...}`.)

- [ ] **Step 4: Grep xác nhận:** `grep -rn "window.confirm\|alert(" frontend/src/features/timeoff/` → kỳ vọng 0 kết quả.

- [ ] **Step 5: Build PASS. Preview: hủy 1 đơn (login `nv.test`) thấy modal, xác nhận thì đơn biến mất; tab Giám sát duyệt xử lý nhanh qua modal.**

- [ ] **Step 6: Commit**

```bash
git add frontend/src/features/timeoff/TimeOff.jsx frontend/src/features/timeoff/LapsedPanel.jsx frontend/src/features/timeoff/ApprovalPanel.jsx
git commit -m "feat(timeoff-ui): thay hết window.confirm/alert bằng ConfirmModal"
```

### Task 18: Lift filter năm/phòng ban lên `TimeOff`

**Files:**
- Modify: `frontend/src/features/timeoff/TimeOff.jsx`
- Modify: `frontend/src/features/timeoff/DashboardPanel.jsx`, `CalendarPanel.jsx`, `ApprovedPanel.jsx`, `BalancesPanel.jsx` (year + dept)
- Modify: `frontend/src/features/timeoff/LapsedPanel.jsx`, `BurnoutPanel.jsx` (chỉ dept)
- Modify: `frontend/src/features/timeoff/SummaryPanel.jsx` (chỉ year)

- [ ] **Step 1: `TimeOff.jsx` thêm state chung + truyền props**

```js
  const [year, setYear] = useState(new Date().getFullYear()); // filter chung xuyên tab
  const [dept, setDept] = useState('');                        // '' = mọi phòng ban
```

```jsx
      {activeTab === 'overview' && data.isOfficer && (
        <DashboardPanel year={year} onYearChange={setYear} dept={dept} onDeptChange={setDept} />
      )}
      {activeTab === 'summary' && !data.isOfficer && (
        <SummaryPanel year={year} onYearChange={setYear} />
      )}
      ...
      {activeTab === 'calendar' && (
        <CalendarPanel isOfficer={data.isOfficer} seeAll={data.seeAll}
          isTeacher={!!(data.employee && data.employee.isTeacher)}
          year={year} onYearChange={setYear} dept={dept} onDeptChange={setDept} />
      )}
      ...
      {activeTab === 'lapsed' && data.isOfficer && (
        <LapsedPanel dept={dept} onDeptChange={setDept}
          onOpenApproval={(id) => { setApprovalFocus(id); setTab('approvals'); }} />
      )}
      {activeTab === 'health' && data.isOfficer && (
        <BurnoutPanel dept={dept} onDeptChange={setDept} />
      )}
      {activeTab === 'approved' && data.isOfficer && (
        <ApprovedPanel search={search} year={year} onYearChange={setYear}
          dept={dept} onDeptChange={setDept} />
      )}
      {activeTab === 'balances' && data.isOfficer && (
        <BalancesPanel search={search} year={year} onYearChange={setYear}
          dept={dept} onDeptChange={setDept} />
      )}
```

- [ ] **Step 2: Từng panel bỏ state cục bộ, dùng props.** Pattern chung (áp dụng đúng biến từng file):

```js
// CŨ (trong panel):
  const [year, setYear] = useState(new Date().getFullYear());
  const [dept, setDept] = useState('');
// MỚI (chữ ký nhận props):
export default function DashboardPanel({ year, onYearChange, dept, onDeptChange }) {
```

Và mọi chỗ `setYear` → `onYearChange`, `setDept` → `onDeptChange` (gồm `<YearNav onChange={onYearChange} />`, `<DeptSelect onChange={onDeptChange} />`). Chi tiết từng file:

- `DashboardPanel({ year, onYearChange, dept, onDeptChange })`: `nav = <YearNav year={year} onChange={onYearChange} />`; `ManagerView` nhận `dept`/`onDeptChange` thay `dept`/`setDept`.
- `SummaryPanel({ year, onYearChange })`.
- `ApprovedPanel({ search, year, onYearChange, dept, onDeptChange })`.
- `BalancesPanel({ search, year, onYearChange, dept, onDeptChange })`.
- `LapsedPanel({ dept, onDeptChange, onOpenApproval })`.
- `BurnoutPanel({ dept, onDeptChange })`.
- `CalendarPanel({ isOfficer, isTeacher, seeAll, year, onYearChange, dept, onDeptChange })`: bỏ `useState` year/dept; `stepBack`/`stepFwd`/nút "Hôm nay" gọi `onYearChange`:

```js
  const stepBack = () => mode === 'year' ? onYearChange(year - 1)
    : (month === 0 ? (setMonth(11), onYearChange(year - 1)) : setMonth((m) => m - 1));
  const stepFwd = () => mode === 'year' ? onYearChange(year + 1)
    : (month === 11 ? (setMonth(0), onYearChange(year + 1)) : setMonth((m) => m + 1));
  // nút "Hôm nay":
  onClick={() => { onYearChange(NOW.getFullYear()); setMonth(NOW.getMonth()); }}
```

LƯU Ý `CalendarPanel`: user thường (`seeAll=false`) không render DeptSelect — giữ nguyên điều kiện `seeAll &&` hiện có. Tương tự `LapsedPanel`/`BurnoutPanel` chỉ render DeptSelect khi `data.seeAll`.

- [ ] **Step 3: Grep sạch:** `grep -rn "useState(new Date().getFullYear())\|useState(THIS_YEAR)" frontend/src/features/timeoff/` → chỉ còn `TimeOff.jsx` (state chung) + `WorkScheduleModal.jsx` (cục bộ có chủ đích) + `YearNav.jsx` (hằng nội bộ).

- [ ] **Step 4: Build PASS. Preview: chọn năm 2025 + 1 phòng ở Tổng quan → sang Đơn đã duyệt / Quỹ phép / Lịch vẫn giữ lựa chọn; NV thường đổi năm ở Tổng hợp → tab Lịch cùng năm.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/timeoff/
git commit -m "feat(timeoff-ui): filter năm/phòng ban dùng chung xuyên tab (lift lên TimeOff)"
```

### Task 19: Gộp KPI Tổng quan còn 6 thẻ

**Files:**
- Modify: `frontend/src/features/timeoff/DashboardPanel.jsx` (ManagerView)

- [ ] **Step 1: Thay 2 thẻ bằng 1**

```jsx
// CŨ:
        <Kpi label="Đã duyệt" value={k.approved} color="var(--green)" />
        <Kpi label="Ngày phép đã duyệt" value={k.approvedDays} sub="tổng số ngày" />
// MỚI:
        <Kpi label="Đã duyệt" value={k.approved} color="var(--green)"
          sub={`${k.approvedDays} ngày phép đã duyệt`} />
```

- [ ] **Step 2: Build PASS. Preview tab Tổng quan: đúng 6 thẻ 1 hàng trên màn rộng (Tổng đơn · Chờ duyệt · Quá hạn · Tuổi đơn cũ nhất · Đã duyệt · Đang nghỉ hôm nay).**

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/timeoff/DashboardPanel.jsx
git commit -m "feat(timeoff-ui): gộp KPI Đã duyệt + Ngày phép đã duyệt — còn 6 thẻ"
```

### Task 20: Hint tìm kiếm không áp dụng

**Files:**
- Modify: `frontend/src/features/timeoff/TimeOff.jsx`

- [ ] **Step 1: Thêm hằng + hint dưới thanh tabs** (search chỉ có tác dụng ở `me`, `approved`, `balances`):

```jsx
const SEARCHABLE_TABS = new Set(['me', 'approved', 'balances']);
```

(đặt cạnh `MY_SORT_FIELDS` cuối file hoặc trên component — trên component, ngoài function.)

Ngay SAU `</div>` đóng khối `className="tabs"`:

```jsx
      {search && !SEARCHABLE_TABS.has(activeTab) && (
        <div className="muted" style={{ fontSize: 12.5, margin: '-8px 0 4px' }}>
          Tìm kiếm không áp dụng cho tab này.
        </div>
      )}
```

- [ ] **Step 2: Build PASS. Preview: gõ từ khóa ở ô search khi đang tab Tổng quan → thấy hint; chuyển sang Quỹ phép → hint biến mất và bảng được lọc.**

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/timeoff/TimeOff.jsx
git commit -m "feat(timeoff-ui): hint khi tìm kiếm không áp dụng cho tab hiện tại"
```

### Task 21: A11y — thao tác bàn phím cho dòng bảng click được

**Files:**
- Modify: `frontend/src/features/timeoff/TimeOff.jsx` (bảng "Đơn nghỉ của tôi")
- Modify: `frontend/src/features/timeoff/ApprovedPanel.jsx` (bảng đơn đã xử lý)
- Modify: `frontend/src/styles/base.css`

- [ ] **Step 1: CSS focus ring** (cuối `base.css`, dưới khối skeleton):

```css
.tbl tr[tabindex]:focus-visible { outline: 2px solid var(--red-600); outline-offset: -2px; }
```

- [ ] **Step 2: `TimeOff.jsx` (MyTimeOff)** — dòng bảng:

```jsx
                <tr key={r.id} tabIndex={0} onClick={() => setDetail(r)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setDetail(r); }
                  }}
                  style={{ cursor: 'pointer' }}>
```

- [ ] **Step 3: `ApprovedPanel.jsx`** — tương tự:

```jsx
                <tr key={r.id} tabIndex={0} style={{ cursor: 'pointer' }} onClick={() => setDetail(r)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setDetail(r); }
                  }}>
```

- [ ] **Step 4: Build PASS. Preview: Tab qua các dòng thấy viền focus, Enter mở modal chi tiết.**

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/timeoff/TimeOff.jsx frontend/src/features/timeoff/ApprovedPanel.jsx frontend/src/styles/base.css
git commit -m "feat(timeoff-ui): dòng bảng click được hỗ trợ bàn phím (tabIndex + Enter/Space)"
```

### Task 22: Kiểm chứng cuối + commit bundle

- [ ] **Step 1: Build cuối:** `cd /Users/nguyenanh/odoo19/frontend && npm run build` → `✓ built`.

- [ ] **Step 2: Chạy checklist thủ công đầy đủ** (preview `/hocba-hrm`, mật khẩu `hocba@123` cho login ngắn hoặc `Hocba@2026` cho email test — xem `docs/DB_TEST_DATA.md`):

| # | Kịch bản | Vai trò | Đạt? |
|---|----------|---------|------|
| 1 | Duyệt/từ chối 1 đơn ở tab Chờ duyệt → badge giảm ngay | `hr.manager` | ☐ |
| 2 | Hủy đơn ở tab Của tôi → ConfirmModal, lỗi server hiện trong modal | `nv.test` | ☐ |
| 3 | Chọn năm 2025 + 1 phòng ở Tổng quan → sang Đơn đã duyệt/Quỹ phép/Lịch giữ nguyên | `hr.manager` | ☐ |
| 4 | Quay lại tab đã xem → data hiện ngay (không skeleton), tự tươi lại | `hr.manager` | ☐ |
| 5 | Tab Tổng quan đúng 6 thẻ KPI, thẻ Đã duyệt có sub số ngày | `hr.manager` | ☐ |
| 6 | Gõ search khi ở tab Tổng quan → hint "không áp dụng" | `hr.manager` | ☐ |
| 7 | Tab/Enter mở modal chi tiết đơn bằng bàn phím | `nv.test` | ☐ |
| 8 | Trưởng phòng chỉ thấy phòng mình; GV: tab dạy thay + badge như cũ | `test_truongphong@hocba.vn`, GV | ☐ |
| 9 | `grep -rn "drawer-head\|window.confirm\|alert(" frontend/src/features/timeoff/` = 0 kết quả | — | ☐ |

- [ ] **Step 3: Commit bundle**

```bash
git add custom-addons/hocba_hrm/static/spa/
git commit -m "build(timeoff-ui): rebuild SPA bundle sau đợt dọn giao diện"
```

- [ ] **Step 4: Invoke skill `requesting-code-review` → `verification-before-completion` → `finishing-a-development-branch`** theo quy trình dự án.

---

## Ánh xạ spec → task (self-review)

| Spec | Task |
|------|------|
| §1.1 useFetch | 1 |
| §1.2 YearNav / §1.3 DeptSelect | 2 (dùng ở 6–14, 18) |
| §1.4 ModalHeader | 3 (dùng ở 9, 11, 13, 14, 15) |
| §1.5 ConfirmModal | 4 (dùng ở 17) |
| §1.6 TableSkeleton | 5 (dùng ở 6–13) |
| §2 migrate 9 file + hành vi giữ nguyên | 6–15 |
| §3.1 badge Chờ duyệt | 16 |
| §3.2 hủy đơn bằng modal | 17 (mở rộng: LapsedPanel + DecisionModal cùng pattern) |
| §3.3 lift filter | 18 |
| §3.4 KPI 6 thẻ | 19 |
| §3.5 hint search | 20 |
| §3.6 a11y | 21 |
| Kiểm chứng + bundle | 22 |
