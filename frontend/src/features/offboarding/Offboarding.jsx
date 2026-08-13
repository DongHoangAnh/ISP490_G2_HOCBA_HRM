/* ============================================================
   Màn Nghỉ việc (Offboarding) — self-service + duyệt 2 cấp.
   Owner: Vu/Tan. Spec: docs/superpowers/specs/2026-07-05-offboarding-spa-design.md
   Mirror cấu trúc màn Nghỉ phép (timeoff).
   ============================================================ */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { useSort, SortTh } from '../../components/sortable';
import { fmtDate } from '../../utils/format';
import { fetchOffboarding, offboardingAction } from '../../api/offboarding';
import OffboardingForm from './OffboardingForm';

const REASON_LABEL = {
  voluntary: 'Tự nguyện', performance: 'Không đạt',
  contract_end: 'Hết hạn HĐ', other: 'Khác',
};

/* onQueueChanged: báo App nạp lại badge "Nghỉ việc" sau mỗi thao tác. Không
   tự trừ số ở client — phạm vi đếm là quyền phía server, đoán ở đây sẽ lệch. */
export default function Offboarding({ search, onQueueChanged }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(null); // id đơn đang thao tác
  const [detail, setDetail] = useState(null);
  const [fState, setFState] = useState('all');
  const [fReason, setFReason] = useState('all');
  const [fTodo, setFTodo] = useState(false);   // chỉ đơn đang chờ chính tôi bấm

  const load = () => {
    setErr(null); setData(null);
    fetchOffboarding().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải dữ liệu nghỉ việc…" />;

  const act = (row, action, confirmMsg) => {
    if (confirmMsg && !window.confirm(confirmMsg)) return;
    setBusy(row.id);
    offboardingAction(row.id, action)
      .then(() => { load(); if (onQueueChanged) onQueueChanged(); })
      .catch((e) => alert('Không thực hiện được: ' + e.message))
      .finally(() => setBusy(null));
  };

  const q = (search || '').toLowerCase();
  const match = (r) => !q || (r.employeeName || '').toLowerCase().includes(q)
    || (r.name || '').toLowerCase().includes(q)
    || (r.reason || '').toLowerCase().includes(q);

  /* Lọc chạy trên tập đang hiển thị (officer xem đơn trong phạm vi, NV xem đơn
     của mình) nên dùng chung một bộ state cho cả 2 bảng. */
  const base = (data.isOfficer ? data.managed : data.mine).filter(match);
  // Chip trạng thái dựng từ chính dữ liệu (khỏi phải đồng bộ tay với backend
  // mỗi lần thêm state mới); nhãn lấy từ stateLabel server trả về.
  const stateChips = [{ k: 'all', lbl: 'Tất cả', n: base.length }];
  for (const r of base) {
    const c = stateChips.find((x) => x.k === r.state);
    if (c) c.n += 1;
    else stateChips.push({ k: r.state, lbl: r.stateLabel, n: 1 });
  }
  const reasonOptions = [...new Set(base.map((r) => r.reasonType).filter(Boolean))];
  const isTodo = (r) => r.canMgrApprove || r.canHrApprove || r.canDone;
  const todoCount = base.filter(isTodo).length;

  const rows = base.filter((r) => {
    if (fState !== 'all' && r.state !== fState) return false;
    if (fReason !== 'all' && r.reasonType !== fReason) return false;
    if (fTodo && !isTodo(r)) return false;
    return true;
  });
  const hasFilter = fState !== 'all' || fReason !== 'all' || fTodo;
  const clearFilter = () => { setFState('all'); setFReason('all'); setFTodo(false); };

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nghỉ việc</h1>
          <p>Đơn thôi việc &amp; phê duyệt 2 cấp · dữ liệu trực tiếp từ Odoo</p>
        </div>
        <div className="actions">
          {data.isEmployee && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Nộp đơn nghỉ</button>
          )}
        </div>
      </div>

      <div className="filterbar">
        {stateChips.map((c) => (
          <button key={c.k} className={'chip' + (fState === c.k ? ' active' : '')}
            onClick={() => setFState(c.k)}>
            {c.lbl} <span className="ct">{c.n}</span></button>
        ))}
        {data.isOfficer && (
          <button className={'chip' + (fTodo ? ' active' : '')}
            title="Chỉ hiện đơn đang chờ chính bạn bấm duyệt / hoàn tất"
            onClick={() => setFTodo((v) => !v)}>
            Chờ tôi xử lý <span className="ct">{todoCount}</span></button>
        )}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 9, alignItems: 'center' }}>
          <select className="sel" value={fReason} onChange={(e) => setFReason(e.target.value)}>
            <option value="all">Mọi lý do</option>
            {reasonOptions.map((k) => (
              <option key={k} value={k}>{REASON_LABEL[k] || k}</option>
            ))}
          </select>
          {hasFilter && (
            <button className="btn btn-ghost btn-sm" onClick={clearFilter}>Xoá lọc</button>
          )}
        </div>
      </div>

      {data.isOfficer
        ? <ManagedTable rows={rows} busy={busy} act={act} filtering={hasFilter} />
        : <MineTable rows={rows} busy={busy} act={act} filtering={hasFilter}
            onOpen={setDetail} />}

      {creating && (
        <OffboardingForm onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }} />
      )}
      {detail && <DetailModal row={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

/* ---- Bảng officer: mọi đơn trong phạm vi, nút thao tác theo cờ can* ---- */
function ManagedTable({ rows, busy, act, filtering }) {
  const sort = useSort();
  const sorted = sort.apply(rows, {
    code: (r) => r.name,
    emp: (r) => r.employeeName,
    reason: (r) => REASON_LABEL[r.reasonType] || r.reasonType,
    requested: (r) => r.requestDate,
    leave: (r) => r.expectedLeaveDate,
    asset: (r) => r.assetCount || 0,
    state: (r) => r.stateLabel,
  });
  return (
    <div className="card">
      <div className="card-head"><h3>Đơn nghỉ việc — chờ xử lý</h3></div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <SortTh sort={sort} k="code">Mã đơn</SortTh>
            <SortTh sort={sort} k="emp">Nhân viên</SortTh>
            <SortTh sort={sort} k="reason">Loại lý do</SortTh>
            <SortTh sort={sort} k="requested" style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày nộp</SortTh>
            <SortTh sort={sort} k="leave" style={{ width: '1%', whiteSpace: 'nowrap' }}>Nghỉ dự kiến</SortTh>
            <SortTh sort={sort} k="asset" className="tbl-num" style={{ width: '1%', whiteSpace: 'nowrap' }}>Tài sản</SortTh>
            <SortTh sort={sort} k="state" style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</SortTh>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
          </tr></thead>
          <tbody>
            {sorted.map((r) => <ManagedRow key={r.id} r={r} busy={busy} act={act} />)}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && (
        <EmptyState>
          {filtering ? 'Không có đơn nào khớp bộ lọc hiện tại.'
            : 'Không có đơn nghỉ việc nào trong phạm vi của bạn.'}
        </EmptyState>
      )}
    </div>
  );
}

function ManagedRow({ r, busy, act }) {
  const b = busy === r.id;
  return (
    <tr>
      <td className="mono" style={{ fontWeight: 600 }}>{r.name}</td>
      <td style={{ fontWeight: 600 }}>{r.employeeName}</td>
      <td>{REASON_LABEL[r.reasonType] || r.reasonType}</td>
      <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(r.requestDate)}</td>
      <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(r.expectedLeaveDate)}</td>
      <td className="tbl-num mono" style={{ fontWeight: 600 }}>
        {r.assetCount > 0
          ? <span title={`Đang giữ: ${r.assetCodes}`}><Badge kind="amber">{r.assetCount} đang giữ</Badge></span>
          : '0'}
      </td>
      <td style={{ overflow: 'visible', maxWidth: 'none', width: '1%', whiteSpace: 'nowrap' }}>
        <Badge kind={r.stateKind} dot>{r.stateLabel}</Badge>
      </td>
      {/* overflow visible + maxWidth none: ô tự co theo nội dung, không bị quy tắc
          .tbl td (max-width:0; overflow:hidden) cắt mất nút thao tác. */}
      <td style={{ overflow: 'visible', maxWidth: 'none', width: '1%', whiteSpace: 'nowrap' }}>
        <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
          {r.canMgrApprove && (
            <button className="btn btn-primary btn-sm" disabled={b}
              onClick={() => act(r, 'mgr_approve')}>Quản lý duyệt</button>
          )}
          {r.canHrApprove && (
            <button className="btn btn-primary btn-sm" disabled={b}
              onClick={() => act(r, 'hr_approve')}>HR duyệt</button>
          )}
          {r.canDone && (
            <button className="btn btn-primary btn-sm" disabled={b}
              onClick={() => act(r, 'done',
                'Hoàn tất nghỉ việc? Hồ sơ sẽ lưu trữ và khoá tài khoản đăng nhập.')}>
              Hoàn tất</button>
          )}
          {r.canRefuse && (
            <button className="btn btn-ghost btn-sm" disabled={b}
              onClick={() => act(r, 'refuse', 'Từ chối đơn nghỉ việc này?')}>Từ chối</button>
          )}
        </div>
      </td>
    </tr>
  );
}

