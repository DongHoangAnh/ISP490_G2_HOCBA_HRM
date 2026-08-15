/* ============================================================
   Form tạo / sửa phòng ban — chỉ HR/Admin. Owner: Tân.
   employees = danh mục NV cho dropdown trưởng phòng (BE đã lọc: chỉ NV có
   tài khoản đăng nhập + trưởng phòng đương nhiệm).
   onDone(deptPayload) nhận phòng ban đã lưu.

   Chốt với khách 2026-08-14 — TẠO phòng ban thì BẮT BUỘC tạo trưởng phòng
   MỚI (hồ sơ NV + tài khoản đăng nhập) ngay trong form này. Lý do: quyền
   "trưởng phòng" suy ra từ hr.department.manager_id, nên chọn một NV có sẵn
   ở bước tạo là âm thầm nâng quyền tài khoản vốn có vai trò khác. Màn SỬA
   vẫn cho chọn NV có sẵn (để thay trưởng phòng nghỉ việc) nhưng chỉ những
   người đã có tài khoản.
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

const emptyMgr = {
  name: '', code: '', login: '', password: '', password_confirm: '',
  email: '', phone: '', empTypeId: '',
};

export default function DepartmentForm({ dept, employees = [], empTypes = [],
                                         minPasswordLen = 8, onClose, onDone }) {
  const edit = !!dept;
  const [name, setName] = useState(dept ? dept.name : '');
  const [functionDesc, setFunctionDesc] = useState(dept ? dept.functionDesc : '');
  const [managerId, setManagerId] = useState(dept && dept.managerId ? String(dept.managerId) : '');
  // Màn tạo luôn ở chế độ "trưởng phòng mới"; màn sửa bật khi HR chọn tạo mới.
  const [newMgr, setNewMgr] = useState(!edit);
  const [mgr, setMgr] = useState(emptyMgr);
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const setM = (k) => (e) => setMgr((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    setErr(null);
    if (newMgr) {
      if (!mgr.name.trim()) { setErr('Vui lòng nhập họ tên trưởng phòng.'); return; }
      if (!mgr.login.trim()) { setErr('Vui lòng nhập tên đăng nhập cho trưởng phòng.'); return; }
      if (mgr.password.length < minPasswordLen) {
        setErr(`Mật khẩu phải có ít nhất ${minPasswordLen} ký tự.`); return;
      }
      if (mgr.password !== mgr.password_confirm) {
        setErr('Xác nhận mật khẩu không khớp.'); return;
      }
    }
    setBusy(true);
    try {
      const payload = { name, functionDesc };
      if (newMgr) payload.manager = mgr;
      else payload.managerId = managerId ? Number(managerId) : false;
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
          {edit
            ? <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{dept.employeeCount} nhân viên</div>
            : <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>Kèm tài khoản trưởng phòng mới</div>}
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px', maxHeight: '60vh', overflowY: 'auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Tên phòng ban *" full>
            <input style={inp} value={name} onChange={(e) => setName(e.target.value)}
              placeholder="VD: Marketing" autoComplete="off" />
          </Field>
          <Field label="Chức năng phòng ban" full>
            <input style={inp} value={functionDesc} onChange={(e) => setFunctionDesc(e.target.value)}
              placeholder="Mô tả ngắn nghiệp vụ" autoComplete="off" />
          </Field>

          {/* Màn SỬA: chọn NV có sẵn (chỉ người đã có tài khoản) hoặc bật tạo mới */}
          {edit && !newMgr && (
            <Field label="Trưởng phòng" full>
              <select style={inp} value={managerId} onChange={(e) => setManagerId(e.target.value)}>
                <option value="">— Không gán —</option>
                {employees.map((e) => (
                  <option key={e.id} value={e.id}>
                    {e.name}{e.code ? ` (${e.code})` : ''}
                    {e.hasAccount === false ? ' — chưa có tài khoản' : ''}
                  </option>
                ))}
              </select>
              <span className="muted" style={{ fontSize: 11.5, marginTop: 4 }}>
                Chỉ liệt kê nhân viên đã có tài khoản đăng nhập.
              </span>
            </Field>
          )}
          {edit && (
            <div style={{ gridColumn: '1 / -1' }}>
              <button className="btn btn-ghost btn-sm" type="button"
                onClick={() => { setNewMgr(!newMgr); setErr(null); }}>
                <Icon name={newMgr ? 'rotateCcw' : 'plus'} size={14} />
                {newMgr ? 'Quay lại chọn nhân viên có sẵn' : 'Tạo trưởng phòng mới'}
              </button>
            </div>
          )}
        </div>

        {newMgr && (
          <div style={{ marginTop: 18 }}>
            <div style={{ fontSize: 12.5, fontWeight: 800, marginBottom: 12, paddingBottom: 7, borderBottom: '1px solid var(--border)', color: 'var(--red-700)' }}>
              Trưởng phòng {edit ? 'mới' : '*'}
            </div>
            {/* Hồ sơ tạo ở đây mặc định Thử việc (mặc định của x_employment_status).
                Đặt Chính thức ngay sẽ vướng BR-010 (bắt CCCD/MST/BHXH) nên để HR
                hoàn thiện ở màn Nhân viên thay vì nhồi hết vào form này. */}
            <div className="muted" style={{ fontSize: 11.5, marginBottom: 12 }}>
              Hồ sơ được tạo ở trạng thái <b>Thử việc</b> — bổ sung CCCD, lương,
              tình trạng chính thức… ở màn Nhân viên sau khi lưu.
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
              <Field label="Họ và tên *">
                <input style={inp} value={mgr.name} onChange={setM('name')}
                  placeholder="Nguyễn Văn A" autoComplete="off" />
              </Field>
              <Field label="Mã nhân sự">
                <input style={inp} value={mgr.code} onChange={setM('code')}
                  placeholder="VD: HB.20" autoComplete="off" />
              </Field>
              <Field label="Loại nhân sự">
                <select style={inp} value={mgr.empTypeId} onChange={setM('empTypeId')}>
                  <option value="">— Chưa phân loại —</option>
                  {empTypes.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
              </Field>
              <Field label="Email công ty">
                <input style={inp} value={mgr.email} onChange={setM('email')}
                  placeholder="a.nv@hocba.edu.vn" autoComplete="off" />
              </Field>
              <Field label="Điện thoại">
                <input style={inp} value={mgr.phone} onChange={setM('phone')}
                  placeholder="09xxxxxxxx" autoComplete="off" />
              </Field>
              <Field label="Tên đăng nhập *">
                <input style={inp} value={mgr.login} onChange={setM('login')}
                  placeholder="email hoặc username" autoComplete="off" />
              </Field>
              <Field label={`Mật khẩu * (≥ ${minPasswordLen} ký tự)`}>
                <input type="password" style={inp} value={mgr.password}
                  autoComplete="new-password" onChange={setM('password')} />
              </Field>
              <Field label="Xác nhận mật khẩu *">
                <input type="password" style={inp} value={mgr.password_confirm}
                  autoComplete="new-password" onChange={setM('password_confirm')} />
              </Field>
            </div>
          </div>
        )}

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
