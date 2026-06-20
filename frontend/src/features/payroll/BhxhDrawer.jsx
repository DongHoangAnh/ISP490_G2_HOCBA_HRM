/* Chi tiết báo cáo BHXH — danh sách NV + số tiền. Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchBhxhReport } from '../../api/payroll';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { hbVND } from '../../utils/format';

const RPT_STATE = { draft: ['Nháp', 'gray'], computed: ['Đã tính', 'blue'], submitted: ['Đã nộp', 'green'] };
const rptState = (k) => RPT_STATE[k] || ['?', 'gray'];

export default function BhxhDrawer({ reportId, onClose }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchBhxhReport(reportId).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [reportId]);

  if (err) return <Modal lg onClose={onClose}><ErrorState message={err} onRetry={load} /></Modal>;
  if (!data) return <Modal lg onClose={onClose}><LoadingState label="Đang tải chi tiết BHXH..." /></Modal>;

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
            {data.employee_count} nhân viên
          </div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      {/* Summary */}
      <div style={{ padding: '14px 24px', background: 'var(--gray-50)', display: 'flex', gap: 20, flexWrap: 'wrap', fontSize: 13.5 }}>
        <div><span className="muted">BHXH (NV):</span> <strong>{hbVND(data.total_bhxh_ee)}</strong></div>
        <div><span className="muted">BHYT (NV):</span> <strong>{hbVND(data.total_bhyt_ee)}</strong></div>
        <div><span className="muted">BHTN (NV):</span> <strong>{hbVND(data.total_bhtn_ee)}</strong></div>
        <div><span className="muted">BHXH (DN):</span> <strong>{hbVND(data.total_bhxh_er)}</strong></div>
        <div><span className="muted">BHYT (DN):</span> <strong>{hbVND(data.total_bhyt_er)}</strong></div>
        <div><span className="muted">BHTN (DN):</span> <strong>{hbVND(data.total_bhtn_er)}</strong></div>
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
                  <th style={{ textAlign: 'right' }}>Mức đóng</th>
                  <th style={{ textAlign: 'right' }}>BHXH</th>
                  <th style={{ textAlign: 'right' }}>BHYT</th>
                  <th style={{ textAlign: 'right' }}>BHTN</th>
                  <th style={{ textAlign: 'right' }}>Tổng NV</th>
                  <th style={{ textAlign: 'right' }}>Tổng DN</th>
                </tr>
              </thead>
              <tbody>
                {lines.map((l) => (
                  <tr key={l.id}>
                    <td><code style={{ fontSize: 12.5 }}>{l.employee_code || '—'}</code></td>
                    <td style={{ fontWeight: 600 }}>{l.employee_name}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.insurance_base)}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.bhxh_ee)}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.bhyt_ee)}</td>
                    <td style={{ textAlign: 'right' }}>{hbVND(l.bhtn_ee)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600, color: 'var(--red-600)' }}>{hbVND(l.total_ee)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>{hbVND(l.total_er)}</td>
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
