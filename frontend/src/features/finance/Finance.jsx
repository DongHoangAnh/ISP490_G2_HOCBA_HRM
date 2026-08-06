/* ============================================================
   Màn Tài chính — Quản lý dòng tiền (module hocba_finance).
   Tabs: Phiếu thu/chi · Báo cáo. Owner: Tài chính.
   Spec: docs/superpowers/specs/2026-07-11-finance-cashflow.md
   ============================================================ */
import { useState, useEffect, useCallback } from 'react';
import {
  fetchFinanceContext, fetchVouchers, voucherAction, fetchSummary,
} from '../../api/finance';
import VoucherForm from './VoucherForm';
import FundCategoryManager from './FundCategoryManager';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND, fmtDate } from '../../utils/format';
import { printVoucher } from '../../utils/printVoucher';

const STATE_BADGE = {
  draft: ['Nháp', 'gray'], approved: ['Đã duyệt', 'amber'],
  posted: ['Đã ghi sổ', 'green'], cancel: ['Huỷ', 'red'],
};
const ACTION_LABEL = {
  approve: 'Duyệt', post: 'Ghi sổ', cancel: 'Huỷ', reset: 'Về nháp',
};

const curMonth = () => {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
};

export default function Finance({ search = '' }) {
  const [ctx, setCtx] = useState(null);
  const [ctxErr, setCtxErr] = useState(null);
  const [tab, setTab] = useState('vouchers');
  const [month, setMonth] = useState(curMonth());

  const loadCtx = useCallback(() => {
    setCtxErr(null);
    fetchFinanceContext().then(setCtx).catch((e) => setCtxErr(e.message));
  }, []);
  useEffect(loadCtx, [loadCtx]);

  if (ctxErr) return <ErrorState message={ctxErr} onRetry={loadCtx} />;
  if (!ctx) return <LoadingState label="Đang tải tài chính…" />;

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Tài chính — Dòng tiền</h1>
          <p>Quản lý thu chi &amp; số dư quỹ · thuần dòng tiền thực tế</p>
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--muted)' }}>
          Kỳ
          <input type="month" value={month} onChange={(e) => setMonth(e.target.value)}
            style={{ padding: '7px 10px', borderRadius: 9, border: '1px solid var(--border-strong)', fontFamily: 'inherit', fontSize: 13 }} />
        </label>
      </div>

      <div className="tabs">
        <button className={'tab' + (tab === 'vouchers' ? ' active' : '')} onClick={() => setTab('vouchers')}>Phiếu thu/chi</button>
        <button className={'tab' + (tab === 'reports' ? ' active' : '')} onClick={() => setTab('reports')}>Báo cáo</button>
        {ctx.isFinance && (
          <button className={'tab' + (tab === 'config' ? ' active' : '')} onClick={() => setTab('config')}>
            Cấu hình
          </button>
        )}
      </div>

      {tab === 'vouchers' && <VouchersTab ctx={ctx} month={month} search={search} onReloadCtx={loadCtx} />}
      {tab === 'reports' && <ReportsTab month={month} />}
      {tab === 'config' && ctx.isFinance && <FundCategoryManager ctx={ctx} onReloadCtx={loadCtx} />}
    </div>
  );
}

