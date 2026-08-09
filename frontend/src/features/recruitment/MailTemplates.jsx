/* Tab "Mail mẫu tuyển dụng" — liệt kê mẫu, thêm/sửa, gửi cho ứng viên chọn.
   Owner: Việt. Spec: docs/SPEC_API_RECRUITMENT.md · 3 trạng thái §5b. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Pagination, { usePaged } from '../../components/Pagination';
import { fetchMailTemplates, deleteMailTemplate } from '../../api/recruitment';
import MailTemplateForm from './MailTemplateForm';
import MailTemplateImport from './MailTemplateImport';
import SendMailModal from './SendMailModal';
import GuideNote from './GuideNote';
import { toFriendly } from './mailTokens';

/* Cắt bớt phần chữ dài mà vẫn giữ nguyên nghĩa: tiêu đề dài ngắn khác nhau từng
   mẫu, để trôi tự do thì thẻ cao thấp lệch nhau và nút "Gửi mail" mỗi thẻ một
   độ cao. Kẹp 2 dòng + đẩy hàng nút xuống đáy ⇒ nút luôn thẳng hàng. */
const clamp = (lines) => ({
  display: '-webkit-box', WebkitLineClamp: lines, WebkitBoxOrient: 'vertical',
  overflow: 'hidden', wordBreak: 'break-word',
});

/* Hướng dẫn thao tác của tab này — khung dùng chung ở GuideNote.jsx. */
const TMPL_STEPS = [
  ['Soạn hoặc mang mẫu cũ vào',
   <>Bấm <b>Thêm mẫu</b> để soạn mới, hoặc <b>Import mẫu</b> rồi dán nguyên lá mail
     đang dùng (Word / Gmail / sheet 7.7) — hệ thống tự tách tiêu đề, dựng nội dung
     và nhận ra các chỗ điền dạng <b>[Tên ứng viên]</b>.</>],
  ['Chèn thông tin tự động',
   <>Trong ô nội dung, bấm nút <b>Chèn</b> để đặt các ô vàng: <b>Họ tên ứng viên</b>,
     <b> Vị trí ứng tuyển</b>, <b>Email</b>, <b>Số điện thoại</b>, <b>Ngày</b> và
     <b> Giờ phỏng vấn</b>. Lúc gửi, mỗi ô vàng được thay bằng dữ liệu thật của
     từng ứng viên — đừng gõ tay tên người vào mẫu.</>],
  ['Gửi cho ứng viên',
   <>Bấm <b>Gửi mail</b> trên thẻ mẫu → tick những ứng viên cần gửi → <b>Tiếp tục</b>
     → bấm <b>Mở Gmail</b> ở từng người và gửi bằng Gmail của bạn → quay lại bấm
     <b> Lưu lịch sử</b>. Cần soát kỹ hoặc sửa nội dung cho riêng một người thì gửi
     từ nút <b>Gửi mail</b> ở tab Danh sách PV / Offer, chỗ đó có <b>Xem trước</b>
     và sửa được trước khi gửi.</>],
  ['Nhớ hệ quả đổi bước',
   <>Gửi <b>“Thư mời phỏng vấn”</b> đẩy ứng viên từ bước Hẹn &amp; mời phỏng vấn sang
     <b> Phỏng vấn</b>; gửi <b>“Thư mời nhận việc”</b> đẩy sang <b>Gửi Offer</b>. Các
     mẫu còn lại gửi đi không đổi bước. Bước chỉ đổi khi bạn bấm <b>Lưu lịch sử</b>,
     nên đừng bỏ qua thao tác đó.</>],
  ['Kiểm tra lại sau khi gửi',
   <>Xem tab <b>Lịch sử gửi mail</b> để biết đã gửi cho ai, lúc nào. Sửa mẫu về sau
     <b> không</b> ảnh hưởng các mail đã gửi.</>],
];

const TMPL_GUIDE_NOTE = (
  <>Mail mẫu là cấu hình dùng chung <b>toàn hệ thống</b>, không theo phòng ban —
    nên chỉ HR mới thêm/sửa/xoá/import được. Trưởng phòng <b>gửi</b> được nhưng
    chỉ tới ứng viên phòng mình (danh sách người nhận đã lọc sẵn).</>
);

