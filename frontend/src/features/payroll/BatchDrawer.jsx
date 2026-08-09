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
import TblWrap from '../../components/TblWrap';

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
    return fetchBatch(batch.id).then((data) => {
      setDet(data);
      return data;
    }).catch((e) => {
      setDerr(e.message);
      return null;
    });
  };

  useEffect(() => {
    loadDet();
  }, [batch.id]);

  // Polling while backend is processing batch calculation
  useEffect(() => {
    if (det?.compute_status !== 'processing') return;

    const timer = setInterval(() => {
      loadDet().then((updated) => {
        if (updated && updated.compute_status !== 'processing') {
          clearInterval(timer);
          if (onChanged) onChanged();
        }
      });
    }, 1500);

    return () => clearInterval(timer);
  }, [det?.compute_status, batch.id]);

  const doAction = async (fn, label) => {
    setBusy(true); setActionErr(null);
    try {
      await fn();
      await loadDet();
      if (onChanged) onChanged();
    } catch (e) {
      setActionErr(`${label} thất bại: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleGenerate = () => doAction(() => generatePayslips(batch.id), 'Sinh phiếu & Tính toán');
  const handleComputeAll = () => doAction(() => generatePayslips(batch.id), 'Tính toán lại toàn bộ');
  const handleClose = () => doAction(() => closeBatch(batch.id), 'Đóng bảng');

  const [stLabel, stKind] = batchState(batch.state);
  const slipCount = det?.payslips?.length || batch.payslip_count || 0;
  const isProcessing = det?.compute_status === 'processing';
  const computedCount = det?.computed_count || 0;
  const totalCount = det?.total_count || slipCount;
  const percent = totalCount > 0 ? Math.round((computedCount / totalCount) * 100) : 0;

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
            {isProcessing && <Badge kind="warning" dot>Đang tính ngầm ({percent}%)</Badge>}
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

      {/* Realtime Batch Compute Progress Bar */}
      {isProcessing && (
        <div style={{ padding: '12px 24px', background: 'var(--blue-50)', borderBottom: '1px solid var(--blue-100)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, fontWeight: 600, color: 'var(--blue-700)', marginBottom: 6 }}>
            <span>⚡ Đang tính toán lương ngầm trong hệ thống...</span>
            <span>{computedCount} / {totalCount} phiếu ({percent}%)</span>
          </div>
          <div style={{ width: '100%', height: 8, background: '#d0e1fd', borderRadius: 4, overflow: 'hidden' }}>
            <div style={{ width: `${percent}%`, height: '100%', background: 'var(--blue-600)', transition: 'width 0.3s ease' }} />
          </div>
        </div>
      )}

      {det?.compute_error && (
        <div style={{ padding: '10px 24px', background: '#fef2f2', color: '#dc2626', fontSize: 13, borderBottom: '1px solid #fecaca' }}>
          ⚠️ Lỗi khi tính lương batch: {det.compute_error}
        </div>
      )}

      <div style={{ padding: '16px 24px', maxHeight: '52vh', overflowY: 'auto' }}>
        {derr && <EmptyState>Không tải được dữ liệu ({derr}).</EmptyState>}
        {!det && !derr && <EmptyState>Đang tải...</EmptyState>}

        {det && tab === 'payslips' && (
          det.payslips.length === 0 ? (
            <EmptyState>Chưa có phiếu lương. Nhấn "Sinh phiếu lương" để tạo.</EmptyState>
          ) : (
            <TblWrap id="batch-drawer">
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
            </TblWrap>
          )
        )}
      </div>

      {/* Action bar */}
      <div style={{ padding: '12px 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        {actionErr && <div style={{ color: 'var(--red-600)', fontSize: 13, flex: '1 1 100%', marginBottom: 6 }}>{actionErr}</div>}

        {det && det.payslips.length === 0 && (batch.state === 'draft' || det.state === 'draft') && (
          <button className="btn btn-primary" onClick={handleGenerate} disabled={busy || isProcessing}>
            <Icon name="users" size={15} />Sinh phiếu & Tính toán
          </button>
        )}
        {det && det.payslips.length > 0 && (
          <button className="btn btn-primary" onClick={handleComputeAll} disabled={busy || isProcessing}>
            <Icon name="calculator" size={15} />{isProcessing ? `Đang tính toán (${percent}%)...` : 'Tính lại tất cả'}
          </button>
        )}
        {det && (det.state === 'draft' || det.state === 'computed') && det.payslips.length > 0 && (
          <button className="btn btn-ghost" onClick={handleClose} disabled={busy || isProcessing}>
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
