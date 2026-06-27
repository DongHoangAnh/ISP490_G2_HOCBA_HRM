/* ============================================================
   Màn Nhân viên — MẪU CHUẨN cho cả team (dữ liệu thật từ
   hocba_employees qua /hocba-hrm/api/*). Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchEmployees } from '../../api/employees';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Avatar from '../../components/Avatar';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate, hbVND, hbStatusKind, hbTypeKind } from '../../utils/format';
import EmployeeDrawer from './EmployeeDrawer';
import EmployeeForm from './EmployeeForm';

export default function Employees({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [dep, setDep] = useState('all');
  const [status, setStatus] = useState('all');
  const [type, setType] = useState('all');
  const [sel, setSel] = useState(null);
  const [vmode, setVmode] = useState('table');
  const [creating, setCreating] = useState(false);

  const load = () => {
    setErr(null); setData(null);
    fetchEmployees().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải dữ liệu nhân sự…" />;

  const emps = data.employees, deps = data.departments;
  const statusOptions = [...new Map(emps.map((e) => [e.statusKey, e.status])).entries()];
  const typeOptions = [...new Set(emps.map((e) => e.type))].filter((t) => t && t !== '—');

  const filtered = emps.filter((e) => {
    if (dep !== 'all' && e.dep !== dep) return false;
    if (status !== 'all' && e.statusKey !== status) return false;
    if (type !== 'all' && e.type !== type) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!((e.name || '').toLowerCase().includes(q) || (e.code || '').toLowerCase().includes(q)
        || (e.jobTitle || '').toLowerCase().includes(q) || (e.depName || '').toLowerCase().includes(q))) return false;
    }
    return true;
  });

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nhân viên</h1>
          <p>{emps.length} nhân sự · {deps.length} phòng ban · dữ liệu trực tiếp từ Odoo</p>
        </div>
        <div className="actions">
          {data.isHr && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Thêm nhân viên</button>
          )}
        </div>
      </div>

      {/* Filter chips theo phòng ban (số liệu thật) */}
      <div className="filterbar">
        <button className={'chip' + (dep === 'all' ? ' active' : '')} onClick={() => setDep('all')}>
          Tất cả <span className="ct">{emps.length}</span></button>
        {deps.map((d) => (
          <button key={d.id} className={'chip' + (dep === d.id ? ' active' : '')} onClick={() => setDep(d.id)}>
            {d.name} <span className="ct">{d.total}</span></button>
        ))}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 9, alignItems: 'center' }}>
          <select className="sel" value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="all">Mọi trạng thái</option>
            {statusOptions.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
          </select>
          <select className="sel" value={type} onChange={(e) => setType(e.target.value)}>
            <option value="all">Mọi hình thức</option>
            {typeOptions.map((t) => <option key={t}>{t}</option>)}
          </select>
          <div className="seg">
            <button className={vmode === 'table' ? 'active' : ''} onClick={() => setVmode('table')}>Bảng</button>
            <button className={vmode === 'grid' ? 'active' : ''} onClick={() => setVmode('grid')}>Thẻ</button>
          </div>
        </div>
      </div>

      {vmode === 'table' ? (
        <div className="card">
          <div className="tbl-wrap">
            <table className="tbl">
              <thead><tr>
                {/* minWidth cho "Nhân viên" + width:1%/nowrap cho các cột phải:
                    các cột Hình thức/Trạng thái/Ngày vào co sát nội dung, nhường
                    khoảng trống cho cột "Nhân viên" rộng ra. */}
                <th style={{ minWidth: 280 }}>Nhân viên</th><th>Phòng ban</th><th>Chức danh</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Hình thức</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày vào</th>
                {data.isHrManager && <th className="tbl-num">Lương CB</th>}
                <th></th>
              </tr></thead>
              <tbody>
                {filtered.map((e) => (
                  <tr key={e.id} onClick={() => setSel(e)}>
                    <td>
                      <div className="cell-emp">
                        <Avatar emp={e} />
                        <div>
                          <div className="nm">{e.name}</div>
                          <div className="id">{e.code} · {e.jobTitle}</div>
                        </div>
                      </div>
                    </td>
                    <td><span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 3, background: (deps.find((d) => d.id === e.dep) || {}).color || 'var(--border-strong)' }}></span>
                      {e.depName}</span></td>
                    <td>{e.jobTitle}{e.posType && <span className="badge badge-gray" style={{ marginLeft: 6 }}>{e.posType}</span>}</td>
                    <td style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}><Badge kind={hbTypeKind(e.type)}>{e.type}</Badge></td>
                    <td style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}><Badge kind={hbStatusKind(e.statusKey)} dot>{e.status}</Badge></td>
                    <td className="muted mono" style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}>{fmtDate(e.start)}</td>
                    {data.isHrManager && <td className="tbl-num mono" style={{ fontWeight: 600 }}>{e.wage ? hbVND(e.wage) : '—'}</td>}
                    <td><button className="icon-btn" onClick={(ev) => { ev.stopPropagation(); setSel(e); }}><Icon name="chevR" size={18} className="faint" /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && <EmptyState>Không tìm thấy nhân viên phù hợp.</EmptyState>}
        </div>
      ) : (
        <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))' }}>
          {filtered.map((e) => (
            <div key={e.id} className="card" style={{ padding: 18, cursor: 'pointer' }} onClick={() => setSel(e)}>
              <div style={{ display: 'flex', gap: 13, alignItems: 'center' }}>
                <Avatar emp={e} size={48} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 700, fontSize: 14 }}>{e.name}</div>
                  <div className="muted" style={{ fontSize: 12 }}>{e.code} · {e.jobTitle}</div>
                </div>
              </div>
              <div className="divider" style={{ margin: '14px 0' }}></div>
              <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                <Badge kind={hbStatusKind(e.statusKey)} dot>{e.status}</Badge>
                <Badge kind={hbTypeKind(e.type)}>{e.type}</Badge>
                <Badge kind="gray">{e.depName}</Badge>
              </div>
            </div>
          ))}
          {filtered.length === 0 && <EmptyState>Không tìm thấy nhân viên phù hợp.</EmptyState>}
        </div>
      )}

      {sel && <EmployeeDrawer emp={sel} onClose={() => { setSel(null); load(); }} isHr={data.isHr} isMgr={data.isHrManager} />}
      {creating && (
        <EmployeeForm emp={null} isMgr={data.isHrManager}
          onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }} />
      )}
    </div>
  );
}
