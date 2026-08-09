/* Tab "Offer & Nhận việc" — danh sách ứng viên đã Pass phỏng vấn.
   Hiển thị: họ tên, ngày ứng tuyển, vị trí, bước hiện tại, nội dung offer,
   ngày nhận việc + gửi mail.
   Gửi mail: chọn mẫu từ tab Mail mẫu; server tự điền thông tin ứng viên khi render. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Pagination, { usePaged } from '../../components/Pagination';
import { fmtDate } from '../../utils/format';
import Badge from '../../components/Badge';
import { fetchCvList, fetchMailTemplates, updateApplicant, createEmployeeFromApplicant } from '../../api/recruitment';
import MailSendModal from './MailSendModal';
import GuideNote from './GuideNote';

/* Tiêu chí vào tab: ĐÃ PASS PHỎNG VẤN. Đó mới là lúc có việc để làm ở đây
   (soạn offer, chốt ngày nhận việc, tạo hồ sơ NV) — chứ không phải lúc ứng viên
   được kéo tới một bước nào đó. Từ khi bỏ luật "Pass PV → tự sang Gửi Offer",
   ứng viên Pass đứng lại ở bước Kết quả phỏng vấn, lọc theo bước thì tab này
   rỗng cho tới khi HR kéo tay.

   Vẫn giữ thêm nhánh lọc theo MÃ bước để không đánh rơi ứng viên đã ở Offer /
   Onboarding mà ô Kết quả PV bỏ trống (dữ liệu cũ, import, tuyển thẳng). Lọc
   bằng xmlid chứ không bằng tên bước: tên sửa được trên màn Cấu hình, so tên là
   tab rỗng ngay khi ai đó đổi chữ. Giống CvList/InterviewSlots. */
const OFFER_STAGE_REFS = ['hb_stage_offer', 'hb_stage_onboarding'];
const inOfferScope = (r) => r.interviewResult === 'pass'
  || OFFER_STAGE_REFS.includes(r.stageRef);

/* Màu badge "Bước hiện tại" — theo MÃ bước, đậm dần theo chặng đường: vàng =
   Pass PV nhưng chưa gửi offer (còn việc phải làm) → xanh dương = đang gửi
   offer → teal = onboarding → xanh lá = đã bàn giao. Bước lạ (admin thêm bước
   mới, hoặc ứng viên bị kéo về bước trước) rơi về xám, tên bước vẫn hiện đúng. */
const STAGE_KIND = {
  hb_stage_result:     'amber',
  hb_stage_offer:      'blue',
  hb_stage_onboarding: 'teal',
  hb_stage_hired:      'green',
};

