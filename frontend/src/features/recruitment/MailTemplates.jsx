/* Tab "Mail mẫu tuyển dụng" — liệt kê mẫu, thêm/sửa, gửi cho ứng viên chọn.
   Owner: Việt. Spec: docs/SPEC_API_RECRUITMENT.md · 3 trạng thái §5b. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fetchMailTemplates, deleteMailTemplate } from '../../api/recruitment';
import MailTemplateForm from './MailTemplateForm';
import SendMailModal from './SendMailModal';

export default function MailTemplates({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null);   // null | 'new' | {id,name,subject}
  const [sending, setSending] = useState(null);   // null | {id,name}
  const [deletingId, setDeletingId] = useState(null);

  const load = () => { setErr(null); setData(null); fetchMailTemplates().then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, []);

  const remove = async (t) => {
    if (!window.confirm(`Xoá mail mẫu "${t.name}"?\nHành động này không hoàn tác được.`)) return;
    setDeletingId(t.id);
    try {
      await deleteMailTemplate(t.id);
      setData((p) => ({ ...p, rows: p.rows.filter((r) => r.id !== t.id) }));
    } catch (e) {
      alert(e.message || 'Không xoá được mẫu.');
    } finally { setDeletingId(null); }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải mail mẫu…" />;

  const { rows, recipients, isRecruiter } = data;
  const filtered = rows.filter((r) => !search
    || (r.name || '').toLowerCase().includes(search.toLowerCase())
    || (r.subject || '').toLowerCase().includes(search.toLowerCase()));

  return (
    <div>
      <div className="filterbar">
        <span className="muted" style={{ fontSize: 13 }}>{rows.length} mẫu · {recipients.length} ứng viên có email</span>
        {isRecruiter && (
          <div style={{ marginLeft: 'auto' }}>
            <button className="btn btn-primary" onClick={() => setEditing('new')}>
              <Icon name="plus" size={16} />Thêm mẫu</button>
          </div>
        )}
      </div>

      <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(320px,1fr))' }}>
        {filtered.map((t) => (
          <div key={t.id} className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ width: 38, height: 38, borderRadius: 10, background: 'var(--red-50)', color: 'var(--red-600)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                <Icon name="mail" size={18} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 700, fontSize: 14 }}>{t.name}</div>
                <div className="muted" style={{ fontSize: 12, marginTop: 3 }}>{t.subject || '(Không có tiêu đề)'}</div>
              </div>
            </div>
            <div className="divider" style={{ margin: '6px 0' }}></div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="btn btn-primary btn-sm" style={{ flex: 1 }} onClick={() => setSending(t)}>
                <Icon name="mail" size={14} />Gửi mail</button>
              {isRecruiter && (
                <button className="btn btn-ghost btn-sm" onClick={() => setEditing(t)}>
                  <Icon name="edit" size={14} />Sửa</button>
              )}
              {isRecruiter && (
                <button className="btn btn-ghost btn-sm" title="Xoá mẫu"
                  style={{ color: 'var(--red-600)' }}
                  disabled={deletingId === t.id} onClick={() => remove(t)}>
                  <Icon name="trash" size={14} />{deletingId === t.id ? '…' : ''}</button>
              )}
            </div>
          </div>
        ))}
        {filtered.length === 0 && <EmptyState>Chưa có mail mẫu nào.</EmptyState>}
      </div>

      {editing && (
        <MailTemplateForm tmpl={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); load(); }} />
      )}
      {sending && (
        <SendMailModal tmpl={sending} recipients={recipients} onClose={() => setSending(null)} />
      )}
    </div>
  );
}
