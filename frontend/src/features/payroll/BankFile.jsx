/* Quản lý file chuyển khoản — Owner: Hùng. */
import { useState, useEffect } from 'react';
import { fetchBankFiles, fetchBatches, fetchBankFormats, generateBankFile, markBankFileUploaded, markBankFileConfirmed } from '../../api/payroll';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import BankFileForm from './BankFileForm';

const FILE_STATE = {
  draft: ['Đã tạo', 'gray'],
  uploaded: ['Đã tải lên', 'blue'],
  confirmed: ['Đã xác nhận', 'green'],
};
const fileState = (k) => FILE_STATE[k] || ['?', 'gray'];

export default function BankFile() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [batchId, setBatchId] = useState('');
  const [batches, setBatches] = useState([]);
  const [creating, setCreating] = useState(false);
  const [busy, setBusy] = useState(null);

  useEffect(() => { fetchBatches().then(setBatches).catch(() => {}); }, []);

  const load = () => {
    setErr(null); setData(null);
    const params = {};
    if (batchId) params.batch_id = batchId;
    fetchBankFiles(params).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [batchId]);

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
  if (!data) return <LoadingState label="Đang tải danh sách file..." />;

  return (
    <>
      <div className="filterbar" style={{ marginBottom: 14 }}>
        <select className="sel" value={batchId} onChange={(e) => setBatchId(e.target.value)}>
          <option value="">Tất cả đợt lương</option>
          {batches.map((b) => <option key={b.id} value={b.id}>{b.name}</option>)}
        </select>
        <div style={{ flex: 1 }} />
        <button className="btn btn-primary" onClick={() => setCreating(true)}>
          <Icon name="plus" size={16} />Tạo file CK
        </button>
      </div>

      <div className="card">
        {data.length === 0 ? (
          <div style={{ padding: 36, textAlign: 'center' }}>
            <EmptyState>Chưa có file chuyển khoản.</EmptyState>
          </div>
        ) : (
          <div className="tbl-wrap">
            <table className="tbl">
              <thead>
                <tr>
                  <th>Đợt lương</th>
                  <th>Ngân hàng</th>
                  <th>Ngày tạo</th>
                  <th>Trạng thái</th>
                  <th style={{ width: 160 }}>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                {data.map((f) => {
                  const [sl, sk] = fileState(f.state);
                  return (
                    <tr key={f.id}>
                      <td style={{ fontWeight: 600 }}>{f.batch_name || `Batch #${f.batch_id}`}</td>
                      <td>{f.format_name || '—'}</td>
                      <td>{fmtDate(f.generated_at?.split(' ')[0])}</td>
                      <td><Badge kind={sk}>{sl}</Badge></td>
                      <td>
                        {f.state === 'draft' && (
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => doAction(f.id, markBankFileUploaded, 'Đánh dấu tải lên')}
                            disabled={busy === f.id}>
                            <Icon name="upload" size={14} />Tải lên
                          </button>
                        )}
                        {f.state === 'uploaded' && (
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => doAction(f.id, markBankFileConfirmed, 'Xác nhận')}
                            disabled={busy === f.id}>
                            <Icon name="check" size={14} />Xác nhận
                          </button>
                        )}
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
        <BankFileForm
          batches={batches}
          onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }}
        />
      )}
    </>
  );
}
