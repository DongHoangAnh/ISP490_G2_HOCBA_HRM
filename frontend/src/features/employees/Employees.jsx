/* ============================================================
   Màn Nhân viên — MẪU CHUẨN cho cả team (dữ liệu thật từ
   hocba_employees qua /hocba-hrm/api/*). Owner: Tân.
   ============================================================ */
import { useState, useEffect, useRef } from 'react';
import { fetchEmployees } from '../../api/employees';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Avatar from '../../components/Avatar';
import Pagination from '../../components/Pagination';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate, hbVND, hbStatusKind, hbTypeKind, hbEmpTypeKind } from '../../utils/format';
import EmployeeDrawer from './EmployeeDrawer';
import EmployeeForm from './EmployeeForm';
import ImportEmployeesModal from './ImportEmployeesModal';

const PAGE_SIZE = 20;

/* Tag loại nhân sự — hiện cả khi hồ sơ chưa gán để HR thấy mà bổ sung, thay
   vì để ô trống trông như lỗi hiển thị. */
function EmpTypeTag({ e }) {
  if (!e.empType) return <span className="badge badge-gray">Chưa phân loại</span>;
  return <Badge kind={hbEmpTypeKind(e.empTypeKey)}>{e.empType}</Badge>;
}

/* "Nhân viên văn phòng" = mọi NV KHÔNG thuộc phòng giảng dạy. Nhận diện phòng
   giảng dạy theo tên (bỏ dấu) vì hr.department không có cờ riêng cho việc này;
   dữ liệu thật đang dùng tên "Giảng viên". Đổi tên phòng → sửa danh sách dưới. */
const noAccent = (s) => (s || '').normalize('NFD')
  .replace(/[̀-ͯ]/g, '').replace(/[đĐ]/g, 'd').toLowerCase();
const TEACHER_DEP_WORDS = ['giang vien', 'giao vien'];
const isTeacherDep = (name) => {
  const n = noAccent(name);
  return TEACHER_DEP_WORDS.some((w) => n.includes(w));
};

