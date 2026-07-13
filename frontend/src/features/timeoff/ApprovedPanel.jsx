/* Trang quản lý "Đơn đã duyệt" — danh sách đơn nghỉ đã xử lý (duyệt / từ chối).
   HR/Admin xem mọi phòng ban; Trưởng phòng chỉ phòng ban mình quản lý.
   Bấm vào 1 đơn để xem chi tiết (gồm lương & lý do). Owner: Nhật Anh. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import useFetch from '../../hooks/useFetch';
import YearNav from './YearNav';
import DeptSelect from './DeptSelect';
import { fmtDate } from '../../utils/format';
import { fetchApproved } from '../../api/timeoff';
import Kpi from './Kpi';
import { downloadXlsx } from '../../utils/xlsx';
import SortBar, { sortRows } from './SortBar';
import HistoryTimeline from './HistoryTimeline';

const SORT_FIELDS = [
  { key: 'employee', label: 'Nhân viên', type: 'text' },
  { key: 'department', label: 'Phòng ban', type: 'text' },
  { key: 'leaveType', label: 'Loại nghỉ', type: 'text' },
  { key: 'stateLabel', label: 'Kết quả', type: 'text' },
  { key: 'createdAt', label: 'Ngày tạo', type: 'date' },
  { key: 'from', label: 'Từ ngày', type: 'date' },
  { key: 'to', label: 'Đến ngày', type: 'date' },
  { key: 'days', label: 'Số ngày', type: 'num' },
];

export default function ApprovedPanel({ search, year, onYearChange, dept, onDeptChange }) {
  const [detail, setDetail] = useState(null); // đơn đang xem chi tiết
  const [sort, setSort] = useState({ key: 'from', dir: 'desc' });
  const { data, err, loading, reload } = useFetch(
    () => fetchApproved(year, dept || undefined), [year, dept],
    `timeoff:approved:${year}:${dept}`);

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !data) return <TableSkeleton />;

  const k = data.kpi;
  const q = (search || '').toLowerCase();
  const rows = sortRows(
    data.requests.filter((r) =>
      !q || (r.employee || '').toLowerCase().includes(q)
         || (r.leaveType || '').toLowerCase().includes(q)
         || (r.department || '').toLowerCase().includes(q)),
    SORT_FIELDS, sort);

  const exportExcel = () => {
    const headers = ['Nhân viên', 'Phòng ban', 'Loại nghỉ', 'Kết quả', 'Ngày tạo',
      'Từ ngày', 'Đến ngày', 'Số ngày', 'Lương', 'Người duyệt/từ chối', 'Lý do'];
    const body = rows.map((r) => [
      r.employee || '', r.department || '', r.leaveType || '', r.stateLabel || '',
      fmtDate(r.createdAt), fmtDate(r.from), fmtDate(r.to), Number(r.days) || 0,
      r.unpaid ? 'Không lương' : 'Có lương', r.approver || '', r.reason || '',
    ]);
    const deptName = dept ? (data.allDepartments.find((d) => String(d.id) === String(dept))?.name || '') : '';
    const fn = `don-nghi-da-duyet-${year}${deptName ? '-' + deptName.replace(/\s+/g, '_') : ''}.xlsx`;
    downloadXlsx(fn, `Đơn đã duyệt ${year}`, headers, body);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Thanh điều khiển */}
      <div className="filterbar">
        <YearNav year={year} onChange={onYearChange} />
        <div style={{ marginLeft: 'auto' }}>
          <DeptSelect value={dept} onChange={onDeptChange} departments={data.allDepartments} />
        </div>
      </div>

      {/* KPI */}
      <div className="stat-grid" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(160px,1fr))' }}>
        <Kpi label="Đã duyệt" value={k.approved} color="var(--green)" />
        <Kpi label="Từ chối" value={k.refused} color="var(--red-600)" />
        <Kpi label="Tổng ngày nghỉ" value={k.days} sub="đã duyệt trong năm" />
      </div>

      {/* Danh sách */}
      <div className="card">
        <div className="card-head">
          <h3>Danh sách đơn nghỉ đã xử lý</h3>
          <span className="sub">{rows.length} đơn · bấm để xem chi tiết</span>
          <div className="actions">
            <SortBar fields={SORT_FIELDS} sort={sort} onChange={setSort} />
            <button className="btn btn-soft btn-sm" onClick={exportExcel} disabled={rows.length === 0}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
              <Icon name="download" size={15} />Xuất Excel</button>
          </div>
        </div>
        <div className="tbl-wrap">
          <table className="tbl">
            <thead><tr>
              <th>Nhân viên</th><th>Phòng ban</th><th>Loại nghỉ</th><th>Kết quả</th>
              <th>Ngày tạo</th><th>Từ ngày</th><th>Đến ngày</th><th className="tbl-num">Số ngày</th>
            </tr></thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} tabIndex={0} style={{ cursor: 'pointer' }} onClick={() => setDetail(r)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setDetail(r); }
                  }}>
                  <td style={{ fontWeight: 600 }}>
                    {r.employee}{r.isEmergency && <Badge kind="red">Khẩn</Badge>}</td>
                  <td className="muted">{r.department}</td>
                  <td>
                    <span style={{ display: 'inline-flex', gap: 7, alignItems: 'center' }}>
                      <span style={{ width: 8, height: 8, borderRadius: 2, background: r.color }}></span>{r.leaveType}
                    </span>
                  </td>
                  <td><Badge kind={r.stateKind} dot>{r.stateLabel}</Badge></td>
                  <td className="mono muted">{fmtDate(r.createdAt)}</td>
                  <td className="mono muted">{fmtDate(r.from)}</td>
                  <td className="mono muted">{fmtDate(r.to)}</td>
                  <td className="tbl-num mono" style={{ fontWeight: 600 }}>{r.days}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có đơn nghỉ nào được xử lý trong năm.</EmptyState>}
      </div>

      {detail && <DetailModal req={detail} onClose={() => setDetail(null)} />}
    </div>
  );
}

