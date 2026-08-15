/* ============================================================
   Tự đổi mật khẩu — MỌI vai trò, mở từ thanh bên (không đặt trong "Hồ sơ của
   tôi" vì tài khoản HR/Admin/Giáo vụ không có màn đó). Owner: Tân.

   Khác với "Cấp lại mật khẩu" của HR (màn Tài khoản): ở đây phải nhập mật
   khẩu HIỆN TẠI. HR chỉ cấp lại khi nhân viên quên.
   ============================================================ */
import { useState } from 'react';
import Modal from './Modal';
import Icon from './Icon';
import { changeMyPassword } from '../api/employees';

const MIN_LEN = 8;

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

export default function ChangePasswordForm({ onClose }) {
  const [f, setF] = useState({ currentPassword: '', password: '', password_confirm: '' });
  const [err, setErr] = useState(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));
  const relogin = () => { window.location.href = '/web/session/logout?redirect=/hocba-hrm'; };

  const submit = async () => {
    setErr(null);
    if (!f.currentPassword) { setErr('Vui lòng nhập mật khẩu hiện tại.'); return; }
    if (f.password.length < MIN_LEN) { setErr(`Mật khẩu mới phải có ít nhất ${MIN_LEN} ký tự.`); return; }
    if (f.password !== f.password_confirm) { setErr('Xác nhận mật khẩu không khớp.'); return; }
    if (f.password === f.currentPassword) { setErr('Mật khẩu mới phải khác mật khẩu hiện tại.'); return; }
    setBusy(true);
    try {
      await changeMyPassword(f);
      // Odoo tính session_token từ mật khẩu → phiên hiện tại đã hết hiệu lực.
      // Không cho bấm tiếp gì nữa, chỉ còn đường đăng nhập lại.
      setDone(true);
    } catch (e) {
      setErr(e.message || 'Đổi mật khẩu thất bại.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={done ? relogin : onClose}>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="lock" size={20} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Đổi mật khẩu</h2>
          <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
            {done ? 'Đã cập nhật' : 'Mật khẩu tài khoản đăng nhập của bạn'}
          </div>
        </div>
        {!done && <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>}
      </div>

      {done ? (
        <div style={{ padding: '22px 24px', display: 'grid', gap: 10, justifyItems: 'center', textAlign: 'center' }}>
          <Icon name="checkCircle" size={34} style={{ color: 'var(--green)' }} />
          <div style={{ fontWeight: 700 }}>Đổi mật khẩu thành công.</div>
          <div className="muted" style={{ fontSize: 13 }}>
            Phiên đăng nhập cũ đã hết hiệu lực. Vui lòng đăng nhập lại bằng mật khẩu mới.
          </div>
        </div>
      ) : (
        /* Enter = bấm "Đổi mật khẩu": form toàn ô mật khẩu, gõ xong ai cũng
           theo phản xạ nhấn Enter. */
        <div style={{ padding: '20px 24px', display: 'grid', gap: 14 }}
          onKeyDown={(e) => { if (e.key === 'Enter' && !busy) submit(); }}>
          <Field label="Mật khẩu hiện tại *">
            <input type="password" style={inp} value={f.currentPassword}
              autoComplete="current-password" onChange={set('currentPassword')} />
          </Field>
          <Field label={`Mật khẩu mới * (≥ ${MIN_LEN} ký tự)`}>
            <input type="password" style={inp} value={f.password}
              autoComplete="new-password" onChange={set('password')} />
          </Field>
          <Field label="Xác nhận mật khẩu mới *">
            <input type="password" style={inp} value={f.password_confirm}
              autoComplete="new-password" onChange={set('password_confirm')} />
          </Field>
          {err && (
            <div style={{ padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
          )}
        </div>
      )}

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        {done ? (
          <button className="btn btn-primary" onClick={relogin}>
            <Icon name="logout" size={16} />Đăng nhập lại</button>
        ) : (
          <>
            <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
            <button className="btn btn-primary" onClick={submit} disabled={busy}>
              <Icon name="checkCircle" size={16} />{busy ? 'Đang đổi…' : 'Đổi mật khẩu'}
            </button>
          </>
        )}
      </div>
    </Modal>
  );
}
