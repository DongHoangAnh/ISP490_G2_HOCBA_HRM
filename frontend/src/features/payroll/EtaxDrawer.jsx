/* Chi tiết báo cáo thuế TNCN — danh sách NV: Gross → trừ BH → trừ thuế → Net. Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchEtaxReport } from '../../api/payroll';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';

const RPT_STATE = { draft: ['Nháp', 'gray'], computed: ['Đã tính', 'blue'], submitted: ['Đã nộp', 'green'] };
const rptState = (k) => RPT_STATE[k] || ['?', 'gray'];

export default function EtaxDrawer({ reportId, onClose }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchEtaxReport(reportId).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [reportId]);

  if (err) return <Modal lg onClose={onClose}><ErrorState message={err} onRetry={load} /></Modal>;
  if (!data) return <Modal lg onClose={onClose}><LoadingState label="Đang tải chi tiết eTax..." /></Modal>;

  const [sl, sk] = rptState(data.state);
  const lines = data.lines || [];

  return (
    <Modal lg onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>{data.name}</h2>
            <Badge kind={sk}>{sl}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {data.employee_count} nhân viên &middot; Tổng thuế: {hbVND(data.total_pit)}
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      {/* Summary */}
      <div style={{ padding: '14px 24px', background: 'var(--gray-50)', display: 'flex', gap: 24, fontSize: 13.5 }}>
        <div><span className="muted">Tổng Gross:</span> <strong>{hbVND(data.total_gross)}</strong></div>
        <div><span className="muted">Tổng thuế TNCN:</span> <strong style={{ color: 'var(--red-600)' }}>{hbVND(data.total_pit)}</strong></div>
      </div>

      {/* Employee lines */}
      <div style={{ padding: '16px 24px', maxHeight: '55vh', overflowY: 'auto' }}>
        {lines.length === 0 ? (
          <EmptyState>Chưa có dữ liệu. Hãy bấm "Tính" ở danh sách báo cáo.</EmptyState>
        ) : (
          <div className="tbl-wrap">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Mã NV</th>
                  <th>Nhân viên</th>
                  <th style={{ textAlign: 'right' }}>Gross</th>
                  <th style={{ textAlign: 'right' }}>Trừ BH</th>
                  <th style={{ textAlign: 'right' }}>GT bản thân</th>
                  <th style={{ textAlign: 'right' }}>NPT</th>
                  <th style={{ textAlign: 'right' }}>GT NPT</th>
                  <th style={{ textAlign: 'right' }}>TN chịu thuế</th>
                  <th style={{ textAlign: 'right', color: 'var(--red-600)' }}>Thuế TNCN</th>
                  <th style={{ textAlign: 'right' }}>Net</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((l) => (
                  <tr key={l.id}>
                    <td><code style={{ fontSize: 12.5 }}>{l.employee_code || '—'}</code></td>
                    <td style={{ fontWeight: 600 }}>{l.employee_name}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.gross_income)}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.insurance_deduction)}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.personal_deduction)}</td>
                    <td style={{ textAlign: 'right' }}>{l.dependent_count}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.dependent_deduction)}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.taxable_income)}</td>
                    <td style={{ textAlign: 'right', color: 'var(--red-600)', fontWeight: 600 }}>{hbVND(l.pit_amount)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700, color: 'var(--green-700)' }}>{hbVND(l.net_income)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Modal>
  );
}
