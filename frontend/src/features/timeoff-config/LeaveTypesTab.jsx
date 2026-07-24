/* Khu Cấu hình → tab "Loại nghỉ": bảng + form tạo/sửa + bật/tắt.
   Chỉ Admin vào được (App.jsx gate me.isAdmin). */
import { useEffect, useState } from 'react';
import { fetchLeaveTypes, saveLeaveType, toggleLeaveType } from '../../api/timeoffConfig';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';

const VALIDATION_LABEL = {
  no_validation: 'Không cần duyệt',
  hr: 'HR Officer duyệt',
  manager: 'Quản lý duyệt',
  both: 'Quản lý + HR',
};
const EMPTY = {
  id: null, name: '', requiresAllocation: false, unpaid: false,
  validationType: 'hr', requestUnit: 'day', supportDocument: false,
  isEmergency: false, color: 0,
};

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

function Check({ checked, onChange, children }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13.5, cursor: 'pointer' }}>
      <input type="checkbox" checked={checked} onChange={onChange} />
      {children}
    </label>
  );
}

export default function LeaveTypesTab() {
  const [rows, setRows] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null); // object hoặc null
  const [saving, setSaving] = useState(false);

  const load = () => {
    setErr(null); setRows(null);
    fetchLeaveTypes()
      .then((d) => setRows(d.leaveTypes))
      .catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const onSave = async () => {
    setSaving(true);
    setErr(null);
    try {
      await saveLeaveType(editing);
      setEditing(null);
      load();
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const onToggle = async (row) => {
    try {
      await toggleLeaveType(row.id, !row.active);
      load();
    } catch (e) {
      window.alert(e.message);
    }
  };

  if (err && !editing) return <ErrorState message={err} onRetry={load} />;
  if (!rows) return <LoadingState label="Đang tải loại nghỉ…" />;

  return (
    <div className="content fade-in" style={{ padding: 0 }}>
      <div className="page-head">
        <div>
          <h1>Loại nghỉ phép</h1>
          <p>{rows.length} loại nghỉ do Học Bá quản lý</p>
        </div>
        <div className="actions">
          <button className="btn btn-primary" onClick={() => { setErr(null); setEditing({ ...EMPTY }); }}>
            <Icon name="plus" size={16} />Thêm loại nghỉ
          </button>
        </div>
      </div>

      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Tên</th><th>Trừ quỹ</th><th>Không lương</th>
                <th>Bậc duyệt</th><th>Nửa ngày</th><th>Chứng từ</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Đang dùng</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Trạng thái</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} style={{ opacity: r.active ? 1 : 0.55 }}>
                  <td><div className="nm">{r.name}</div></td>
                  <td>{r.requiresAllocation ? '✓' : '—'}</td>
                  <td>{r.unpaid ? '✓' : '—'}</td>
                  <td>{VALIDATION_LABEL[r.validationType] || r.validationType}</td>
                  <td>{r.requestUnit === 'half_day' ? '✓' : '—'}</td>
                  <td>{r.supportDocument ? '✓' : '—'}</td>
                  <td className="mono" style={{ width: '1%', whiteSpace: 'nowrap' }}>{r.inUseCount}</td>
                  <td style={{ width: '1%', whiteSpace: 'nowrap' }}>
                    <Badge kind={r.active ? 'green' : 'gray'} dot>{r.active ? 'Đang bật' : 'Đã tắt'}</Badge>
                  </td>
                  <td style={{ display: 'flex', gap: 6, width: '1%', whiteSpace: 'nowrap' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => { setErr(null); setEditing({ ...r }); }}>
                      <Icon name="edit" size={14} />Sửa</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => onToggle(r)}>
                      <Icon name={r.active ? 'trash' : 'rotateCcw'} size={14} />
                      {r.active ? 'Tắt' : 'Bật'}</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có loại nghỉ nào.</EmptyState>}
      </div>

      {editing && (
        <Modal onClose={() => !saving && setEditing(null)}>
          <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
            <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <Icon name={editing.id ? 'edit' : 'plus'} size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{editing.id ? 'Sửa loại nghỉ' : 'Thêm loại nghỉ'}</h2>
            </div>
            <button className="icon-btn" onClick={() => !saving && setEditing(null)}><Icon name="x" size={20} /></button>
          </div>

          <div style={{ padding: '20px 24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
              <Field label="Tên loại nghỉ *">
                <input style={inp} value={editing.name} autoComplete="off"
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
              </Field>
              <Field label="Bậc duyệt">
                <select style={inp} value={editing.validationType}
                  onChange={(e) => setEditing({ ...editing, validationType: e.target.value })}>
                  {Object.entries(VALIDATION_LABEL).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </Field>
              <Field label="Đơn vị nghỉ">
                <select style={inp} value={editing.requestUnit}
                  onChange={(e) => setEditing({ ...editing, requestUnit: e.target.value })}>
                  <option value="day">Cả ngày</option>
                  <option value="half_day">Cho phép nửa ngày</option>
                </select>
              </Field>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 16 }}>
              <Check checked={editing.requiresAllocation}
                onChange={(e) => setEditing({ ...editing, requiresAllocation: e.target.checked })}>
                Trừ vào quỹ phép</Check>
              <Check checked={editing.unpaid}
                onChange={(e) => setEditing({ ...editing, unpaid: e.target.checked })}>
                Nghỉ không lương</Check>
              <Check checked={editing.supportDocument}
                onChange={(e) => setEditing({ ...editing, supportDocument: e.target.checked })}>
                Yêu cầu chứng từ</Check>
              <Check checked={editing.isEmergency}
                onChange={(e) => setEditing({ ...editing, isEmergency: e.target.checked })}>
                Loại khẩn cấp (fast-track)</Check>
            </div>

            {err && (
              <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{err}</div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
            <button className="btn btn-ghost" disabled={saving} onClick={() => setEditing(null)}>Huỷ</button>
            <button className="btn btn-primary" disabled={saving} onClick={onSave}>
              <Icon name="checkCircle" size={16} />{saving ? 'Đang lưu…' : 'Lưu'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