function DetailModal({ req, onClose }) {
  return (
    <Modal onClose={onClose}>
      <ModalHeader lg icon="calendar" iconBg={req.color}
        title={req.employee} sub={req.department} onClose={onClose} />

      <div style={{ padding: '20px 24px', display: 'flex', flexDirection: 'column', gap: 14 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <Badge kind={req.stateKind} dot>{req.stateLabel}</Badge>
          <Badge kind={req.unpaid ? 'gray' : 'green'}>{req.unpaid ? 'Không lương' : 'Có lương'}</Badge>
          {req.isEmergency && <Badge kind="red">Khẩn cấp</Badge>}
        </div>

        <Row label="Loại nghỉ">
          <span style={{ display: 'inline-flex', gap: 7, alignItems: 'center', fontWeight: 600 }}>
            <span style={{ width: 9, height: 9, borderRadius: 2, background: req.color }}></span>{req.leaveType}
          </span>
        </Row>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 14 }}>
          <Row label="Từ ngày"><span className="mono">{fmtDate(req.from)}</span></Row>
          <Row label="Đến ngày"><span className="mono">{fmtDate(req.to)}</span></Row>
          <Row label="Số ngày"><span className="mono" style={{ fontWeight: 700 }}>{req.days}</span></Row>
        </div>
        <Row label={req.state === 'refuse' ? 'Người từ chối' : 'Người duyệt'}>
          <span style={{ color: req.approver ? 'var(--ink)' : 'var(--muted)', fontWeight: req.approver ? 600 : 400 }}>
            {req.approver || '— Không xác định —'}
          </span>
        </Row>
        <Row label="Lý do">
          <span style={{ color: req.reason ? 'var(--ink)' : 'var(--muted)' }}>{req.reason || '— Không có —'}</span>
        </Row>

        {/* Lịch sử xử lý (Phase 5, audit) */}
        <Row label="Lịch sử xử lý">
          <HistoryTimeline requestId={req.id} />
        </Row>

        {/* Chứng từ y tế — chỉ với loại nghỉ yêu cầu chứng từ (nghỉ ốm) */}
        {req.supportDocument && (
          <Row label="Chứng từ y tế">
            {req.attachments && req.attachments.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                {req.attachments.map((a) => (
                  <a key={a.id} href={a.url} target="_blank" rel="noreferrer"
                     style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: 'var(--red-600)', fontWeight: 600, textDecoration: 'none' }}>
                    <Icon name="file" size={15} />{a.name}
                    <span style={{ color: 'var(--muted)' }}><Icon name="download" size={14} /></span>
                  </a>
                ))}
              </div>
            ) : (
              <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8, color: '#b45309', background: '#fffbeb', border: '1px solid #fde68a', borderRadius: 8, padding: '7px 11px', fontSize: 13 }}>
                <Icon name="bell" size={15} /> Đơn nghỉ ốm này không có chứng từ y tế đính kèm.
              </div>
            )}
          </Row>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose}>Đóng</button>
      </div>
    </Modal>
  );
}

function Row({ label, children }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      <div style={{ fontSize: 13.5 }}>{children}</div>
    </div>
  );
}
