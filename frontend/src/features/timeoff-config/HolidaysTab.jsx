/* Khu Cấu hình → tab "Ngày lễ": chọn NĂM rồi tạo/sửa/xoá ngày lễ trong năm đó.
   Mỗi thao tác (tạo/sửa/xoá) backend ghi đồng bộ 2 model: mandatory.day + calendar.leaves.
   Chỉ Admin vào được (App.jsx gate me.isAdmin). */
import { useEffect, useState } from 'react';
import { fetchHolidays, saveHoliday, deleteHoliday } from '../../api/timeoffConfig';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';

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

export default function HolidaysTab() {
  const [year, setYear] = useState(new Date().getFullYear());
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);        // lỗi tải danh sách → ErrorState toàn trang
  const [saveErr, setSaveErr] = useState(null); // lỗi lưu trong modal → chỉ hiện inline
  const [editing, setEditing] = useState(null); // object hoặc null
  const [saving, setSaving] = useState(false);

  const load = (y) => {
    setErr(null); setData(null);
    fetchHolidays(y)
      .then((d) => setData(d))
      .catch((e) => setErr(e.message));
  };
  useEffect(() => load(year), [year]);

  const closeModal = () => { setEditing(null); setSaveErr(null); };

  const onSave = async () => {
    setSaving(true);
    setSaveErr(null);
    try {
      await saveHoliday({
        id: editing.id || undefined,
        name: editing.name,
        startDate: editing.startDate,
        endDate: editing.endDate,
        color: editing.color,
      });
      closeModal();
      load(year);
    } catch (e) {
      setSaveErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (row) => {
    if (!window.confirm(`Xoá ngày lễ "${row.name}"?`)) return;
    try {
      await deleteHoliday(row.id);
      load(year);
    } catch (e) {
      window.alert(e.message);  // lỗi xoá (ngoài modal) → cảnh báo, không thay cả tab bằng ErrorState
    }
  };

  if (err) return <ErrorState message={err} onRetry={() => load(year)} />;
  if (!data) return <LoadingState label="Đang tải ngày lễ…" />;

  const rows = data.holidays;
  const yearOptions = Array.from(
    new Set([...(data.years || []), new Date().getFullYear(), new Date().getFullYear() + 1, year])
  ).sort((a, b) => a - b);

  return (
    <div className="content fade-in" style={{ padding: 0 }}>
      <div className="page-head">
        <div>
          <h1>Ngày lễ</h1>
          <p>{rows.length} ngày lễ trong năm {year}</p>
        </div>
        <div className="actions">
          <select style={{ ...inp, width: 'auto' }} value={year}
            onChange={(e) => setYear(Number(e.target.value))}>
            {yearOptions.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
          <button className="btn btn-primary"
            onClick={() => { setSaveErr(null); setEditing({ id: null, name: '', startDate: `${year}-01-01`, endDate: `${year}-01-01`, color: 1 }); }}>
            <Icon name="plus" size={16} />Thêm ngày lễ
          </button>
        </div>
      </div>

      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Tên</th>
                <th>Bắt đầu</th>
                <th>Kết thúc</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((h) => (
                <tr key={h.id}>
                  <td><div className="nm">{h.name}</div></td>
                  <td>{h.startDate}</td>
                  <td>{h.endDate}</td>
                  <td style={{ width: '1%', whiteSpace: 'nowrap' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => { setSaveErr(null); setEditing({ ...h }); }}>
                      <Icon name="edit" size={14} />Sửa</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => onDelete(h)}>
                      <Icon name="trash" size={14} />Xoá</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có ngày lễ nào trong năm {year}.</EmptyState>}
      </div>

      {editing && (
        <Modal onClose={() => !saving && closeModal()}>
          <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
            <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <Icon name={editing.id ? 'edit' : 'plus'} size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{editing.id ? 'Sửa ngày lễ' : 'Thêm ngày lễ'}</h2>
            </div>
            <button className="icon-btn" onClick={() => !saving && closeModal()}><Icon name="x" size={20} /></button>
          </div>

          <div style={{ padding: '20px 24px' }}>
            <Field label="Tên ngày lễ *">
              <input style={inp} value={editing.name} autoComplete="off"
                onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
            </Field>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px', marginTop: 14 }}>
              <Field label="Ngày bắt đầu">
                <input style={inp} type="date" value={editing.startDate}
                  onChange={(e) => setEditing({ ...editing, startDate: e.target.value })} />
              </Field>
              <Field label="Ngày kết thúc">
                <input style={inp} type="date" value={editing.endDate}
                  onChange={(e) => setEditing({ ...editing, endDate: e.target.value })} />
              </Field>
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
