/* ============================================================
   Form tạo / sửa phòng ban — chỉ HR/Admin. Owner: Tân.
   employees = danh mục NV THẬT, chỉ dùng cho ô "điền nhanh" (lấy sẵn họ tên /
   email / điện thoại). onDone(deptPayload) nhận phòng ban đã lưu.

   Chốt với khách 2026-08-27 — người đứng đầu phòng ban LUÔN là một tài khoản
   vai trò MỚI (tên đăng nhập + mật khẩu riêng), không bao giờ là hồ sơ NV có
   sẵn. Lý do: quyền suy ra từ hr.department.manager_id, nên gán một NV thật là
   âm thầm nâng quyền tài khoản cá nhân của họ. Chọn người ở ô điền nhanh chỉ
   là mượn thông tin để đỡ gõ — backend không nhận id người được chọn.

   Hai vai trò: Trưởng phòng (quản lý NV phòng mình) và Giáo vụ (quản lý giảng
   viên). Cả hai đều đứng tên manager_id; giáo vụ được cấp thêm nhóm giáo vụ và
   phạm vi thực tế của họ là toàn bộ giảng viên mọi phòng, không bó theo phòng.
   ============================================================ */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createDepartment, updateDepartment } from '../../api/departments';

const HEAD_ROLES = [
  ['truongphong', 'Trưởng phòng'],
  ['giaovu', 'Giáo vụ'],
];

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
  role: 'truongphong', name: '', login: '', password: '', password_confirm: '',
  email: '', phone: '',
};