export default function MailTemplates({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [editing, setEditing] = useState(null);   // null | 'new' | {id,name,subject}
  const [sending, setSending] = useState(null);   // null | {id,name}
  const [deletingId, setDeletingId] = useState(null);
  const [importing, setImporting] = useState(false);

  const load = () => { setErr(null); setData(null); fetchMailTemplates().then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, []);

  const remove = async (t) => {
    if (!window.confirm(`Xoá mail mẫu "${t.name}"?\nHành động này không hoàn tác được.`)) return;
    setDeletingId(t.id);
    try {
      await deleteMailTemplate(t.id);
      setData((p) => ({ ...p, rows: p.rows.filter((r) => r.id !== t.id) }));
    } catch (e) {
      alert(e.message || 'Không xoá được mẫu.');
    } finally { setDeletingId(null); }
  };

  /* Lọc + phân trang đặt TRƯỚC early-return (quy tắc hook — xem Requests.jsx). */
  const filtered = (data ? data.rows : []).filter((r) => !search
    || (r.name || '').toLowerCase().includes(search.toLowerCase())
    || (r.subject || '').toLowerCase().includes(search.toLowerCase()));
  const pg = usePaged(filtered, [search]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải mail mẫu…" />;

  /* canEdit = quản mẫu (chỉ HR) · canSend = gửi mail cho ứng viên (HR hoặc
     trưởng phòng, người nhận đã được BE lọc theo phòng ban). Hai quyền tách
     rời — xem ghi chú ở controller api_recruitment_mail_templates. */
  const { rows, recipients, canEdit, canSend } = data;

  return (
    <div>
      <div className="filterbar">
        <span className="muted" style={{ fontSize: 13 }}>{rows.length} mẫu · {recipients.length} ứng viên có email</span>
        {canEdit && (
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 9 }}>
            <button className="btn btn-soft" onClick={() => setImporting(true)}>
              <Icon name="upload" size={16} />Import mẫu</button>
            <button className="btn btn-primary" onClick={() => setEditing('new')}>
              <Icon name="plus" size={16} />Thêm mẫu</button>
          </div>
        )}
      </div>

      <div className="grid-3" style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(320px,1fr))' }}>
        {pg.rows.map((t) => {
          // Tiêu đề hiện dạng thẻ tiếng Việt ([Vị trí ứng tuyển]) thay vì biểu
          // thức Odoo thô — vừa dễ đọc vừa ngắn hơn hẳn.
          const subject = toFriendly(t.subject) || '(Không có tiêu đề)';
          return (
          <div key={t.id} className="card" style={{ padding: 18, display: 'flex', flexDirection: 'column', gap: 8 }}>
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{ width: 38, height: 38, borderRadius: 10, background: 'var(--red-50)', color: 'var(--red-600)', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
                <Icon name="mail" size={18} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 700, fontSize: 14, ...clamp(2) }} title={t.name}>{t.name}</div>
                <div className="muted" style={{ fontSize: 12, marginTop: 3, ...clamp(2) }} title={subject}>{subject}</div>
              </div>
            </div>
            {/* marginTop:auto — hàng nút bám đáy thẻ, không bị tiêu đề dài đẩy lệch */}
            <div className="divider" style={{ margin: '6px 0', marginTop: 'auto' }}></div>
            <div style={{ display: 'flex', gap: 8 }}>
              {canSend && (
                <button className="btn btn-primary btn-sm" style={{ flex: 1 }} onClick={() => setSending(t)}>
                  <Icon name="mail" size={14} />Gửi mail</button>
              )}
              {canEdit && (
                <button className="btn btn-ghost btn-sm" onClick={() => setEditing(t)}>
                  <Icon name="edit" size={14} />Sửa</button>
              )}
              {canEdit && (
                <button className="btn btn-ghost btn-sm" title="Xoá mẫu"
                  style={{ color: 'var(--red-600)' }}
                  disabled={deletingId === t.id} onClick={() => remove(t)}>
                  <Icon name="trash" size={14} />{deletingId === t.id ? '…' : ''}</button>
              )}
            </div>
          </div>
          );
        })}
        {filtered.length === 0 && <div style={{ gridColumn: '1/-1' }}><EmptyState>Chưa có mail mẫu nào.</EmptyState></div>}
        <div style={{ gridColumn: '1/-1' }}><Pagination {...pg} /></div>
      </div>

      <GuideNote title="Các bước bộ phận tuyển dụng cần làm ở màn này"
        steps={TMPL_STEPS} note={TMPL_GUIDE_NOTE} />

      {editing && (
        <MailTemplateForm tmpl={editing === 'new' ? null : editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); load(); }} />
      )}
      {importing && (
        <MailTemplateImport
          onClose={() => setImporting(false)}
          onSaved={() => { setImporting(false); load(); }} />
      )}
      {sending && (
        <SendMailModal tmpl={sending} recipients={recipients} onClose={() => setSending(null)} />
      )}
    </div>
  );
}
