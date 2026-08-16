/* Tab "Theo dõi tuyển dụng" — bảng theo PHIẾU YÊU CẦU đang tuyển. Owner: Việt.

   Ba tầng theo yêu cầu khách:
     1. Bảng cơ bản: Vị trí · Phòng ban · Trạng thái · Số lượng tuyển · Đã tuyển
        · Deadline (lấy từ "Ngày cần onboard" của phiếu).
     2. Bấm "Xem chi tiết" → xổ dòng dưới: Đã nộp CV · Đã tuyển (= ứng viên ở
        stage Bàn giao nhân sự, tức đã hoàn thiện thử việc) · Fail CV · Fail PV.
     3. Bấm vào con số → ApplicantsModal: danh sách ứng viên + thông tin JD.

   Bản trước gom theo phòng ban và lấy hr.job làm gốc; nay lấy PHIẾU làm gốc vì
   khách theo dõi theo đợt tuyển. Soạn/tra JD vẫn ở tab "Kho quản lý JD".

   API: GET /recruitment/jobs (data.requests) · /recruitment/request/<id>/applicants */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import Pagination, { usePaged } from '../../components/Pagination';
import { fmtDate } from '../../utils/format';
import { fetchJobs, updateJob } from '../../api/recruitment';
import ApplicantsModal, { APPLICANT_GROUPS, GROUP_COLOR } from './ApplicantsModal';
import CopyLinkBtn from './CopyLinkBtn';
import GuideNote from './GuideNote';

const TRACK_STEPS = [
  ['Đọc bảng',
   <>Mỗi dòng là <b>một đợt tuyển</b> (phiếu yêu cầu đã duyệt). Cột
     <b> Đã tuyển</b> đếm người đã sang bước <b>Bàn giao nhân sự</b> — tức đã lên
     Chính thức, không phải số người vừa nhận việc.</>],
  ['Ba trạng thái',
   <><b>Đang tuyển</b> = phiếu mở, tin đang đăng. <b>Dừng tuyển</b> = đã tắt tin
     nhưng phiếu vẫn mở, bật lại được. <b>Đã đóng</b> = phiếu đã chốt; tuyển đủ
     chỉ tiêu thì hệ thống tự đóng.</>],
  ['Xem phễu tuyển dụng',
   <>Bấm vào dòng để xổ phễu: <b>Tổng CV → CV pass → CV fail → PV → PV pass →
     PV fail → Nhận việc → Đã tuyển</b>. Di chuột vào ô để xem cách đếm.</>],
  ['Xem ứng viên nào',
   <>Bấm thẳng vào con số để mở danh sách ứng viên của nhóm đó; trong popup đổi
     qua lại giữa các nhóm được ngay.</>],
  ['Deadline',
   <>Lấy từ ô <b>Ngày cần onboard</b> của phiếu. Quá hạn mà chưa tuyển đủ thì hiện
     đỏ kèm số ngày trễ — sửa hạn ở tab <b>Phiếu yêu cầu</b>.</>],
];

const TRACK_GUIDE_NOTE = (
  <>Hai mốc <b>PV</b> và <b>Nhận việc</b> không có ô nhập riêng: hệ thống suy ra
    từ bước hiện tại cộng dữ liệu đã điền, nên số có thể nhích lên khi bạn cập
    nhật hồ sơ ứng viên.</>
);

/* Cột "Trạng thái" ghép HAI nguồn, ưu tiên từ nặng đến nhẹ:
     1. Phiếu không còn 'recruiting'  → Đã đóng   (tuyển đủ chỉ tiêu thì hệ thống
        tự đóng phiếu — xem hr_applicant._hb_auto_close_if_filled)
     2. JD đang 'stopped'             → Dừng tuyển (nút Ngừng đăng lật cờ này)
     3. còn lại                       → Đang tuyển
   Tách riêng vì hai khái niệm khác nhau: "đóng phiếu" là chốt đợt tuyển, còn
   "dừng tuyển / ngừng đăng" là tắt tin tuyển của JD mà đợt vẫn đang mở. */
const TRACK_STATUS = {
  closed:     ['Đã đóng',    'blue'],
  stopped:    ['Dừng tuyển', 'gray'],
  recruiting: ['Đang tuyển', 'green'],
};

/* Thứ tự xếp bảng: việc còn phải làm lên trước. Đợt đang tuyển là việc đang
   chạy; dừng tuyển vẫn còn mở nên có thể bật lại; đã đóng thì chỉ để tra cứu. */
const TRACK_ORDER = { recruiting: 0, stopped: 1, closed: 2 };

