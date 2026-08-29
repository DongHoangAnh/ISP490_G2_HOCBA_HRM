/* Form Thêm / Sửa vị trí tuyển dụng / JD — Owner: Việt.
   Meta (departments/teachingLevels/statusLabels) truyền từ JdLibrary. */
import { useState } from 'react';
import Icon from '../../components/Icon';
import Modal from '../../components/Modal';
import { createJob, updateJob } from '../../api/recruitment';
import { htmlToText } from './mailSend';

const inp = {
  width: '100%', padding: '9px 12px', borderRadius: 10,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};

function Field({ label, full, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5, gridColumn: full ? '1 / -1' : 'auto' }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>{label}</span>
      {children}
    </label>
  );
}

/* meta.departments đã lọc theo phạm vi ở backend: HR = mọi phòng, trưởng phòng =
   phòng mình. Chỉ có đúng 1 phòng thì chọn sẵn, khỏi bắt bấm "— Chọn —". */
function initForm(j, meta) {
  const deps = (meta && meta.departments) || [];
  const depMacDinh = deps.length === 1 ? deps[0].id : '';
  return {
    name: j?.name || '', depId: j?.depId || depMacDinh, status: j?.status || 'recruiting',
    jdLink: j?.jdLink || '',
    teachingLevel: j?.teachingLevel || '',
    /* description là field Html của Odoo (form backend lưu <p>…</p>). HR không
       cần biết thẻ là gì nên ô này luôn hiện TEXT THUẦN; controller hoá HTML
       lại lúc lưu (_job_vals + plaintext2html). */
    description: htmlToText(j?.description) || '',
  };
}

export default function JobForm({ job, meta, onClose, onSaved }) {
  const isEdit = !!job;
  const [f, setF] = useState(() => initForm(job, meta));
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const set = (k) => (e) => setF((p) => ({ ...p, [k]: e.target.value }));

  const submit = async () => {
    if (!f.name.trim()) { setErr('Vui lòng nhập tên vị trí.'); return; }
    setBusy(true); setErr(null);
    try {
      const det = isEdit ? await updateJob(job.id, f) : await createJob(f);
      onSaved(det);
    } catch (e) {
      setErr(e.message || 'Lưu thất bại.');
    } finally { setBusy(false); }
  };

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 48, height: 48, borderRadius: 12, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name={isEdit ? 'edit' : 'plus'} size={22} />
        </div>
        <div style={{ flex: 1 }}>
          <h2 style={{ margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-.3px' }}>
            {isEdit ? 'Chỉnh sửa vị trí' : 'Thêm vị trí tuyển dụng'}</h2>
          <div className="muted" style={{ fontSize: 13, marginTop: 2 }}>
            {isEdit ? job.name : 'Tạo vị trí và mô tả công việc (JD) mới'}</div>
        </div>
        <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
      </div>

      <div style={{ padding: '22px 24px', maxHeight: '58vh', overflowY: 'auto' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px 16px' }}>
          <Field label="Tên vị trí *" full>
            <input style={inp} value={f.name} onChange={set('name')} placeholder="VD: Giảng viên Tiếng Trung" /></Field>
          <Field label="Phòng ban">
            <select style={inp} value={f.depId} onChange={set('depId')}>
              <option value="">— Chọn —</option>
              {meta.departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select></Field>
          <Field label="Trạng thái tuyển">
            <select style={inp} value={f.status} onChange={set('status')}>
              {Object.entries(meta.statusLabels).map(([k, l]) => <option key={k} value={k}>{l}</option>)}
            </select></Field>
          {/* KHÔNG có ô "Số lượng cần tuyển" và "Số buổi/tuần tối thiểu" ở form
              này — bỏ 2026-08-29, cả lúc tạo lẫn lúc sửa. Chỉ tiêu là của ĐỢT
              tuyển: duyệt phiếu cộng qty_expected vào vị trí, đóng phiếu trả
              lại phần chưa tuyển. Gõ tay ở đây là chỉ tiêu ma — tuyển đủ người
              của phiếu mà vị trí vẫn còn "còn thiếu" nên không bao giờ tự ngừng
              đăng. Xem hr_applicant._hb_auto_close_if_filled. Form vì vậy không
              gửi `expected` / `sessionsPerWeek`, sửa JD không đụng hai số này;
              số lượng còn cần tuyển vẫn xem được ở drawer chi tiết vị trí. */}
          {/* Combobox: chọn trong gợi ý (HSK1-9 / HSKK / TOCFL) HOẶC gõ trình độ
              khác — trung tâm gặp chứng chỉ lạ thì không phải chờ sửa code. */}
          <Field label="Trình độ">
            <input style={inp} list="hb-teaching-levels" value={f.teachingLevel}
              onChange={set('teachingLevel')}
              placeholder="Chọn hoặc gõ, VD: HSK4, TOCFL Band B…" />
            <datalist id="hb-teaching-levels">
              {(meta.teachingLevels || []).map((l) => <option key={l} value={l} />)}
            </datalist></Field>
          <Field label="Link JD (Google Docs/Drive)" full>
            <input style={inp} value={f.jdLink} onChange={set('jdLink')} placeholder="https://docs.google.com/..." /></Field>
          <Field label="Mô tả công việc (JD)" full>
            <textarea style={{ ...inp, minHeight: 120, resize: 'vertical' }} value={f.description} onChange={set('description')} placeholder="Mô tả nhiệm vụ, yêu cầu, quyền lợi…" /></Field>
          {/* KHÔNG có ô "Đăng tuyển lên website" ở form này (bỏ 2026-08-29):
              đăng / ngừng đăng chỉ còn MỘT chỗ là nút toggle ở tab Theo dõi
              tuyển dụng — nút đó chỉ gửi {published} nên trạng thái tuyển suy
              theo cờ đăng. Form này vì vậy KHÔNG gửi khoá `published`: không
              gửi thì `_job_vals` không đụng `x_published`, sửa JD không vô
              tình gỡ tin đang chạy. */}
        </div>

        {err && (
          <div style={{ marginTop: 12, padding: '10px 13px', background: 'var(--red-50)', border: '1px solid var(--red-100)', borderRadius: 10, color: 'var(--red-700)', fontSize: 12.5 }}>
            {err}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '14px 24px', borderTop: '1px solid var(--border)' }}>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Huỷ</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy}>
          <Icon name={isEdit ? 'checkCircle' : 'plus'} size={16} />
          {busy ? 'Đang lưu…' : (isEdit ? 'Lưu thay đổi' : 'Tạo vị trí')}
        </button>
      </div>
    </Modal>
  );
}
