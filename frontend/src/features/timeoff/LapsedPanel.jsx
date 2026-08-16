/* Tab "Kiểm duyệt phát sinh" (Phase 12) — đơn QUÁ HẠN duyệt (qua ngày bắt đầu
   nghỉ mà vẫn chờ duyệt) + đối chiếu chấm công + KPI. Payload vẫn dùng tên
   lapsed* của spec gốc; nhãn hiển thị thống nhất là "quá hạn".
   Chỉ officer (HR Manager/Admin mọi phòng, Trưởng phòng phòng mình, HR User
   chỉ xem). Nút xử lý nhanh còn phụ thuộc bậc duyệt của từng loại nghỉ
   (r.canDecide — xem _can_decide_leave ở controllers/main.py).
   Spec: docs/superpowers/specs/2026-07-03-timeoff-lapsed-approvals-design.md
   Owner: Nhật Anh. */
import { useState } from 'react';
import Badge from '../../components/Badge';
import ConfirmModal from '../../components/ConfirmModal';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import DeptSelect from './DeptSelect';
import { fmtDate } from '../../utils/format';
import { fetchLapsedDashboard, decideRequest } from '../../api/timeoff';
import Kpi from './Kpi';

export default function LapsedPanel({ dept, onDeptChange, onOpenApproval }) {
  const [confirming, setConfirming] = useState(null); // dòng chờ xác nhận xử lý nhanh
  const { data, err, loading, reload } = useFetch(
    () => fetchLapsedDashboard(dept || undefined), [dept], `timeoff:lapsed:${dept}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;

  const k = data.kpi;
  const maxDept = Math.max(...data.byDepartment.map((r) => r.count), 1);
  // Nút "Xử lý theo đề xuất" bám theo r.canDecide (backend _can_decide_leave):
  // HR User chỉ xem, và bậc duyệt của loại nghỉ còn giới hạn HR Manager hay
  // trưởng phòng. Không đủ quyền → chỉ còn đường dẫn sang tab Chờ duyệt.

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {data.seeAll && (
        <div className="filterbar">
          <div style={{ marginLeft: 'auto' }}>
            <DeptSelect value={dept} onChange={onDeptChange} departments={data.allDepartments} />
          </div>
        </div>
      )}

      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))' }}>
        <Kpi label="Đơn quá hạn duyệt" value={k.total}
          color={k.total > 0 ? 'var(--red-600)' : 'var(--ink)'}
          sub="qua ngày nghỉ, chưa duyệt" />
        <Kpi label="Đề xuất duyệt trễ" value={k.suggestApprove} color="var(--green)"
          sub="nhân viên nghỉ thật" />
        <Kpi label="Mâu thuẫn chấm công" value={k.suggestRefuse} color="var(--amber)"
          sub="xin nghỉ nhưng vẫn đi làm" />
        <Kpi label="Cần xem tay" value={k.needsReview} sub="lẫn lộn / chưa đủ dữ liệu" />
        <Kpi label="Quá hạn lâu nhất" value={k.oldestLapsedDays} sub="ngày làm việc" />
      </div>

      {data.byDepartment.length > 0 && (
        <div className="card">
          <div className="card-head"><h3>Đơn quá hạn theo phòng ban</h3></div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 13, padding: 16 }}>
            {data.byDepartment.map((r) => (
              <div key={r.id || r.name}>
                <div className="between" style={{ marginBottom: 5 }}>
                  <span style={{ fontSize: 13, fontWeight: 600 }}>{r.name}</span>
                  <span className="muted mono" style={{ fontSize: 12 }}>{r.count} đơn</span>
                </div>
                <div className="bar">
                  <span style={{ width: (r.count / maxDept) * 100 + '%', background: 'var(--red-600)' }}></span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card">
        <div className="card-head">
          <h3>Chi tiết đơn quá hạn</h3>
          <span className="sub">{data.items.length} đơn — đối chiếu bảng chấm công các ngày nghỉ đã qua</span>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th><th>Loại nghỉ</th>
              <th>Từ</th><th>Đến</th><th className="tbl-num">Quá hạn</th>
              <th>Đối chiếu chấm công</th><th>Đề xuất</th><th></th>
            </tr></thead>
            <tbody>
              {data.items.map((r) => (
                <tr key={r.requestId}>
                  <td style={{ fontWeight: 600 }}>{r.employee}</td>
                  <td className="muted">{r.department}</td>
                  <td>{r.leaveType}</td>
                  <td className="mono muted">{fmtDate(r.from)}</td>
                  <td className="mono muted">{fmtDate(r.to)}</td>
                  <td className="tbl-num mono" style={{ fontWeight: 700, color: 'var(--red-700)' }}>
                    {r.lapsedDays} ngày</td>
                  <td className="muted" style={{ fontSize: 12.5 }}>{r.summary}</td>
                  <td>
                    {r.suggestion === 'approve' && <Badge kind="green">Duyệt trễ</Badge>}
                    {r.suggestion === 'refuse' && <Badge kind="amber">Từ chối</Badge>}
                    {!r.suggestion && <Badge kind="gray">Xem tay</Badge>}
                  </td>
                  <td style={{ overflow: 'visible', maxWidth: 'none', width: '1%', whiteSpace: 'nowrap' }}>
                    {r.canDecide && r.suggestion ? (
                      <button className="btn btn-primary btn-sm"
                        onClick={() => setConfirming(r)}>Xử lý theo đề xuất</button>
                    ) : (
                      <button className="btn btn-ghost btn-sm"
                        title={r.canDecide ? '' : `${r.approverRoleLabel || ''} duyệt loại nghỉ này`}
                        onClick={() => onOpenApproval && onOpenApproval(r.requestId)}>
                        {r.canDecide ? 'Xử lý ở tab Chờ duyệt →' : 'Xem ở tab Chờ duyệt →'}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {data.items.length === 0 && (
          <EmptyState>Không có đơn nào quá hạn duyệt. 🎉</EmptyState>
        )}
      </div>

      {/* Nút 1-chạm: gọi thẳng flow duyệt hiện có với action theo đề xuất (BR-L04).
          decideRequest trả payload dạng approvals (khác shape lapsed-dashboard)
          → không setData được, phải reload. */}
      {confirming && (
        <ConfirmModal
          title={confirming.suggestion === 'approve' ? 'Duyệt trễ theo đề xuất' : 'Từ chối theo đề xuất'}
          confirmLabel={confirming.suggestion === 'approve' ? 'Duyệt trễ' : 'Từ chối'}
          message={`${confirming.suggestion === 'approve'
            ? 'Duyệt trễ' : 'Từ chối (nhân viên vẫn đi làm)'} đơn của ${confirming.employee}?`}
          onClose={() => setConfirming(null)}
          onConfirm={() => decideRequest(confirming.requestId, { action: confirming.suggestion })
            .then(() => { setConfirming(null); reload(); })} />
      )}
    </div>
  );
}
