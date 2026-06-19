/* Quản lý báo cáo thuế TNCN (eTax) — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchEtaxReports, fetchBatches, createEtaxReport, computeEtax, submitEtax } from '../../api/payroll';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';
import { monthOptions, yearOptions, currentMonth, currentYear } from './util';
import EtaxDrawer from './EtaxDrawer';

const RPT_STATE = {
  draft: ['Nháp', 'gray'],
  computed: ['Đã tính', 'blue'],
  submitted: ['Đã nộp', 'green'],
};
const rptState = (k) => RPT_STATE[k] || ['?', 'gray'];

export default function EtaxReport() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(null);
  const [sel, setSel] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchEtaxReports().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const doAction = async (id, fn, label) => {
    setBusy(id);
    try {
      await fn(id);
      load();
    } catch (e) {
      alert(`${label} thất bại: ${e.message}`);
    } finally {
      setBusy(null);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải báo cáo eTax..." />;

  return (
    <>
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <div style={{ flex: 1 }} />
        <button className="btn btn-primary" onClick={() => setCreating(true)}>
          <Icon name="plus" size={16} />Tạo báo cáo
        </button>
      </div>

      <div className="card">
        {data.length === 0 ? (
          <div style={{ padding: 36, textAlign: 'center' }}>
            <EmptyState>Chưa có báo cáo thuế TNCN.</EmptyState>
          </div>
        ) : (
          <div className="tbl-wrap">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Kỳ báo cáo</th>
                  <th style={{ textAlign: 'right' }}>Số NV</th>
                  <th style={{ textAlign: 'right' }}>Tổng Gross</th>
                  <th style={{ textAlign: 'right' }}>Tổng thuế TNCN</th>
                  <th>Trạng thái</th>
                  <th style={{ width: 180 }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {data.map((r) => {
                  const [sl, sk] = rptState(r.state);
                  return (
                    <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => setSel(r)}>
                      <td style={{ fontWeight: 600, color: 'var(--red-600)' }}>{r.name}</td>
                      <td style={{ textAlign: 'right' }}>{r.employee_count}</td>
                      <td style={{ textAlign: 'right' }}>{hbVND(r.total_gross)}</td>
                      <td style={{ textAlign: 'right', color: 'var(--red-600)' }}>{hbVND(r.total_pit)}</td>
                      <td><Badge kind={sk}>{sl}</Badge></td>
                      <td>
                        <div style={{ display: 'flex', gap: 6 }} onClick={(e) => e.stopPropagation()}>
                          {r.state === 'draft' && (
                            <button className="btn btn-ghost btn-sm"
                              onClick={() => doAction(r.id, computeEtax, 'Tính thuế')}
                              disabled={busy === r.id}>
                              <Icon name="calculator" size={14} />Tính
                            </button>
                          )}
                          {r.state === 'computed' && (
                            <button className="btn btn-ghost btn-sm"
                              onClick={() => doAction(r.id, submitEtax, 'Nộp thuế')}
                              disabled={busy === r.id}>
                              <Icon name="send" size={14} />Nộp
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {creating && (
        <EtaxForm
          onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }}
        />
      )}
      {sel && (
        <EtaxDrawer
          reportId={sel.id}
          onClose={() => setSel(null)}
        />
      )}
    </>
  );
}

/* ── Inline form — tạo báo cáo eTax ── */
function EtaxForm({ onClose, onSaved }) {
  const [batches, setBatches] = useState([]);
  const [form, setForm] = useState({
    period_month: currentMonth(),
    period_year: currentYear(),
    batch_id: '',
  });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchBatches().then(setBatches).catch(() => {}); }, []);

  const set = (k, v) => setForm((f) => ({ ...f, [k]: v }));

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true); setErr(null);
    try {
      await createEtaxReport({
        period_month: form.period_month,
        period_year: form.period_year,
        batch_id: Number(form.batch_id),
      });
      onSaved();
    } catch (ex) {
      setErr(ex.message || 'Tạo báo cáo thất bại.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Tạo báo cáo thuế TNCN</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Tạo báo cáo eTax 05/KK hàng tháng</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <form onSubmit={submit} style={{ padding: '22px 24px' }}>
        {err && <div style={{ color: 'var(--red-600)', marginBottom: 14, fontSize: 13.5 }}>{err}</div>}

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 14, marginBottom: 16 }}>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Tháng</label>
            <select className="sel" style={{ width: '100%' }} value={form.period_month} onChange={(e) => set('period_month', e.target.value)}>
              {monthOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
          <div>
            <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Năm</label>
            <select className="sel" style={{ width: '100%' }} value={form.period_year} onChange={(e) => set('period_year', e.target.value)}>
              {yearOptions().map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
            </select>
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <label style={{ fontWeight: 600, fontSize: 13.5, marginBottom: 5, display: 'block' }}>Đợt lương (Batch)</label>
          <select className="sel" style={{ width: '100%' }} value={form.batch_id} onChange={(e) => set('batch_id', e.target.value)} required>
            <option value="">Chọn đợt lương</option>
            {batches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 8 }}>
          <button type="button" className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
          <button type="submit" className="btn btn-primary" disabled={busy}>
            {busy ? 'Đang tạo...' : 'Tạo báo cáo'}
          </button>
        </div>
      </form>
    </Modal>
  );
}
