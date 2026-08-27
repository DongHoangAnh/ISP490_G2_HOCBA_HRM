/* ============================================================
   Form tạo / cấp lại tài khoản đăng nhập — chỉ HR/Admin. Owner: Tân.
   mode='create' | 'reset'. onDone(accountPayload) nhận khối account mới.

   Chốt với khách 2026-08-27: màn này CHỈ cấp tài khoản nhân viên thường. Trưởng
   phòng và giáo vụ là tài khoản vai trò riêng, tạo ở form phòng ban — trước đây
   chọn được ở đây chính là đường đeo quyền quản lý vào tài khoản cá nhân của
   một NV có thật (mô hình kiêm nhiệm đã bỏ). Backend chặn độc lập.
   ============================================================ */
import { useState } from 'react';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import { createAccount, resetAccountPassword } from '../../api/employees';

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

export default function AccountForm({ emp, mode = 'create', onClose, onDone }) {
  const reset = mode === 'reset';
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);

  const submit = async () => {
    setErr(null); setBusy(true);
    try {
      const res = reset
        ? await resetAccountPassword(emp.id, { password, password_confirm: confirm })
        : await createAccount(emp.id, { login, password, password_confirm: confirm });
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
          <Icon name={reset ? 'shield' : 'plus'} size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{reset ? 'Cấp lại mật khẩu' : 'Tạo tài khoản'}</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{emp.name}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '20px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          {!reset && (
            <Field label="Tên đăng nhập *" full>
              <input style={inp} value={login} onChange={(e) => setLogin(e.target.value)}
                placeholder="email hoặc username" autoComplete="off" />
            </Field>
          )}
          <Field label={reset ? 'Mật khẩu mới *' : 'Mật khẩu *'}>
            <input type="password" style={inp} value={password} autoComplete="new-password"
              onChange={(e) => setPassword(e.target.value)} />
          </Field>
          <Field label="Xác nhận mật khẩu *">
            <input type="password" style={inp} value={confirm} autoComplete="new-password"
              onChange={(e) => setConfirm(e.target.value)} />
          </Field>
        </div>
        {!reset && (
          <div className="muted" style={{ fontSize: 11.5, marginTop: 12 }}>
            Tài khoản nhân viên thường. Quyền trưởng phòng / giáo vụ không cấp ở
            đây — đó là tài khoản vai trò riêng, tạo ở màn <b>Phòng ban</b>.
          </div>
        )}
        {err && (
          <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name="checkCircle" size={16} />{busy ? 'Đang lưu…' : (reset ? 'Cấp lại' : 'Tạo tài khoản')}
        </button>
      </div>
    </Modal>
  );
}
