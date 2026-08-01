/* ============================================================
   Tab "Cần xử lý" — hộp thư của HR / Trưởng phòng. Owner: Nhật Anh. Spec §7.2.
   Phạm vi đơn do BE quyết (_inbox_domain, BR-SVC-13: HR Manager KHÔNG giám sát
   đơn gửi Trưởng phòng) — panel này KHÔNG tự lọc lại theo vai trò.
   Thao tác vòng đời (nhận xử lý / trả lời / ghi chú nội bộ / chốt / đóng) nằm
   trong RequestThread với role='handler'.
   ============================================================ */
import { useState, useEffect, useCallback } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { ErrorState, EmptyState, TableSkeleton } from '../../components/states';
import { fetchInbox } from '../../api/service';
import { fmtDateOnly, slaInfo, stateMeta } from './svcMeta';
import RequestThread from './RequestThread';

/* 'open' = new + in_progress (pseudo-state của _state_domain ở BE). Mặc định
   mở ở 'open' vì đó đúng nghĩa "cần xử lý"; vẫn giữ "Tất cả" để tra cứu. */
const FILTERS = [
  ['open', 'Đang mở'],
  ['new', 'Mới'],
  ['in_progress', 'Đang xử lý'],
  ['answered', 'Đã trả lời'],
  ['closed', 'Đã đóng'],
  ['cancelled', 'Đã rút'],
  ['', 'Tất cả'],
];

/* Cắt chữ dài trong 1 ô (bù cho .tbl-scroll đã bỏ ellipsis của td). */
const clip = (max) => ({
  display: 'inline-block', maxWidth: max, overflow: 'hidden',
  textOverflow: 'ellipsis', verticalAlign: 'middle',
});

