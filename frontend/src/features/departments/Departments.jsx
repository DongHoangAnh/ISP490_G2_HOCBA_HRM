/* ============================================================
   Trang quản lý Phòng ban (HR/Admin) — danh sách + tạo/sửa + lưu trữ.
   Owner: Tân.
   ============================================================ */
import { useState, useEffect } from 'react';
import { fetchDepartments, archiveDepartment } from '../../api/departments';
import DepartmentForm from './DepartmentForm';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import SortTh from '../../components/SortTh';
import useSort from '../../hooks/useSort';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';

const SORT_ACC = {
  name: (d) => d.name,
  functionDesc: (d) => d.functionDesc,
  managerName: (d) => d.managerName,
  employeeCount: (d) => d.employeeCount || 0,
  active: (d) => (d.active ? 0 : 1), // Hoạt động lên trước khi tăng dần
};

export default function Departments({ search = '' }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [showArchived, setShowArchived] = useState(false);
  const [form, setForm] = useState(null); // { dept } | { dept: null } | null
  // Khai báo trước các return sớm bên dưới — hook không được gọi có điều kiện.
  const sort = useSort(SORT_ACC, 'name');

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
  const rows = sort.apply(departments.filter((d) => !q
    || d.name.toLowerCase().includes(q)
    || (d.functionDesc || '').toLowerCase().includes(q)
    || (d.managerName || '').toLowerCase().includes(q)));

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
              <SortTh sk="name" sort={sort}>Phòng ban</SortTh>
              <SortTh sk="functionDesc" sort={sort}>Chức năng</SortTh>
              <SortTh sk="managerName" sort={sort}>Trưởng phòng</SortTh>
              {/* width:1% + nowrap: các cột phải co sát nội dung, dồn khoảng trống
                  cho 3 cột text bên trái → nút thao tác kéo về gần cột Trạng thái,
                  không bị đẩy khỏi khung. */}
              <SortTh sk="employeeCount" sort={sort} style={{ width: '1%', whiteSpace: 'nowrap' }}>Số NV</SortTh>
              <SortTh sk="active" sort={sort} style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</SortTh>
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
        {rows.length === 0 && <EmptyState>Chưa có phòng ban.</EmptyState>}
      </div>

      {form && (
        <DepartmentForm dept={form.dept} employees={employees}
          empTypes={data.empTypes || []} minPasswordLen={data.minPasswordLen || 8}
          onClose={() => setForm(null)}
          onDone={() => { setForm(null); load(); }} />
      )}
    </div>
  );
}