export default function Offers({ search }) {
  const [cv, setCv] = useState(null);
  const [tmpls, setTmpls] = useState(null);
  const [err, setErr] = useState(null);
  const [mailFor, setMailFor] = useState(null); // ứng viên đang gửi mail

  const [savingId, setSavingId] = useState(null);

  const load = () => { setErr(null); setCv(null); fetchCvList().then(setCv).catch((e) => setErr(e.message)); };
  useEffect(load, []);
  useEffect(() => { fetchMailTemplates().then(setTmpls).catch(() => setTmpls({ rows: [] })); }, []);

  const [empBusyId, setEmpBusyId] = useState(null);

  // Lưu 1 trường (offer / ngày nhận việc) rồi cập nhật dòng vào state — chỉ recruiter.
  const saveField = async (id, patch) => {
    setSavingId(id);
    try {
      const det = await updateApplicant(id, patch);
      setCv((p) => ({ ...p, rows: p.rows.map((r) => (r.id === id ? det : r)) }));
    } catch (e) {
      alert(e.message || 'Không lưu được thay đổi.');
    } finally { setSavingId(null); }
  };

  // Tạo hồ sơ nhân viên từ ứng viên đã nhận việc (chống tạo trùng ở backend).
  const createEmployee = async (r) => {
    if (!window.confirm(`Tạo hồ sơ nhân viên (thử việc) cho "${r.name}"?\nBạn sẽ điền nốt CCCD / MST / BHXH ở module Nhân sự.`)) return;
    setEmpBusyId(r.id);
    try {
      const res = await createEmployeeFromApplicant(r.id);
      setCv((p) => ({ ...p, rows: p.rows.map((x) => (x.id === r.id
        ? { ...x, employeeId: res.employeeId, employeeName: res.employeeName, employeeCode: res.employeeCode } : x)) }));
      // BE vừa đẩy bước sang Onboarding ⇒ tải lại để cột "Bước hiện tại" đúng.
      if (res.created) load();
      alert(res.created
        ? `Đã tạo hồ sơ nhân viên ${res.employeeCode ? '(' + res.employeeCode + ') ' : ''}cho ${res.employeeName}.`
        : (res.message || 'Ứng viên này đã có hồ sơ nhân viên.'));
    } catch (e) {
      alert(e.message || 'Không tạo được hồ sơ nhân viên.');
    } finally { setEmpBusyId(null); }
  };

  /* Lọc + phân trang đặt TRƯỚC early-return (quy tắc hook — xem Requests.jsx). */
  const rows = (cv ? cv.rows : [])
    .filter(inOfferScope)
    .filter((r) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return [r.name, r.phone, r.email, r.jobName].some((v) => (v || '').toLowerCase().includes(q));
    })
    .sort((a, b) => (b.startDate || '').localeCompare(a.startDate || ''));
  const pg = usePaged(rows, [search]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!cv) return <LoadingState label="Đang tải danh sách offer…" />;

  const isRecruiter = cv.isRecruiter;
  // Nhãn "Đã đến / Không nhận việc" lấy từ payload, không hard-code tiếng Việt.
  const onboardLabels = cv.onboardResultLabels || {};

  return (
    <div>
      <div className="filterbar">
        <span className="muted" style={{ fontSize: 13 }}>{rows.length} ứng viên đã Pass phỏng vấn</span>
      </div>

      <div className="card">
        <div className="tbl-wrap tbl-scroll">
          <table className="tbl">
            <thead><tr>
              <th>Họ tên ứng viên</th><th>Ngày ứng tuyển</th><th>Vị trí ứng tuyển</th>
              <th>Bước hiện tại</th><th>Offer</th><th>Ngày nhận việc</th>
              <th>Kết quả nhận việc</th><th></th>
            </tr></thead>
            <tbody>
              {pg.rows.map((r) => (
                <tr key={r.id}>
                  <td>
                    <div className="nm">{r.name || '—'}</div>
                    <div className="id">{[r.phone, r.email].filter(Boolean).join(' · ') || '—'}</div>
                  </td>
                  <td className="muted mono">{fmtDate(r.dateReceived)}</td>
                  <td>{r.jobName || '—'}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {r.stage
                      ? <Badge kind={STAGE_KIND[r.stageRef] || 'gray'}>{r.stage}</Badge>
                      : <span className="muted">—</span>}
                  </td>
                  <td style={{ maxWidth: 300 }}>
                    {isRecruiter ? (
                      <textarea
                        defaultValue={r.offerContent || ''}
                        placeholder="VD: Lương cứng 8tr, thử việc 85%…"
                        disabled={savingId === r.id}
                        onBlur={(e) => { if ((e.target.value || '') !== (r.offerContent || '')) saveField(r.id, { offerContent: e.target.value }); }}
                        style={{
                          width: 280, minHeight: 38, resize: 'vertical', padding: '6px 9px',
                          borderRadius: 8, border: '1px solid var(--border-strong)', background: '#fff',
                          fontSize: 12.5, lineHeight: 1.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
                          opacity: savingId === r.id ? 0.6 : 1,
                        }} />
                    ) : (r.offerContent
                      ? <span style={{ fontSize: 12.5, lineHeight: 1.5 }}>{r.offerContent}</span>
                      : <span className="muted">—</span>)}
                  </td>
                  <td>
                    {isRecruiter ? (
                      <input type="date"
                        value={r.startDate ? r.startDate.slice(0, 10) : ''}
                        disabled={savingId === r.id}
                        onChange={(e) => saveField(r.id, { startDate: e.target.value || '' })}
                        style={{
                          width: 150, padding: '6px 9px', borderRadius: 8,
                          border: '1px solid var(--border-strong)', background: '#fff',
                          fontSize: 12.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
                          opacity: savingId === r.id ? 0.6 : 1,
                        }} />
                    ) : (
                      <span className="muted mono">{r.startDate ? fmtDate(r.startDate) : '—'}</span>
                    )}
                  </td>
                  {/* Kết quả nhận việc (sheet 7.6) — chốt luồng cuối của tab này:
                      gửi thư mời xong thì chờ tới ngày hẹn, đến thì đánh "Đã đến"
                      rồi bấm Onboard, không đến thì đánh "Không nhận việc".
                      Bỏ trống = chưa xác định, KHÔNG phải một giá trị riêng. */}
                  <td style={{ whiteSpace: 'nowrap' }}>
                    {isRecruiter ? (
                      <select className="sel" value={r.onboardResult || ''}
                        disabled={savingId === r.id}
                        onChange={(e) => saveField(r.id, { onboardResult: e.target.value })}
                        style={{
                          fontSize: 12.5, minWidth: 148,
                          opacity: savingId === r.id ? 0.6 : 1,
                          color: r.onboardResult === 'no_show' ? 'var(--red-600)'
                            : r.onboardResult === 'arrived' ? 'var(--green)' : undefined,
                          fontWeight: r.onboardResult ? 700 : 400,
                        }}>
                        <option value="">— Chưa xác định —</option>
                        {Object.entries(onboardLabels).map(([k, l]) => (
                          <option key={k} value={k}>{l}</option>
                        ))}
                      </select>
                    ) : r.onboardResult ? (
                      <Badge kind={r.onboardResult === 'arrived' ? 'green' : 'red'} dot>
                        {onboardLabels[r.onboardResult] || r.onboardResult}</Badge>
                    ) : <span className="muted">—</span>}
                  </td>
                  {/* Hai chỗ đứng CỐ ĐỊNH bề rộng. Trước đây ô căn phải mà phần tử
                      thứ hai lúc là badge "Đã tạo hồ sơ · HB.357", lúc là nút
                      Onboard, lúc là chữ "Đã dừng" — mỗi dòng một bề rộng nên nút
                      Gửi mail bị đẩy so le, nhìn dọc cột thấy răng cưa. */}
                  <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>
                    <div style={{ display: 'inline-flex', gap: 8, alignItems: 'center' }}>
                      {/* Gửi mail đứng trước: gửi offer là việc làm TRƯỚC, onboard
                          chỉ tới khi ứng viên đã đồng ý. canSend từ payload mail
                          mẫu — cùng luật với tab Mail mẫu: HR hoặc trưởng phòng.
                          Tài khoản không được gửi thì không hiện nút (BE cũng đã
                          chặn /preview + /log-sent). */}
                      <span style={{ display: 'inline-flex', justifyContent: 'flex-end', minWidth: 104 }}>
                        {tmpls && tmpls.canSend && (
                          <button className="btn btn-primary btn-sm" onClick={() => setMailFor(r)}>
                            <Icon name="mail" size={14} />Gửi mail</button>
                        )}
                      </span>
                      <span style={{ display: 'inline-flex', justifyContent: 'flex-start', alignItems: 'center', minWidth: 172 }}>
                        {r.employeeId ? (
                          <Badge kind="teal">
                            <Icon name="check" size={12} /> Đã tạo hồ sơ{r.employeeCode ? ' · ' + r.employeeCode : ''}</Badge>
                        ) : r.onboardResult === 'no_show' ? (
                          // Bùng thì không còn hồ sơ nào để tạo — ẩn nút Onboard cho
                          // khỏi bấm nhầm. BE cũng chặn (BR-OB-02), đây chỉ là lớp mềm.
                          <span className="muted" style={{ fontSize: 12.5 }}>Đã dừng</span>
                        ) : isRecruiter ? (
                          <button className="btn btn-soft btn-sm" disabled={empBusyId === r.id} onClick={() => createEmployee(r)}>
                            <Icon name="user" size={14} />{empBusyId === r.id ? 'Đang tạo…' : 'Onboard'}</button>
                        ) : null}
                      </span>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {rows.length === 0 && <EmptyState>Chưa có ứng viên nào Pass phỏng vấn.</EmptyState>}
        <Pagination {...pg} />
      </div>

      <GuideNote title="Các bước bộ phận tuyển dụng cần làm ở màn này"
        steps={STEPS} note={GUIDE_NOTE} />

      {mailFor && (
        <MailSendModal applicant={mailFor} templates={(tmpls && tmpls.rows) || []}
          onSent={load} onClose={() => setMailFor(null)} />
      )}
    </div>
  );
}

/* Hướng dẫn thao tác của tab này — khung dùng chung ở GuideNote.jsx. */
const STEPS = [
  ['Kiểm tra danh sách',
   <>Ứng viên có <b>Kết quả PV = Pass</b> tự xuất hiện ở đây, không cần kéo thẻ
     trên kanban. Cột <b>Bước hiện tại</b> cho biết họ đang ở đâu: vàng
     “Kết quả phỏng vấn” = chưa gửi offer, còn việc phải làm.</>],
  ['Điền Offer & Ngày nhận việc',
   <>Gõ nội dung offer (lương, chế độ, thời gian thử việc) và chọn
     <b> Ngày nhận việc</b>. Nội dung tự lưu khi bạn bấm ra ngoài ô. Nên điền
     <b> trước</b> khi gửi mail vì mẫu thư mời nhận việc lấy dữ liệu từ hai ô này,
     và ngày nhận việc sẽ thành mốc bắt đầu thử việc của hồ sơ nhân viên.</>],
  ['Gửi thư mời nhận việc',
   <>Bấm <b>Gửi mail</b> → chọn mẫu <b>“Thư mời nhận việc – Học Bá”</b> →
     <b> Xem trước</b> để kiểm tra và chỉnh nội dung → <b>Mở Gmail</b> → bấm Gửi
     trong Gmail → quay lại bấm <b>“Đã gửi — lưu lịch sử”</b>. Bấm xong hệ thống
     tự chuyển ứng viên sang bước <b>Gửi Offer</b> và ghi vào Lịch sử gửi mail.</>],
  ['Chốt phản hồi của ứng viên',
   <>Ứng viên đồng ý thì ghi lại vào ô <b>Ghi chú Offer</b> / <b>UV xác nhận mail</b>
     ở hồ sơ ứng viên (tab Danh sách CV). Ứng viên từ chối thì kéo thẻ về bước phù
     hợp trên kanban — hệ thống không tự xử lý trường hợp từ chối.</>],
  ['Tới ngày hẹn: chốt Kết quả nhận việc',
   <>Gửi thư mời xong thì <b>chưa tạo hồ sơ</b> — chờ tới ngày hẹn xem ứng viên có
     đến không, rồi điền cột <b>Kết quả nhận việc</b>. <b>Đã đến</b> → làm tiếp bước
     dưới. <b>Không nhận việc</b> → dòng chuyển đỏ, nút Onboard biến mất, ứng viên
     vẫn nằm lại đây để còn theo dõi; chọn nhầm thì đổi lại được. Bỏ trống nghĩa là
     chưa xác định.</>],
  ['Onboard',
   <>Ứng viên nhận việc thì bấm <b>Onboard</b> để tạo hồ sơ nhân viên (trạng thái
     <b> Thử việc</b>), ứng viên tự chuyển sang bước <b>Onboarding</b>. Bấm nhầm 2
     lần không tạo trùng hồ sơ.</>],
  ['Hoàn tất hồ sơ & hết thử việc',
   <>Sang module <b>Nhân sự</b> điền nốt CCCD · MST · BHXH cho hồ sơ vừa tạo —
     thiếu ba mục này thì không chuyển Chính thức được. Hết thử việc, khi nhân
     viên <b>đạt cổng đánh giá và lên Chính thức</b>, ứng viên tự chuyển sang bước
     <b> Bàn giao nhân sự</b>; bước này mới trừ chỉ tiêu tuyển và kích hoạt tự ngừng
     đăng tin khi tuyển đủ.</>],
];

const GUIDE_NOTE = (
  <>Ba bước <b>3</b>, <b>6</b> và <b>7</b> tự đổi bước cho ứng viên, mỗi lần đều
    ghi một dòng vào lịch sử trao đổi của hồ sơ để truy lại được ai/khi nào. Hệ
    thống chỉ đẩy tới, không kéo lùi — ứng viên đã đi xa hơn thì đứng yên.</>
);

