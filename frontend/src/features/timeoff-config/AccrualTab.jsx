/* Khu Cấu hình → tab "Tích lũy": tạo/sửa/xoá kế hoạch tích lũy (accrual plan) + các mốc (level).
   SPA chỉ hỗ trợ tần suất Hằng ngày/Hàng tháng; các tần suất khác đặt qua backend.
   Chỉ Admin vào được (App.jsx gate me.isAdmin). */
import { useEffect, useState } from 'react';
import { fetchAccrualPlans, saveAccrualPlan, deleteAccrualPlan } from '../../api/timeoffConfig';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Modal from '../../components/Modal';
import Icon from '../../components/Icon';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

const EMPTY_LEVEL = {
  addedValue: 1, addedValueType: 'day', frequency: 'monthly',
  startType: 'day', startCount: 0, milestoneDate: 'creation',
  capAccruedTime: true, maximumLeave: 12,
  actionWithUnusedAccruals: 'all', carryoverOptions: 'limited', postponeMaxDays: 5,
};
const EMPTY_PLAN = {
  id: null, name: '', timeOffTypeId: false, accruedGainTime: 'start',
  canBeCarryover: true, carryoverMonth: '3', carryoverDay: '31',
  levels: [{ ...EMPTY_LEVEL }],
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

function Sel({ value, onChange, options }) {
  return (
    <select style={inp} value={value} onChange={onChange}>
      {options.map((o) => (
        <option key={o.value} value={o.value}>{o.label}</option>
      ))}
    </select>
  );
}

export default function AccrualTab() {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);        // lỗi tải danh sách → ErrorState toàn trang
  const [saveErr, setSaveErr] = useState(null); // lỗi lưu trong modal → chỉ hiện inline
  const [editing, setEditing] = useState(null); // object hoặc null
  const [saving, setSaving] = useState(false);

  const load = () => {
    setErr(null); setData(null);
    fetchAccrualPlans()
      .then((d) => setData(d))
      .catch((e) => setErr(e.message));
  };
  useEffect(load, []);

  const closeModal = () => { setEditing(null); setSaveErr(null); };

  const opt = (key) => (data.fieldOptions[key] || []);

  const setLevel = (idx, patch) => {
    setEditing({
      ...editing,
      levels: editing.levels.map((l, i) => (i === idx ? { ...l, ...patch } : l)),
    });
  };
  const addLevel = () => setEditing({ ...editing, levels: [...editing.levels, { ...EMPTY_LEVEL }] });
  const removeLevel = (idx) => {
    if (editing.levels.length <= 1) return; // backend yêu cầu ≥1 mốc
    setEditing({ ...editing, levels: editing.levels.filter((_, i) => i !== idx) });
  };

  const onSave = async () => {
    setSaving(true);
    setSaveErr(null);
    try {
      await saveAccrualPlan(editing);
      closeModal();
      load();
    } catch (e) {
      setSaveErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (p) => {
    if (!window.confirm(`Xoá kế hoạch "${p.name}"?`)) return;
    try {
      await deleteAccrualPlan(p.id);
      load();
    } catch (e) {
      window.alert(e.message);  // lỗi xoá (ngoài modal) → cảnh báo, không thay cả tab bằng ErrorState
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải kế hoạch tích lũy…" />;

  const rows = data.plans;

  return (
    <div className="content fade-in" style={{ padding: 0 }}>
      <div className="page-head">
        <div>
          <h1>Kế hoạch tích lũy</h1>
          <p>{rows.length} kế hoạch</p>
        </div>
        <div className="actions">
          <button className="btn btn-primary"
            onClick={() => { setSaveErr(null); setEditing({ ...EMPTY_PLAN, levels: [{ ...EMPTY_LEVEL }] }); }}>
            <Icon name="plus" size={16} />Thêm kế hoạch
          </button>
        </div>
      </div>

      <div className="card">
        <div className="tbl-wrap">
          <table className="tbl">
            <thead>
              <tr>
                <th>Tên</th>
                <th>Loại nghỉ</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>Số mốc</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}>NV áp dụng</th>
                <th style={{ width: '1%', whiteSpace: 'nowrap' }}></th>
              </tr>
            </thead>
            <tbody>
              {rows.map((p) => (
                <tr key={p.id}>
                  <td><div className="nm">{p.name}</div></td>
                  <td>{p.timeOffTypeName || '—'}</td>
                  <td className="mono" style={{ width: '1%', whiteSpace: 'nowrap' }}>{p.levels.length}</td>
                  <td className="mono" style={{ width: '1%', whiteSpace: 'nowrap' }}>{p.employeesCount}</td>
                  <td style={{ width: '1%', whiteSpace: 'nowrap' }}>
                    <button className="btn btn-ghost btn-sm" onClick={() => { setSaveErr(null); setEditing({ ...p, levels: p.levels.map((l) => ({ ...l })) }); }}>
                      <Icon name="edit" size={14} />Sửa</button>
                    <button className="btn btn-ghost btn-sm" onClick={() => onDelete(p)}>
                      <Icon name="trash" size={14} />Xoá</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có kế hoạch tích lũy nào.</EmptyState>}
      </div>

      {editing && (
        <Modal onClose={() => !saving && closeModal()}>
          <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
            <div style={{ width: 44, height: 44, borderRadius: 11, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
              <Icon name={editing.id ? 'edit' : 'plus'} size={20} />
            </div>
            <div style={{ flex: 1 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>{editing.id ? 'Sửa kế hoạch tích lũy' : 'Thêm kế hoạch tích lũy'}</h2>
            </div>
            <button className="icon-btn" onClick={() => !saving && closeModal()}><Icon name="x" size={20} /></button>
          </div>

          <div style={{ padding: '20px 24px', maxHeight: '70vh', overflowY: 'auto' }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
              <Field label="Tên kế hoạch *">
                <input style={inp} value={editing.name} autoComplete="off"
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
              </Field>
              <Field label="Loại nghỉ áp dụng">
                <select style={inp} value={editing.timeOffTypeId || ''}
                  onChange={(e) => setEditing({ ...editing, timeOffTypeId: Number(e.target.value) || false })}>
                  <option value="">— Chọn —</option>
                  {data.leaveTypeChoices.map((lt) => (
                    <option key={lt.id} value={lt.id}>{lt.name}</option>
                  ))}
                </select>
              </Field>
              <Field label="Thời điểm cộng dồn">
                <Sel value={editing.accruedGainTime} options={opt('accruedGainTime')}
                  onChange={(e) => setEditing({ ...editing, accruedGainTime: e.target.value })} />
              </Field>
            </div>

            <div style={{ marginTop: 16 }}>
              <Check checked={editing.canBeCarryover}
                onChange={(e) => setEditing({ ...editing, canBeCarryover: e.target.checked })}>
                Cho phép chuyển năm (carry-over)</Check>
              {editing.canBeCarryover && (
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px', marginTop: 10 }}>
                  <Field label="Tháng hết hạn">
                    <Sel value={String(editing.carryoverMonth)} options={opt('carryoverMonth')}
                      onChange={(e) => setEditing({ ...editing, carryoverMonth: e.target.value })} />
                  </Field>
                  <Field label="Ngày">
                    <input style={inp} type="number" min={1} max={31} value={editing.carryoverDay}
                      onChange={(e) => setEditing({ ...editing, carryoverDay: e.target.value })} />
                  </Field>
                </div>
              )}
            </div>

            <div style={{ marginTop: 16 }}>
              <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>Các mốc tích lũy</span>
              <div style={{ marginTop: 10 }}>
                {editing.levels.map((lv, idx) => (
                  <div key={idx} style={{ border: '1px solid var(--border)', borderRadius: 12, padding: 12, marginBottom: 10, background: 'var(--surface)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
                      <span style={{ fontSize: 13, fontWeight: 700, color: 'var(--ink)' }}>Mốc {idx + 1}</span>
                      <button className="btn btn-ghost btn-sm" disabled={editing.levels.length <= 1} onClick={() => removeLevel(idx)}>
                        <Icon name="trash" size={14} />Xoá mốc</button>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(150px,1fr))', gap: 10 }}>
                      <Field label="Cộng">
                        <input style={inp} type="number" step={0.5} min={0} value={lv.addedValue}
                          onChange={(e) => setLevel(idx, { addedValue: e.target.value === '' ? 0 : Number(e.target.value) })} />
                      </Field>
                      <Field label="Đơn vị">
                        <Sel value={lv.addedValueType} options={opt('addedValueType')}
                          onChange={(e) => setLevel(idx, { addedValueType: e.target.value })} />
                      </Field>
                      <Field label="Tần suất">
                        <Sel value={lv.frequency} options={opt('frequency')}
                          onChange={(e) => setLevel(idx, { frequency: e.target.value })} />
                      </Field>
                      <Field label="Loại mốc bắt đầu">
                        <Sel value={lv.startType} options={opt('startType')}
                          onChange={(e) => setLevel(idx, { startType: e.target.value })} />
                      </Field>
                      <Field label="Sau (số)">
                        <input style={inp} type="number" min={0} value={lv.startCount}
                          onChange={(e) => setLevel(idx, { startCount: e.target.value === '' ? 0 : Number(e.target.value) })} />
                      </Field>
                      <Field label="Thời điểm mốc">
                        <Sel value={lv.milestoneDate} options={opt('milestoneDate')}
                          onChange={(e) => setLevel(idx, { milestoneDate: e.target.value })} />
                      </Field>
                      <Field label="Khi hết hạn">
                        <Sel value={lv.actionWithUnusedAccruals} options={opt('actionWithUnusedAccruals')}
                          onChange={(e) => setLevel(idx, { actionWithUnusedAccruals: e.target.value })} />
                      </Field>
                      <Field label="Chuyển năm">
                        <Sel value={lv.carryoverOptions} options={opt('carryoverOptions')}
                          onChange={(e) => setLevel(idx, { carryoverOptions: e.target.value })} />
                      </Field>
                      {lv.carryoverOptions === 'limited' && (
                        <Field label="Tối đa chuyển (ngày)">
                          <input style={inp} type="number" min={0} value={lv.postponeMaxDays}
                            onChange={(e) => setLevel(idx, { postponeMaxDays: e.target.value === '' ? 0 : Number(e.target.value) })} />
                        </Field>
                      )}
                    </div>
                    <div style={{ marginTop: 10 }}>
                      <Check checked={lv.capAccruedTime}
                        onChange={(e) => setLevel(idx, { capAccruedTime: e.target.checked })}>
                        Trần tích lũy</Check>
                      {lv.capAccruedTime && (
                        <div style={{ marginTop: 10, maxWidth: 200 }}>
                          <Field label="Tối đa">
                            <input style={inp} type="number" step={0.5} min={0} value={lv.maximumLeave}
                              onChange={(e) => setLevel(idx, { maximumLeave: e.target.value === '' ? 0 : Number(e.target.value) })} />
                          </Field>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                <button className="btn btn-ghost btn-sm" onClick={addLevel}>
                  <Icon name="plus" size={14} />Thêm mốc</button>
              </div>
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
