/* ============================================================
   Form gửi yêu cầu / góp ý tới HR hoặc Trưởng phòng. Owner: Nhật Anh.
   Spec §7.3 — form phải CHẶN TẠI CHỖ các luật ẩn danh (dữ liệu lấy từ
   GET /service/meta) chứ không để người dùng viết xong đơn mới ăn 400.
   BE vẫn là nơi chốt cuối: mọi luật ở đây đều có bản sao trong
   hocba.hr.request.create_request().
   ============================================================ */
import { useState, useMemo } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import ModalHeader from '../../components/ModalHeader';
import { createRequest } from '../../api/service';
import { ALLOWED_MIME, MAX_FILES, MAX_SIZE, fileToBase64, inp } from './svcMeta';

function Field({ label, hint, children }) {
  return (
    <label style={{ display: 'flex', flexDirection: 'column', gap: 5 }}>
      <span style={{ fontSize: 11, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '.3px' }}>
        {label}
      </span>
      {children}
      {hint && <span className="muted" style={{ fontSize: 12 }}>{hint}</span>}
    </label>
  );
}

/* Khối cảnh báo/giải thích nhẹ trong form. */
function Note({ tone = 'info', children }) {
  const c = tone === 'warn'
    ? { bg: 'var(--red-50)', bd: 'var(--red-100)', fg: 'var(--red-700)' }
    : { bg: 'var(--surface-2, #f7f8fa)', bd: 'var(--border)', fg: 'var(--ink)' };
  return (
    <div style={{
      padding: '10px 13px', background: c.bg, border: `1px solid ${c.bd}`,
      borderRadius: 10, color: c.fg, fontSize: 12.5, lineHeight: 1.55,
    }}>{children}</div>
  );
}

