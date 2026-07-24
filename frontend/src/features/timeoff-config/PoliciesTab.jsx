/* Khu Cấu hình → tab "Chính sách": bảng 6 chính sách theo loại NV + form sửa.
   Loại nhân viên (employmentLabel) là bất biến — chỉ sửa các trường còn lại.
   Chỉ Admin vào được (App.jsx gate me.isAdmin). */
import { useEffect, useState } from 'react';
import { fetchPolicies, savePolicy } from '../../api/timeoffConfig';
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

function Check({ checked, onChange, children }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13.5, cursor: 'pointer' }}>
      <input type="checkbox" checked={checked} onChange={onChange} />
      {children}
    </label>
  );
}

export default function PoliciesTab() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null); // object hoặc null
  const [saving, setSaving] = useState(false);

  const load = () => {
    setErr(null); setData(null);
    fetchPolicies()
      .then((d) => setData(d))
      .catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const allocLabel = (mode) => {
    const m = (data?.allocationModes || []).find((x) => x.value === mode);
    return m ? m.label : mode;
  };

  const toggleLeaveType = (id) => {
    const has = editing.leaveTypeIds.includes(id);
    setEditing({
      ...editing,
      leaveTypeIds: has
        ? editing.leaveTypeIds.filter((x) => x !== id)
        : [...editing.leaveTypeIds, id],
    });
  };

  const onSave = async () => {
    setSaving(true);
    setErr(null);
    try {
      await savePolicy({
        id: editing.id,
        name: editing.name,
        leaveTypeIds: editing.leaveTypeIds,
        allocationMode: editing.allocationMode,
        accrualPlanId: editing.accrualPlanId,
        annualDays: editing.annualDays,
        notes: editing.notes,
      });
      setEditing(null);
      load();
    } catch (e) {
      setErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  if (err && !editing) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải chính sách…" />;

  const rows = data.policies;

  return (
    <div className="content fade-in" style={{ padding: 0 }}>
      <div className="page-head">
        <div>
          <h1>Chính sách nghỉ phép</h1>
          <p>{rows.length} chính sách theo loại nhân viên</p>
        </div>
      </div>

      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Loại nhân viên</th>
                <th>Tên chính sách</th>
                <th>Phân bổ</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Ngày phép năm</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Số loại nghỉ</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>NV áp dụng</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id}>
                  <td><div className="nm">{r.employmentLabel}</div></td>
                  <td>{r.name}</td>
                  <td>{allocLabel(r.allocationMode)}</td>
                  <td className="mono" style={{ width: '1%', whiteSpace: 'nowrap' }}>{r.annualDays}</td>
                  <td className="mono" style={{ width: '1%', whiteSpace: 'nowrap' }}>{r.leaveTypeIds.length}</td>
                  <td className="mono" style={{ width: '1%', whiteSpace: 'nowrap' }}>{r.employeeCount}</td>
                  <td style={{ width: '1%', whiteSpace: 'nowrap' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => { setErr(null); setEditing({ ...r, leaveTypeIds: [...r.leaveTypeIds] }); }}>
                      <Icon name="edit" size={14} />Sửa</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có chính sách nào.</EmptyState>}
      </div>

      {editing && (
        <Modal onClose={() => !saving && setEditing(null)}>
          <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
            <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <Icon name="edit" size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Sửa chính sách</h2>
              <p style={{ margin: '2px 0 0', fontSize: 12.5, color: 'var(--muted)' }}>{editing.employmentLabel}</p>
            </div>
            <button className="icon-btn" onClick={() => !saving && setEditing(null)}><Icon name="x" size={20} /></button>
          </div>

          <div style={{ padding: '20px 24px' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
              <Field label="Tên chính sách *">
                <input style={inp} value={editing.name} autoComplete="off"
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
              </Field>
              <Field label="Chế độ phân bổ">
                <select style={inp} value={editing.allocationMode}
                  onChange={(e) => setEditing({ ...editing, allocationMode: e.target.value })}>
                  {(data.allocationModes || []).map((m) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </Field>
              <Field label="Kế hoạch tích lũy">
                <select style={inp} value={editing.accrualPlanId || ''}
                  onChange={(e) => setEditing({ ...editing, accrualPlanId: e.target.value ? Number(e.target.value) : false })}>
                  <option value="">— Không —</option>
                  {(data.accrualPlanChoices || []).map((p) => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </Field>
              <Field label="Số ngày phép năm">
                <input style={inp} type="number" min={0} step={0.5} value={editing.annualDays}
                  onChange={(e) => setEditing({ ...editing, annualDays: e.target.value === '' ? 0 : Number(e.target.value) })} />
              </Field>
            </div>

            <div style={{ marginTop: 16 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>Loại nghỉ được phép</span>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 10 }}>
                {(data.leaveTypeChoices || []).map((lt) => (
                  <Check key={lt.id}
                    checked={editing.leaveTypeIds.includes(lt.id)}
                    onChange={() => toggleLeaveType(lt.id)}>
                    {lt.name}</Check>
                ))}
              </div>
            </div>

            <div style={{ marginTop: 16 }}>
              <Field label="Ghi chú">
                <textarea style={{ ...inp, minHeight: 72, resize: 'vertical' }} value={editing.notes || ''}
                  onChange={(e) => setEditing({ ...editing, notes: e.target.value })} />
              </Field>
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
