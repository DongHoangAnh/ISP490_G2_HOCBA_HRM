/* Form Thêm / Sửa phiếu yêu cầu tuyển dụng — Owner: Việt.
   Meta (departments/jobs/labels) truyền từ Requests. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { createRequest, updateRequest } from '../../api/recruitment';

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

function initForm(r) {
  return {
    depId: r?.depId || '', jobId: r?.jobId || '', jobTitle: r?.jobTitle || '',
    jdLink: r?.jdLink || '', qty: r?.qty ?? 1, reason: r?.reason || 'new', level: r?.level || '',
    dateRequest: r?.dateRequest || '', expectedStartDate: r?.expectedStartDate || '',
    education: r?.education || 'none', experienceYears: r?.experienceYears ?? '',
    skillDescription: r?.skillDescription || '', languageRequirement: r?.languageRequirement || '',
    salaryRange: r?.salaryRange || '', workType: r?.workType || 'onsite',
  };
}

export default function RequestForm({ req, meta, onClose, onSaved }) {
  const isEdit = !!req;
  const [f, setF] = useState(() => initForm(req));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  /* Chọn JD từ kho → điền luôn tên vị trí + link JD. Ghi đè chứ không "chỉ điền
     khi trống": người dùng vừa chủ động chọn JD, giá trị cũ là của JD trước đó
     nên giữ lại chỉ gây sai lệch. Vẫn sửa tay được sau khi điền. */
  const onJob = (e) => {
    const jobId = e.target.value;
    const job = meta.jobs.find((j) => String(j.id) === String(jobId));
    setF((p) => (job
      ? { ...p, jobId, jobTitle: job.name || p.jobTitle, jdLink: job.jdLink || p.jdLink }
      : { ...p, jobId: '' }));
  };

  /* Đổi phòng ban → bỏ JD đã chọn (JD thuộc phòng khác). Giữ nguyên tên vị trí
     và link đã điền: người dùng có thể đã sửa tay, xoá là mất công gõ lại. */
  const onDep = (e) => setF((p) => ({ ...p, depId: e.target.value, jobId: '' }));

  // Kho JD lọc theo phòng ban đang chọn (meta.jobs đã bị BE cắt theo phạm vi).
  const jobs = meta.jobs.filter((j) => !f.depId || j.dep === Number(f.depId));

  const submit = async () => {
    if (!f.depId) { setErr('Vui lòng chọn phòng ban.'); return; }
    if (!f.jobTitle.trim()) { setErr('Vui lòng nhập tên vị trí.'); return; }
    setBusy(true); setErr(null);
    try {
      const det = isEdit ? await updateRequest(req.id, f) : await createRequest(f);
      onSaved(det);
    } catch (e) { setErr(e.message || 'Lưu thất bại.'); } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={isEdit ? 'edit' : 'plus'} size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>
            {isEdit ? 'Chỉnh sửa phiếu yêu cầu' : 'Thêm phiếu yêu cầu'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? req.name : 'Tạo phiếu yêu cầu tuyển dụng mới'}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto' }}>
        <Section title="Vị trí cần tuyển">
          <Field label="Phòng ban *">
            <select style={inp} value={f.depId} onChange={onDep}>
              <option value="">— Chọn —</option>
              {meta.departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select></Field>
          <Field label="JD từ kho">
            <select style={inp} value={f.jobId} onChange={onJob} disabled={!f.depId}>
              <option value="">{f.depId
                ? (jobs.length ? '— Chọn JD —' : '— Phòng ban này chưa có JD —')
                : '— Chọn phòng ban trước —'}</option>
              {jobs.map((j) => <option key={j.id} value={j.id}>{j.name}</option>)}
            </select>
            <span className="muted" style={{ fontSize: 11.5 }}>
              Lấy từ tab <b>Kho quản lý JD</b>, lọc theo phòng ban đã chọn. Chọn xong
              tự điền tên vị trí và link JD.</span></Field>
          <Field label="Tên vị trí *">
            <input style={inp} value={f.jobTitle} onChange={set('jobTitle')} placeholder="VD: Giáo viên Tiếng Trung" /></Field>
          <Field label="Số lượng cần tuyển">
            <input type="number" style={inp} value={f.qty} onChange={set('qty')} /></Field>
          <Field label="Lý do tuyển">
            <select style={inp} value={f.reason} onChange={set('reason')}>
              {Object.entries(meta.reasonLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Cấp bậc">
            <select style={inp} value={f.level} onChange={set('level')}>
              <option value="">— Chọn —</option>
              {Object.entries(meta.levelLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Link JD / Google Drive" full>
            <input style={inp} value={f.jdLink} onChange={set('jdLink')} placeholder="https://..." /></Field>
        </Section>

        <Section title="Yêu cầu ứng viên">
          <Field label="Bằng cấp tối thiểu">
            <select style={inp} value={f.education} onChange={set('education')}>
              {Object.entries(meta.educationLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          <Field label="Kinh nghiệm tối thiểu (năm)">
            <input type="number" step="0.5" style={inp} value={f.experienceYears} onChange={set('experienceYears')} /></Field>
          <Field label="Yêu cầu ngoại ngữ">
            <input style={inp} value={f.languageRequirement} onChange={set('languageRequirement')} /></Field>
          <Field label="Kỹ năng yêu cầu" full>
            <textarea style={{ ...inp, minHeight: 60, resize: 'vertical' }} value={f.skillDescription} onChange={set('skillDescription')} /></Field>
        </Section>

        <Section title="Điều kiện">
          <Field label="Ngày order">
            <input type="date" style={inp} value={f.dateRequest || ''} onChange={set('dateRequest')} /></Field>
          <Field label="Ngày cần onboard">
            <input type="date" style={inp} value={f.expectedStartDate || ''} onChange={set('expectedStartDate')} /></Field>
          <Field label="Mức lương dự kiến">
            <input style={inp} value={f.salaryRange} onChange={set('salaryRange')} placeholder="VD: 10–15 triệu" /></Field>
          <Field label="Hình thức làm việc">
            <select style={inp} value={f.workType} onChange={set('workType')}>
              {Object.entries(meta.workTypeLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
        </Section>

        {err && (
          <div style={{ marginTop: 4, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name={isEdit ? 'checkCircle' : 'plus'} size={16} />
          {busy ? 'Đang lưu…' : (isEdit ? 'Lưu thay đổi' : 'Tạo phiếu')}
        </button>
      </div>
    </Modal>
  );
}
