/* Form Thêm / Sửa CV ứng viên — ngay trong SPA. Dùng chung tạo mới (app=null)
   và chỉnh sửa. Owner: Việt. Meta (jobs/stages/labels) truyền từ CvList. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { createCv, updateApplicant, uploadCvFile } from '../../api/recruitment';

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

function Section({ title, children }) {
  return (
    <div style={{ marginBottom: 20 }}>
      <div style={{ fontSize: 12.5, fontWeight: 800, marginBottom: 12, paddingBottom: 7, borderBottom: '1px solid var(--border)', color: 'var(--red-700)' }}>{title}</div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>{children}</div>
    </div>
  );
}

function initForm(a) {
  return {
    name: a?.name || '', phone: a?.phone || '', email: a?.email || '',
    jobId: a?.jobId || '', dateReceived: a?.dateReceived || '', ctv: a?.ctv || '',
    cvLink: a?.cvLink || '', cvResult: a?.cvResult || '', cvNote: a?.cvNote || '',
    callStatus: a?.callStatus || '', stageId: a?.stageId || '',
    interviewDate: a?.interviewDate || '', interviewTime: a?.interviewTime || '',
    interviewer: a?.interviewer || '',
    attendanceStatus: a?.attendanceStatus || '', interviewResult: a?.interviewResult || '',
    offerContent: a?.offerContent || '', startDate: a?.startDate || '',
    offerNote: a?.offerNote || '', candidateConfirmed: a?.candidateConfirmed || '',
  };
}

export default function ApplicantForm({ app, meta, onClose, onSaved }) {
  const isEdit = !!app;
  const [f, setF] = useState(() => initForm(app));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const [cvFile, setCvFile] = useState(null);   // file PDF mới chọn (chưa upload)
  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    if (!f.name.trim()) { setErr('Vui lòng nhập họ tên ứng viên.'); return; }
    setBusy(true); setErr(null);
    try {
      let det = isEdit ? await updateApplicant(app.id, f) : await createCv(f);
      // Có chọn file CV → upload sau khi đã có id ứng viên.
      if (cvFile) det = await uploadCvFile(det.id, cvFile);
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
            {isEdit ? 'Chỉnh sửa CV' : 'Thêm CV ứng viên'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? app.name : 'Nhập hồ sơ ứng viên mới vào pipeline tuyển dụng'}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto' }}>
        <Section title="Thông tin ứng viên">
          <Field label="Họ và tên *" full>
            <input style={inp} value={f.name} onChange={set('name')} placeholder="Nguyễn Văn A" /></Field>
          <Field label="Số điện thoại">
            <input style={inp} value={f.phone} onChange={set('phone')} placeholder="09xxxxxxxx" /></Field>
          <Field label="Email">
            <input style={inp} value={f.email} onChange={set('email')} placeholder="a@example.com" /></Field>
          <Field label="Vị trí ứng tuyển">
            <select style={inp} value={f.jobId} onChange={set('jobId')}>
              <option value="">— Chọn —</option>
              {meta.jobs.map((j) => <option key={j.id} value={j.id}>{j.name}</option>)}
            </select></Field>
          <Field label="Bước (stage)">
            <select style={inp} value={f.stageId} onChange={set('stageId')}>
              <option value="">— Chọn —</option>
              {meta.stages.map((s) => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select></Field>
          <Field label="Ngày nhận CV">
            <input type="date" style={inp} value={f.dateReceived || ''} onChange={set('dateReceived')} /></Field>
          <Field label="CTV tuyển dụng">
            <input style={inp} value={f.ctv} onChange={set('ctv')} placeholder="Tên CTV" /></Field>
          <Field label="Link CV / Tên file" full>
            <input style={inp} value={f.cvLink} onChange={set('cvLink')} placeholder="Link Google Drive…" /></Field>
          <Field label="File CV (PDF)" full>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
              <input id="cv-pdf-upload" type="file" accept=".pdf,application/pdf" style={{ display: 'none' }}
                onChange={(e) => setCvFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)} />
              <label htmlFor="cv-pdf-upload" className="btn btn-ghost btn-sm" style={{ cursor: 'pointer' }}>
                <Icon name="plus" size={14} />Chọn file PDF</label>
              {cvFile
                ? <span style={{ fontSize: 12.5, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                    <Icon name="file" size={14} className="faint" />{cvFile.name}</span>
                : app?.cvFileUrl
                  ? <a href={app.cvFileUrl} target="_blank" rel="noreferrer" style={{ color: 'var(--red-700)', fontSize: 12.5, display: 'inline-flex', alignItems: 'center', gap: 6 }}>
                      <Icon name="file" size={14} />Xem file hiện tại ({app.cvFileName || 'PDF'})</a>
                  : <span className="muted" style={{ fontSize: 12.5 }}>Chưa có file</span>}
            </div>
          </Field>
        </Section>

        <Section title="Lọc CV & Gọi điện">
          <Field label="Kết quả lọc CV">
            <select style={inp} value={f.cvResult} onChange={set('cvResult')}>
              <option value="">— Chưa lọc —</option>
              {Object.entries(meta.cvResultLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Trạng thái gọi điện">
            <select style={inp} value={f.callStatus} onChange={set('callStatus')}>
              <option value="">— Chưa gọi —</option>
              {Object.entries(meta.callStatusLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Ghi chú CV" full>
            <textarea style={{ ...inp, minHeight: 64, resize: 'vertical' }} value={f.cvNote} onChange={set('cvNote')} /></Field>
        </Section>

        <Section title="Lịch phỏng vấn">
          <Field label="Ngày hẹn PV">
            <input type="date" style={inp} value={f.interviewDate || ''} onChange={set('interviewDate')} /></Field>
          <Field label="Giờ hẹn PV">
            <input style={inp} value={f.interviewTime} onChange={set('interviewTime')} placeholder="VD: 10h30" /></Field>
          <Field label="Người PV">
            <input style={inp} value={f.interviewer} onChange={set('interviewer')} placeholder="VD: Dunglt" /></Field>
          <Field label="Tham gia PV">
            <select style={inp} value={f.attendanceStatus} onChange={set('attendanceStatus')}>
              <option value="">— Chưa ghi nhận —</option>
              {Object.entries(meta.attendanceLabels || {}).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Kết quả PV">
            <select style={inp} value={f.interviewResult} onChange={set('interviewResult')}>
              <option value="">— Chưa có —</option>
              {Object.entries(meta.interviewResultLabels || {}).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
        </Section>

        <Section title="Offer & Nhận việc">
          <Field label="Ngày nhận việc">
            <input type="date" style={inp} value={f.startDate || ''} onChange={set('startDate')} /></Field>
          <Field label="UV xác nhận mail">
            <input style={inp} value={f.candidateConfirmed} onChange={set('candidateConfirmed')} placeholder="VD: Đã xác nhận" /></Field>
          <Field label="Nội dung Offer" full>
            <textarea style={{ ...inp, minHeight: 60, resize: 'vertical' }} value={f.offerContent} onChange={set('offerContent')} placeholder="VD: Lương cứng 8tr, thử việc 85%..." /></Field>
          <Field label="Ghi chú Offer" full>
            <textarea style={{ ...inp, minHeight: 48, resize: 'vertical' }} value={f.offerNote} onChange={set('offerNote')} /></Field>
        </Section>

        {err && (
          <div style={{ marginTop: 4, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name={isEdit ? 'checkCircle' : 'plus'} size={16} />
          {busy ? 'Đang lưu…' : (isEdit ? 'Lưu thay đổi' : 'Tạo CV')}
        </button>
      </div>
    </Modal>
  );
}
