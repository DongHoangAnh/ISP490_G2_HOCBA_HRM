/* Tab "Hợp đồng" trong hồ sơ nhân viên — các lần ký của một người.
   Cột bám sheet "2.5. Theo dõi ký hợp đồng" của khách.
   Chỉ hiện với vai trò được xem lương (BE cũng gác cùng cổng đó).
   Owner: Việt. */
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { EmptyState } from '../../components/states';
import { fmtDate, hbVND } from '../../utils/format';

const STATE_KIND = {
  open: 'green', draft: 'gray', close: 'gray', cancel: 'red',
};

/* Dòng cảnh báo khi nhân viên đã chính thức mà hồ sơ chưa có hợp đồng nào —
   đúng trường hợp làm HB.03/HB.357 biến mất khỏi bảng lương tháng 8. */
function NoContractWarning({ official }) {
  if (!official) return <EmptyState>Chưa có hợp đồng nào.</EmptyState>;
  return (
    <div className="card" style={{
      padding: '14px 16px', display: 'flex', gap: 11, alignItems: 'flex-start',
      borderLeft: '3px solid var(--red-600)',
    }}>
      <Icon name="alertTriangle" size={18} />
      <div style={{ fontSize: 13.5, lineHeight: 1.6 }}>
        <b>Nhân viên đã chính thức nhưng chưa có hợp đồng.</b><br />
        Bảng tính lương lọc theo hợp đồng đang hiệu lực, nên người này sẽ
        không xuất hiện trong kỳ lương nào cho tới khi hợp đồng được tạo.
      </div>
    </div>
  );
}

export default function ContractsTab({ det }) {
  const rows = det.contracts || [];
  const official = det.statusKey === 'official';
  const current = rows.find((r) => r.state === 'open');

  return (
    <div>
      <div className="between" style={{ marginBottom: 12 }}>
        <div style={{ fontWeight: 700, fontSize: 13 }}>
          Hợp đồng đã ký ({rows.length})
        </div>
        {current && (
          <div className="muted" style={{ fontSize: 12.5 }}>
            Đang hiệu lực: <b>{hbVND(current.wage)} ₫</b>
            {current.insuranceBase
              ? <> · đóng BHXH trên {hbVND(current.insuranceBase)} ₫</> : null}
          </div>
        )}
      </div>

      {!rows.length ? <NoContractWarning official={official} /> : (
        <div className="card" style={{ padding: 0 }}>
          <table className="tbl">
            <thead>
              <tr>
                <th style={{ width: 58 }}>Lần ký</th>
                <th>Loại hợp đồng</th>
                <th>Ngày ký</th>
                <th>Hiệu lực</th>
                <th>Hết hạn</th>
                <th style={{ textAlign: 'right' }}>Lương cơ bản</th>
                <th>Trạng thái</th>
                <th>File</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((c) => (
                <tr key={c.id} style={{ cursor: 'default' }}>
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
                  <td><Badge kind={STATE_KIND[c.state] || 'gray'}>{c.stateLabel}</Badge></td>
                  <td>
                    {c.files.length
                      ? c.files.map((f) => (
                        <a key={f.id} href={f.url} target="_blank" rel="noreferrer"
                          style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                          <Icon name="file" size={13} />{f.name}
                        </a>))
                      : <span className="faint">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Bản xem thử: dữ liệu chỉ đọc. Tạo/tái ký hợp đồng vẫn phải làm trong
          Odoo gốc (HR → Payroll → Hợp đồng) cho tới khi có form ở vòng sau. */}
      <div className="muted" style={{ fontSize: 12, marginTop: 12 }}>
        Bản xem thử — chỉ hiển thị. Thêm / tái ký hợp đồng hiện vẫn làm trong
        Odoo (HR → Payroll → Hợp đồng).
      </div>
    </div>
  );
}
