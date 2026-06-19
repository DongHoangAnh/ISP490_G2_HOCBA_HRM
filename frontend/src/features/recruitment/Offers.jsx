/* Tab "Offer & Nhận việc" — danh sách ứng viên ở bước Gửi Offer / Onboarding.
   Hiển thị: họ tên, ngày ứng tuyển, vị trí, nội dung offer, ngày nhận việc + gửi mail.
   Gửi mail: chọn mẫu từ tab Mail mẫu; server tự điền thông tin ứng viên khi render. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchCvList, fetchMailTemplates, updateApplicant } from '../../api/recruitment';
import MailSendModal from './MailSendModal';

const OFFER_STAGES = ['Gửi Offer', 'Onboarding'];

export default function Offers({ search }) {
  const [cv, setCv] = useState(null);
  const [tmpls, setTmpls] = useState(null);
  const [err, setErr] = useState(null);
  const [mailFor, setMailFor] = useState(null); // ứng viên đang gửi mail

  const [savingId, setSavingId] = useState(null);

  const load = () => { setErr(null); setCv(null); fetchCvList().then(setCv).catch((e) => setErr(e.message)); };
  useEffect(load, []);
  useEffect(() => { fetchMailTemplates().then(setTmpls).catch(() => setTmpls({ rows: [] })); }, []);

  // Lưu 1 trường (offer / ngày nhận việc) rồi cập nhật dòng vào state — chỉ recruiter.
  const saveField = async (id, patch) => {
    setSavingId(id);
    try {
      const det = await updateApplicant(id, patch);
      setCv((p) => ({ ...p, rows: p.rows.map((r) => (r.id === id ? det : r)) }));
    } catch (e) {
      alert(e.message || 'Không lưu được thay đổi.');
    } finally { setSavingId(null); }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!cv) return <LoadingState label="Đang tải danh sách offer…" />;

  const isRecruiter = cv.isRecruiter;

  const rows = cv.rows
    .filter((r) => OFFER_STAGES.includes(r.stage))
    .filter((r) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return [r.name, r.phone, r.email, r.jobName].some((v) => (v || '').toLowerCase().includes(q));
    })
    .sort((a, b) => (b.startDate || '').localeCompare(a.startDate || ''));

  return (
    <div>
      <div className="filterbar">
        <span className="muted" style={{ fontSize: 13 }}>{rows.length} ứng viên ở bước Offer &amp; Nhận việc</span>
      </div>

      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Họ tên ứng viên</th><th>Ngày ứng tuyển</th><th>Vị trí ứng tuyển</th>
              <th>Offer</th><th>Ngày nhận việc</th><th></th>
            </tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="nm">{r.name || '—'}</div>
                    <div className="id">{[r.phone, r.email].filter(Boolean).join(' · ') || '—'}</div>
                  </td>
                  <td className="muted mono">{fmtDate(r.dateReceived)}</td>
                  <td>{r.jobName || '—'}</td>
                  <td style={{ maxWidth: 300 }}>
                    {isRecruiter ? (
                      <textarea
                        defaultValue={r.offerContent || ''}
                        placeholder="VD: Lương cứng 8tr, thử việc 85%…"
                        disabled={savingId === r.id}
                        onBlur={(e) => { if ((e.target.value || '') !== (r.offerContent || '')) saveField(r.id, { offerContent: e.target.value }); }}
                        style={{
                          width: 280, minHeight: 38, resize: 'vertical', padding: '6px 9px',
                          borderRadius: 8, border: '1px solid var(--border-strong)', background: '#fff',
                          fontSize: 12.5, lineHeight: 1.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
                          opacity: savingId === r.id ? 0.6 : 1,
                        }} />
                    ) : (r.offerContent
                      ? <span style={{ fontSize: 12.5, lineHeight: 1.5 }}>{r.offerContent}</span>
                      : <span className="muted">—</span>)}
                  </td>
                  <td>
                    {isRecruiter ? (
                      <input type="date"
                        value={r.startDate ? r.startDate.slice(0, 10) : ''}
                        disabled={savingId === r.id}
                        onChange={(e) => saveField(r.id, { startDate: e.target.value || '' })}
                        style={{
                          width: 150, padding: '6px 9px', borderRadius: 8,
                          border: '1px solid var(--border-strong)', background: '#fff',
                          fontSize: 12.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
                          opacity: savingId === r.id ? 0.6 : 1,
                        }} />
                    ) : (
                      <span className="muted mono">{r.startDate ? fmtDate(r.startDate) : '—'}</span>
                    )}
                  </td>
                  <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <button className="btn btn-primary btn-sm" onClick={() => setMailFor(r)}>
                      <Icon name="mail" size={14} />Gửi mail</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có ứng viên nào ở bước Offer &amp; Nhận việc.</EmptyState>}
      </div>

      {mailFor && (
        <MailSendModal applicant={mailFor} templates={(tmpls && tmpls.rows) || []}
          onClose={() => setMailFor(null)} />
      )}
    </div>
  );
}