/* ---- Bảng nhân viên: đơn của tôi ---- */
function MineTable({ rows, busy, act, onOpen, filtering }) {
  const sort = useSort();
  const sorted = sort.apply(rows, {
    code: (r) => r.name,
    reason: (r) => REASON_LABEL[r.reasonType] || r.reasonType,
    requested: (r) => r.requestDate,
    leave: (r) => r.expectedLeaveDate,
    state: (r) => r.stateLabel,
  });
  return (
    <div className="card">
      <div className="card-head"><h3>Đơn nghỉ việc của tôi</h3></div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <SortTh sort={sort} k="code">Mã đơn</SortTh>
            <SortTh sort={sort} k="reason">Loại lý do</SortTh>
            <SortTh sort={sort} k="requested" style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày nộp</SortTh>
            <SortTh sort={sort} k="leave" style={{ width: '1%', whiteSpace: 'nowrap' }}>Nghỉ dự kiến</SortTh>
            <SortTh sort={sort} k="state" style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</SortTh>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
          </tr></thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.id} onClick={() => onOpen(r)} style={{ cursor: 'pointer' }}>
                <td className="mono" style={{ fontWeight: 600 }}>{r.name}</td>
                <td>{REASON_LABEL[r.reasonType] || r.reasonType}</td>
                <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(r.requestDate)}</td>
                <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>{fmtDate(r.expectedLeaveDate)}</td>
                <td style={{ overflow: 'visible', maxWidth: 'none', width: '1%', whiteSpace: 'nowrap' }}>
                  <Badge kind={r.stateKind} dot>{r.stateLabel}</Badge>
                </td>
                <td style={{ overflow: 'visible', maxWidth: 'none', width: '1%', whiteSpace: 'nowrap' }}>
                  {r.canCancel && (
                    <button className="btn btn-ghost btn-sm" disabled={busy === r.id}
                      onClick={(e) => {
                        e.stopPropagation();
                        act(r, 'cancel', 'Huỷ đơn nghỉ việc này?');
                      }}>
                      {busy === r.id ? 'Đang huỷ…' : 'Huỷ'}</button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && (
        <EmptyState>
          {filtering ? 'Không có đơn nào khớp bộ lọc hiện tại.'
            : 'Chưa có đơn nghỉ việc nào.'}
        </EmptyState>
      )}
    </div>
  );
}

