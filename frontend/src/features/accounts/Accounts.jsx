/* ============================================================
   Trang danh sách tài khoản đăng nhập (HR/Admin) — chỉ liệt kê NV
   đã có tài khoản + cấp lại mật khẩu. Tạo tài khoản làm ở drawer NV.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchAccounts } from '../../api/employees';
import AccountForm from '../employees/AccountForm';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

const ROLE_LABEL = { employee: 'Nhân viên', giaovu: 'Giáo vụ', truongphong: 'Trưởng phòng' };

export default function Accounts({ search = '' }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [reset, setReset] = useState(null); // { id, name } | null

  const load = () => {
    setErr(null); setData(null);
    fetchAccounts().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải tài khoản…" />;

  const { accounts, departments } = data;
  const q = search.trim().toLowerCase();
  const rows = accounts.filter((r) => !q
    || r.name.toLowerCase().includes(q)
    || (r.login || '').toLowerCase().includes(q)
    || (r.code || '').toLowerCase().includes(q));

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Tài khoản</h1>
          <p>{accounts.length} tài khoản đăng nhập · {departments.length} phòng ban</p>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Danh sách tài khoản</h3>
          <span className="sub">{rows.length} người</span>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Mã</th><th>Phòng ban</th>
              <th>Đăng nhập</th><th>Loại</th><th>Trạng thái</th><th></th>
            </tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.employeeId}>
                  <td><div className="nm">{r.name}</div></td>
                  <td className="muted mono">{r.code}</td>
                  <td>{r.depName}</td>
                  <td className="mono">{r.login}</td>
                  <td>{ROLE_LABEL[r.role] || r.role}</td>
                  <td><Badge kind={r.active ? 'green' : 'gray'} dot>{r.active ? 'Hoạt động' : 'Khóa'}</Badge></td>
                  <td>
                    <button className="btn btn-ghost btn-sm" onClick={() => setReset({ id: r.employeeId, name: r.name })}>
                      <Icon name="rotateCcw" size={14} />Cấp lại MK</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có tài khoản.</EmptyState>}
      </div>

      {reset && (
        <AccountForm emp={reset} mode="reset"
          onClose={() => setReset(null)}
          onDone={() => { setReset(null); load(); }} />
      )}
    </div>
  );
}
