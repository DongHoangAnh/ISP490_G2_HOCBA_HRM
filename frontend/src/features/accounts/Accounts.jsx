/* ============================================================
   Trang danh sách tài khoản đăng nhập (HR/Admin) — liệt kê NV đã có tài
   khoản (gồm cả NV đã nghỉ), lọc theo phòng ban / trạng thái, khóa-mở
   khóa + cấp lại mật khẩu. Tạo tài khoản làm ở drawer NV. Owner: Tân.
   Spec: docs/superpowers/specs/2026-08-08-account-lock-independent-onboarding-step-design.md
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchAccounts, setAccountActive } from '../../api/employees';
import AccountForm from '../employees/AccountForm';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import ConfirmModal from '../../components/ConfirmModal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

const ROLE_LABEL = { employee: 'Nhân viên', giaovu: 'Giáo vụ', truongphong: 'Trưởng phòng' };

const sel = {
  padding: '6px 10px', borderRadius: 9, border: '1px solid var(--border-strong)',
  background: '#fff', fontSize: 13, color: 'var(--ink)', fontFamily: 'inherit',
};
/* width:1% + nowrap: các cột phải co sát nội dung, dồn khoảng trống cho
   cột Đăng nhập → nút thao tác kéo về gần cột Trạng thái, không bị đẩy khỏi khung. */
const nowrap = { width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' };

export default function Accounts({ search = '' }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [reset, setReset] = useState(null);  // { id, name } | null
  const [lock, setLock] = useState(null);    // { id, name, active } | null
  const [depId, setDepId] = useState('');    // '' = mọi phòng ban
  const [status, setStatus] = useState('');  // '' | 'active' | 'locked'

  const load = () => {
    setErr(null); setData(null);
    fetchAccounts().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải tài khoản…" />;

  const { accounts, departments } = data;
  const q = search.trim().toLowerCase();
  const rows = accounts.filter((r) => {
    if (depId && String(r.depId) !== depId) return false;
    if (status === 'active' && !r.active) return false;
    if (status === 'locked' && r.active) return false;
    return !q
      || r.name.toLowerCase().includes(q)
      || (r.login || '').toLowerCase().includes(q)
      || (r.code || '').toLowerCase().includes(q);
  });
  const lockedCount = accounts.filter((r) => !r.active).length;

  const doToggleLock = () => setAccountActive(lock.id, !lock.active)
    .then(() => { setLock(null); load(); });

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Tài khoản</h1>
          <p>
            {accounts.length} tài khoản đăng nhập · {lockedCount} đang khóa
            {' '}· {departments.length} phòng ban
          </p>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Danh sách tài khoản</h3>
          <span style={{ marginLeft: 'auto', display: 'flex', gap: 8, alignItems: 'center' }}>
            <select style={sel} value={depId} onChange={(e) => setDepId(e.target.value)}>
              <option value="">Tất cả phòng ban</option>
              {departments.map((d) => (
                <option key={d.id} value={String(d.id)}>{d.name}</option>
              ))}
            </select>
            <select style={sel} value={status} onChange={(e) => setStatus(e.target.value)}>
              <option value="">Mọi trạng thái</option>
              <option value="active">Đang sử dụng</option>
              <option value="locked">Đang khóa</option>
            </select>
            <span className="sub">{rows.length} người</span>
          </span>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Mã</th><th>Phòng ban</th>
              <th>Đăng nhập</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Loại</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
            </tr></thead>
            <tbody>
              {rows.map((r) => {
                const resigned = r.empActive === false;
                // BE từ chối khóa/mở tài khoản quản trị hệ thống.
                const locked = !!r.isSystem;
                return (
                  <tr key={r.employeeId}>
                    <td><div className="nm">{r.name}</div></td>
                    <td className="muted mono">{r.code}</td>
                    <td>{r.depName}</td>
                    <td className="mono">{r.login}</td>
                    <td style={nowrap}>{ROLE_LABEL[r.role] || r.role}</td>
                    <td style={nowrap}>
                      <span style={{ display: 'inline-flex', gap: 5 }}>
                        <Badge kind={r.active ? 'green' : 'gray'} dot>
                          {r.active ? 'Hoạt động' : 'Khóa'}
                        </Badge>
                        {resigned && <Badge kind="gray">Đã nghỉ</Badge>}
                      </span>
                    </td>
                    <td style={nowrap}>
                      {/* NV đã nghỉ: offboarding đã khóa tài khoản họ. Mở lại ở
                          đây sẽ tạo user đăng nhập được trong khi hồ sơ NV vẫn
                          archived (env.user.employee_id rỗng) → BE từ chối. Còn
                          cấp lại mật khẩu thì chạy trót lọt nhưng vô nghĩa. Ẩn
                          cả hai thay vì bày nút chỉ để báo lỗi. */}
                      {locked && <span className="faint" style={{ fontSize: 12 }}>Quản trị hệ thống</span>}
                      {!locked && !resigned && (
                        <>
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => setLock({ id: r.employeeId, name: r.name, active: r.active })}>
                            <Icon name={r.active ? 'lock' : 'check'} size={14} />
                            {r.active ? 'Khóa' : 'Mở khóa'}
                          </button>
                          <button className="btn btn-ghost btn-sm"
                            onClick={() => setReset({ id: r.employeeId, name: r.name })}>
                            <Icon name="rotateCcw" size={14} />Cấp lại MK</button>
                        </>
                      )}
                      {!locked && resigned && r.active && (
                        <button className="btn btn-ghost btn-sm"
                          onClick={() => setLock({ id: r.employeeId, name: r.name, active: true })}>
                          <Icon name="lock" size={14} />Khóa
                        </button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Không có tài khoản khớp bộ lọc.</EmptyState>}
      </div>

      {reset && (
        <AccountForm emp={reset} mode="reset"
          onClose={() => setReset(null)}
          onDone={() => { setReset(null); load(); }} />
      )}

      {lock && (
        <ConfirmModal
          title={lock.active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}
          message={lock.active
            ? `Khóa tài khoản của ${lock.name}? Người này sẽ không đăng nhập được cho tới khi được mở khóa.`
            : `Mở khóa tài khoản của ${lock.name}? Người này đăng nhập lại được ngay.`}
          confirmLabel={lock.active ? 'Khóa' : 'Mở khóa'}
          onConfirm={doToggleLock}
          onClose={() => setLock(null)} />
      )}
    </div>
  );
}
