/* Màn Đánh giá nhân viên — 2 tab: Giảng viên / Nhân viên văn phòng.
   Owner: Việt.
   Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md
   Công thức chấm điểm: docs/CONG_THUC_DANH_GIA.md */
import { useState } from 'react';
import useFetch from '../../hooks/useFetch';
import { fetchReviews, createReview, bulkOpenReviews } from '../../api/reviews';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import TblWrap from '../../components/TblWrap';
import { useSort, SortTh } from '../../components/sortable';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import ReviewDrawer from './ReviewDrawer';
import ReviewGuide from './ReviewGuide';
import {
  GRADE_LABEL, GRADE_KIND, STATE_LABEL, STATE_KIND,
  PERIOD_TYPES, periodCount, periodLabel, unitLabel,
} from './util';

const TABS = [
  ['teacher', 'Giảng viên'],
  ['office', 'Nhân viên văn phòng'],
  // Tài liệu cho người chấm: công thức, bảng quy đổi, cách chấm từng tiêu chí.
  ['guide', 'Hướng dẫn chấm điểm'],
];

const sel = {
  padding: '6px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', fontFamily: 'inherit',
};

function Kpi({ label, value, hint }) {
  return (
    <div className="card" style={{ padding: '12px 16px', minWidth: 132, flex: 1 }}>
      <div className="faint" style={{ fontSize: 11 }}>{label}</div>
      <div style={{ fontSize: 22, fontWeight: 800, lineHeight: 1.2 }}>{value}</div>
      {hint && <div className="muted" style={{ fontSize: 11.5 }}>{hint}</div>}
    </div>
  );
}

/* Sắp cột Trạng thái theo tiến độ quy trình chấm, không theo bảng chữ cái. */
const STATE_ORDER = { none: 0, draft: 1, confirmed: 2, published: 3 };

/* Màu chấm theo bậc — cùng bảng màu với badge Xếp loại trong bảng. */
const GRADE_DOT = { a: 'var(--green)', b: 'var(--blue)', c: 'var(--gold-600)', d: 'var(--red-600)' };

/* Phân bố xếp loại A/B/C/D trong MỘT thẻ: 4 thẻ riêng sẽ đẩy hàng KPI quá dài,
   mà người dùng luôn đọc 4 số này cùng nhau. Chỉ đếm phiếu đã chấm. */
