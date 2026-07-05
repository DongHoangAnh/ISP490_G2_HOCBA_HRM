/* ============================================================
   Màn Nhập việc (Onboarding) — theo dõi NV thử việc qua 2 cổng
   (F-004/005) + thử giảng (F-008). Owner: Tân.
   ============================================================ */
import { useState, useEffect, useRef } from 'react';
import { fetchOnboarding } from '../../api/employees';
import Icon from '../../components/Icon';
import Avatar from '../../components/Avatar';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate, HB_RESULT } from '../../utils/format';
import EmployeeDrawer from './EmployeeDrawer';

const TODAY = new Date().toISOString().slice(0, 10);

/* Suy ra giai đoạn hiện tại + hạn kế tiếp từ trạng thái 2 cổng / thử giảng */
function phaseOf(o) {
  if (o.isGroupB) {
    if (o.g1Result === 'fail' || o.g1mResult === 'fail' || o.g2Result === 'fail')
      return { key: 'fail', label: 'Không đạt thử việc', due: null };
    if (o.officialDate) return { key: 'done', label: 'Đã lên chính thức', due: null };
    if (o.g1Result !== 'pass') return { key: 'gate1', label: 'Chờ cổng tuần-2', due: o.g1Due };
    if (!o.equipDate) return { key: 'equip', label: 'Chờ cấp thiết bị', due: null };
    if (o.g1mResult === 'draft') return { key: 'gateMid', label: 'Chờ cổng tháng-1', due: o.g1mDue };
    if (o.g2Result !== 'pass') return { key: 'gate2', label: 'Chờ cổng tháng-2', due: o.g2Due };
    return { key: 'done', label: 'Đã qua các cổng', due: null };
  }
  if (o.trialResult === 'pass') return { key: 'done', label: 'Thử giảng đạt', due: null };
  if (o.trialResult === 'fail') return { key: 'fail', label: 'Thử giảng không đạt', due: o.trialDate };
  return { key: 'trial', label: 'Chờ thử giảng', due: o.trialDate };
}
const isOverdue = (ph) => ph.due && ph.due < TODAY && !['done'].includes(ph.key);
const phaseKind = (ph) => (ph.key === 'done' ? 'green' : ph.key === 'fail' ? 'red' : 'amber');

/* Ô trạng thái 1 cổng: badge kết quả + hạn (đỏ nếu quá hạn mà chưa đạt) */
function GateCell({ result, due, date }) {
  if (!due && !date && result === 'draft') return <span className="faint">—</span>;
  const [lbl, kind] = HB_RESULT[result] || HB_RESULT.draft;
  const overdue = due && due < TODAY && result === 'draft';
  return (
    <div>
      <Badge kind={kind} dot>{lbl}</Badge>
      {date ? (
        <div className="mono muted" style={{ fontSize: 11.5, marginTop: 3 }}>{fmtDate(date)}</div>
      ) : due ? (
        <div className="mono" style={{ fontSize: 11.5, marginTop: 3, color: overdue ? 'var(--red-600)' : 'var(--muted)' }}>
          hạn {fmtDate(due)}{overdue && ' ⚠'}
        </div>
      ) : null}
    </div>
  );
}

export default function Onboarding({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [sel, setSel] = useState(null);
  // Đóng drawer khi CHỈ XEM → không tải lại; chỉ khi đánh giá cổng/thử
  // giảng (đổi dữ liệu) mới refresh ngầm.
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

  const waitG1 = items.filter((o) => o.isGroupB && o.g1Result === 'draft').length;
  const waitMid = items.filter((o) => o.isGroupB && o.g1Result === 'pass' && o.g1mResult === 'draft').length;
  const waitG2 = items.filter((o) => o.isGroupB && o.g1mResult === 'extend' && o.g2Result === 'draft').length;
  const overdue = items.filter((o) => isOverdue(phaseOf(o))).length;

  const stats = [
    { ico: 'users', col: 'var(--blue)', bg: 'var(--blue-bg)', val: items.length, lbl: 'Đang thử việc' },
    { ico: 'checkCircle', col: 'var(--gold-600)', bg: 'var(--gold-50)', val: waitG1, lbl: 'Chờ cổng tuần-2' },
    { ico: 'award', col: 'var(--teal)', bg: 'var(--teal-bg)', val: waitMid + waitG2, lbl: 'Chờ cổng tháng-1/2' },
    { ico: 'bell', col: 'var(--red-600)', bg: 'var(--red-50)', val: overdue, lbl: 'Quá hạn đánh giá' },
  ];

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nhận việc</h1>
          <p>Thử việc 3 mốc (tuần-2 → cấp thiết bị → tháng-1 → tháng-2) · có thể Gia hạn · thử giảng cho giảng viên</p>
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
              <th>Nhân viên</th><th>Nhóm</th><th>Ngày bắt đầu</th>
              <th>Cổng tuần-2</th><th>Cổng tháng-1</th><th>Cổng tháng-2</th><th>Thử giảng</th><th>Giai đoạn</th>
            </tr></thead>
            <tbody>
              {filtered.map((o) => {
                const ph = phaseOf(o);
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
                    <td><Badge kind={o.isGroupB ? 'teal' : 'blue'}>{o.isGroupB ? 'B · Offline' : 'A · Giảng viên'}</Badge></td>
                    <td className="muted mono">{fmtDate(o.start)}</td>
                    <td>{o.isGroupB ? <GateCell result={o.g1Result} due={o.g1Due} date={o.g1Date} /> : <span className="faint">—</span>}</td>
                    <td>{o.isGroupB ? <GateCell result={o.g1mResult} due={o.g1mDue} date={o.g1mDate} /> : <span className="faint">—</span>}</td>
                    <td>{o.isGroupB ? <GateCell result={o.g2Result} due={o.g2Due} date={o.g2Date} /> : <span className="faint">—</span>}</td>
                    <td>{!o.isGroupB ? <GateCell result={o.trialResult} due={o.trialDate} date={o.trialResult !== 'draft' ? o.trialDate : null} /> : <span className="faint">—</span>}</td>
                    <td>
                      <Badge kind={phaseKind(ph)} dot>{ph.label}</Badge>
                      {isOverdue(ph) && <div style={{ fontSize: 11, color: 'var(--red-600)', fontWeight: 700, marginTop: 3 }}>⚠ quá hạn</div>}
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
