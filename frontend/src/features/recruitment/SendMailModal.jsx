/* Gửi mail mẫu cho ứng viên được chọn — Owner: Việt.
   Chọn nhiều ứng viên (có email) rồi gửi template đã render cho từng người. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { sendMailTemplate } from '../../api/recruitment';

export default function SendMailModal({ tmpl, recipients, onClose }) {
  const [q, setQ] = useState('');
  const [picked, setPicked] = useState(() => new Set());
  const [busy, setBusy] = useState(false);
  const [result, setResult] = useState(null);
  const [err, setErr] = useState(null);

  const filtered = recipients.filter((r) => {
    if (!q) return true;
    const s = q.toLowerCase();
    return (r.name || '').toLowerCase().includes(s) || (r.email || '').toLowerCase().includes(s) || (r.jobName || '').toLowerCase().includes(s);
  });

  const toggle = (id) => setPicked((p) => { const n = new Set(p); n.has(id) ? n.delete(id) : n.add(id); return n; });
  const allShown = filtered.length > 0 && filtered.every((r) => picked.has(r.id));
  const toggleAll = () => setPicked((p) => {
    const n = new Set(p);
    if (allShown) filtered.forEach((r) => n.delete(r.id));
    else filtered.forEach((r) => n.add(r.id));
    return n;
  });

  const send = async () => {
    setBusy(true); setErr(null);
    try {
      const res = await sendMailTemplate(tmpl.id, [...picked]);
      setResult(res);
    } catch (e) { setErr(e.message || 'Gửi thất bại.'); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="mail" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Gửi mail: {tmpl.name}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>Chọn ứng viên nhận email (đã có địa chỉ email)</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      {result ? (
        <div style={{ padding: '28px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 8 }}>Đã đưa vào hàng đợi gửi</div>
          <p className="muted" style={{ margin: 0 }}>
            Đã tạo <b>{result.sent}</b> email{result.skipped ? `, bỏ qua ${result.skipped} (thiếu email)` : ''}.
            <br />Email sẽ được gửi qua máy chủ thư của hệ thống.
          </p>
          <button className="btn btn-primary" style={{ marginTop: 18 }} onClick={onClose}>Đóng</button>
        </div>
      ) : (
        <>
          <div style={{ padding: '12px 24px', borderBottom: '1px solid var(--border)', display: 'flex', gap: 10, alignItems: 'center' }}>
            <label className="search" style={{ flex: 1 }}>
              <Icon name="search" size={16} />
              <input placeholder="Tìm ứng viên / email / vị trí…" value={q} onChange={(e) => setQ(e.target.value)} />
            </label>
            <button className="btn btn-ghost btn-sm" onClick={toggleAll}>{allShown ? 'Bỏ chọn' : 'Chọn tất cả'}</button>
          </div>

          <div style={{ padding: '8px 12px', maxHeight: '46vh', overflowY: 'auto' }}>
            {filtered.length === 0 && <EmptyState>Không có ứng viên phù hợp.</EmptyState>}
            {filtered.map((r) => (
              <label key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '9px 8px', borderBottom: '1px solid var(--border)', cursor: 'pointer' }}>
                <input type="checkbox" checked={picked.has(r.id)} onChange={() => toggle(r.id)} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 13.5 }}>{r.name}</div>
                  <div className="muted" style={{ fontSize: 12 }}>{r.email}{r.jobName ? ' · ' + r.jobName : ''}</div>
                </div>
                {r.stage && <span className="badge badge-gray">{r.stage}</span>}
              </label>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
            <span className="muted" style={{ fontSize: 13 }}>Đã chọn <b>{picked.size}</b> ứng viên{err && <span style={{ color: 'var(--red-600)', marginLeft: 10 }}>{err}</span>}</span>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
              <button className="btn btn-primary" onClick={send} disabled={busy || picked.size === 0}>
                <Icon name="mail" size={16} />{busy ? 'Đang gửi…' : `Gửi (${picked.size})`}
              </button>
            </div>
          </div>
        </>
      )}
    </Modal>
  );
}
