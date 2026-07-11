/* Gửi mail mẫu cho nhiều ứng viên qua Gmail — Owner: Việt.
   B1 chọn ứng viên → B2 mở Gmail soạn sẵn cho từng người (bấm tay, tránh chặn popup)
   → B3 lưu lịch sử cho những người đã mở. Nội dung render từ mail mẫu của app. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { EmptyState } from '../../components/states';
import { renderForGmail, gmailComposeUrl, logSentMail } from './mailSend';

export default function SendMailModal({ tmpl, recipients, onClose }) {
  const [phase, setPhase] = useState('pick');   // 'pick' | 'links' | 'done'
  const [q, setQ] = useState('');
  const [picked, setPicked] = useState(() => new Set());
  const [prepared, setPrepared] = useState([]);  // [{id,name,email,subject,url}]
  const [opened, setOpened] = useState(() => new Set());
  const [busy, setBusy] = useState(false);
  const [sentCount, setSentCount] = useState(0);
  const [err, setErr] = useState(null);

  const withEmail = recipients.filter((r) => r.email);
  const filtered = withEmail.filter((r) => {
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

  // Render nội dung từng người được chọn rồi sang bước "mở Gmail".
  const prepare = async () => {
    setBusy(true); setErr(null);
    try {
      const targets = withEmail.filter((r) => picked.has(r.id));
      const rows = [];
      for (const r of targets) {
        const { subject, bodyText } = await renderForGmail(tmpl.id, r.id);
        rows.push({ id: r.id, name: r.name, email: r.email, subject, url: gmailComposeUrl(r.email, subject, bodyText) });
      }
      setPrepared(rows); setPhase('links');
    } catch (e) { setErr(e.message || 'Không chuẩn bị được nội dung.'); } finally { setBusy(false); }
  };

  const markOpened = (id) => setOpened((p) => new Set(p).add(id));

  // Lưu lịch sử cho những người đã mở Gmail (coi như đã gửi).
  const saveHistory = async () => {
    const logs = prepared.filter((r) => opened.has(r.id)).map((r) => ({ applicantId: r.id, subject: r.subject }));
    if (logs.length === 0) { setErr('Chưa mở Gmail cho ứng viên nào.'); return; }
    setBusy(true); setErr(null);
    try {
      await logSentMail(logs);
      setSentCount(logs.length); setPhase('done');
    } catch (e) { setErr(e.message || 'Không lưu được lịch sử.'); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="mail" size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 19, fontWeight: 800 }}>Gửi mail: {tmpl.name}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {phase === 'pick' ? 'Chọn ứng viên nhận email (đã có địa chỉ email)' : 'Mở Gmail gửi cho từng ứng viên rồi lưu lịch sử'}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      {phase === 'done' ? (
        <div style={{ padding: '28px 24px', textAlign: 'center' }}>
          <div style={{ fontSize: 16, fontWeight: 800, marginBottom: 8 }}>Đã ghi nhận đã gửi</div>
          <p className="muted" style={{ margin: 0 }}>
            Đã lưu lịch sử gửi cho <b>{sentCount}</b> ứng viên. Xem ở tab "Lịch sử gửi mail".
          </p>
          <button className="btn btn-primary" style={{ marginTop: 18 }} onClick={onClose}>Đóng</button>
        </div>
      ) : phase === 'links' ? (
        <>
          <div style={{ padding: '12px 24px 4px' }} className="muted">
            <span style={{ fontSize: 12.5 }}>Bấm "Mở Gmail" ở từng dòng → bấm Gửi trong Gmail. Xong tất cả thì "Lưu lịch sử".</span>
          </div>
          <div style={{ padding: '8px 12px', maxHeight: '52vh', overflowY: 'auto' }}>
            {prepared.map((r) => (
              <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '9px 8px', borderBottom: '1px solid var(--border)' }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: 13.5 }}>{r.name}</div>
                  <div className="muted" style={{ fontSize: 12 }}>{r.email}</div>
                </div>
                {opened.has(r.id) && <span className="badge badge-gray"><Icon name="check" size={12} /> đã mở</span>}
                <a className="btn btn-soft btn-sm" href={r.url} target="_blank" rel="noreferrer" onClick={() => markOpened(r.id)}>
                  <Icon name="mail" size={14} />Mở Gmail</a>
              </div>
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
            <span className="muted" style={{ fontSize: 13 }}>Đã mở <b>{opened.size}</b>/{prepared.length}{err && <span style={{ color: 'var(--red-600)', marginLeft: 10 }}>{err}</span>}</span>
            <div style={{ display: 'flex', gap: 10 }}>
              <button className="btn btn-ghost" onClick={() => setPhase('pick')} disabled={busy}>Quay lại</button>
              <button className="btn btn-primary" onClick={saveHistory} disabled={busy || opened.size === 0}>
                <Icon name="check" size={16} />{busy ? 'Đang lưu…' : `Lưu lịch sử (${opened.size})`}</button>
            </div>
          </div>
        </>
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
              <button className="btn btn-primary" onClick={prepare} disabled={busy || picked.size === 0}>
                <Icon name="mail" size={16} />{busy ? 'Đang chuẩn bị…' : `Tiếp tục (${picked.size})`}
              </button>
            </div>
          </div>
        </>
      )}
    </Modal>
  );
}
