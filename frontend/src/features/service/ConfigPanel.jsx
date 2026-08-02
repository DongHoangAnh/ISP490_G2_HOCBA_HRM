/* ============================================================
   Tab "Cấu hình" — danh mục loại yêu cầu + 2 ngưỡng ẩn danh. Owner: Nhật Anh.
   Spec §10 (P6). Chỉ hiện khi meta.canConfig (HR Manager / Admin) — BE vẫn
   chốt lại bằng _config_guard(), tab này chỉ là lớp che.
   ============================================================ */
import { useState, useEffect, useCallback } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import {
  fetchServiceConfig, saveRequestType, toggleRequestType, saveServiceParams,
} from '../../api/service';
import { RECIPIENT_LABEL, inp } from './svcMeta';

const EMPTY = {
  id: null, name: '', code: '', sequence: 50, defaultRecipient: 'hr',
  forceHrOnly: false, allowAnonymous: false, allowAttachment: true,
  hasRating: false, slaDays: 5, description: '',
};

function Field({ label, hint, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{
        fontSize: 11, fontWeight: 700, color: 'var(--muted)',
        textTransform: 'uppercase', letterSpacing: '.3px',
      }}>{label}</span>
      {children}
      {hint && <span className="muted" style={{ fontSize: 11.5 }}>{hint}</span>}
    </label>
  );
}

function Check({ checked, onChange, disabled, children }) {
  return (
    <label style={{
      display: 'flex', alignItems: 'center', gap: 8, fontSize: 13.5,
      cursor: disabled ? 'not-allowed' : 'pointer',
      opacity: disabled ? 0.55 : 1,
    }}>
      <input type="checkbox" checked={checked} disabled={disabled}
        onChange={onChange} />
      {children}
    </label>
  );
}