/* ── Tab Phiếu thu/chi ──────────────────────────────────────────────── */
function VouchersTab({ ctx, month, search, onReloadCtx }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [fType, setFType] = useState('');
  const [fState, setFState] = useState('');
  const [showForm, setShowForm] = useState(false);
  const [busyId, setBusyId] = useState(0);

  const load = useCallback(() => {
    setErr(null);
    fetchVouchers({ month, type: fType, state: fState })
      .then(setData).catch((e) => setErr(e.message));
  }, [month, fType, fState]);
  useEffect(load, [load]);

  const doAction = async (v, action) => {
    if (action === 'cancel' && !window.confirm(`Huỷ phiếu ${v.name}? Nếu đã ghi sổ, số dư quỹ sẽ được hoàn lại.`)) return;
    setBusyId(v.id);
    try {
      await voucherAction(v.id, action);
      load();
      onReloadCtx();               // số dư quỹ có thể đổi sau ghi sổ/huỷ
    } catch (e) { window.alert(e.message); } finally { setBusyId(0); }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;

  const q = search.trim().toLowerCase();
  const rows = (data?.vouchers || []).filter((v) => !q
    || v.name.toLowerCase().includes(q)
    || (v.partnerName || '').toLowerCase().includes(q)
    || (v.categoryName || '').toLowerCase().includes(q)
    || (v.memo || '').toLowerCase().includes(q));

  return (
    <>
      <div className="card">
        <div className="card-head" style={{ gap: 10, flexWrap: 'wrap' }}>
          <h3 style={{ marginRight: 'auto' }}>Phiếu thu/chi</h3>
          <select value={fType} onChange={(e) => setFType(e.target.value)}
            style={selStyle}>
            <option value="">Tất cả loại</option>
            <option value="income">Phiếu thu</option>
            <option value="expense">Phiếu chi</option>
          </select>
          <select value={fState} onChange={(e) => setFState(e.target.value)}
            style={selStyle}>
            <option value="">Mọi trạng thái</option>
            <option value="draft">Nháp</option>
            <option value="approved">Đã duyệt</option>
            <option value="posted">Đã ghi sổ</option>
            <option value="cancel">Huỷ</option>
          </select>
          <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>
            <Icon name="plus" size={15} />Tạo phiếu
          </button>
        </div>
        <div className="tbl-wrap">
          <table className="tbl" style={{ tableLayout: 'fixed', minWidth: 880 }}>
            <colgroup>
              <col style={{ width: 118 }} />
              <col style={{ width: 92 }} />
              <col style={{ width: 66 }} />
              <col />
              <col style={{ width: '13%' }} />
              <col />
              <col style={{ width: 148 }} />
              <col style={{ width: 116 }} />
              <col style={{ width: 104 }} />
            </colgroup>
            <thead><tr>
              <th>Số phiếu</th><th>Ngày</th><th>Loại</th><th>Mục</th>
              <th>Phòng ban</th><th>Người nộp/nhận</th>
              <th style={{ textAlign: 'right' }}>Số tiền</th>
              <th>Trạng thái</th>
              <th style={{ textAlign: 'right' }}>Thao tác</th>
            </tr></thead>
            <tbody>
              {rows.map((v) => {
                const [lbl, kind] = STATE_BADGE[v.state] || ['—', 'gray'];
                return (
                  <tr key={v.id}>
                    <td style={nowrapCell}><span className="mono" style={{ fontWeight: 600 }}>{v.name}</span></td>
                    <td className="muted" style={nowrapCell}>{fmtDate(v.date)}</td>
                    <td style={nowrapCell}>
                      <Badge kind={v.type === 'income' ? 'green' : 'red'}>
                        {v.type === 'income' ? 'Thu' : 'Chi'}
                      </Badge>
                    </td>
                    <td title={v.categoryName}>{v.categoryName}</td>
                    <td className="muted" title={v.departmentName || ''}>{v.departmentName || '—'}</td>
                    <td className="muted" title={v.partnerName || ''}>{v.partnerName || '—'}</td>
                    <td className="mono" style={{ ...nowrapCell, textAlign: 'right', fontWeight: 700, color: v.type === 'income' ? 'var(--green-600,#16a34a)' : 'var(--red-600)' }}>
                      {v.type === 'income' ? '+' : '−'}{hbVND(v.amount)}
                    </td>
                    <td style={nowrapCell}><Badge kind={kind} dot>{lbl}</Badge></td>
                    <td style={{ ...nowrapCell, textAlign: 'right' }}>
                      <div style={{ display: 'flex', gap: 6, justifyContent: 'flex-end' }}>
                        {/* In phiếu — luôn hiển thị */}
                        <ActBtn icon="printer" title="In phiếu (Mẫu TT200)"
                          onClick={() => printVoucher(v, ctx.company)} />
                        {v.canApprove && (
                          <ActBtn icon="check" title="Duyệt" disabled={busyId === v.id}
                            onClick={() => doAction(v, 'approve')} />
                        )}
                        {v.canPost && (
                          <ActBtn icon="checkCircle" title="Ghi sổ" kind="primary" disabled={busyId === v.id}
                            onClick={() => doAction(v, 'post')} />
                        )}
                        {v.canCancel && v.state !== 'draft' && (
                          <ActBtn icon="x" title="Huỷ" disabled={busyId === v.id}
                            onClick={() => doAction(v, 'cancel')} />
                        )}
                        {!v.canApprove && !v.canPost && !(v.canCancel && v.state !== 'draft') && v.state === 'cancel' && (
                          <span className="muted" style={{ fontSize: 12 }}>—</span>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {!data && <div className="empty">Đang tải…</div>}
        {data && rows.length === 0 && <EmptyState>Chưa có phiếu nào trong kỳ.</EmptyState>}
      </div>

      {showForm && (
        <VoucherForm ctx={ctx}
          onClose={() => setShowForm(false)}
          onDone={() => { setShowForm(false); load(); }} />
      )}
    </>
  );
}

/* ── Tab Báo cáo ────────────────────────────────────────────────────── */
function ReportsTab({ month }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const load = useCallback(() => {
    setErr(null);
    fetchSummary({ month }).then(setData).catch((e) => setErr(e.message));
  }, [month]);
  useEffect(load, [load]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải báo cáo…" />;

  const stats = [
    { lbl: 'Tổng thu', val: hbVND(data.totalIncome), ico: 'arrowDown', bg: '#dcfce7', col: '#16a34a' },
    { lbl: 'Tổng chi', val: hbVND(data.totalExpense), ico: 'arrowUp', bg: 'var(--red-50)', col: 'var(--red-600)' },
    { lbl: 'Lãi / Lỗ', val: hbVND(data.net), ico: 'trend', bg: '#e0e7ff', col: '#4f46e5' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="stat-grid">
        {stats.map((s, i) => (
          <div className="stat" key={i}>
            <div className="stat-ico" style={{ background: s.bg, color: s.col }}><Icon name={s.ico} size={22} /></div>
            <div className="stat-val" style={{ color: s.col }}>{s.val}</div>
            <div className="stat-lbl">{s.lbl}</div>
            <div className="stat-trend muted">VND · kỳ {month}</div>
          </div>
        ))}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
        <div className="card">
          <div className="card-head"><h3>Theo phòng ban</h3></div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Phòng ban</th>
                <th style={{ textAlign: 'right' }}>Thu</th>
                <th style={{ textAlign: 'right' }}>Chi</th>
                <th style={{ textAlign: 'right' }}>Lãi/Lỗ</th>
              </tr></thead>
              <tbody>
                {data.byDepartment.map((d, i) => (
                  <tr key={i}>
                    <td>{d.name}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{hbVND(d.income)}</td>
                    <td className="mono" style={{ textAlign: 'right' }}>{hbVND(d.expense)}</td>
                    <td className="mono" style={{ textAlign: 'right', fontWeight: 700, color: d.net >= 0 ? 'var(--green-600,#16a34a)' : 'var(--red-600)' }}>{hbVND(d.net)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.byDepartment.length === 0 && <EmptyState>Chưa có dữ liệu.</EmptyState>}
        </div>

        <div className="card">
          <div className="card-head"><h3>Số dư quỹ</h3></div>
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                <th>Quỹ</th>
                <th style={{ textAlign: 'right' }}>Số dư</th>
              </tr></thead>
              <tbody>
                {data.funds.map((f) => (
                  <tr key={f.id}>
                    <td>{f.name}</td>
                    <td className="mono" style={{ textAlign: 'right', fontWeight: 700, color: f.balance < 0 ? 'var(--red-600)' : 'var(--ink)' }}>{hbVND(f.balance)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.funds.length === 0 && <EmptyState>Chưa có quỹ.</EmptyState>}
        </div>
      </div>

      <div className="card">
        <div className="card-head"><h3>Cơ cấu theo mục thu/chi</h3></div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Mục</th><th>Loại</th>
              <th style={{ textAlign: 'right' }}>Số tiền</th>
            </tr></thead>
            <tbody>
              {data.byCategory.map((c, i) => (
                <tr key={i}>
                  <td>{c.name}</td>
                  <td><Badge kind={c.type === 'income' ? 'green' : 'red'}>{c.type === 'income' ? 'Thu' : 'Chi'}</Badge></td>
                  <td className="mono" style={{ textAlign: 'right' }}>{hbVND(c.amount)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.byCategory.length === 0 && <EmptyState>Chưa có dữ liệu.</EmptyState>}
      </div>
    </div>
  );
}

const selStyle = {
  padding: '7px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  fontFamily: 'inherit', fontSize: 12.5, color: 'var(--ink)', background: '#fff',
};

/* Ô không cắt chữ (ghi đè max-width:0 mặc định của .tbl td cho cột số/ngày/trạng thái). */
const nowrapCell = { whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' };

/* Nút thao tác icon-only, vuông gọn — không chiếm chiều ngang như nút có chữ. */
function ActBtn({ icon, title, kind = 'ghost', onClick, disabled }) {
  return (
    <button className={`btn btn-${kind} btn-sm`} title={title} aria-label={title}
      onClick={onClick} disabled={disabled}
      style={{ padding: '6px 8px', lineHeight: 0 }}>
      <Icon name={icon} size={15} />
    </button>
  );
}
