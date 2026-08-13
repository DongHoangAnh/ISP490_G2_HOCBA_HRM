/* Tab "Offer & Nhận việc" — danh sách ứng viên đã Pass phỏng vấn.
   Hiển thị: họ tên, ngày ứng tuyển, vị trí, bước hiện tại, nội dung offer,
   ngày nhận việc + gửi mail.
   Gửi mail: chọn mẫu từ tab Mail mẫu; server tự điền thông tin ứng viên khi render. */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { useSort, SortTh } from '../../components/sortable';
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

/* Sắp cột "Bước hiện tại" theo chặng đường thật, không theo bảng chữ cái.
   Bước lạ (admin thêm mới) rơi xuống cuối. */
const STAGE_ORDER = {
  hb_stage_result: 1, hb_stage_offer: 2, hb_stage_onboarding: 3, hb_stage_hired: 4,
};

export default function Offers({ search }) {
  const [cv, setCv] = useState(null);
  const [tmpls, setTmpls] = useState(null);
  const [err, setErr] = useState(null);
  const [mailFor, setMailFor] = useState(null); // ứng viên đang gửi mail

  const [savingId, setSavingId] = useState(null);
  const sort = useSort();
  const [fStage, setFStage] = useState('all');     // theo mã bước
  const [fJob, setFJob] = useState('all');         // vị trí ứng tuyển
  const [fResult, setFResult] = useState('all');   // kết quả nhận việc ('' = chưa xác định)
  const [fNoOffer, setFNoOffer] = useState(false); // chưa điền nội dung offer
  const [fNoDate, setFNoDate] = useState(false);   // chưa hẹn ngày nhận việc

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
  const searched = (cv ? cv.rows : [])
    .filter(inOfferScope)
    .filter((r) => {
      if (!search) return true;
      const q = search.toLowerCase();
      return [r.name, r.phone, r.email, r.jobName].some((v) => (v || '').toLowerCase().includes(q));
    })
    // Mặc định: hẹn nhận việc gần nhất lên đầu. Bấm tiêu đề cột thì sort đè lên.
    .sort((a, b) => (b.startDate || '').localeCompare(a.startDate || ''));

  /* Chip bước dựng từ chính dữ liệu, giữ đúng thứ tự chặng đường. */
  const stageChips = [];
  for (const r of searched) {
    const k = r.stageRef || '';
    const c = stageChips.find((x) => x.k === k);
    if (c) c.n += 1;
    else stageChips.push({ k, lbl: r.stage || 'Chưa có bước', n: 1 });
  }
  stageChips.sort((a, b) => (STAGE_ORDER[a.k] || 99) - (STAGE_ORDER[b.k] || 99));
  const jobOptions = [...new Set(searched.map((r) => r.jobName).filter(Boolean))]
    .sort((a, b) => a.localeCompare(b, 'vi'));
  const noOfferCount = searched.filter((r) => !r.offerContent).length;
  const noDateCount = searched.filter((r) => !r.startDate).length;

  const filtered = searched.filter((r) => {
    if (fStage !== 'all' && (r.stageRef || '') !== fStage) return false;
    if (fJob !== 'all' && r.jobName !== fJob) return false;
    // fResult === '' → lọc đúng nhóm CHƯA xác định kết quả.
    if (fResult !== 'all' && (r.onboardResult || '') !== fResult) return false;
    if (fNoOffer && r.offerContent) return false;
    if (fNoDate && r.startDate) return false;
    return true;
  });
  const hasFilter = fStage !== 'all' || fJob !== 'all' || fResult !== 'all' || fNoOffer || fNoDate;
  const clearFilter = () => {
    setFStage('all'); setFJob('all'); setFResult('all');
    setFNoOffer(false); setFNoDate(false);
  };

  const rows = sort.apply(filtered, {
    name: (r) => r.name,
    applied: (r) => r.dateReceived,
    job: (r) => r.jobName,
    stage: (r) => STAGE_ORDER[r.stageRef] || 99,
    start: (r) => r.startDate,
    // Chưa xác định xuống cuối; còn lại: Đã đến trước, Không nhận việc sau.
    result: (r) => (r.onboardResult === 'arrived' ? 1
      : r.onboardResult === 'no_show' ? 2 : null),
  });
  const pg = usePaged(rows, [search, fStage, fJob, fResult, fNoOffer, fNoDate,
    sort.key, sort.dir]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!cv) return <LoadingState label="Đang tải danh sách offer…" />;

  const isRecruiter = cv.isRecruiter;
  // Nhãn "Đã đến / Không nhận việc" lấy từ payload, không hard-code tiếng Việt.
  const onboardLabels = cv.onboardResultLabels || {};

  return (
    <div>
      <div className="filterbar">
        <button className={'chip' + (fStage === 'all' ? ' active' : '')}
          onClick={() => setFStage('all')}>
          Tất cả <span className="ct">{searched.length}</span></button>
        {stageChips.map((c) => (
          <button key={c.k} className={'chip' + (fStage === c.k ? ' active' : '')}
            onClick={() => setFStage(c.k)}>
            {c.lbl} <span className="ct">{c.n}</span></button>
        ))}
        <button className={'chip' + (fNoOffer ? ' active' : '')}
          title="Ứng viên chưa được điền nội dung offer"
          onClick={() => setFNoOffer((v) => !v)}>
          Chưa điền offer <span className="ct">{noOfferCount}</span></button>
        <button className={'chip' + (fNoDate ? ' active' : '')}
          title="Ứng viên chưa chốt ngày nhận việc"
          onClick={() => setFNoDate((v) => !v)}>
          Chưa hẹn ngày <span className="ct">{noDateCount}</span></button>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 9, alignItems: 'center' }}>
          <select className="sel" value={fJob} onChange={(e) => setFJob(e.target.value)}>
            <option value="all">Mọi vị trí</option>
            {jobOptions.map((j) => <option key={j}>{j}</option>)}
          </select>
          <select className="sel" value={fResult} onChange={(e) => setFResult(e.target.value)}>
            <option value="all">Mọi kết quả nhận việc</option>
            <option value="">— Chưa xác định —</option>
            {Object.entries(onboardLabels).map(([k, l]) => (
              <option key={k} value={k}>{l}</option>
            ))}
          </select>
          {hasFilter && (
            <button className="btn btn-ghost btn-sm" onClick={clearFilter}>Xoá lọc</button>
          )}
        </div>
      </div>
      <div className="muted" style={{ fontSize: 13, margin: '0 0 10px' }}>
        {rows.length} ứng viên
        {hasFilter ? ` (lọc từ ${searched.length} đã Pass phỏng vấn)` : ' đã Pass phỏng vấn'}
      </div>

      <div className="card">
        <div className="tbl-wrap tbl-scroll">
          <table className="tbl">
            {/* Cột Offer không sắp xếp được: ô nhập nhiều dòng, sắp theo nội dung
                tự do không giúp gì cho người dùng. */}
            <thead><tr>
              <SortTh sort={sort} k="name">Họ tên ứng viên</SortTh>
              <SortTh sort={sort} k="applied">Ngày ứng tuyển</SortTh>
              <SortTh sort={sort} k="job">Vị trí ứng tuyển</SortTh>
              <SortTh sort={sort} k="stage">Bước hiện tại</SortTh>
              <th>Offer</th>
              <SortTh sort={sort} k="start">Ngày nhận việc</SortTh>
              <SortTh sort={sort} k="result">Kết quả nhận việc</SortTh>
              <th></th>
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
                        ) : r.onboardResult !== 'arrived' ? (
                          // Chưa chốt "Đã đến" thì chưa có gì để onboard: tới ngày hẹn
                          // mà chưa biết ứng viên có đến hay không, tạo hồ sơ NV là
                          // tạo sớm. Bắt HR đánh Kết quả nhận việc trước, nút mới hiện.
                          <span className="muted" style={{ fontSize: 12.5 }}>Chờ kết quả nhận việc</span>
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
        {rows.length === 0 && (
          <EmptyState>
            {hasFilter || search ? 'Không có ứng viên nào khớp bộ lọc hiện tại.'
              : 'Chưa có ứng viên nào Pass phỏng vấn.'}
          </EmptyState>
        )}
        <Pagination {...pg} />
      </div>

      <GuideNote title="Các bước cần làm ở màn này"
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
  ['Xem danh sách',
   <>Ứng viên <b>Pass phỏng vấn</b> tự vào đây, không cần kéo thẻ kanban. Cột
     <b> Bước hiện tại</b> màu vàng = chưa gửi offer, còn việc phải làm.</>],
  ['Điền Offer & Ngày nhận việc',
   <>Gõ nội dung offer và chọn ngày — tự lưu khi bấm ra ngoài ô. Điền
     <b> trước</b> khi gửi mail, vì thư mời lấy dữ liệu từ hai ô này và ngày nhận
     việc là mốc bắt đầu thử việc.</>],
  ['Gửi thư mời nhận việc',
   <><b>Gửi mail</b> → mẫu <b>“Thư mời nhận việc”</b> → <b>Xem trước</b> →
     <b> Mở Gmail</b> → gửi → quay lại bấm <b>“Đã gửi — lưu lịch sử”</b>. Bấm xong
     ứng viên tự sang bước <b>Gửi Offer</b>.</>],
  ['Chốt Kết quả nhận việc',
   <>Tới ngày hẹn mới chốt: <b>Đã đến</b> hoặc <b>Không nhận việc</b> (bỏ trống =
     chưa xác định). Chọn “Không nhận việc” thì nút Onboard ẩn đi; chọn nhầm đổi
     lại được.</>],
  ['Onboard',
   <>Nút <b>Onboard</b> chỉ hiện khi kết quả là <b>Đã đến</b>. Bấm để tạo hồ sơ
     nhân viên (<b>Thử việc</b>); bấm hai lần không tạo trùng.</>],
  ['Hoàn tất hồ sơ',
   <>Sang module <b>Nhân sự</b> điền CCCD · MST · BHXH — thiếu thì không lên
     Chính thức được. Khi nhân viên lên Chính thức, ứng viên tự sang bước
     <b> Bàn giao nhân sự</b> và mới trừ chỉ tiêu tuyển.</>],
];

const GUIDE_NOTE = (
  <>Ứng viên <b>từ chối offer</b> thì kéo thẻ trên kanban — hệ thống không tự xử
    lý. Mọi lần đổi bước đều ghi vào lịch sử hồ sơ, và chỉ đẩy tới chứ không kéo
    lùi: ai đã đi xa hơn thì đứng yên.</>
);