export default function ConfigPanel({ onChanged }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null);
  const [saveErr, setSaveErr] = useState(null);
  const [saving, setSaving] = useState(false);
  const [params, setParams] = useState(null);      // bản nháp 2 ngưỡng
  const [paramErr, setParamErr] = useState(null);
  const [paramOk, setParamOk] = useState(false);

  const apply = useCallback((d) => {
    setData(d);
    setParams({ ...d.params });
  }, []);

  /* Mọi lần LƯU thành công (khác lúc tải đầu) đều báo màn cha nạp lại meta —
     danh mục loại và 2 ngưỡng vừa đổi phải có hiệu lực ngay ở form gửi. */
  const applySaved = useCallback((d) => {
    apply(d);
    if (onChanged) onChanged();
  }, [apply, onChanged]);

  const load = useCallback(() => {
    setErr(null); setData(null);
    fetchServiceConfig().then(apply).catch((e) => setErr(e.message));
  }, [apply]);
  useEffect(() => { load(); }, [load]);

  const closeModal = () => { setEditing(null); setSaveErr(null); };

  const onSave = async () => {
    setSaving(true); setSaveErr(null);
    try {
      applySaved(await saveRequestType(editing));
      closeModal();
    } catch (e) {
      setSaveErr(e.message);
    } finally {
      setSaving(false);
    }
  };

  const onToggle = async (row) => {
    try {
      applySaved(await toggleRequestType(row.id, !row.active));
    } catch (e) {
      window.alert(e.message);
    }
  };

  const onSaveParams = async () => {
    setParamErr(null); setParamOk(false);
    try {
      applySaved(await saveServiceParams({
        minAnonDeptSize: Number(params.minAnonDeptSize),
        anonDailyLimit: Number(params.anonDailyLimit),
      }));
      setParamOk(true);
    } catch (e) {
      setParamErr(e.message);
    }
  };

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <TableSkeleton rows={5} />;

  const dirtyParams = params && (
    Number(params.minAnonDeptSize) !== data.params.minAnonDeptSize
    || Number(params.anonDailyLimit) !== data.params.anonDailyLimit);

  /* BR-SVC-09: hai ô này loại trừ nhau — khoá chéo ngay trên form thay vì để
     người dùng bấm Lưu rồi mới ăn lỗi từ @api.constrains. */
  const anonLocked = editing && editing.allowAttachment;
  const attachLocked = editing && editing.allowAnonymous;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <div className="card">
        <div className="card-head between">
          <h3>Loại yêu cầu ({data.types.length})</h3>
          <button className="btn btn-primary btn-sm"
            onClick={() => { setSaveErr(null); setEditing({ ...EMPTY }); }}>
            <Icon name="plus" size={15} />Thêm loại
          </button>
        </div>
        <div className="tbl-wrap tbl-scroll">
          <table className="tbl">
            <thead>
              <tr>
                <th>Tên loại</th>
                <th>Mã</th>
                <th>Người nhận</th>
                <th style={{ whiteSpace: 'nowrap' }}>SLA</th>
                <th>Tuỳ chọn</th>
                <th style={{ whiteSpace: 'nowrap' }}>Đã dùng</th>
                <th style={{ whiteSpace: 'nowrap' }}>Trạng thái</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {data.types.map((r) => (
                <tr key={r.id} style={{ opacity: r.active ? 1 : 0.55 }}>
                  <td>
                    <div className="nm">{r.name}</div>
                    {r.forceHrOnly && (
                      <div className="muted" style={{ fontSize: 11.5 }}>
                        Luôn về HR — trưởng phòng không đọc được
                      </div>
                    )}
                  </td>
                  <td className="mono" style={{ fontSize: 12 }}>{r.code}</td>
                  <td>{RECIPIENT_LABEL[r.defaultRecipient] || r.defaultRecipient}</td>
                  <td className="mono" style={{ whiteSpace: 'nowrap' }}>{r.slaDays} ngày</td>
                  {/* Gộp 3 cờ thành 1 cột: 3 cột dấu ✓ riêng đẩy nút Sửa/Tắt
                      ra ngoài vùng nhìn thấy ở màn 1440px. */}
                  <td>
                    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                      {r.allowAnonymous && <Badge kind="violet">Ẩn danh</Badge>}
                      {r.allowAttachment && <Badge kind="gray">Đính kèm</Badge>}
                      {r.hasRating && <Badge kind="amber">Chấm điểm</Badge>}
                      {!r.allowAnonymous && !r.allowAttachment && !r.hasRating && '—'}
                    </div>
                  </td>
                  <td className="mono" style={{ whiteSpace: 'nowrap' }}>
                    {r.usageCount} đơn
                    {r.openCount > 0 && (
                      <span className="muted"> · {r.openCount} đang mở</span>
                    )}
                  </td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    <Badge kind={r.active ? 'green' : 'gray'} dot>
                      {r.active ? 'Đang bật' : 'Đã tắt'}
                    </Badge>
                  </td>
                  <td style={{ display: 'flex', gap: 6, whiteSpace: 'nowrap' }}>
                    <button className="btn btn-ghost btn-sm"
                      onClick={() => { setSaveErr(null); setEditing({ ...r }); }}>
                      <Icon name="edit" size={14} />Sửa
                    </button>
                    <button className="btn btn-ghost btn-sm" onClick={() => onToggle(r)}>
                      <Icon name={r.active ? 'trash' : 'rotateCcw'} size={14} />
                      {r.active ? 'Tắt' : 'Bật'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {!data.types.length && <EmptyState>Chưa có loại yêu cầu nào.</EmptyState>}
      </div>

      <div className="card">
        <div className="card-head"><h3>Ngưỡng gửi ẩn danh</h3></div>
        <div style={{ padding: '4px 16px 18px' }}>
          <div style={{
            display: 'grid', gridTemplateColumns: 'repeat(auto-fit,minmax(240px,1fr))',
            gap: 16, maxWidth: 720,
          }}>
            <Field label="Số NV tối thiểu của phòng"
              hint="Phòng ít người hơn mức này thì không cho gửi ẩn danh tới trưởng phòng — tập nghi vấn quá nhỏ sẽ suy ra được người gửi.">
              <input style={inp} type="number" min="1" max="999"
                value={params.minAnonDeptSize}
                onChange={(e) => setParams({ ...params, minAnonDeptSize: e.target.value })} />
            </Field>
            <Field label="Số đơn ẩn danh / người / ngày"
              hint="Chống spam mà không cần lộ danh tính người gửi.">
              <input style={inp} type="number" min="1" max="999"
                value={params.anonDailyLimit}
                onChange={(e) => setParams({ ...params, anonDailyLimit: e.target.value })} />
            </Field>
          </div>

          {paramErr && (
            <div style={{
              marginTop: 14, padding: '10px 13px', background: 'var(--red-50)',
              border: '1px solid var(--red-100)', borderRadius: 10,
              color: 'var(--red-700)', fontSize: 12.5,
            }}>{paramErr}</div>
          )}

          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 16 }}>
            <button className="btn btn-primary" disabled={!dirtyParams}
              onClick={onSaveParams}>
              <Icon name="checkCircle" size={16} />Lưu ngưỡng
            </button>
            {paramOk && !dirtyParams && (
              <span className="muted" style={{ fontSize: 12.5 }}>Đã lưu.</span>
            )}
          </div>
        </div>
      </div>

      {editing && (
        <Modal onClose={() => !saving && closeModal()}>
          <div className="drawer-head">
            <div style={{ flex: 1 }}>
              <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>
                {editing.id ? 'Sửa loại yêu cầu' : 'Thêm loại yêu cầu'}
              </h2>
            </div>
            <button className="icon-btn" onClick={() => !saving && closeModal()}>
              <Icon name="x" size={20} />
            </button>
          </div>

          <div style={{ padding: '20px 24px' }}>
            <div style={{
              display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px',
            }}>
              <Field label="Tên loại *">
                <input style={inp} value={editing.name} autoComplete="off"
                  onChange={(e) => setEditing({ ...editing, name: e.target.value })} />
              </Field>
              <Field label="Mã *" hint="Chữ thường không dấu, số, gạch dưới.">
                <input style={inp} value={editing.code} autoComplete="off"
                  onChange={(e) => setEditing({ ...editing, code: e.target.value })} />
              </Field>
              <Field label="Người nhận mặc định">
                <select style={inp} value={editing.defaultRecipient}
                  onChange={(e) => setEditing({ ...editing, defaultRecipient: e.target.value })}>
                  {Object.entries(RECIPIENT_LABEL).map(([v, l]) => (
                    <option key={v} value={v}>{l}</option>
                  ))}
                </select>
              </Field>
              <Field label="SLA (ngày) *"
                hint="Chỉ áp cho đơn gửi TỪ BÂY GIỜ — đơn đang chạy giữ hạn cũ.">
                <input style={inp} type="number" min="1" value={editing.slaDays}
                  onChange={(e) => setEditing({ ...editing, slaDays: e.target.value })} />
              </Field>
              <Field label="Thứ tự hiển thị">
                <input style={inp} type="number" value={editing.sequence}
                  onChange={(e) => setEditing({ ...editing, sequence: e.target.value })} />
              </Field>
            </div>

            <div style={{ marginTop: 14 }}>
              <Field label="Hướng dẫn cho người gửi">
                <textarea style={{ ...inp, minHeight: 70, resize: 'vertical' }}
                  value={editing.description || ''}
                  onChange={(e) => setEditing({ ...editing, description: e.target.value })} />
              </Field>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 16 }}>
              <Check checked={editing.forceHrOnly}
                onChange={(e) => setEditing({
                  ...editing, forceHrOnly: e.target.checked,
                  // BR-SVC-01: loại HR-only mà mặc định gửi TP là mâu thuẫn.
                  defaultRecipient: e.target.checked ? 'hr' : editing.defaultRecipient,
                })}>
                Luôn gửi HR (khiếu nại về quản lý — trưởng phòng không đọc được)
              </Check>
              <Check checked={editing.allowAnonymous} disabled={anonLocked}
                onChange={(e) => setEditing({ ...editing, allowAnonymous: e.target.checked })}>
                Cho gửi ẩn danh
                {anonLocked && ' — tắt "cho đính kèm" trước (tệp đính kèm ghi lại người tạo)'}
              </Check>
              <Check checked={editing.allowAttachment} disabled={attachLocked}
                onChange={(e) => setEditing({ ...editing, allowAttachment: e.target.checked })}>
                Cho đính kèm tệp
                {attachLocked && ' — loại ẩn danh không được đính kèm'}
              </Check>
              <Check checked={editing.hasRating}
                onChange={(e) => setEditing({ ...editing, hasRating: e.target.checked })}>
                Có chấm điểm 1–5 sao
              </Check>
            </div>

            {saveErr && (
              <div style={{
                marginTop: 14, padding: '10px 13px', background: 'var(--red-50)',
                border: '1px solid var(--red-100)', borderRadius: 10,
                color: 'var(--red-700)', fontSize: 12.5,
              }}>{saveErr}</div>
            )}
          </div>

          <div style={{
            display: 'flex', justifyContent: 'flex-end', gap: 10,
            padding: '14px 24px', borderTop: '1px solid var(--border)',
          }}>
            <button className="btn btn-ghost" disabled={saving} onClick={closeModal}>
              Huỷ
            </button>
            <button className="btn btn-primary" disabled={saving} onClick={onSave}>
              <Icon name="checkCircle" size={16} />{saving ? 'Đang lưu…' : 'Lưu'}
            </button>
          </div>
        </Modal>
      )}
    </div>
  );
}