function GradeKpi({ s }) {
  const items = [['a', s.gradeA], ['b', s.gradeB], ['c', s.gradeC], ['d', s.gradeD]];
  return (
    <div className="card" style={{ padding: '12px 16px', minWidth: 212, flex: 1.4 }}>
      <div className="faint" style={{ fontSize: 11 }}>Phân bố xếp loại</div>
      <div style={{ display: 'flex', gap: 14, marginTop: 4 }}>
        {items.map(([g, n]) => (
          <div key={g} title={GRADE_LABEL[g]} style={{ minWidth: 34 }}>
            <div style={{ fontSize: 20, fontWeight: 800, lineHeight: 1.2 }}>{n || 0}</div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4, fontSize: 11.5 }}>
              <span style={{ width: 7, height: 7, borderRadius: '50%', background: GRADE_DOT[g] }} />
              <span className="muted">{g.toUpperCase()}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function GroupPanel({ group, search, canPromote }) {
  const thisYear = new Date().getFullYear();
  const [periodType, setPeriodType] = useState('quarter');
  const [year, setYear] = useState(thisYear);
  const [index, setIndex] = useState(Math.floor(new Date().getMonth() / 3) + 1);
  const [openId, setOpenId] = useState(null);
  const [msg, setMsg] = useState(null);
  const [busy, setBusy] = useState(false);
  const sort = useSort();

  const { data, err, loading, reload } = useFetch(
    () => fetchReviews({ group, periodType, year, index }),
    [group, periodType, year, index],
    `reviews:${group}:${periodType}:${year}:${index}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <LoadingState label="Đang tải dữ liệu đánh giá…" />;

  const q = (search || '').trim().toLowerCase();
  const found = q
    ? data.rows.filter((r) => (r.empName + ' ' + r.empCode + ' ' + r.department)
      .toLowerCase().includes(q))
    : data.rows;

  /* Xếp loại: 'a'…'d' đã đúng thứ tự giỏi→kém khi so chuỗi. Người chưa có phiếu
     (state 'none') không có điểm/xếp loại → trả null để luôn nằm cuối bảng,
     bất kể đang sắp tăng hay giảm. */
  const rows = sort.apply(found, {
    emp: (r) => r.empName,
    dep: (r) => r.department,
    punctual: (r) => (r.totalUnits ? r.punctualPct : null),
    score: (r) => (r.state === 'none' ? null : r.totalScore),
    grade: (r) => r.grade || null,
    state: (r) => STATE_ORDER[r.state] ?? 99,
  });

  const changeType = (t) => {
    setPeriodType(t);
    if (index > periodCount(t)) setIndex(1);
  };

  const openPeriod = async () => {
    setMsg(null); setBusy(true);
    try {
      const r = await bulkOpenReviews({ group, periodType, year, index });
      setMsg(r.created
        ? `Đã mở ${r.created} phiếu đánh giá mới${r.skipped ? `, bỏ qua ${r.skipped} người đã có phiếu` : ''}.`
        : 'Mọi nhân viên trong nhóm đã có phiếu cho kỳ này.');
      await reload();
    } catch (e) { setMsg(e.message || 'Mở đợt thất bại.'); }
    finally { setBusy(false); }
  };

  const openRow = async (row) => {
    if (row.id) { setOpenId(row.id); return; }
    setMsg(null); setBusy(true);
    try {
      const created = await createReview({
        employeeId: row.empId, periodType, year, index,
      });
      await reload();
      setOpenId(created.id);
    } catch (e) { setMsg(e.message || 'Không tạo được phiếu.'); }
    finally { setBusy(false); }
  };

  const s = data.stats;
  return (
    <>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 12 }}>
        <select style={sel} value={periodType} onChange={(e) => changeType(e.target.value)}>
          {PERIOD_TYPES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
        {periodType !== 'year' && (
          <select style={sel} value={index} onChange={(e) => setIndex(Number(e.target.value))}>
            {Array.from({ length: periodCount(periodType) }, (_, i) => (
              <option key={i + 1} value={i + 1}>
                {periodType === 'half' ? `Nửa năm ${i + 1}` : `Quý ${i + 1}`}
              </option>
            ))}
          </select>
        )}
        <select style={sel} value={year} onChange={(e) => setYear(Number(e.target.value))}>
          {[thisYear + 1, thisYear, thisYear - 1, thisYear - 2].map((y) => (
            <option key={y} value={y}>{y}</option>
          ))}
        </select>
        <span className="muted" style={{ fontSize: 12.5 }}>
          {periodLabel(periodType, index, year)}
        </span>
        <button className="btn btn-primary btn-sm" style={{ marginLeft: 'auto' }}
          disabled={busy} onClick={openPeriod}>
          <Icon name="plus" size={15} />Mở đợt đánh giá
        </button>
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginBottom: 12 }}>
        <Kpi label="Nhân sự trong nhóm" value={s.employees} />
        <Kpi label="Đã đánh giá" value={s.done} hint={`Còn ${s.pending} chưa chốt`} />
        <Kpi label="Điểm trung bình" value={s.avgScore} hint="Trên thang 100" />
        <GradeKpi s={s} />
      </div>

      {msg && (
        <div style={{
          marginBottom: 12, padding: '9px 13px', background: 'var(--surface-2)',
          border: '1px solid var(--border)', borderRadius: 10, fontSize: 12.5,
        }}>{msg}</div>
      )}

      {!rows.length ? (
        <EmptyState>Không có nhân sự nào trong nhóm này.</EmptyState>
      ) : (
        <TblWrap>
          <table className="tbl">
            <thead>
              <tr>
                <SortTh sort={sort} k="emp">Nhân viên</SortTh>
                <SortTh sort={sort} k="dep">Phòng ban</SortTh>
                <SortTh sort={sort} k="punctual" className="tbl-num">Đúng giờ</SortTh>
                <SortTh sort={sort} k="score" className="tbl-num">Tổng điểm</SortTh>
                <SortTh sort={sort} k="grade">Xếp loại</SortTh>
                <SortTh sort={sort} k="state">Trạng thái</SortTh>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.empId} style={{ cursor: 'pointer' }}
                  onClick={() => openRow(r)}>
                  <td>
                    <div style={{ fontWeight: 600 }}>{r.empName}</div>
                    <div className="faint" style={{ fontSize: 11.5 }}>
                      {r.empCode || '—'}{r.jobTitle ? ` · ${r.jobTitle}` : ''}
                    </div>
                  </td>
                  <td>{r.department || '—'}</td>
                  <td style={{ textAlign: 'right' }}>
                    {r.totalUnits
                      ? <>{r.punctualPct}%<div className="faint" style={{ fontSize: 11 }}>
                        {r.totalUnits} {unitLabel(group)}</div></>
                      : <span className="faint">—</span>}
                  </td>
                  <td style={{ textAlign: 'right', fontWeight: 700 }}>
                    {r.state === 'none' ? <span className="faint">—</span> : r.totalScore}
                  </td>
                  <td>
                    {r.grade
                      ? <Badge kind={GRADE_KIND[r.grade]}>{GRADE_LABEL[r.grade]}</Badge>
                      : <span className="faint">—</span>}
                  </td>
                  <td>
                    <Badge kind={STATE_KIND[r.state]}>{STATE_LABEL[r.state]}</Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </TblWrap>
      )}

      {openId && (
        <ReviewDrawer reviewId={openId} canPromote={canPromote}
          onClose={() => setOpenId(null)}
          onSaved={reload} />
      )}
    </>
  );
}

/* canPromote: chỉ HR Manager mới tạo được quyết định thăng tiến từ
   phiếu đã chốt (khớp guard _hr_flags của route promotion). */
export default function Reviews({ search, canPromote }) {
  const [tab, setTab] = useState(
    () => localStorage.getItem('hocba_review_tab') || 'teacher');
  const activeTab = TABS.some(([id]) => id === tab) ? tab : 'teacher';
  const select = (id) => { setTab(id); localStorage.setItem('hocba_review_tab', id); };

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Đánh giá nhân viên</h1>
          <p>Đánh giá định kỳ theo bộ tiêu chí có trọng số · chỉ số chuyên cần
            lấy tự động từ dữ liệu chấm công</p>
        </div>
      </div>

      <div className="tabs">
        {TABS.map(([id, l]) => (
          <button key={id} className={'tab' + (activeTab === id ? ' active' : '')}
            onClick={() => select(id)}>{l}</button>
        ))}
      </div>

      {activeTab === 'guide'
        ? <ReviewGuide />
        : <GroupPanel key={activeTab} group={activeTab} search={search}
            canPromote={canPromote} />}
    </div>
  );
}
