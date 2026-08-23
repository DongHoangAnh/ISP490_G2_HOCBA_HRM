/* Tab "Hợp đồng" trong hồ sơ nhân viên — các lần ký của một người.
   Cột bám sheet "2.5. Theo dõi ký hợp đồng" của khách.
   Chỉ hiện với vai trò được xem lương; sửa được khi vai trò đó cũng quản lý
   được hồ sơ (HR Manager/Admin toàn bộ, Trưởng phòng & Giáo vụ trong phạm vi).
   Owner: Việt. */
import { useState } from 'react';
import { deleteContract } from '../../api/employees';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { EmptyState } from '../../components/states';
import { fmtDate, hbVND } from '../../utils/format';
import ContractForm from './ContractForm';

const STATE_KIND = {
  open: 'green', draft: 'gray', close: 'gray', cancel: 'red',
};

/* Cảnh báo khi nhân viên đã chính thức mà hồ sơ chưa có hợp đồng nào — đúng
   trường hợp làm HB.03/HB.357 biến mất khỏi bảng lương tháng 8. */
function NoContractWarning({ official, onAdd }) {
  if (!official) return <EmptyState>Chưa có hợp đồng nào.</EmptyState>;
  return (
    <div className="card" style={{
      padding: '14px 16px', display: 'flex', gap: 11, alignItems: 'flex-start',
      borderLeft: '3px solid var(--red-600)',
    }}>
      <Icon name="alertTriangle" size={18} />
      <div style={{ fontSize: 13.5, lineHeight: 1.6, flex: 1 }}>
        <b>Nhân viên đã chính thức nhưng chưa có hợp đồng.</b><br />
        Bảng tính lương lọc theo hợp đồng đang hiệu lực, nên người này sẽ không
        xuất hiện trong kỳ lương nào cho tới khi hợp đồng được tạo.
      </div>
      {onAdd && (
        <button className="btn btn-primary btn-sm" onClick={onAdd}>
          <Icon name="plus" size={13} />Tạo hợp đồng
        </button>
      )}
    </div>
  );
}

export default function ContractsTab({ det, onUpdated }) {
  const [form, setForm] = useState(null); // null | {mode, contract}
  const [busy, setBusy] = useState(0);
  const rows = det.contracts || [];
  const official = det.statusKey === 'official';
  const current = rows.find((r) => r.state === 'open');
  const canEdit = det.canEditContract && onUpdated;

  const remove = async (c) => {
    if (!window.confirm(`Xoá hợp đồng "${c.name}" khỏi hồ sơ ${det.name}?`)) return;
    setBusy(c.id);
    try { onUpdated(await deleteContract(c.id)); }
    catch (e) { alert(e.message); }
    finally { setBusy(0); }
  };

  return (
    <div>
      <div className="between" style={{ marginBottom: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 13 }}>
          Hợp đồng đã ký ({rows.length})
          {current && (
            <span className="muted" style={{ fontWeight: 500, marginLeft: 8 }}>
              · đang hiệu lực {hbVND(current.wage)} ₫
              {current.insuranceBase
                ? `, đóng BHXH trên ${hbVND(current.insuranceBase)} ₫` : ''}
            </span>
          )}
        </div>
        {canEdit && (
          <div style={{ display: 'flex', gap: 8 }}>
            {current && (
              <button className="btn btn-soft btn-sm"
                onClick={() => setForm({ mode: 'renew', contract: current })}>
                <Icon name="rotateCcw" size={13} />Tái ký
              </button>
            )}
            <button className="btn btn-soft btn-sm"
              onClick={() => setForm({ mode: 'create' })}>
              <Icon name="plus" size={13} />Thêm hợp đồng
            </button>
          </div>
        )}
      </div>

      {!rows.length ? (
        <NoContractWarning official={official}
          onAdd={canEdit ? () => setForm({ mode: 'create' }) : null} />
      ) : (
        <div className="card" style={{ padding: 0 }}>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 54 }}>Lần ký</th>
                <th>Loại hợp đồng</th>
                <th>Ngày ký</th>
                <th>Hiệu lực</th>
                <th>Hết hạn</th>
                <th style={{ textAlign: 'right' }}>Lương cơ bản</th>
                <th style={{ textAlign: 'right' }}>Lương đóng BH</th>
                <th>Trạng thái</th>
                {canEdit && <th></th>}
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id} style={{ cursor: canEdit ? 'pointer' : 'default' }}
                  onClick={canEdit ? () => setForm({ mode: 'edit', contract: c }) : undefined}>
                  <td className="mono" style={{ fontWeight: 600 }}>{c.signCount}</td>
                  <td>{c.type || <span className="faint">Chưa phân loại</span>}</td>
                  <td className="mono">{fmtDate(c.dateSigned)}</td>
                  <td className="mono">{fmtDate(c.dateStart)}</td>
                  <td className="mono">
                    {c.dateEnd ? fmtDate(c.dateEnd)
                      : <span className="muted">Không thời hạn</span>}
                    {c.expiringSoon && (
                      <div style={{ marginTop: 3 }}>
                        <Badge kind="amber">Còn {c.daysToExpire} ngày</Badge>
                      </div>
                    )}
                  </td>
                  <td className="mono" style={{ textAlign: 'right' }}>
                    {c.wage ? `${hbVND(c.wage)} ₫` : '—'}
                  </td>
                  <td className="mono" style={{ textAlign: 'right' }}>
                    {c.insuranceBase ? `${hbVND(c.insuranceBase)} ₫` : '—'}
                  </td>
                  <td><Badge kind={STATE_KIND[c.state] || 'gray'}>{c.stateLabel}</Badge></td>
                  {canEdit && (
                    <td style={{ whiteSpace: 'nowrap', textAlign: 'right', width: '1%', overflow: 'visible', maxWidth: 'none' }}
                      onClick={(ev) => ev.stopPropagation()}>
                      <button className="btn btn-ghost btn-sm" title="Sửa hợp đồng"
                        onClick={() => setForm({ mode: 'edit', contract: c })}>Sửa</button>
                      <button className="btn btn-ghost btn-sm" title="Xoá hợp đồng"
                        disabled={busy === c.id} onClick={() => remove(c)}>Xoá</button>
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {rows.length > 0 && canEdit && (
        <div className="muted" style={{ fontSize: 12, marginTop: 10 }}>
          Bấm vào một dòng để sửa. File hợp đồng bản scan hiện vẫn đính trong
          Odoo (HR → Payroll → Hợp đồng).
        </div>
      )}

      {form && (
        <ContractForm empId={det.id} mode={form.mode} contract={form.contract}
          options={det.contractOptions}
          onClose={() => setForm(null)}
          onSaved={(d) => { setForm(null); onUpdated(d); }} />
      )}
    </div>
  );
}
