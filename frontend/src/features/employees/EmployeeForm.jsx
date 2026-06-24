/* ============================================================
   Form Thêm / Sửa nhân viên — ngay trong SPA (thay "Sửa trong Odoo").
   Dùng chung cho tạo mới (emp=null) và chỉnh sửa. Field chia theo quyền:
   cơ bản (mọi HR) · pháp lý (HR) · lương+bảo hiểm (HR Manager). Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchFormMeta, createEmployee, updateEmployee } from '../../api/employees';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { LoadingState } from '../../components/states';

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

function initForm(emp) {
  return {
    name: emp?.name || '', code: (emp?.code && emp.code !== '—') ? emp.code : '',
    depId: emp?.dep || '', jobId: emp?.jobId || '',
    workForm: emp?.workFormKey || '', status: emp?.statusKey || 'probation',
    posType: emp?.posTypeKey || '', email: emp?.email || '', phone: emp?.phone || '',
    probStart: emp?.probStart || '', bday: emp?.bday || '', cccd: emp?.cccd || '',
    idIssue: emp?.idIssue || '', idPlace: emp?.idPlace || '',
    hi: emp?.hi || '', hiPlace: emp?.hiPlace || '',
    pit: emp?.pit || '', si: emp?.si || '', wage: emp?.wage || '',
    bankAccountNo: emp?.bankAccountNo || '', bankCode: emp?.bankCode || '',
  };
}

export default function EmployeeForm({ emp, isMgr, onClose, onSaved }) {
  const isEdit = !!emp;
  const [meta, setMeta] = useState(null);
  const [metaErr, setMetaErr] = useState(null);
  const [f, setF] = useState(() => initForm(emp));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => { fetchFormMeta().then(setMeta).catch((e) => setMetaErr(e.message)); }, []);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    if (!f.name.trim()) { setErr('Vui lòng nhập họ tên.'); return; }
    setBusy(true); setErr(null);
    try {
      const det = isEdit ? await updateEmployee(emp.id, f) : await createEmployee(f);
      onSaved(det);
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  const jobs = meta ? meta.jobs.filter((j) => !f.depId || j.dep === Number(f.depId)) : [];

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={isEdit ? 'edit' : 'plus'} size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>
            {isEdit ? 'Chỉnh sửa nhân viên' : 'Thêm nhân viên'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? `${emp.code} · ${emp.name}` : 'Tạo hồ sơ nhân sự mới trong hệ thống'}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto' }}>
        {metaErr && <div style={{ color: 'var(--red-600)', fontSize: 13 }}>Không tải được dữ liệu form ({metaErr}).</div>}
        {!meta && !metaErr && <LoadingState label="Đang tải biểu mẫu…" />}
        {meta && (
          <>
            <Section title="Thông tin cơ bản">
              <Field label="Họ và tên *" full>
                <input style={inp} value={f.name} onChange={set('name')} placeholder="Nguyễn Văn A" /></Field>
              <Field label="Mã nhân sự">
                <input style={inp} value={f.code} onChange={set('code')} placeholder="VD: HB.07" /></Field>
              <Field label="Phòng ban">
                <select style={inp} value={f.depId} onChange={(e) => setF((p) => ({ ...p, depId: e.target.value, jobId: '' }))}>
                  <option value="">— Chọn —</option>
                  {meta.departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
                </select></Field>
              <Field label="Chức danh">
                <select style={inp} value={f.jobId} onChange={set('jobId')}>
                  <option value="">— Chọn —</option>
                  {jobs.map((j) => <option key={j.id} value={j.id}>{j.name}</option>)}
                </select></Field>
              <Field label="Hình thức làm việc">
                <select style={inp} value={f.workForm} onChange={set('workForm')}>
                  <option value="">— Chọn —</option>
                  {meta.workForm.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </select></Field>
              <Field label="Tình trạng">
                <select style={inp} value={f.status} onChange={set('status')}>
                  {meta.status.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </select></Field>
              <Field label="Loại vị trí">
                <select style={inp} value={f.posType} onChange={set('posType')}>
                  <option value="">— Chọn —</option>
                  {meta.position.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
                </select></Field>
              <Field label="Ngày bắt đầu thử việc">
                <input type="date" style={inp} value={f.probStart || ''} onChange={set('probStart')} /></Field>
              <Field label="Email công ty">
                <input style={inp} value={f.email} onChange={set('email')} placeholder="a.nv@hocba.edu.vn" /></Field>
              <Field label="Điện thoại">
                <input style={inp} value={f.phone} onChange={set('phone')} placeholder="09xxxxxxxx" /></Field>
            </Section>

            <Section title="Hồ sơ pháp lý">
              <Field label="Ngày sinh">
                <input type="date" style={inp} value={f.bday || ''} onChange={set('bday')} /></Field>
              <Field label="CCCD (12 số)">
                <input style={inp} value={f.cccd} onChange={set('cccd')} placeholder="0xxxxxxxxxxx" /></Field>
              <Field label="Ngày cấp CCCD">
                <input type="date" style={inp} value={f.idIssue || ''} onChange={set('idIssue')} /></Field>
              <Field label="Nơi cấp CCCD">
                <input style={inp} value={f.idPlace} onChange={set('idPlace')} placeholder="Cục CS QLHC..." /></Field>
              <Field label="Số thẻ BHYT">
                <input style={inp} value={f.hi} onChange={set('hi')} /></Field>
              <Field label="Nơi KCB ban đầu">
                <input style={inp} value={f.hiPlace} onChange={set('hiPlace')} /></Field>
            </Section>

            {isMgr && (
              <Section title="Lương & bảo hiểm (Quản lý)">
                <Field label="Lương cơ bản (₫)">
                  <input type="number" style={inp} value={f.wage} onChange={set('wage')} placeholder="0" /></Field>
                <Field label="MST TNCN (10/13 số)">
                  <input style={inp} value={f.pit} onChange={set('pit')} /></Field>
                <Field label="Số sổ BHXH (10 số)">
                  <input style={inp} value={f.si} onChange={set('si')} /></Field>
                <Field label="Ngân hàng nhận lương">
                  <select style={inp} value={f.bankCode} onChange={set('bankCode')}>
                    <option value="">— Chọn —</option>
                    {(meta.banks || []).map((b) => <option key={b.code} value={b.code}>{b.name}</option>)}
                  </select></Field>
                <Field label="Số tài khoản nhận lương">
                  <input style={inp} value={f.bankAccountNo} onChange={set('bankAccountNo')} placeholder="VD: 0123456789" /></Field>
              </Section>
            )}
          </>
        )}
        {err && (
          <div style={{ marginTop: 4, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || !meta}>
          <Icon name={isEdit ? 'checkCircle' : 'plus'} size={16} />
          {busy ? 'Đang lưu…' : (isEdit ? 'Lưu thay đổi' : 'Tạo nhân viên')}
        </button>
      </div>
    </Modal>
  );
}