export default function Employees({ search, focus, onOpenCareer }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [dep, setDep] = useState('all');
  const [status, setStatus] = useState('all');
  const [type, setType] = useState('all');
  const [empType, setEmpType] = useState('all');
  const [sel, setSel] = useState(null);
  const [vmode, setVmode] = useState('table');
  const [creating, setCreating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [page, setPage] = useState(1);
  // Đóng drawer khi CHỈ XEM → không tải lại; chỉ khi có sửa mới refresh ngầm.
  const dirtyRef = useRef(false);

  const load = () => {
    setErr(null); setData(null);
    fetchEmployees().then(setData).catch((e) => setErr(e.message));
  };
  // Làm mới ngầm: không xoá data hiện có → không chớp màn "Đang tải…".
  const reloadQuiet = () => {
    fetchEmployees().then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, []);
  // Đổi bộ lọc / từ khoá → quay về trang 1.
  useEffect(() => { setPage(1); }, [dep, status, type, empType, search]);

  /* Bấm thông báo ở chuông (vd "Cần hoàn thiện hồ sơ" sau khi Onboard) → mở
     thẳng drawer hồ sơ đó. Phải gỡ bộ lọc đang bật: hồ sơ cần mở có thể không
     nằm trong tập đang lọc, khi đó đóng drawer ra là màn hình trống trơn, người
     dùng tưởng hỏng. nonce để bấm lại cùng một thông báo vẫn mở lại được. */
  const focusId = focus && focus.requestId;
  const focusNonce = focus && focus.nonce;
  useEffect(() => {
    if (!focusId || !data) return;
    const emp = data.employees.find((e) => e.id === focusId);
    if (!emp) return;
    setDep('all'); setStatus('all'); setType('all'); setEmpType('all');
    setSel(emp);
  }, [focusId, focusNonce, data]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải dữ liệu nhân sự…" />;

  const emps = data.employees, deps = data.departments;
  const statusOptions = [...new Map(emps.map((e) => [e.statusKey, e.status])).entries()];
  const typeOptions = [...new Set(emps.map((e) => e.type))].filter((t) => t && t !== '—');
  // Tag loại nhân sự có trong tập đang xem + luôn có mục lọc hồ sơ chưa gán tag.
  const empTypeOptions = [...new Map(
    emps.filter((e) => e.empTypeKey).map((e) => [e.empTypeKey, e.empType])).entries()];
  const hasUntagged = emps.some((e) => !e.empTypeKey);

  /* Thứ tự chip: Tất cả → phòng giảng dạy → khối văn phòng → các phòng còn lại.
     Hai khối lớn (giảng viên / văn phòng) đứng trước vì HR lọc theo chúng nhiều
     nhất; phòng ban chi tiết xếp sau. */
  const teacherDeps = deps.filter((d) => isTeacherDep(d.name));
  const otherDeps = deps.filter((d) => !isTeacherDep(d.name));
  const teacherDepIds = new Set(teacherDeps.map((d) => d.id));

  /* Một hàm lọc duy nhất cho cả bảng lẫn số trên chip, cho phép ghi đè từng
     tiêu chí: số trên chip phải là "bấm chip này thì thấy bao nhiêu dòng", tức
     đếm theo các bộ lọc CÒN LẠI đang bật. Trước đây chip phòng ban lấy thẳng
     d.total của server nên không nhúc nhích theo ô tìm kiếm lẫn 3 select bên
     phải — gõ tìm kiếm xong chip vẫn ghi số cũ. */
  const keep = (e, o = {}) => {
    const d = 'dep' in o ? o.dep : dep;
    const st = 'status' in o ? o.status : status;
    const tp = 'type' in o ? o.type : type;
    const et = 'empType' in o ? o.empType : empType;
    if (d === 'office') { if (teacherDepIds.has(e.dep)) return false; }
    else if (d !== 'all' && e.dep !== d) return false;
    if (st !== 'all' && e.statusKey !== st) return false;
    if (tp !== 'all' && e.type !== tp) return false;
    if (et === 'none' && e.empTypeKey) return false;
    if (et !== 'all' && et !== 'none' && e.empTypeKey !== et) return false;
    if (search) {
      const q = search.toLowerCase();
      if (!((e.name || '').toLowerCase().includes(q) || (e.code || '').toLowerCase().includes(q)
        || (e.jobTitle || '').toLowerCase().includes(q) || (e.depName || '').toLowerCase().includes(q))) return false;
    }
    return true;
  };
  const countIf = (o) => emps.filter((e) => keep(e, o)).length;

  const cntAll = countIf({ dep: 'all' });
  const officeCount = countIf({ dep: 'office' });
  const depCount = (id) => countIf({ dep: id });
  /* Ẩn chip phòng ban không còn ai sau bộ lọc/tìm kiếm — chip ghi 0 bấm vào chỉ
     ra bảng rỗng. Vẫn giữ chip đang được chọn để người dùng thấy đường tắt nó. */
  const showDep = (d) => depCount(d.id) > 0 || dep === d.id;

  const filtered = emps.filter((e) => keep(e));

  const total = filtered.length;
  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const curPage = Math.min(page, pageCount);
  const pageRows = filtered.slice((curPage - 1) * PAGE_SIZE, curPage * PAGE_SIZE);

  return (
    <div className="content fade-in">
      <div className="page-head">
        <div>
          <h1>Nhân viên</h1>
          <p>{emps.length} nhân sự · {deps.length} phòng ban · dữ liệu trực tiếp từ Odoo</p>
        </div>
        <div className="actions">
          {data.canImport && (
            <button className="btn btn-ghost" onClick={() => setImporting(true)}
              title="Nhập hàng loạt hồ sơ nhân sự cũ từ file Excel">
              <Icon name="upload" size={16} />Nhập từ Excel</button>
          )}
          {data.canEditEmp && (
            <button className="btn btn-primary" onClick={() => setCreating(true)}>
              <Icon name="plus" size={16} />Thêm nhân viên</button>
          )}
        </div>
      </div>

      {/* Filter chips theo phòng ban (số liệu thật) */}
      <div className="filterbar">
        <button className={'chip' + (dep === 'all' ? ' active' : '')} onClick={() => setDep('all')}>
          Tất cả <span className="ct">{cntAll}</span></button>
        {teacherDeps.filter(showDep).map((d) => (
          <button key={d.id} className={'chip' + (dep === d.id ? ' active' : '')} onClick={() => setDep(d.id)}>
            {d.name} <span className="ct">{depCount(d.id)}</span></button>
        ))}
        {teacherDeps.length > 0 && (officeCount > 0 || dep === 'office') && (
          <button className={'chip' + (dep === 'office' ? ' active' : '')}
            title="Nhân sự ở mọi phòng ban trừ phòng giảng dạy"
            onClick={() => setDep('office')}>
            Nhân viên văn phòng <span className="ct">{officeCount}</span></button>
        )}
        {otherDeps.filter(showDep).map((d) => (
          <button key={d.id} className={'chip' + (dep === d.id ? ' active' : '')} onClick={() => setDep(d.id)}>
            {d.name} <span className="ct">{depCount(d.id)}</span></button>
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
          <select className="sel" value={empType} onChange={(e) => setEmpType(e.target.value)}>
            <option value="all">Mọi loại nhân sự</option>
            {empTypeOptions.map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            {hasUntagged && <option value="none">Chưa phân loại</option>}
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
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Loại nhân sự</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Hình thức</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày vào</th>
                {data.canSeeSalary && <th className="tbl-num">Lương CB</th>}
                <th></th>
              </tr></thead>
              <tbody>
                {pageRows.map((e) => (
                  <tr key={e.id} onClick={() => setSel(e)}>
                    <td>
                      <div className="cell-emp">
                        <Avatar emp={e} />
                        <div>
                          <div className="nm">
                            {e.name}
                            {e.missingDocs && (
                              <span title={'Cần hoàn thiện hồ sơ — thiếu ' + e.missingDocs}
                                style={{ marginLeft: 6, color: 'var(--amber-600, #b45309)', verticalAlign: '-2px' }}>
                                <Icon name="alertTriangle" size={14} />
                              </span>
                            )}
                          </div>
                          <div className="id">{e.code} · {e.jobTitle}</div>
                        </div>
                      </div>
                    </td>
                    <td><span style={{ display: 'inline-flex', alignItems: 'center', gap: 7 }}>
                      <span style={{ width: 8, height: 8, borderRadius: 3, background: (deps.find((d) => d.id === e.dep) || {}).color || 'var(--border-strong)' }}></span>
                      {e.depName}</span></td>
                    <td>{e.jobTitle}{e.posType && <span className="badge badge-gray" style={{ marginLeft: 6 }}>{e.posType}</span>}</td>
                    <td style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}><EmpTypeTag e={e} /></td>
                    <td style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}><Badge kind={hbTypeKind(e.type)}>{e.type}</Badge></td>
                    <td style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}><Badge kind={hbStatusKind(e.statusKey)} dot>{e.status}</Badge></td>
                    <td className="muted mono" style={{ width: '1%', whiteSpace: 'nowrap', overflow: 'visible', maxWidth: 'none' }}>{fmtDate(e.start)}</td>
                    {data.canSeeSalary && <td className="tbl-num mono" style={{ fontWeight: 600 }}>{e.wage ? hbVND(e.wage) : '—'}</td>}
                    <td><button className="icon-btn" onClick={(ev) => { ev.stopPropagation(); setSel(e); }}><Icon name="chevR" size={18} className="faint" /></button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {filtered.length === 0 && <EmptyState>Không tìm thấy nhân viên phù hợp.</EmptyState>}
          <Pagination page={curPage} pageCount={pageCount} total={total} pageSize={PAGE_SIZE} onPage={setPage} />
        </div>
      ) : (
        <>
        <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))' }}>
          {pageRows.map((e) => (
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
                <EmpTypeTag e={e} />
                <Badge kind={hbTypeKind(e.type)}>{e.type}</Badge>
                <Badge kind="gray">{e.depName}</Badge>
              </div>
            </div>
          ))}
          {filtered.length === 0 && <EmptyState>Không tìm thấy nhân viên phù hợp.</EmptyState>}
        </div>
        <Pagination page={curPage} pageCount={pageCount} total={total} pageSize={PAGE_SIZE} onPage={setPage} />
        </>
      )}

      {sel && <EmployeeDrawer emp={sel}
        onClose={() => { setSel(null); if (dirtyRef.current) { dirtyRef.current = false; reloadQuiet(); } }}
        onChanged={() => { dirtyRef.current = true; }}
        canEdit={data.canEditEmp} canManageAccount={data.canManageAccount}
        isMgr={data.isHrManager} canSeeSalary={data.canSeeSalary}
        onOpenCareer={onOpenCareer} />}
      {creating && (
        <EmployeeForm emp={null} isMgr={data.isHrManager}
          onClose={() => setCreating(false)}
          onSaved={() => { setCreating(false); load(); }} />
      )}
      {importing && (
        <ImportEmployeesModal
          onClose={() => setImporting(false)}
          onDone={() => { setImporting(false); load(); }} />
      )}
    </div>
  );
}