/* Tooltip từng ô số của phễu — nói rõ ĐẾM CÁI GÌ, vì hai mốc "PV" và
   "Nhận việc" không có trường riêng mà suy ra từ bước + dữ liệu đã điền
   (định nghĩa gốc: APPLICANT_GROUPS trong controllers/main.py). */
const GROUP_HINT = {
  cv:      'Tổng CV nhận vào đợt tuyển này',
  cv_pass: 'CV được đánh Pass ở khâu lọc CV',
  fail_cv: 'CV bị đánh Fail ở khâu lọc CV',
  pv:      'Đã vào vòng phỏng vấn: sang bước Phỏng vấn trở đi, hoặc đã có lịch hẹn / tình trạng tham gia / kết quả PV',
  pv_pass: 'Kết quả phỏng vấn Pass',
  fail_pv: 'Kết quả phỏng vấn Fail',
  onboard: 'Đã nhận việc: sang bước Onboarding trở đi, hoặc đã điền ngày nhận việc, hoặc đánh "Đã đến" — đã trừ ai bị đánh "Không nhận việc"',
  hired:   'Đã bàn giao nhân sự — hoàn thiện thử việc và lên Chính thức',
};

function trackStatus(r) {
  if (r.state !== 'recruiting') return 'closed';
  if (r.jobStatus === 'stopped') return 'stopped';
  return 'recruiting';
}

/* Deadline: chỉ báo động khi CÒN THIẾU người. Phiếu đã đủ chỉ tiêu mà quá hạn
   thì không phải việc cần xử lý nữa, tô đỏ chỉ gây nhiễu. */
function deadlineInfo(r) {
  if (!r.deadline) return null;
  const today = new Date(); today.setHours(0, 0, 0, 0);
  const d = new Date(r.deadline + 'T00:00:00');
  const days = Math.round((d - today) / 86400000);
  const missing = Math.max(0, (r.qty || 0) - (r.hired || 0));
  if (days < 0) return { days, late: missing > 0, text: `trễ ${-days} ngày` };
  if (days === 0) return { days, late: missing > 0, text: 'hôm nay' };
  return { days, late: false, soon: days <= 7, text: `còn ${days} ngày` };
}

