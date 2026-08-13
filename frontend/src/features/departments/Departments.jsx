/* ============================================================
   Trang quản lý Phòng ban (HR/Admin) — danh sách + tạo/sửa + lưu trữ.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchDepartments, archiveDepartment } from '../../api/departments';
import DepartmentForm from './DepartmentForm';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { useSort, SortTh } from '../../components/sortable';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

export default function Departments({ search = '' }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [form, setForm] = useState(null); // { dept } | { dept: null } | null
  const sort = useSort();
  const [fState, setFState] = useState('all');    // all | active | archived
  const [fMgr, setFMgr] = useState('all');        // tên trưởng phòng
  const [fNoMgr, setFNoMgr] = useState(false);    // chưa gán trưởng phòng
  const [fEmpty, setFEmpty] = useState(false);    // chưa có nhân viên nào

  const load = () => {
    setErr(null); setData(null);
    fetchDepartments(showArchived).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [showArchived]); // eslint-disable-line react-hooks/exhaustive-deps

  const onArchive = async (d) => {
    const next = !d.active;
    if (next === false && d.employeeCount > 0
        && !window.confirm(`Phòng "${d.name}" còn ${d.employeeCount} nhân viên. Vẫn lưu trữ?`)) return;
    try {
      await archiveDepartment(d.id, next);
      load();
    } catch (e) { window.alert(e.message); }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải phòng ban…" />;

  const { departments, employees } = data;
  const q = search.trim().toLowerCase();
  const searched = departments.filter((d) => !q
    || d.name.toLowerCase().includes(q)
    || (d.functionDesc || '').toLowerCase().includes(q)
    || (d.managerName || '').toLowerCase().includes(q));

  /* Chip "Lưu trữ" chỉ có nghĩa khi ô "Hiện phòng đã lưu trữ" đang bật — nếu
     tắt thì API không trả phòng lưu trữ, chip sẽ luôn 0 nên ẩn luôn. */
  const cntActive = searched.filter((d) => d.active).length;
  const cntArchived = searched.length - cntActive;
  const noMgrCount = searched.filter((d) => !d.managerName).length;
  const emptyCount = searched.filter((d) => !d.employeeCount).length;
  const mgrOptions = [...new Set(searched.map((d) => d.managerName).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'vi'));

  const filtered = searched.filter((d) => {
    if (fState === 'active' && !d.active) return false;
    if (fState === 'archived' && d.active) return false;
    if (fMgr !== 'all' && d.managerName !== fMgr) return false;
    if (fNoMgr && d.managerName) return false;
    if (fEmpty && d.employeeCount) return false;
    return true;
  });
  const hasFilter = fState !== 'all' || fMgr !== 'all' || fNoMgr || fEmpty;
  const clearFilter = () => { setFState('all'); setFMgr('all'); setFNoMgr(false); setFEmpty(false); };

  const rows = sort.apply(filtered, {
    name: (d) => d.name,
    func: (d) => d.functionDesc,
    mgr: (d) => d.managerName,
    count: (d) => d.employeeCount || 0,
    state: (d) => (d.active ? 0 : 1),
  });

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Phòng ban</h1>
          <p>{departments.length} phòng ban</p>
        </div>
        <button className="btn btn-primary" onClick={() => setForm({ dept: null })}>
          <Icon name="plus" size={16} />Thêm phòng ban
        </button>
      </div>

      <div className="filterbar">
        <button className={'chip' + (fState === 'all' ? ' active' : '')}
          onClick={() => setFState('all')}>
          Tất cả <span className="ct">{searched.length}</span></button>
        <button className={'chip' + (fState === 'active' ? ' active' : '')}
          onClick={() => setFState('active')}>
          Hoạt động <span className="ct">{cntActive}</span></button>
        {cntArchived > 0 && (
          <button className={'chip' + (fState === 'archived' ? ' active' : '')}
            onClick={() => setFState('archived')}>
            Lưu trữ <span className="ct">{cntArchived}</span></button>
        )}
        <button className={'chip' + (fNoMgr ? ' active' : '')}
          title="Phòng chưa gán trưởng phòng"
          onClick={() => setFNoMgr((v) => !v)}>
          Chưa có trưởng phòng <span className="ct">{noMgrCount}</span></button>
        <button className={'chip' + (fEmpty ? ' active' : '')}
          title="Phòng chưa có nhân viên nào"
          onClick={() => setFEmpty((v) => !v)}>
          Chưa có nhân viên <span className="ct">{emptyCount}</span></button>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 9, alignItems: 'center' }}>
          <select className="sel" value={fMgr} onChange={(e) => setFMgr(e.target.value)}>
            <option value="all">Mọi trưởng phòng</option>
            {mgrOptions.map((m) => <option key={m}>{m}</option>)}
          </select>
          {hasFilter && (
            <button className="btn btn-ghost btn-sm" onClick={clearFilter}>Xoá lọc</button>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Danh sách phòng ban</h3>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 12.5, cursor: 'pointer' }}>
            <input type="checkbox" checked={showArchived}
              onChange={(e) => setShowArchived(e.target.checked)} />
            Hiện phòng đã lưu trữ
          </label>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <SortTh sort={sort} k="name">Phòng ban</SortTh>
              <SortTh sort={sort} k="func">Chức năng</SortTh>
              <SortTh sort={sort} k="mgr">Trưởng phòng</SortTh>
              {/* width:1% + nowrap: các cột phải co sát nội dung, dồn khoảng trống
                  cho 3 cột text bên trái → nút thao tác kéo về gần cột Trạng thái,
                  không bị đẩy khỏi khung. */}
              <SortTh sort={sort} k="count" style={{ width: '1%', whiteSpace: 'nowrap' }}>Số NV</SortTh>
              <SortTh sort={sort} k="state" style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</SortTh>
              <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
            </tr></thead>
            <tbody>
              {rows.map((d) => (
                <tr key={d.id}>
                  <td><div className="nm">{d.name}</div></td>
                  <td className="muted">{d.functionDesc || '—'}</td>
                  <td>{d.managerName || '—'}</td>
                  <td className="mono" style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}>{d.employeeCount}</td>
                  <td style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}><Badge kind={d.active ? 'green' : 'gray'} dot>{d.active ? 'Hoạt động' : 'Lưu trữ'}</Badge></td>
                  <td style={{ display: 'flex', gap: 6, width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => setForm({ dept: d })}>
                      <Icon name="edit" size={14} />Sửa</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => onArchive(d)}>
                      <Icon name={d.active ? 'trash' : 'rotateCcw'} size={14} />
                      {d.active ? 'Lưu trữ' : 'Khôi phục'}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && (
          <EmptyState>
            {hasFilter || q ? 'Không có phòng ban nào khớp bộ lọc hiện tại.'
              : 'Chưa có phòng ban.'}
          </EmptyState>
        )}
      </div>

      {form && (
        <DepartmentForm dept={form.dept} employees={employees}
          onClose={() => setForm(null)}
          onDone={() => { setForm(null); load(); }} />
      )}
    </div>
  );
}
