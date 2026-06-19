/* Chi tiết đợt lương — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchBatch, generatePayslips, computePayslip, closeBatch } from '../../api/payroll';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { hbVND, fmtDate } from '../../utils/format';
import { batchState, slipState } from './util';
import PayslipDrawer from './PayslipDrawer';

export default function BatchDrawer({ batch, onClose, onChanged }) {
  const [det, setDet] = useState(null);
  const [derr, setDerr] = useState(null);
  const [tab, setTab] = useState('payslips');
  const [slipSel, setSlipSel] = useState(null);
  const [busy, setBusy] = useState(false);
  const [actionErr, setActionErr] = useState(null);
  const [progress, setProgress] = useState(null);

  const loadDet = () => {
    setDerr(null);
    fetchBatch(batch.id).then(setDet).catch((e) => setDerr(e.message));
  };
  useEffect(loadDet, [batch.id]);

  const doAction = async (fn, label) => {
    setBusy(true); setActionErr(null);
    try {
      await fn();
      loadDet();
    } catch (e) {
      setActionErr(`${label} thất bại: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleGenerate = () => doAction(() => generatePayslips(batch.id), 'Sinh phiếu');
  const handleClose = () => doAction(() => closeBatch(batch.id), 'Đóng bảng');

  const handleComputeAll = async () => {
    if (!det?.payslips?.length) return;
    setBusy(true); setActionErr(null);
    const slips = det.payslips.filter((s) => s.state === 'draft');
    for (let i = 0; i < slips.length; i++) {
      setProgress(`Đang tính ${i + 1}/${slips.length}...`);
      try {
        await computePayslip(slips[i].id);
      } catch (e) {
        setActionErr(`Lỗi phiếu ${slips[i].employee_name}: ${e.message}`);
        break;
      }
    }
    setProgress(null);
    setBusy(false);
    loadDet();
  };

  const [stLabel, stKind] = batchState(batch.state);
  const slipCount = det?.payslips?.length || batch.payslip_count || 0;
  const tabs = [
    ['payslips', `Phiếu lương (${slipCount})`],
  ];

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.4px' }}>{batch.name}</h2>
            <Badge kind={stKind} dot>{stLabel}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>
            {fmtDate(batch.date_start)} — {fmtDate(batch.date_end)} · {slipCount} phiếu lương
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '0 24px' }}>
        <div className="tabs" style={{ marginBottom: 0 }}>
          {tabs.map(([id, l]) => (
            <button key={id} className={'tab' + (tab === id ? ' active' : '')} onClick={() => setTab(id)}>{l}</button>
          ))}
        </div>
      </div>

      <div style={{ padding: '16px 24px', maxHeight: '52vh', overflowY: 'auto' }}>
        {derr && <EmptyState>Không tải được dữ liệu ({derr}).</EmptyState>}
        {!det && !derr && <EmptyState>Đang tải...</EmptyState>}

        {det && tab === 'payslips' && (
          det.payslips.length === 0 ? (
            <EmptyState>Chưa có phiếu lương. Nhấn "Sinh phiếu lương" để tạo.</EmptyState>
          ) : (
            <div className="tbl-wrap">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Mã phiếu</th>
                    <th>Nhân viên</th>
                    <th style={{ textAlign: 'right' }}>Gross</th>
                    <th style={{ textAlign: 'right' }}>Net</th>
                    <th>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {det.payslips.map((s) => {
                    const [sl, sk] = slipState(s.state);
                    return (
                      <tr key={s.id} onClick={() => setSlipSel(s)} style={{ cursor: 'pointer' }}>
                        <td className="mono" style={{ fontSize: 12.5 }}>{s.number || `#${s.id}`}</td>
                        <td style={{ fontWeight: 600 }}>{s.employee_name}</td>
                        <td style={{ textAlign: 'right' }} className="mono">{hbVND(s.gross_amount)}</td>
                        <td style={{ textAlign: 'right', fontWeight: 600 }} className="mono">{hbVND(s.net_amount)}</td>
                        <td><Badge kind={sk}>{sl}</Badge></td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )
        )}
      </div>

      {/* Action bar */}
      <div style={{ padding: '12px 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        {actionErr && <div style={{ color: 'var(--red-600)', fontSize: 13, flex: '1 1 100%', marginBottom: 6 }}>{actionErr}</div>}
        {progress && <div style={{ fontSize: 13, color: 'var(--blue)', flex: '1 1 100%', marginBottom: 6 }}>{progress}</div>}

        {det && det.payslips.length === 0 && (batch.state === 'draft' || det.state === 'draft') && (
          <button className="btn btn-primary" onClick={handleGenerate} disabled={busy}>
            <Icon name="users" size={15} />Sinh phiếu lương
          </button>
        )}
        {det && det.payslips.length > 0 && det.payslips.some((s) => s.state === 'draft') && (
          <button className="btn btn-primary" onClick={handleComputeAll} disabled={busy}>
            <Icon name="calculator" size={15} />{busy && progress ? progress : 'Tính tất cả'}
          </button>
        )}
        {det && (det.state === 'draft' || det.state === 'computed') && det.payslips.length > 0 && (
          <button className="btn btn-ghost" onClick={handleClose} disabled={busy}>
            <Icon name="lock" size={15} />Đóng bảng lương
          </button>
        )}
        <div style={{ flex: 1 }} />
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>

      {slipSel && (
        <PayslipDrawer
          slip={slipSel}
          onClose={() => setSlipSel(null)}
          onChanged={() => { setSlipSel(null); loadDet(); }}
        />
      )}
    </Modal>
  );
}