export default function RequestTracking({ search }) {
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);
  const [dep, setDep] = useState('all');
  const [st, setSt] = useState('all');
  const [open, setOpen] = useState({});      // reqId -> đang xổ chi tiết
  const [popup, setPopup] = useState(null);  // { req, group }
  const [busyJob, setBusyJob] = useState(null);

  const load = () => { setErr(null); setData(null); fetchJobs().then(setData).catch((e) => setErr(e.message)); };
  useEffect(load, []);

  /* Một hàm lọc duy nhất cho cả bảng lẫn số trên chip, cho phép ghi đè từng
     tiêu chí. Số trên chip đếm theo các bộ lọc CÒN LẠI đang bật ("bấm chip này
     thì thấy bao nhiêu dòng") — đếm trên tập chưa lọc thì chọn phòng ban hoặc
     gõ ô tìm kiếm là chip đứng yên trong khi bảng đã đổi. Cùng khuôn với
     Phòng ban / Nhận việc / Nghỉ việc (xem Offboarding.jsx). */
  const keep = (r, o = {}) => {
    const s = 'st' in o ? o.st : st;
    const d = 'dep' in o ? o.dep : dep;
    if (s !== 'all' && trackStatus(r) !== s) return false;
    if (d !== 'all' && r.depId !== d) return false;
    if (search) {
      const q = search.toLowerCase();
      const hay = `${r.jobTitle || ''} ${r.depName || ''} ${r.code || ''}`.toLowerCase();
      if (!hay.includes(q)) return false;
    }
    return true;
  };

  /* Lọc + phân trang đặt TRƯỚC early-return (quy tắc hook — xem Requests.jsx). */
  const all = (data && data.requests) || [];
  const filtered = all.filter((r) => keep(r))
    /* Xếp theo TRACK_ORDER: Đang tuyển → Dừng tuyển → Đã đóng. Sort ổn định nên
       trong cùng nhóm vẫn giữ nguyên thứ tự BE trả về. */
    .sort((a, b) => TRACK_ORDER[trackStatus(a)] - TRACK_ORDER[trackStatus(b)]);
  const pg = usePaged(filtered, [st, dep, search]);

  if (err) return <ErrorState message={err} onRetry={load} />;
  if (!data) return <LoadingState label="Đang tải tiến độ tuyển dụng…" />;

  const { departments, isHr, isRecruiter } = data;

  const toggle = (id) => setOpen((p) => ({ ...p, [id]: !p[id] }));

  const togglePublish = async (jobId, next) => {
    setBusyJob(jobId);
    try {
      const det = await updateJob(jobId, { published: next });
      // Đồng bộ cả `jobStatus` chứ không chỉ `published`: nút này lật luôn trạng
      // thái tuyển của JD, cột "Trạng thái" phải đổi ngay chứ không đợi F5.
      setData((p) => ({
        ...p,
        rows: p.rows.map((x) => (x.id === det.id ? { ...x, ...det } : x)),
        requests: p.requests.map((q) => (q.jobId === det.id
          ? { ...q, published: det.published, jobStatus: det.status } : q)),
      }));
    } catch (e) { alert(e.message || 'Không đổi được trạng thái đăng tuyển.'); }
    finally { setBusyJob(null); }
  };

  const totalNeed = filtered.reduce((s, r) => s + (r.qty || 0), 0);
  const totalHired = filtered.reduce((s, r) => s + (r.hired || 0), 0);
  const lateCount = filtered.filter((r) => (deadlineInfo(r) || {}).late).length;

  return (
    <div>
      <div className="filterbar">
        <button className={'chip' + (st === 'all' ? ' active' : '')} onClick={() => setSt('all')}>
          Tất cả <span className="ct">{all.filter((r) => keep(r, { st: 'all' })).length}</span></button>
        {Object.entries(TRACK_STATUS).reverse().map(([key, [label]]) => (
          <button key={key} className={'chip' + (st === key ? ' active' : '')} onClick={() => setSt(key)}>
            {label} <span className="ct">{all.filter((r) => keep(r, { st: key })).length}</span></button>
        ))}
        {isHr && (
          <div style={{ marginLeft: 'auto' }}>
            <select className="sel" value={dep}
              onChange={(e) => setDep(e.target.value === 'all' ? 'all' : Number(e.target.value))}>
              <option value="all">Mọi phòng ban</option>
              {departments.map((d) => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
          </div>
        )}
      </div>

      <div className="filterbar" style={{ marginTop: -4 }}>
        <Badge kind="blue">Cần tuyển {totalNeed}</Badge>
        <Badge kind="green">Đã tuyển {totalHired}</Badge>
        <Badge kind={totalNeed - totalHired > 0 ? 'amber' : 'teal'}>
          Còn thiếu {Math.max(0, totalNeed - totalHired)}</Badge>
        {lateCount > 0 && <Badge kind="red" dot>Trễ deadline {lateCount}</Badge>}
      </div>

      <div className="card">
        <div className="tbl-wrap tbl-scroll">
          <table className="tbl">
            <thead><tr>
              <th style={{ width: 34 }}></th>
              <th>Vị trí</th><th>Phòng ban</th><th>Trạng thái</th>
              <th className="tbl-num">Số lượng tuyển</th>
              <th className="tbl-num">Đã tuyển</th>
              <th>Deadline</th>
              <th></th>
            </tr></thead>
            <tbody>
              {pg.rows.map((r) => {
                const dl = deadlineInfo(r);
                const isOpen = !!open[r.id];
                return [
                  <tr key={r.id} onClick={() => toggle(r.id)} style={{ cursor: 'pointer' }}>
                    <td>
                      <Icon name="chevR" size={17} className="faint"
                        style={{ transform: isOpen ? 'rotate(90deg)' : 'none', transition: 'transform .12s' }} />
                    </td>
                    <td>
                      <div className="nm">{r.jobTitle}
                        {r.levelLabel && <span className="muted" style={{ fontWeight: 400 }}> · {r.levelLabel}</span>}
                      </div>
                      <div className="id">{r.code}</div>
                    </td>
                    <td className="muted">{r.depName}</td>
                    <td>
                      <Badge kind={TRACK_STATUS[trackStatus(r)][1]} dot>
                        {TRACK_STATUS[trackStatus(r)][0]}</Badge>
                      {trackStatus(r) === 'stopped' && (
                        <div className="id" title="Phiếu vẫn mở, chỉ đang tắt tin tuyển">
                          phiếu còn mở</div>
                      )}
                    </td>
                    <td className="tbl-num mono">{r.qty || 0}</td>
                    <td className="tbl-num mono" style={{ fontWeight: 700 }}>{r.hired || 0}</td>
                    <td>
                      {!dl ? <span className="muted">Chưa đặt</span> : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                          <span className="mono" style={dl.late ? { color: 'var(--red-600)', fontWeight: 700 } : undefined}>
                            {fmtDate(r.deadline)}</span>
                          <span style={{
                            fontSize: 11.5,
                            color: dl.late ? 'var(--red-600)' : dl.soon ? 'var(--amber-700, #b45309)' : 'var(--muted)',
                          }}>{dl.text}</span>
                        </div>
                      )}
                    </td>
                    <td>
                      <button className="btn btn-ghost btn-sm"
                        onClick={(e) => { e.stopPropagation(); toggle(r.id); }}>
                        {isOpen ? 'Thu gọn' : 'Xem chi tiết'}</button>
                    </td>
                  </tr>,
                  isOpen && (
                    <tr key={`${r.id}-detail`}>
                      <td colSpan={8} style={{ background: 'var(--bg-soft, #fafafa)', padding: '14px 18px' }}>
                        {/* 8 ô của phễu: dùng flex-basis chứ KHÔNG min-width — bảng nằm
                            trong khung cuộn ngang, min-width sẽ kéo cả bảng rộng ra và
                            đẩy ô cuối khỏi màn thay vì xuống dòng. Chặn bề ngang ở 950px
                            vì bảng (1220px) rộng hơn vùng nhìn thấy: để dải phễu giãn hết
                            bề ngang bảng thì ô "Đã tuyển" rơi ra ngoài, phải cuộn mới thấy.
                            920 = 8×104 + 7×10 gap + dư, vừa khít khung ~964px của khung cuộn
                            trừ padding ô; màn hẹp hơn thì tự xuống hàng. */}
                        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', maxWidth: 920 }}>
                          {APPLICANT_GROUPS.map(([key, label, countKey, tone]) => (
                            <button key={key} className="card"
                              onClick={() => setPopup({ req: r, group: key })}
                              title={`${GROUP_HINT[key]} · bấm để xem danh sách ứng viên`}
                              style={{
                                padding: '11px 12px', flex: '1 1 104px', minWidth: 0,
                                textAlign: 'left',
                                cursor: 'pointer', border: '1px solid var(--border)', background: '#fff',
                              }}>
                              {/* Nhãn một dòng, cắt bằng "…" nếu hẹp — ô chỉ ~106px,
                                  để nhãn xuống dòng thì tám ô cao thấp so le. */}
                              <div className="muted" style={{
                                fontSize: 12, whiteSpace: 'nowrap',
                                overflow: 'hidden', textOverflow: 'ellipsis',
                              }}>{label}</div>
                              {/* Mũi tên nằm CÙNG HÀNG với con số thay vì thành dòng
                                  "Xem danh sách →" riêng: dòng đó cần ~92px trong khi ô
                                  chỉ còn ~82px bề ngang chữ nên bị thòi ra ngoài. Ý nghĩa
                                  "bấm để xem danh sách" đã có ở tooltip của cả ô. */}
                              <div style={{
                                display: 'flex', alignItems: 'center', gap: 4, marginTop: 2,
                              }}>
                                <span style={{
                                  fontSize: 22, fontWeight: 800, lineHeight: 1.15,
                                  color: GROUP_COLOR[tone || ''],
                                }}>{r[countKey] || 0}</span>
                                <Icon name="chevR" size={15} className="faint"
                                  style={{ marginLeft: 'auto', flexShrink: 0 }} />
                              </div>
                            </button>
                          ))}
                        </div>

                        <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginTop: 14 }}>
                          {!r.jobId ? (
                            <span className="muted" style={{ fontSize: 12.5 }}>
                              Phiếu chưa gắn JD — chưa đăng tuyển và chưa đếm được ứng viên.</span>
                          ) : (
                            <>
                              {r.published && <Badge kind="teal">PUBLISHED</Badge>}
                              {r.published && <CopyLinkBtn url={r.websiteUrl} label="Chép link" />}
                              {isRecruiter && (
                                <button className="btn btn-ghost btn-sm" disabled={busyJob === r.jobId}
                                  onClick={() => togglePublish(r.jobId, !r.published)}>
                                  <Icon name={r.published ? 'x' : 'check'} size={14} />
                                  {r.published ? 'Ngừng đăng' : 'Đăng tuyển'}</button>
                              )}
                              {r.jdLink && (
                                <a className="btn btn-ghost btn-sm" href={r.jdLink} target="_blank" rel="noreferrer">
                                  <Icon name="file" size={14} />Mở file JD</a>
                              )}
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ),
                ];
              })}
            </tbody>
          </table>
        </div>
        {filtered.length === 0 && (
          <EmptyState>Không có phiếu yêu cầu nào đang tuyển.</EmptyState>
        )}
        <Pagination {...pg} />
      </div>

      <GuideNote title="Cách đọc màn này" steps={TRACK_STEPS}
        note={<>Mỗi CV thuộc <b>đúng một đợt tuyển</b> — gắn sai thì sửa ô
          <b> Đợt tuyển</b> trong form CV; CV nộp lúc vị trí không mở đợt nào sẽ
          không lên bảng này. {TRACK_GUIDE_NOTE}</>} />

      {popup && (
        <ApplicantsModal req={popup.req} group={popup.group} onClose={() => setPopup(null)} />
      )}
    </div>
  );
}