export default function RequestForm({ meta, onClose, onSaved }) {
  const types = meta.types || [];
  const dept = meta.myDepartment;

  const [typeId, setTypeId] = useState(types.length ? String(types[0].id) : '');
  const [scope, setScope] = useState(types.length ? types[0].defaultRecipient : 'hr');
  const [subject, setSubject] = useState('');
  const [body, setBody] = useState('');
  const [anon, setAnon] = useState(false);
  const [rating, setRating] = useState('');
  const [urgent, setUrgent] = useState(false);
  const [files, setFiles] = useState([]);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);

  const type = useMemo(
    () => types.find((t) => String(t.id) === String(typeId)) || null,
    [types, typeId]);

  /* Đổi loại → reset các lựa chọn mà loại mới không cho phép, để state không
     mang theo giá trị "mồ côi" (vd còn tick ẩn danh khi loại mới cấm ẩn danh). */
  const pickType = (id) => {
    const t = types.find((x) => String(x.id) === String(id));
    setTypeId(id);
    setErr(null);
    if (t) {
      setScope(t.forceHrOnly ? 'hr' : t.defaultRecipient);
      if (!t.allowAnonymous) setAnon(false);
      if (!t.allowAttachment) setFiles([]);
      if (!t.hasRating) setRating('');
    }
  };

  const toggleAnon = (on) => {
    setAnon(on);
    setErr(null);
    // BR-SVC-02: đơn ẩn danh không được đính kèm — bỏ luôn file đã chọn thay vì
    // giữ ngầm rồi để BE bác đơn.
    if (on) setFiles([]);
    // BR-SVC-12: ẩn danh gửi 'both' để HR suy ra phòng ban ⇒ đưa về HR.
    if (on && scope === 'both') setScope('hr');
  };

  const anonQuotaLeft = (meta.anonDailyLimit || 0) - (meta.anonUsedToday || 0);
  const managerAvailable = !!(dept && dept.hasManager);
  const smallDept = !!(dept && dept.headcount < (meta.minAnonDeptSize || 0));

  /* Vì sao checkbox "Ẩn danh" bị khoá (null = không khoá). */
  const anonLock = !type ? 'Chọn loại yêu cầu trước.'
    : !type.allowAnonymous ? `Loại "${type.name}" không cho gửi ẩn danh.`
      : anonQuotaLeft <= 0
        ? `Bạn đã dùng hết ${meta.anonDailyLimit} đơn ẩn danh của hôm nay — gửi tiếp vào ngày mai.`
        : null;

  const attachAllowed = !!(type && type.allowAttachment && !anon);

  /* Lý do CHẶN gửi (hiện ngay dưới nút, đồng thời disable nút). Mỗi dòng ở đây
     tương ứng 1 SvcError của create_request — chặn sớm để người dùng không mất
     công viết. */
  const block = !type ? 'Chưa chọn loại yêu cầu.'
    : !subject.trim() ? 'Chưa nhập tiêu đề.'
      : !body.trim() ? 'Chưa nhập nội dung.'
        : scope !== 'hr' && !dept
          ? 'Hồ sơ của bạn chưa gắn phòng ban nên chỉ gửi được cho HR.'
          : scope !== 'hr' && !managerAvailable
            ? `Phòng "${dept.name}" chưa có trưởng phòng — hãy gửi cho HR.`
            : anon && scope === 'manager' && smallDept
              ? `Phòng "${dept.name}" chỉ có ${dept.headcount} nhân viên (cần từ ${meta.minAnonDeptSize}) nên gửi ẩn danh cho trưởng phòng sẽ dễ bị suy ra bạn là ai — hãy gửi cho HR.`
              : null;

  const addFiles = (list) => {
    setErr(null);
    const picked = Array.from(list || []);
    const bad = picked.find((f) => !ALLOWED_MIME.includes(f.type));
    if (bad) { setErr(`Tệp "${bad.name}" không phải PDF, JPG hoặc PNG.`); return; }
    const big = picked.find((f) => f.size > MAX_SIZE);
    if (big) { setErr(`Tệp "${big.name}" vượt quá 5 MB.`); return; }
    const next = [...files, ...picked];
    if (next.length > MAX_FILES) { setErr(`Mỗi đơn đính kèm tối đa ${MAX_FILES} tệp.`); return; }
    setFiles(next);
  };

  const submit = async () => {
    if (block) { setErr(block); return; }
    setBusy(true); setErr(null);
    try {
      const attachments = attachAllowed && files.length
        ? await Promise.all(files.map(async (f) => ({
          name: f.name, mimetype: f.type, data: await fileToBase64(f),
        })))
        : undefined;
      const saved = await createRequest({
        typeId: Number(typeId),
        subject: subject.trim(),
        body: body.trim(),
        recipientScope: scope,
        isAnonymous: anon,
        rating: type.hasRating && rating ? rating : undefined,
        priority: urgent ? 'urgent' : 'normal',
        attachments,
      });
      onSaved(saved);
    } catch (e) {
      setErr(e.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal onClose={onClose} lg>
      <ModalHeader lg icon="mail" title="Gửi yêu cầu / góp ý"
        sub="Đơn sẽ tới HR hoặc trưởng phòng của bạn — bạn theo dõi và trả lời ngay ở tab “Đơn của tôi”."
        onClose={onClose} />

      <div style={{ padding: '18px 24px', maxHeight: '58vh', overflowY: 'auto', display: 'grid', gap: 14 }}>
        <Field label="Loại yêu cầu *">
          <select style={inp} value={typeId} onChange={(e) => pickType(e.target.value)}>
            {types.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          {type && (
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap', marginTop: 7 }}>
              <Badge kind="blue" dot>Hạn xử lý {type.slaDays} ngày</Badge>
              {type.allowAnonymous && <Badge kind="violet">Cho ẩn danh</Badge>}
              {type.forceHrOnly && <Badge kind="amber">Chỉ HR đọc được</Badge>}
            </div>
          )}
          {type && type.description && (
            <div className="muted" style={{ fontSize: 12.5, marginTop: 7, lineHeight: 1.55 }}>
              {type.description}
            </div>
          )}
        </Field>

        {/* ---- Người nhận ------------------------------------------------ */}
        <Field label="Gửi tới *">
          {type && type.forceHrOnly ? (
            <>
              <div style={{ ...inp, background: 'var(--surface-2, #f7f8fa)', color: 'var(--muted)', display: 'flex', alignItems: 'center', gap: 7 }}>
                <Icon name="lock" size={14} />HR (bắt buộc)
              </div>
              <div style={{ marginTop: 7 }}>
                <Note>
                  Loại “{type.name}” <b>chỉ HR đọc được</b> — trưởng phòng của bạn
                  không nhìn thấy đơn này, kể cả khi họ là người bị khiếu nại
                  (BR-SVC-01).
                </Note>
              </div>
            </>
          ) : (
            <select style={inp} value={scope}
              onChange={(e) => { setScope(e.target.value); setErr(null); }}>
              <option value="hr">HR</option>
              <option value="manager" disabled={!managerAvailable}>
                Trưởng phòng{dept ? ` (${dept.name})` : ''}
                {!managerAvailable ? ' — chưa có trưởng phòng' : ''}
              </option>
              {!anon && (
                <option value="both" disabled={!managerAvailable}>HR và Trưởng phòng</option>
              )}
            </select>
          )}
          {scope !== 'hr' && dept && dept.iAmManager && (
            <div style={{ marginTop: 7 }}>
              <Note>
                Bạn chính là trưởng phòng “{dept.name}”, nên đơn sẽ được
                <b> chuyển về HR</b> — không ai tự gửi đơn cho chính mình xử lý
                (BR-SVC-04).
              </Note>
            </div>
          )}
        </Field>

        {/* ---- Ẩn danh --------------------------------------------------- */}
        <div>
          <label style={{ display: 'flex', gap: 9, alignItems: 'flex-start', cursor: anonLock ? 'not-allowed' : 'pointer' }}>
            <input type="checkbox" checked={anon} disabled={!!anonLock}
              onChange={(e) => toggleAnon(e.target.checked)}
              style={{ marginTop: 2, width: 16, height: 16, cursor: 'inherit' }} />
            <span>
              <b style={{ fontSize: 13.5 }}>Gửi ẩn danh</b>
              <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>
                {anonLock || `Còn ${anonQuotaLeft}/${meta.anonDailyLimit} đơn ẩn danh hôm nay.`}
              </div>
            </span>
          </label>

          {anon && (
            <div style={{ marginTop: 10 }}>
              <Note tone="warn">
                HR/Trưởng phòng sẽ <b>không thấy tên và phòng ban</b> của bạn. Bạn vẫn
                theo dõi và trả lời được đơn ở tab “Đơn của tôi”.
                <br />Lưu ý: <b>đừng viết thông tin có thể nhận ra bạn</b> trong nội dung
                (chức danh, lớp phụ trách, mốc thời gian riêng…) — hệ thống ẩn danh tính
                chứ không kiểm duyệt nội dung.
              </Note>
            </div>
          )}
        </div>

        <Field label="Tiêu đề *">
          <input style={inp} value={subject} maxLength={200}
            onChange={(e) => { setSubject(e.target.value); setErr(null); }}
            placeholder="VD: Xin giấy xác nhận công tác để làm thủ tục vay vốn" />
        </Field>

        <Field label="Nội dung *"
          hint={anon ? 'Đơn ẩn danh: tránh chi tiết chỉ mình bạn có.' : undefined}>
          <textarea rows={6} style={{ ...inp, resize: 'vertical' }} value={body}
            onChange={(e) => { setBody(e.target.value); setErr(null); }}
            placeholder="Mô tả rõ yêu cầu của bạn…" />
        </Field>

        {/* ---- Chấm điểm (loại đánh giá) --------------------------------- */}
        {type && type.hasRating && (
          <Field label="Điểm đánh giá" hint="Không bắt buộc — bỏ trống nếu chỉ muốn góp ý.">
            <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
              {[1, 2, 3, 4, 5].map((n) => (
                <button key={n} type="button"
                  onClick={() => setRating(String(rating) === String(n) ? '' : String(n))}
                  title={`${n} sao`}
                  style={{
                    width: 36, height: 36, borderRadius: 9, cursor: 'pointer',
                    display: 'grid', placeItems: 'center', fontFamily: 'inherit',
                    border: '1px solid ' + (Number(rating) >= n ? 'var(--gold-500)' : 'var(--border-strong)'),
                    background: Number(rating) >= n ? 'var(--gold-500)' : '#fff',
                    color: Number(rating) >= n ? '#fff' : 'var(--muted)',
                  }}>
                  <Icon name="star" size={16} />
                </button>
              ))}
              {rating && <span className="muted" style={{ fontSize: 12.5, marginLeft: 4 }}>{rating}/5</span>}
            </div>
          </Field>
        )}

        {/* ---- Đính kèm -------------------------------------------------- */}
        {/* BR-SVC-02: ẩn danh → khối này ẩn HOÀN TOÀN (không chỉ disable), vì
            một file đính kèm ghi create_uid là đủ để lộ người gửi. */}
        {attachAllowed && (
          <Field label="Tệp đính kèm"
            hint={`Tối đa ${MAX_FILES} tệp · PDF, JPG, PNG · mỗi tệp ≤ 5 MB.`}>
            <div style={{ display: 'grid', gap: 8 }}>
              {files.map((f, i) => (
                <div key={`${f.name}-${i}`} style={{
                  display: 'flex', alignItems: 'center', gap: 8, padding: '7px 11px',
                  border: '1px solid var(--border)', borderRadius: 9, fontSize: 12.5,
                }}>
                  <Icon name="file" size={15} />
                  <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {f.name}
                  </span>
                  <span className="muted mono">{Math.round(f.size / 1024)} KB</span>
                  <button className="icon-btn" title="Bỏ tệp"
                    onClick={() => setFiles(files.filter((_, k) => k !== i))}>
                    <Icon name="x" size={15} />
                  </button>
                </div>
              ))}
              {files.length < MAX_FILES && (
                <label className="btn btn-ghost btn-sm" style={{ justifySelf: 'start', cursor: 'pointer' }}>
                  <Icon name="upload" size={14} />Chọn tệp
                  <input type="file" multiple accept={ALLOWED_MIME.join(',')}
                    style={{ display: 'none' }}
                    onChange={(e) => { addFiles(e.target.files); e.target.value = ''; }} />
                </label>
              )}
            </div>
          </Field>
        )}
        {type && !type.allowAttachment && !anon && (
          <div className="muted" style={{ fontSize: 12.5 }}>
            Loại “{type.name}” không cho đính kèm tệp.
          </div>
        )}

        <label style={{ display: 'flex', gap: 9, alignItems: 'center', cursor: 'pointer' }}>
          <input type="checkbox" checked={urgent} onChange={(e) => setUrgent(e.target.checked)}
            style={{ width: 16, height: 16, cursor: 'pointer' }} />
          <span style={{ fontSize: 13.5 }}>Đánh dấu <b>Gấp</b></span>
        </label>

        {err && <Note tone="warn">{err}</Note>}
      </div>

      <div style={{ padding: '14px 24px', borderTop: '1px solid var(--border)', display: 'flex', alignItems: 'center', gap: 12 }}>
        <div className="muted" style={{ fontSize: 12, flex: 1 }}>
          {block || (anon ? 'Đơn sẽ được gửi ẩn danh.' : '')}
        </div>
        <button className="btn btn-ghost" onClick={onClose} disabled={busy}>Hủy</button>
        <button className="btn btn-primary" onClick={submit} disabled={busy || !!block}>
          <Icon name="send" size={15} />{busy ? 'Đang gửi…' : 'Gửi đơn'}
        </button>
      </div>
    </Modal>
  );
}