export default function InboxPanel({ meta, search, focus }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [state, setState] = useState('open');
  const [typeId, setTypeId] = useState('');
  const [overdue, setOverdue] = useState(false);
  const [q, setQ] = useState('');
  const [open, setOpen] = useState(null);

  /* Tìm kiếm chạy ở BE (route /inbox có tham số q, quét cả mã đơn + nội dung —
     nội dung KHÔNG có trong bảng nên lọc ở client sẽ bỏ sót). Debounce để mỗi
     ký tự gõ không thành một request. */
  useEffect(() => {
    const t = setTimeout(() => setQ((search || '').trim()), 350);
    return () => clearTimeout(t);
  }, [search]);

  /* setData(null) nằm TRONG load (không ở onChange của select): nếu đặt ở
     onChange mà giá trị không đổi thật thì load giữ nguyên identity ⇒ effect
     không chạy lại ⇒ skeleton treo vĩnh viễn. */
  const load = useCallback(() => {
    setErr(null); setData(null);
    fetchInbox({ state, overdue, typeId, q })
      .then(setData)
      .catch((e) => setErr(e.message));
  }, [state, overdue, typeId, q]);
  useEffect(() => { load(); }, [load]);

  /* Bấm thông báo ở chuông (P5) → mở đúng đơn. */
  useEffect(() => {
    if (focus && focus.requestId) setOpen(focus.requestId);
  }, [focus]);

  if (err) return <ErrorState message={err} onRetry={load} />;

  const rows = data ? data.requests : [];
  const nOverdue = rows.filter((r) => r.isOverdue).length;
  const nUnclaimed = rows.filter((r) => r.state === 'new').length;
  const types = (meta && meta.types) || [];
  // 'open' là mặc định của tab nên không tính là "đang lọc" — hộp thư rỗng ở
  // đó nghĩa là hết việc, không phải lọc quá tay.
  const filtering = !!(typeId || overdue || q) || !['', 'open'].includes(state);

  return (
    <div className="card">
      <div className="card-head" style={{ gap: 10, flexWrap: 'wrap' }}>
        <h3>Cần xử lý</h3>
        {data && (
          <span className="muted" style={{ fontSize: 12.5 }}>
            {rows.length} đơn
            {nUnclaimed ? ` · ${nUnclaimed} chưa nhận` : ''}
            {nOverdue ? ` · ${nOverdue} trễ hạn` : ''}
          </span>
        )}
        <div style={{ flex: 1 }} />
        <label style={{
          display: 'flex', alignItems: 'center', gap: 7, fontSize: 12.5,
          cursor: 'pointer', whiteSpace: 'nowrap',
        }}>
          <input type="checkbox" checked={overdue}
            onChange={(e) => { setOverdue(e.target.checked); }}
            style={{ width: 15, height: 15, cursor: 'pointer' }} />
          Chỉ đơn trễ hạn
        </label>
        <select className="sel" value={typeId}
          onChange={(e) => { setTypeId(e.target.value); }}>
          <option value="">Mọi loại</option>
          {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
        </select>
        <select className="sel" value={state}
          onChange={(e) => { setState(e.target.value); }}>
          {FILTERS.map(([v, l]) => <option key={v} value={v}>{l}</option>)}
        </select>
      </div>

      {!data ? <div style={{ padding: '0 16px 16px' }}><TableSkeleton rows={5} /></div> : (
        <>
          {/* tbl-scroll: `table.tbl td` mặc định nowrap + max-width:0 nên badge
              sau tiêu đề bị cắt mất (xem §10.3 của spec). */}
          <div className="tbl-wrap tbl-scroll">
            <table className="tbl">
              {/* Đo thật ở 1500px: 9 cột = 1394px trong khung 1194px ⇒ nút "Xử
                  lý" và trạng thái rơi ra ngoài, phải cuộn ngang mới thấy. Rút
                  còn 6 cột: bỏ "Gửi lúc" (giờ gửi xem trong RequestThread; với
                  người xử lý thì HẠN mới là con số phải nhìn — SLA theo ngày nên
                  hạn chỉ hiện ngày), "Loại" xuống dòng phụ của tiêu đề, "Người
                  xử lý" gộp vào ô trạng thái. */}
              <thead><tr>
                <th>Mã đơn</th><th>Tiêu đề</th><th>Người gửi</th>
                <th>Hạn xử lý</th><th>Trạng thái</th><th></th>
              </tr></thead>
              <tbody>
                {rows.map((r) => {
                  const st = stateMeta(r.state);
                  const sla = slaInfo(r);
                  return (
                    <tr key={r.id} style={{ cursor: 'pointer' }} onClick={() => setOpen(r.id)}>
                      <td className="mono muted">{r.name}</td>
                      {/* tbl-scroll bỏ ellipsis mặc định của td ⇒ chữ dài phải
                          tự cắt bằng span, không thì bảng đẩy nút "Xử lý" ra
                          ngoài khung. */}
                      <td style={{ whiteSpace: 'nowrap' }}>
                        <div style={{ fontWeight: 600 }}>
                          <span style={clip(300)} title={r.subject}>{r.subject}</span>
                          {r.isAnonymous && (
                            <span style={{ marginLeft: 7 }}><Badge kind="violet">Ẩn danh</Badge></span>
                          )}
                          {r.priority === 'urgent' && (
                            <span style={{ marginLeft: 7 }}><Badge kind="amber">Gấp</Badge></span>
                          )}
                        </div>
                        <div className="muted" style={{ fontSize: 11.5, marginTop: 2 }}>
                          <span style={clip(300)} title={r.typeName}>{r.typeName}</span>
                        </div>
                      </td>
                      {/* senderName đã là 'Người gửi (ẩn danh)' và departmentName
                          là null với đơn ẩn danh — serialize() lo, không xử ở đây. */}
                      <td>
                        <span style={clip(210)}
                          title={r.senderName + (r.departmentName ? ' · ' + r.departmentName : '')}>
                          {r.senderName}
                          {r.departmentName && (
                            <span className="muted"> · {r.departmentName}</span>
                          )}
                        </span>
                      </td>
                      <td className="mono muted" style={{ whiteSpace: 'nowrap' }}>
                        {fmtDateOnly(r.deadline)}
                        {sla && <span style={{ marginLeft: 7 }}><Badge kind={sla.kind}>{sla.label}</Badge></span>}
                      </td>
                      {/* Người xử lý đi kèm trạng thái trong CÙNG ô: tách thành
                          cột riêng thì bảng vượt khung, mà "đang xử lý" mà
                          không biết ai xử lý thì vô nghĩa. */}
                      <td>
                        <Badge kind={st.kind} dot>{st.label}</Badge>
                        <div className="muted" style={{ fontSize: 11.5, marginTop: 3 }}>
                          {r.handlerName
                            ? <span style={clip(130)} title={r.handlerName}>{r.handlerName}</span>
                            : 'Chưa nhận'}
                        </div>
                      </td>
                      <td>
                        <button className="btn btn-ghost btn-sm"
                          onClick={(e) => { e.stopPropagation(); setOpen(r.id); }}>
                          <Icon name="eye" size={14} />Xử lý
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          {rows.length === 0 && (
            <EmptyState>
              {filtering
                ? 'Không có đơn nào khớp bộ lọc hiện tại.'
                : state === 'open'
                  ? 'Không còn đơn nào đang mở — bạn đã xử lý hết.'
                  : 'Hộp thư trống — chưa có yêu cầu nào cần bạn xử lý.'}
            </EmptyState>
          )}
        </>
      )}

      {open && (
        <RequestThread requestId={open} role="handler"
          onClose={() => setOpen(null)} onChanged={load} />
      )}
    </div>
  );
}