export default function DepartmentForm({ dept, employees = [],
                                         minPasswordLen = 8, onClose, onDone }) {
  const edit = !!dept;
  const [name, setName] = useState(dept ? dept.name : '');
  const [functionDesc, setFunctionDesc] = useState(dept ? dept.functionDesc : '');
  // 'keep' giữ nguyên người đang đứng đầu · 'new' tạo tài khoản vai trò mới ·
  // 'clear' gỡ trắng. Màn tạo không có gì để giữ nên luôn ở 'new'.
  const [headMode, setHeadMode] = useState(edit ? 'keep' : 'new');
  const [mgr, setMgr] = useState(emptyMgr);
  const [prefillId, setPrefillId] = useState('');
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const setM = (k) => (e) => setMgr((p) => ({ ...p, [k]: e.target.value }));

  /* Điền nhanh: chép họ tên/email/điện thoại của NV được chọn vào form. KHÔNG
     đụng tới tên đăng nhập và mật khẩu — đó là tài khoản mới, HR phải tự đặt. */
  const prefillFrom = (e) => {
    const id = e.target.value;
    setPrefillId(id);
    const src = employees.find((x) => String(x.id) === id);
    if (!src) return;
    setMgr((p) => ({
      ...p,
      name: src.name || '',
      email: src.email || '',
      phone: src.phone || '',
    }));
  };

  const submit = async () => {
    setErr(null);
    if (!name.trim()) { setErr('Vui lòng nhập tên phòng ban.'); return; }
    if (headMode === 'new') {
      if (!mgr.name.trim()) { setErr('Vui lòng nhập họ tên người đứng đầu.'); return; }
      if (!mgr.login.trim()) { setErr('Vui lòng nhập tên đăng nhập.'); return; }
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
      // Backend phân biệt 3 ý định bằng KHÓA CÓ MẶT, không bằng giá trị:
      // 'manager' = tạo mới · 'managerId' rỗng = gỡ · không khóa nào = giữ.
      if (headMode === 'new') payload.manager = mgr;
      else if (headMode === 'clear') payload.managerId = 0;
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

  const roleLabel = HEAD_ROLES.find(([v]) => v === mgr.role)?.[1] || 'Trưởng phòng';

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
            : <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>Kèm tài khoản người đứng đầu</div>}
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      {/* Enter = bấm nút lưu, trừ khi con trỏ đang ở <select> (Enter ở đó là
          thao tác chọn của trình duyệt). */}
      <div style={{ padding: '20px 24px', maxHeight: '60vh', overflowY: 'auto' }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && !busy && e.target.tagName !== 'SELECT') submit();
        }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Tên phòng ban *" full>
            <input style={inp} value={name} onChange={(e) => setName(e.target.value)}
              placeholder="VD: Marketing" autoComplete="off" />
          </Field>
          <Field label="Chức năng phòng ban" full>
            <input style={inp} value={functionDesc} onChange={(e) => setFunctionDesc(e.target.value)}
              placeholder="Mô tả ngắn nghiệp vụ" autoComplete="off" />
          </Field>
        </div>

        {/* Màn SỬA: người đang đứng đầu + 3 lựa chọn xử lý */}
        {edit && (
          <div style={{ marginTop: 16, padding: '12px 14px', border: '1px solid var(--border)', borderRadius: 10, background: 'var(--bg-soft, #fafafa)' }}>
            <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px', marginBottom: 6 }}>
              Người đứng đầu hiện tại
            </div>
            <div style={{ fontSize: 13.5, fontWeight: 600, marginBottom: 10 }}>
              {dept.managerName || <span className="muted" style={{ fontWeight: 400 }}>— Chưa có —</span>}
            </div>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {headMode !== 'new' && (
                <button className="btn btn-ghost btn-sm" type="button"
                  onClick={() => { setHeadMode('new'); setErr(null); }}>
                  <Icon name="plus" size={14} />
                  {dept.managerId ? 'Đổi người đứng đầu' : 'Thêm người đứng đầu'}
                </button>
              )}
              {headMode === 'new' && (
                <button className="btn btn-ghost btn-sm" type="button"
                  onClick={() => { setHeadMode('keep'); setErr(null); }}>
                  <Icon name="rotateCcw" size={14} />Huỷ đổi, giữ nguyên
                </button>
              )}
              {dept.managerId && headMode !== 'clear' && (
                <button className="btn btn-ghost btn-sm" type="button"
                  onClick={() => { setHeadMode('clear'); setErr(null); }}>
                  <Icon name="x" size={14} />Gỡ người đứng đầu
                </button>
              )}
              {headMode === 'clear' && (
                <button className="btn btn-ghost btn-sm" type="button"
                  onClick={() => { setHeadMode('keep'); setErr(null); }}>
                  <Icon name="rotateCcw" size={14} />Huỷ gỡ
                </button>
              )}
            </div>
            {headMode === 'clear' && (
              <div style={{ marginTop: 9, fontSize: 12, color: 'var(--red-700)' }}>
                Lưu xong phòng này sẽ không còn ai quản — nhân viên trong phòng
                không có người duyệt cho tới khi bạn gán lại.
              </div>
            )}
          </div>
        )}

        {headMode === 'new' && (
          <div style={{ marginTop: 18 }}>
            <div style={{ fontSize: 12.5, fontWeight: 800, marginBottom: 12, paddingBottom: 7, borderBottom: '1px solid var(--border)', color: 'var(--red-700)' }}>
              Tài khoản {roleLabel.toLowerCase()} {edit ? 'mới' : '*'}
            </div>
            <div className="muted" style={{ fontSize: 11.5, marginBottom: 12 }}>
              Đây là <b>tài khoản quản lý riêng</b>, không phải hồ sơ nhân sự —
              không có mã nhân viên, không vào danh sách Nhân viên, không qua
              Nhận việc. Người đã có tài khoản nhân viên vẫn cần tài khoản này
              để quản lý.
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
              <Field label="Vai trò *">
                <select style={inp} value={mgr.role} onChange={setM('role')}>
                  {HEAD_ROLES.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
                </select>
              </Field>
              <Field label="Điền nhanh từ nhân viên có sẵn">
                <select style={inp} value={prefillId} onChange={prefillFrom}>
                  <option value="">— Tự nhập —</option>
                  {employees.map((e) => (
                    <option key={e.id} value={e.id}>
                      {e.name}{e.code ? ` (${e.code})` : ''}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Họ và tên *">
                <input style={inp} value={mgr.name} onChange={setM('name')}
                  placeholder="Nguyễn Văn A" autoComplete="off" />
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
            {mgr.role === 'giaovu' && (
              <div className="muted" style={{ fontSize: 11.5, marginTop: 10 }}>
                Giáo vụ quản lý <b>toàn bộ giảng viên</b> ở mọi phòng ban, không
                chỉ phòng này — phạm vi đó rộng hơn quyền trưởng phòng.
              </div>
            )}
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
