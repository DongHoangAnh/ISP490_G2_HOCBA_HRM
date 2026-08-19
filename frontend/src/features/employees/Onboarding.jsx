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
import { useSort, SortTh } from '../../components/sortable';
import { fmtDate } from '../../utils/format';
import EmployeeDrawer from './EmployeeDrawer';

const TODAY = new Date().toISOString().slice(0, 10);

/* Cắt 1 dòng + "…" cho chữ dài — bù cho .tbl-scroll đã bỏ ellipsis của td. */
const CLIP = { overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' };

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

/* Ngày kết thúc thử việc — hệ thống KHÔNG lưu field riêng, suy từ quy trình:
   chuỗi xong rồi thì lấy ngày làm xong bước cuối; còn đang chạy thì lấy hạn
   muộn nhất của chuỗi (dự kiến). Trả {date, planned} — planned=true để bảng
   nói rõ đó mới là dự kiến.

   KHÔNG dùng officialDate: bảng này chỉ chứa NV đang thử việc, nên hồ sơ nào
   còn giữ officialDate thì đó là dữ liệu rác cũ (có hồ sơ mang ngày chính thức
   sớm hơn cả ngày bắt đầu thử việc) — bày ra là bảng tự mâu thuẫn. */
function probationEndOf(o) {
  const steps = o.steps || [];
  if (steps.length && overallOf(o).key === 'done') {
    const dones = steps.map((s) => s.doneDate).filter(Boolean).sort();
    if (dones.length) return { date: dones[dones.length - 1], planned: false };
  }
  const dues = steps.map((s) => s.dueDate).filter(Boolean).sort();
  if (dues.length) return { date: dues[dues.length - 1], planned: true };
  return { date: null, planned: false };
}

/* Ô "ngày kết thúc thử việc": đỏ khi dự kiến đã trôi qua mà chưa xong. */
function EndDateCell({ o }) {
  const { date, planned } = probationEndOf(o);
  if (!date) return <span className="faint">—</span>;
  const late = planned && date < TODAY;
  return (
    <div>
      <div className="mono" style={{ fontSize: 12.5, color: late ? 'var(--red-600)' : undefined }}>
        {fmtDate(date)}
      </div>
      {planned && (
        <div className="faint" style={{ fontSize: 11 }}>dự kiến</div>
      )}
    </div>
  );
}

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

/* onQueueChanged: báo App nạp lại badge "Nhận việc" sau khi xử lý bước.
   Không tự trừ số ở client — phạm vi đếm là quyền phía server. */
export default function Onboarding({ search, onQueueChanged }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);
  const sort = useSort();
  const [fState, setFState] = useState('all');   // trạng thái tổng
  const [fDep, setFDep] = useState('all');
  const [fTpl, setFTpl] = useState('all');       // quy trình áp dụng
  const [fOverdue, setFOverdue] = useState(false);
  const [fEval, setFEval] = useState(false);     // đang chờ bước đánh giá
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
  const searched = items.filter((o) => {
    if (!search) return true;
    const q = search.toLowerCase();
    return (o.name || '').toLowerCase().includes(q) || (o.code || '').toLowerCase().includes(q)
      || (o.depName || '').toLowerCase().includes(q);
  });

  /* Bộ lọc: chip trạng thái tổng + 2 nút bật/tắt (quá hạn, chờ đánh giá) khớp
     đúng 2 thẻ số ở trên, và select phòng ban / quy trình.

     Một hàm lọc duy nhất cho cả bảng lẫn số trên chip, cho phép ghi đè từng
     tiêu chí: số trên chip đếm theo các bộ lọc CÒN LẠI đang bật, tức "bấm chip
     này thì thấy bao nhiêu dòng". Đếm trên `searched` chỉ đúng khi mỗi lần
     dùng một bộ lọc — bật thêm cái thứ hai là chip ghi một đằng, bảng ra một
     nẻo. Thẻ số ở đầu trang vẫn theo toàn bộ danh sách, không dính bộ lọc. */
  const isEval = (o) => !!(o.current && o.current.stepType === 'evaluation');
  const keep = (o, ov = {}) => {
    const st = 'fState' in ov ? ov.fState : fState;
    const dep = 'fDep' in ov ? ov.fDep : fDep;
    const tpl = 'fTpl' in ov ? ov.fTpl : fTpl;
    const overdue = 'fOverdue' in ov ? ov.fOverdue : fOverdue;
    const evalOnly = 'fEval' in ov ? ov.fEval : fEval;
    if (st !== 'all' && overallOf(o).key !== st) return false;
    if (dep !== 'all' && o.depName !== dep) return false;
    if (tpl !== 'all' && o.templateName !== tpl) return false;
    if (overdue && !isOverdue(o)) return false;
    if (evalOnly && !isEval(o)) return false;
    return true;
  };
  const countIf = (ov) => searched.filter((o) => keep(o, ov)).length;

  const stateChips = [
    { k: 'all', lbl: 'Tất cả' },
    { k: 'run', lbl: 'Đang thử việc' },
    { k: 'done', lbl: 'Hoàn tất quy trình' },
    { k: 'fail', lbl: 'Không đạt thử việc' },
    { k: 'none', lbl: 'Chưa có quy trình' },
  ].map((c) => ({ ...c, n: countIf({ fState: c.k }) }))
    .filter((c) => c.k === 'all' || c.n > 0 || fState === c.k);

  const evalChipN = countIf({ fEval: true });
  const overdueChipN = countIf({ fOverdue: true });

  // Chỉ bày phòng ban / quy trình còn xuất hiện sau các bộ lọc khác.
  const depOptions = [...new Set(searched.filter((o) => keep(o, { fDep: 'all' }))
    .map((o) => o.depName).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'vi'));
  const tplOptions = [...new Set(searched.filter((o) => keep(o, { fTpl: 'all' }))
    .map((o) => o.templateName).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'vi'));

  const filtered = searched.filter((o) => keep(o));
  const hasFilter = fState !== 'all' || fDep !== 'all' || fTpl !== 'all' || fOverdue || fEval;

  /* Tiến độ so theo % (3/4 phải đứng trên 5/10); bước hiện tại so theo HẠN
     để người dùng kéo được các ca sắp/đã quá hạn lên đầu. */
  const rows = sort.apply(filtered, {
    name: (o) => o.name,
    dep: (o) => o.depName,
    start: (o) => o.start,
    end: (o) => probationEndOf(o).date,
    tpl: (o) => o.templateName,
    progress: (o) => {
      const p = o.progress || { done: 0, total: 0 };
      return p.total ? p.done / p.total : -1;
    },
    step: (o) => (o.current ? o.current.dueDate : null),
    state: (o) => overallOf(o).label,
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

      <div className="filterbar">
        {stateChips.map((c) => (
          <button key={c.k} className={'chip' + (fState === c.k ? ' active' : '')}
            onClick={() => setFState(c.k)}>
            {c.lbl} <span className="ct">{c.n}</span></button>
        ))}
        <button className={'chip' + (fEval ? ' active' : '')}
          title="Chỉ hiện người đang dừng ở một bước đánh giá"
          onClick={() => setFEval((v) => !v)}>
          Chờ đánh giá <span className="ct">{evalChipN}</span></button>
        <button className={'chip' + (fOverdue ? ' active' : '')}
          title="Chỉ hiện người có bước hiện tại đã quá hạn"
          onClick={() => setFOverdue((v) => !v)}>
          Quá hạn <span className="ct">{overdueChipN}</span></button>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 9, alignItems: 'center' }}>
          <select className="sel" value={fDep} onChange={(e) => setFDep(e.target.value)}>
            <option value="all">Mọi phòng ban</option>
            {depOptions.map((d) => <option key={d}>{d}</option>)}
          </select>
          <select className="sel" value={fTpl} onChange={(e) => setFTpl(e.target.value)}>
            <option value="all">Mọi quy trình</option>
            {tplOptions.map((t) => <option key={t}>{t}</option>)}
          </select>
          {hasFilter && (
            <button className="btn btn-ghost btn-sm"
              onClick={() => { setFState('all'); setFDep('all'); setFTpl('all'); setFOverdue(false); setFEval(false); }}>
              Xoá lọc</button>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Nhân viên đang thử việc</h3>
          <span className="sub">{filtered.length} người</span>
        </div>
        {/* tbl-scroll: 8 cột không vừa bề ngang thì cho KÉO NGANG. Mặc định
            .tbl-wrap ép bảng width:100% + td ellipsis nên cột bị bóp lại và
            cắt mất chữ mà chẳng bao giờ hiện thanh cuộn — đúng lỗi che dữ
            liệu. Cùng cách các bảng bên Tuyển dụng đang dùng. */}
        <div className="tbl-wrap tbl-scroll">
          <table className="tbl">
            <thead><tr>
              <SortTh sort={sort} k="name">Nhân viên</SortTh>
              <SortTh sort={sort} k="dep">Phòng ban</SortTh>
              <SortTh sort={sort} k="start">Ngày bắt đầu</SortTh>
              <SortTh sort={sort} k="end">Ngày kết thúc thử việc</SortTh>
              <SortTh sort={sort} k="tpl">Quy trình thử việc</SortTh>
              <SortTh sort={sort} k="progress">Tiến độ</SortTh>
              <SortTh sort={sort} k="step">Bước hiện tại</SortTh>
              <SortTh sort={sort} k="state">Trạng thái</SortTh>
            </tr></thead>
            <tbody>
              {rows.map((o) => {
                const ov = overallOf(o);
                return (
                  <tr key={o.id} onClick={() => setSel(o)}>
                    <td>
                      <div className="cell-emp">
                        <Avatar emp={o} size={34} />
                        {/* tbl-scroll bỏ ellipsis của td → chặn bề ngang tại
                            đây, không thì một chức danh dài kéo cả bảng ra. */}
                        <div style={{ minWidth: 0, maxWidth: 240 }}>
                          <div className="nm" style={CLIP}>{o.name}</div>
                          <div className="id" style={CLIP}>{o.code} · {o.jobTitle}</div>
                        </div>
                      </div>
                    </td>
                    <td className="muted">{o.depName}</td>
                    <td className="muted mono">{fmtDate(o.start)}</td>
                    <td className="muted"><EndDateCell o={o} /></td>
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
        {filtered.length === 0 && (
          <EmptyState>
            {hasFilter || search
              ? 'Không có ai khớp bộ lọc hiện tại.'
              : 'Không có nhân viên thử việc nào.'}
          </EmptyState>
        )}
      </div>

      {sel && (
        <EmployeeDrawer
          emp={{ id: sel.id, code: sel.code, name: sel.name, depName: sel.depName,
                 jobTitle: sel.jobTitle, hasImg: sel.hasImg, statusKey: 'probation', status: 'Thử việc' }}
          initialTab="probation"
          isHr={data.isHr} isMgr={data.isHrManager}
          onChanged={() => { dirtyRef.current = true; }}
          onClose={() => {
            setSel(null);
            if (dirtyRef.current) {
              dirtyRef.current = false;
              reloadQuiet();
              if (onQueueChanged) onQueueChanged();
            }
          }} />
      )}
    </div>
  );
}
