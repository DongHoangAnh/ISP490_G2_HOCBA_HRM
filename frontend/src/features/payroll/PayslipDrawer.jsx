/* Chi tiết phiếu lương — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchPayslip, computePayslip, confirmPayslip, resetPayslip } from '../../api/payroll';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';
import { slipState, CATEGORY_LABEL, HIGHLIGHT_CODES, MUTED_CATEGORIES } from './util';
import TblWrap from '../../components/TblWrap';

export default function PayslipDrawer({ slip, onClose, onChanged }) {
  const [det, setDet] = useState(null);
  const [derr, setDerr] = useState(null);
  const [tab, setTab] = useState('lines');
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [resetReason, setResetReason] = useState('');
  const [showReset, setShowReset] = useState(false);

  const loadDet = () => {
    setDerr(null);
    fetchPayslip(slip.id).then(setDet).catch((e) => setDerr(e.message));
  };
  useEffect(loadDet, [slip.id]);

  const doAction = async (fn, label) => {
    setBusy(true); setErr(null);
    try {
      await fn();
      loadDet();
      if (onChanged) onChanged();
    } catch (e) {
      setErr(`${label} thất bại: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const handleCompute = () => doAction(() => computePayslip(slip.id), 'Tính lương');
  const handleConfirm = () => doAction(() => confirmPayslip(slip.id), 'Xác nhận');
  const handleReset = () => {
    if (!resetReason.trim()) return;
    doAction(() => resetPayslip(slip.id, resetReason), 'Reset');
    setShowReset(false);
    setResetReason('');
  };

  const [stLabel, stKind] = slipState((det || slip).state);
  const tabs = [
    ['lines', 'Chi tiết lương'],
    ['work', `Ngày công${det ? ` (${det.worked_days?.length || 0})` : ''}`],
    ['inputs', `Đầu vào${det ? ` (${det.inputs?.length || 0})` : ''}`],
  ];

  /* Group lines by category for visual separators */
  const groupedLines = () => {
    if (!det?.lines) return [];
    const groups = [];
    let lastCat = null;
    for (const line of det.lines) {
      const catCode = line.category_code || '';
      if (catCode && catCode !== lastCat) {
        groups.push({ type: 'header', code: catCode, label: CATEGORY_LABEL[catCode] || catCode });
        lastCat = catCode;
      }
      groups.push({ type: 'line', ...line, _catCode: catCode });
    }
    return groups;
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.4px' }}>
              {(det || slip).employee_name}
            </h2>
            <Badge kind={stKind} dot>{stLabel}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>
            {(det || slip).number || `#${slip.id}`}
            {det?.structure_name && ` · ${det.structure_name}`}
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
        {derr && <EmptyState>Không tải được phiếu lương ({derr}).</EmptyState>}
        {!det && !derr && <EmptyState>Đang tải...</EmptyState>}

        {/* Tab: Chi tiết lương */}
        {det && tab === 'lines' && (
          det.lines.length === 0 ? (
            <EmptyState>Chưa có dòng lương. Nhấn "Tính lương" để tính.</EmptyState>
          ) : (
            <TblWrap id="slip-lines">
              <table className="tbl">
                <thead>
                  <tr>
                    <th style={{ width: 110 }}>Mã</th>
                    <th>Tên</th>
                    <th style={{ textAlign: 'right' }}>Số tiền</th>
                  </tr>
                </thead>
                <tbody>
                  {groupedLines().map((item, i) => {
                    if (item.type === 'header') {
                      const isHighlight = HIGHLIGHT_CODES.has(item.code);
                      return (
                        <tr key={`h-${i}`}>
                          <td colSpan={3} style={{
                            fontWeight: 700, fontSize: 12, textTransform: 'uppercase',
                            color: isHighlight ? 'var(--red-700)' : 'var(--text-2)',
                            borderTop: isHighlight ? '2px solid var(--red-200)' : undefined,
                            paddingTop: isHighlight ? 10 : 6,
                            paddingBottom: 2,
                            background: isHighlight ? 'var(--red-50)' : undefined,
                          }}>
                            {item.label}
                          </td>
                        </tr>
                      );
                    }
                    const isHL = HIGHLIGHT_CODES.has(item._catCode);
                    const isMuted = MUTED_CATEGORIES.has(item._catCode);
                    const isNeg = item.total < 0;
                    return (
                      <tr key={item.id} style={{
                        background: isHL ? 'var(--red-50)' : undefined,
                        opacity: isMuted ? 0.55 : 1,
                      }}>
                        <td className="mono" style={{ fontSize: 12.5 }}>{item.code}</td>
                        <td style={{ fontWeight: isHL ? 700 : 400 }}>{item.name}</td>
                        <td className="mono" style={{
                          textAlign: 'right',
                          fontWeight: isHL ? 800 : 500,
                          color: item._catCode === 'NET' ? 'var(--green)' : isNeg ? 'var(--red-600)' : undefined,
                          fontSize: isHL ? 15 : 14,
                        }}>
                          {hbVND(item.total)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </TblWrap>
          )
        )}

        {/* Tab: Ngày công */}
        {det && tab === 'work' && (
          det.worked_days?.length === 0 ? (
            <EmptyState>Chưa có dữ liệu ngày công.</EmptyState>
          ) : (
            <TblWrap id="slip-work">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Mã</th>
                    <th>Tên</th>
                    <th style={{ textAlign: 'right' }}>Số ngày</th>
                    <th style={{ textAlign: 'right' }}>Số giờ</th>
                  </tr>
                </thead>
                <tbody>
                  {(det.worked_days || []).map((w) => (
                    <tr key={w.id}>
                      <td className="mono" style={{ fontSize: 12.5 }}>{w.code}</td>
                      <td>{w.name}</td>
                      <td style={{ textAlign: 'right' }} className="mono">{w.number_of_days}</td>
                      <td style={{ textAlign: 'right' }} className="mono">{w.number_of_hours}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TblWrap>
          )
        )}

        {/* Tab: Đầu vào */}
        {det && tab === 'inputs' && (
          det.inputs?.length === 0 ? (
            <EmptyState>Chưa có dữ liệu đầu vào.</EmptyState>
          ) : (
            <TblWrap id="slip-inputs">
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Mã</th>
                    <th>Tên</th>
                    <th style={{ textAlign: 'right' }}>Số tiền</th>
                  </tr>
                </thead>
                <tbody>
                  {(det.inputs || []).map((inp) => (
                    <tr key={inp.id}>
                      <td className="mono" style={{ fontSize: 12.5 }}>{inp.code}</td>
                      <td>{inp.name}</td>
                      <td style={{ textAlign: 'right' }} className="mono">{hbVND(inp.amount)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TblWrap>
          )
        )}
      </div>

      {/* Action bar */}
      <div style={{ padding: '12px 24px', borderTop: '1px solid var(--border)', display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        {err && <div style={{ color: 'var(--red-600)', fontSize: 13, flex: '1 1 100%', marginBottom: 6 }}>{err}</div>}

        {showReset && (
          <div style={{ flex: '1 1 100%', display: 'flex', gap: 8, marginBottom: 6 }}>
            <input
              placeholder="Lý do reset..."
              value={resetReason}
              onChange={(e) => setResetReason(e.target.value)}
              style={{ flex: 1, padding: '7px 10px', borderRadius: 6, border: '1px solid var(--border)', fontSize: 13 }}
            />
            <button className="btn btn-sm btn-primary" onClick={handleReset} disabled={busy || !resetReason.trim()}>Xác nhận</button>
            <button className="btn btn-sm btn-ghost" onClick={() => { setShowReset(false); setResetReason(''); }}>Huỷ</button>
          </div>
        )}

        {det && det.state === 'draft' && (
          <button className="btn btn-primary" onClick={handleCompute} disabled={busy}>
            <Icon name="calculator" size={15} />Tính lương
          </button>
        )}
        {det && det.state === 'draft' && det.lines?.length > 0 && (
          <button className="btn btn-ghost" onClick={handleConfirm} disabled={busy}>
            <Icon name="check" size={15} />Xác nhận
          </button>
        )}
        {det && det.state === 'done' && !showReset && (
          <button className="btn btn-ghost" onClick={() => setShowReset(true)} disabled={busy}>
            <Icon name="rotateCcw" size={15} />Reset về nháp
          </button>
        )}
        <div style={{ flex: 1 }} />
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>
    </Modal>
  );
}
