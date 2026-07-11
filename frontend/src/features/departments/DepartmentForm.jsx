/* ============================================================
   Form tạo / sửa phòng ban — chỉ HR/Admin. Owner: Tân.
   mode='create' | 'edit'. employees = danh mục NV cho dropdown trưởng phòng.
   onDone(deptPayload) nhận phòng ban đã lưu.
   ============================================================ */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createDepartment, updateDepartment } from '../../api/departments';

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

export default function DepartmentForm({ dept, employees = [], onClose, onDone }) {
  const edit = !!dept;
  const [name, setName] = useState(dept ? dept.name : '');
  const [functionDesc, setFunctionDesc] = useState(dept ? dept.functionDesc : '');
  const [managerId, setManagerId] = useState(dept && dept.managerId ? String(dept.managerId) : '');
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setErr(null); setBusy(true);
    try {
      const payload = { name, functionDesc, managerId: managerId ? Number(managerId) : false };
      const res = edit
        ? await updateDepartment(dept.id, payload)
        : await createDepartment(payload);
      onDone(res);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={edit ? 'edit' : 'plus'} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{edit ? 'Sửa phòng ban' : 'Thêm phòng ban'}</h2>
          {edit && <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{dept.employeeCount} nhân viên</div>}
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Tên phòng ban *" full>
            <input style={inp} value={name} onChange={(e) => setName(e.target.value)}
              placeholder="VD: Marketing" autoComplete="off" />
          </Field>
          <Field label="Chức năng phòng ban" full>
            <input style={inp} value={functionDesc} onChange={(e) => setFunctionDesc(e.target.value)}
              placeholder="Mô tả ngắn nghiệp vụ" autoComplete="off" />
          </Field>
          <Field label="Trưởng phòng" full>
            <select style={inp} value={managerId} onChange={(e) => setManagerId(e.target.value)}>
              <option value="">— Không gán —</option>
              {employees.map((e) => (
                <option key={e.id} value={e.id}>{e.name}{e.code ? ` (${e.code})` : ''}</option>
              ))}
            </select>
          </Field>
        </div>
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : (edit ? 'Lưu' : 'Thêm phòng ban')}
        </button>
      </div>
    </Modal>
  );
}
