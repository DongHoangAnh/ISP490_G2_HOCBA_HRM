import { useState } from 'react';
import logo from '../../assets/logo-hb.png';
import mascot from '../../assets/logo1.jpg';
import './Login.css';

export default function Login({ onSuccess }) {
  const [login, setLogin] = useState('');
  const [password, setPassword] = useState('');
  const [showPwd, setShowPwd] = useState(false);
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [authError, setAuthError] = useState('');

  function validate() {
    const e = {};
    if (!login.trim()) e.login = 'Vui lòng nhập tài khoản.';
    if (!password) e.password = 'Vui lòng nhập mật khẩu.';
    return e;
  }

  async function handleSubmit(evt) {
    evt.preventDefault();
    const e = validate();
    setErrors(e);
    if (Object.keys(e).length) return;

    setLoading(true);
    setAuthError('');
    try {
      const res = await fetch('/web/session/authenticate', {
        method: 'POST',
        credentials: 'same-origin',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          jsonrpc: '2.0',
          method: 'call',
          // Tên DB do server nhúng vào trang (controller hrm_dashboard).
          // Ghi cứng 'neondb' như trước thì mọi DB khác (local, demo) đều
          // báo sai mật khẩu dù mật khẩu đúng.
          params: {
            db: window.__HB_DB__ || 'neondb',
            login: login.trim(),
            password,
          },
        }),
      });
      const data = await res.json();
      if (data.result && data.result.uid) {
        onSuccess();
      } else {
        setAuthError('Tài khoản hoặc mật khẩu không đúng.');
      }
    } catch {
      setAuthError('Không thể kết nối tới máy chủ. Vui lòng thử lại.');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="login-page">
      {/* Left panel */}
      <div className="login-left">
        <div className="login-left-content">
          <img src={mascot} alt="Học Bá" className="login-left-logo" />
          <h1 className="login-left-title">
            Chào mừng đến với <span>Học Bá</span>
          </h1>
          <p className="login-left-sub">
            Hệ thống quản lý nhân sự dành cho trung tâm tiếng Trung Học Bá Education
          </p>
        </div>
        <div className="login-left-decor" aria-hidden />
      </div>

      {/* Right panel */}
      <div className="login-right">
        <div className="login-card">
          <img src={logo} alt="Học Bá" className="login-card-logo" />

          <div className="login-card-heading">
            <p className="login-card-welcome">Chào mừng</p>
            <p className="login-card-sub">Vui lòng nhập thông tin để đăng nhập</p>
          </div>

          <form onSubmit={handleSubmit} noValidate className="login-form">
            <div className="login-field">
              <label className="login-label">
                Tài khoản <span className="login-req">*</span>
              </label>
              <div className={`login-input-wrap ${errors.login ? 'is-error' : ''}`}>
                <input
                  type="text"
                  value={login}
                  onChange={(e) => { setLogin(e.target.value); setErrors((x) => ({ ...x, login: '' })); setAuthError(''); }}
                  placeholder="Nhập email hoặc tên đăng nhập"
                  autoComplete="username"
                  autoFocus
                />
                <span className="login-input-icon">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="8" r="4"/><path d="M4 20c0-4 3.6-7 8-7s8 3 8 7"/></svg>
                </span>
              </div>
              {errors.login && <p className="login-error-msg">{errors.login}</p>}
            </div>

            <div className="login-field">
              <label className="login-label">
                Mật khẩu <span className="login-req">*</span>
              </label>
              <div className={`login-input-wrap ${errors.password ? 'is-error' : ''}`}>
                <input
                  type={showPwd ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => { setPassword(e.target.value); setErrors((x) => ({ ...x, password: '' })); setAuthError(''); }}
                  placeholder="Nhập mật khẩu"
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  className="login-toggle-pwd"
                  onClick={() => setShowPwd((v) => !v)}
                  tabIndex={-1}
                  aria-label={showPwd ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'}
                >
                  {showPwd ? (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
                  )}
                </button>
              </div>
              {errors.password && <p className="login-error-msg">{errors.password}</p>}
            </div>

            {authError && (
              <div className="login-auth-error">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
                {authError}
              </div>
            )}

            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? (
                <>
                  <span className="login-spinner" />
                  Đang đăng nhập…
                </>
              ) : 'Đăng nhập'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
