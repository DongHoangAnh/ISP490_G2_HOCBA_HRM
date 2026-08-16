/* Khu Cấu hình → tab "Loại nghỉ": bảng + form tạo/sửa + bật/tắt.
   Chỉ Admin vào được (App.jsx gate me.isAdmin). */
import { useEffect, useState } from 'react';
import { fetchLeaveTypes, saveLeaveType, toggleLeaveType } from '../../api/timeoffConfig';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';

/* Bậc duyệt = AI được duyệt đơn của loại nghỉ này (backend: _can_decide_leave
   trong hocba_timeoff/controllers/main.py). Dùng lại 3 giá trị của Odoo nhưng
   'both' ở Học Bá nghĩa là "một trong hai duyệt là đủ", KHÔNG phải duyệt hai
   bậc nối tiếp. */
const VALIDATION_LABEL = {
  no_validation: 'Không cần duyệt',
  hr: 'HR Manager duyệt',
  manager: 'Trưởng phòng duyệt',
  both: 'HR Manager / Trưởng phòng duyệt',
};
// Chỉ 3 bậc duyệt được chọn khi tạo/sửa. 'no_validation' là dữ liệu cũ: chỉ
// thêm vào danh sách khi loại nghỉ đang mở thực sự đang dùng giá trị đó.
const VALIDATION_CHOICES = ['hr', 'manager', 'both'];
const VALIDATION_HINT = {
  no_validation: 'Đơn được duyệt tự động, không cần ai xử lý.',
  hr: 'Chỉ HR Manager / Admin duyệt được. Trưởng phòng chỉ xem.',
  manager: 'Chỉ trưởng phòng của nhân viên duyệt được. HR Manager chỉ xem '
    + '(trừ khi phòng ban chưa gán trưởng phòng).',
  both: 'HR Manager hoặc trưởng phòng đều duyệt được — một trong hai xử lý là xong.',
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
  const [err, setErr] = useState(null);        // lỗi tải danh sách → ErrorState toàn trang
  const [saveErr, setSaveErr] = useState(null); // lỗi lưu trong modal → chỉ hiện inline
  const [editing, setEditing] = useState(null); // object hoặc null
  const [saving, setSaving] = useState(false);

  const load = () => {
    setErr(null); setRows(null);
    fetchLeaveTypes()
      .then((d) => setRows(d.leaveTypes))
      .catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const closeModal = () => { setEditing(null); setSaveErr(null); };

  const onSave = async () => {
    setSaving(true);
    setSaveErr(null);
    try {
      await saveLeaveType(editing);
      closeModal();
      load();
    } catch (e) {
      setSaveErr(e.message);
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

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!rows) return <LoadingState label="Đang tải loại nghỉ…" />;

  return (
    <div className="content fade-in" style={{ padding: 0 }}>
      <div className="page-head">
        <div>
          <h1>Loại nghỉ phép</h1>
          <p>{rows.length} loại nghỉ do Học Bá quản lý</p>
        </div>
        <div className="actions">
          <button className="btn btn-primary" onClick={() => { setSaveErr(null); setEditing({ ...EMPTY }); }}>
            <Icon name="plus" size={16} />Thêm loại nghỉ
          </button>
        </div>
      </div>

      <div className="card">
        <div className="tbl-wrap tbl-scroll">
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
                    <button className="btn btn-ghost btn-sm" onClick={() => { setSaveErr(null); setEditing({ ...r }); }}>
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
        <Modal onClose={() => !saving && closeModal()}>
          <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
            <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <Icon name={editing.id ? 'edit' : 'plus'} size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{editing.id ? 'Sửa loại nghỉ' : 'Thêm loại nghỉ'}</h2>
            </div>
            <button className="icon-btn" onClick={() => !saving && closeModal()}><Icon name="x" size={20} /></button>
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
                  {(VALIDATION_CHOICES.includes(editing.validationType)
                    ? VALIDATION_CHOICES
                    : [editing.validationType, ...VALIDATION_CHOICES]).map((v) => (
                      <option key={v} value={v}>{VALIDATION_LABEL[v] || v}</option>
                    ))}
                </select>
                <span className="muted" style={{ fontSize: 11.5, lineHeight: 1.45 }}>
                  {VALIDATION_HINT[editing.validationType] || ''}
                </span>
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

            {saveErr && (
              <div style={{ marginTop: 14, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>{saveErr}</div>
            )}
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
            <button className="btn btn-ghost" disabled={saving} onClick={closeModal}>Huỷ</button>
            <button className="btn btn-primary" disabled={saving} onClick={onSave}>
              <Icon name="checkCircle" size={16} />{saving ? 'Đang lưu…' : 'Lưu'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
