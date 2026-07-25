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
import { fmtDate } from '../../utils/format';
import { fetchOffboarding, offboardingAction } from '../../api/offboarding';
import OffboardingForm from './OffboardingForm';

const REASON_LABEL = {
  voluntary: 'Tự nguyện', performance: 'Không đạt',
  contract_end: 'Hết hạn HĐ', other: 'Khác',
};

export default function Offboarding({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(null); // id đơn đang thao tác
  const [detail, setDetail] = useState(null);

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
      .then(load)
      .catch((e) => alert('Không thực hiện được: ' + e.message))
      .finally(() => setBusy(null));
  };

  const q = (search || '').toLowerCase();
  const match = (r) => !q || (r.employeeName || '').toLowerCase().includes(q)
    || (r.name || '').toLowerCase().includes(q)
    || (r.reason || '').toLowerCase().includes(q);

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

      {data.isOfficer
        ? <ManagedTable rows={data.managed.filter(match)} busy={busy} act={act} />
        : <MineTable rows={data.mine.filter(match)} busy={busy} act={act}
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
function ManagedTable({ rows, busy, act }) {
  return (
    <div className="card">
      <div className="card-head"><h3>Đơn nghỉ việc — chờ xử lý</h3></div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Mã đơn</th><th>Nhân viên</th><th>Loại lý do</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày nộp</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Nghỉ dự kiến</th>
            <th className="tbl-num" style={{ width: '1%', whiteSpace: 'nowrap' }}>Tài sản</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
          </tr></thead>
          <tbody>
            {rows.map((r) => <ManagedRow key={r.id} r={r} busy={busy} act={act} />)}
          </tbody>
        </table>
      </div>
      {rows.length === 0 && (
        <EmptyState>Không có đơn nghỉ việc nào trong phạm vi của bạn.</EmptyState>
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
function MineTable({ rows, busy, act, onOpen }) {
  return (
    <div className="card">
      <div className="card-head"><h3>Đơn nghỉ việc của tôi</h3></div>
      <div className="tbl-wrap">
        <table className="tbl">
          <thead><tr>
            <th>Mã đơn</th><th>Loại lý do</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày nộp</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Nghỉ dự kiến</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
            <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
          </tr></thead>
          <tbody>
            {rows.map((r) => (
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
      {rows.length === 0 && <EmptyState>Chưa có đơn nghỉ việc nào.</EmptyState>}
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
