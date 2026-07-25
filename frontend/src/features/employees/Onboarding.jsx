/* ============================================================
   Màn Nhập việc (Onboarding) — theo dõi NV thử việc qua QUY TRÌNH
   BƯỚC ĐỘNG (hb.onboarding.step, admin config được). Owner: Tân.
   Spec: docs/superpowers/specs/2026-07-15-onboarding-config-design.md
   ============================================================ */
import { useState, useEffect, useRef } from 'react';
import { fetchOnboarding } from '../../api/employees';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import EmployeeDrawer from './EmployeeDrawer';

const TODAY = new Date().toISOString().slice(0, 10);

/* Trạng thái tổng của 1 NV suy từ danh sách bước động. */
function overallOf(o) {
  if (!o.steps || !o.steps.length)
    return { key: 'none', label: 'Chưa có quy trình' };
  if (o.steps.some((s) => s.result === 'fail'))
    return { key: 'fail', label: 'Không đạt thử việc' };
  if (o.steps.every((s) => s.state === 'done' || s.state === 'skipped'))
    return { key: 'done', label: 'Hoàn tất quy trình' };
  return { key: 'run', label: 'Đang thử việc' };
}
const overallKind = { done: 'green', fail: 'red', run: 'amber', none: 'gray' };
const isOverdue = (o) =>
  o.current && o.current.dueDate && o.current.dueDate < TODAY;

/* Ô "bước hiện tại": tên + loại + hạn (đỏ nếu quá hạn). */
function CurrentStepCell({ o }) {
  const c = o.current;
  if (!c) return <span className="faint">—</span>;
  const late = isOverdue(o);
  return (
    <div>
      <div style={{ fontWeight: 600, fontSize: 12.5 }}>
        {c.name}
        {c.extendCount > 0 && <span style={{ color: 'var(--gold-600)' }}> ↻×{c.extendCount}</span>}
      </div>
      <div className="mono" style={{ fontSize: 11.5, marginTop: 2, color: late ? 'var(--red-600)' : 'var(--muted)' }}>
        {c.stepType === 'evaluation' ? 'Đánh giá' : 'Việc cần làm'}
        {c.dueDate ? ` · hạn ${fmtDate(c.dueDate)}` : ''}{late && ' ⚠'}
      </div>
    </div>
  );
}

/* Thanh tiến độ nhỏ trong bảng. */
function ProgressCell({ o }) {
  const { done, total } = o.progress || { done: 0, total: 0 };
  const pct = total ? Math.round((done / total) * 100) : 0;
  return (
    <div style={{ minWidth: 110 }}>
      <div className="mono" style={{ fontSize: 12 }}>{done}/{total} bước</div>
      <div style={{ height: 5, borderRadius: 3, background: 'var(--surface-2)', marginTop: 4, overflow: 'hidden' }}>
        <div style={{ width: `${pct}%`, height: '100%', borderRadius: 3, background: pct === 100 ? 'var(--green)' : 'var(--gold-500)' }} />
      </div>
    </div>
  );
}

export default function Onboarding({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);
  // Đóng drawer khi CHỈ XEM → không tải lại; chỉ khi thao tác bước (đổi
  // dữ liệu) mới refresh ngầm.
  const dirtyRef = useRef(false);

  const load = () => {
    setErr(null); setData(null);
    fetchOnboarding().then(setData).catch((e) => setErr(e.message));
  };
  // Làm mới ngầm: không xoá data hiện có → không chớp màn "Đang tải…".
  const reloadQuiet = () => {
    fetchOnboarding().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải dữ liệu nhận việc…" />;

  const items = data.items;
  const filtered = items.filter((o) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (o.name || '').toLowerCase().includes(q) || (o.code || '').toLowerCase().includes(q)
      || (o.depName || '').toLowerCase().includes(q);
  });

  const running = items.filter((o) => overallOf(o).key === 'run').length;
  const waitingEval = items.filter((o) =>
    o.current && o.current.stepType === 'evaluation').length;
  const overdue = items.filter(isOverdue).length;

  const stats = [
    { ico: 'users', col: 'var(--blue)', bg: 'var(--blue-bg)', val: items.length, lbl: 'Đang thử việc' },
    { ico: 'checkCircle', col: 'var(--teal)', bg: 'var(--teal-bg)', val: running, lbl: 'Đang chạy quy trình' },
    { ico: 'award', col: 'var(--gold-600)', bg: 'var(--gold-50)', val: waitingEval, lbl: 'Chờ đánh giá' },
    { ico: 'bell', col: 'var(--red-600)', bg: 'var(--red-50)', val: overdue, lbl: 'Quá hạn bước' },
  ];

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nhận việc</h1>
          <p>Theo dõi nhân viên thử việc theo quy trình bước động — admin cấu hình được trong màn Cấu hình nhận việc</p>
        </div>
      </div>

      <div className="stat-grid">
        {stats.map((s, i) => (
          <div className="stat" key={i}>
            <div className="stat-ico" style={{ background: s.bg, color: s.col }}><Icon name={s.ico} size={22} /></div>
            <div className="stat-val">{s.val}</div>
            <div className="stat-lbl">{s.lbl}</div>
          </div>
        ))}
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Nhân viên đang thử việc</h3>
          <span className="sub">{filtered.length} người</span>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th><th>Ngày bắt đầu</th>
              <th>Quy trình</th><th>Tiến độ</th><th>Bước hiện tại</th><th>Trạng thái</th>
            </tr></thead>
            <tbody>
              {filtered.map((o) => {
                const ov = overallOf(o);
                return (
                  <tr key={o.id} onClick={() => setSel(o)}>
                    <td>
                      <div className="cell-emp">
                        <Avatar emp={o} size={34} />
                        <div>
                          <div className="nm">{o.name}</div>
                          <div className="id">{o.code} · {o.jobTitle}</div>
                        </div>
                      </div>
                    </td>
                    <td className="muted">{o.depName}</td>
                    <td className="muted mono">{fmtDate(o.start)}</td>
                    <td className="muted" style={{ fontSize: 12.5 }}>{o.templateName || '—'}</td>
                    <td><ProgressCell o={o} /></td>
                    <td><CurrentStepCell o={o} /></td>
                    <td>
                      <Badge kind={overallKind[ov.key]} dot>{ov.label}</Badge>
                      {isOverdue(o) && ov.key === 'run' && (
                        <div style={{ fontSize: 11, color: 'var(--red-600)', fontWeight: 700, marginTop: 3 }}>⚠ quá hạn</div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && <EmptyState>Không có nhân viên thử việc nào.</EmptyState>}
      </div>

      {sel && (
        <EmployeeDrawer
          emp={{ id: sel.id, code: sel.code, name: sel.name, depName: sel.depName,
                 jobTitle: sel.jobTitle, hasImg: sel.hasImg, statusKey: 'probation', status: 'Thử việc' }}
          initialTab="probation"
          isHr={data.isHr} isMgr={data.isHrManager}
          onChanged={() => { dirtyRef.current = true; }}
          onClose={() => { setSel(null); if (dirtyRef.current) { dirtyRef.current = false; reloadQuiet(); } }} />
      )}
    </div>
  );
}
