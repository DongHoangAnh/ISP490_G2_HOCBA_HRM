/* Form Thêm / Sửa vị trí tuyển dụng / JD — Owner: Việt.
   Meta (departments/teachingLevels/statusLabels) truyền từ Jobs. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { createJob, updateJob } from '../../api/recruitment';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, full, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: full ? '1 / -1' : 'auto' }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

function initForm(j) {
  return {
    name: j?.name || '', depId: j?.depId || '', status: j?.status || 'recruiting',
    published: j?.published ?? false, jdLink: j?.jdLink || '', expected: j?.expected ?? '',
    teachingLevel: j?.teachingLevel || 'na', sessionsPerWeek: j?.sessionsPerWeek ?? '',
    description: j?.description || '',
  };
}

export default function JobForm({ job, meta, onClose, onSaved }) {
  const isEdit = !!job;
  const [f, setF] = useState(() => initForm(job));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    if (!f.name.trim()) { setErr('Vui lòng nhập tên vị trí.'); return; }
    setBusy(true); setErr(null);
    try {
      const det = isEdit ? await updateJob(job.id, f) : await createJob(f);
      onSaved(det);
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={isEdit ? 'edit' : 'plus'} size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>
            {isEdit ? 'Chỉnh sửa vị trí' : 'Thêm vị trí tuyển dụng'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? job.name : 'Tạo vị trí và mô tả công việc (JD) mới'}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Tên vị trí *" full>
            <input style={inp} value={f.name} onChange={set('name')} placeholder="VD: Giảng viên Tiếng Trung" /></Field>
          <Field label="Phòng ban">
            <select style={inp} value={f.depId} onChange={set('depId')}>
              <option value="">— Chọn —</option>
              {meta.departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select></Field>
          <Field label="Trạng thái tuyển">
            <select style={inp} value={f.status} onChange={set('status')}>
              {Object.entries(meta.statusLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Số lượng cần tuyển">
            <input type="number" style={inp} value={f.expected} onChange={set('expected')} placeholder="0" /></Field>
          <Field label="Trình độ giảng dạy">
            <select style={inp} value={f.teachingLevel} onChange={set('teachingLevel')}>
              {Object.entries(meta.teachingLevels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Số buổi/tuần tối thiểu">
            <input type="number" style={inp} value={f.sessionsPerWeek} onChange={set('sessionsPerWeek')} placeholder="0" /></Field>
          <Field label="Link JD (Google Docs/Drive)" full>
            <input style={inp} value={f.jdLink} onChange={set('jdLink')} placeholder="https://docs.google.com/..." /></Field>
          <Field label="Mô tả công việc (JD)" full>
            <textarea style={{ ...inp, minHeight: 120, resize: 'vertical' }} value={f.description} onChange={set('description')} placeholder="Mô tả nhiệm vụ, yêu cầu, quyền lợi…" /></Field>
          <label style={{ gridColumn: '1 / -1', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
            <input type="checkbox" checked={f.published} onChange={(e) => setF((p) => ({ ...p, published: e.target.checked }))} />
            Đăng tuyển lên website công khai (/jobs)
          </label>
        </div>

        {err && (
          <div style={{ marginTop: 12, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name={isEdit ? 'checkCircle' : 'plus'} size={16} />
          {busy ? 'Đang lưu…' : (isEdit ? 'Lưu thay đổi' : 'Tạo vị trí')}
        </button>
      </div>
    </Modal>
  );
}