function Field({ label, value }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      <span style={{ fontSize: 13.5, color: 'var(--ink)', whiteSpace: 'pre-wrap' }}>{value}</span>
    </div>
  );
}

/* Modal chi tiết 1 đơn (mở khi NV bấm vào dòng ở "Đơn của tôi"). */
function DetailModal({ row, onClose }) {
  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="logout" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{row.name}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Chi tiết đơn nghỉ việc</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>
      <div style={{ padding: '18px 24px', display: 'grid', gap: 14 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="muted" style={{ fontSize: 12.5 }}>Trạng thái</span>
          <Badge kind={row.stateKind} dot>{row.stateLabel}</Badge>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 12 }}>
          <Field label="Loại lý do" value={REASON_LABEL[row.reasonType] || row.reasonType} />
          <Field label="Ngày nộp đơn" value={fmtDate(row.requestDate)} />
          <Field label="Ngày nghỉ dự kiến" value={fmtDate(row.expectedLeaveDate)} />
          <Field label="Quản lý duyệt" value={row.mgrApprovedBy || '—'} />
          <Field label="HR duyệt" value={row.hrApprovedBy || '—'} />
        </div>
        <Field label="Lý do chi tiết" value={row.reason || '—'} />
      </div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>
    </Modal>
  );
}
