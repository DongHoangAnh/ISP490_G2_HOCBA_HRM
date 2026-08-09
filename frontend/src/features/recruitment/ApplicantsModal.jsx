/* Popup "xem chi tiết số ứng viên" — mở khi bấm vào một con số ở dòng chi tiết
   của tab Theo dõi tuyển dụng (RequestTracking.jsx). Owner: Việt.

   Hai phần: khối JD / phiếu yêu cầu ở trên (để đối chiếu đang tuyển cái gì) và
   danh sách ứng viên thuộc nhóm vừa bấm ở dưới. Đổi nhóm ngay trong popup bằng
   hàng chip — người xem hay so "fail CV" với "fail PV", bắt đóng ra mở lại thì
   mất mạch.

   API: GET /recruitment/request/<id>/applicants?group=<khoá trong APPLICANT_GROUPS> */
import { useState, useEffect } from 'react';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import Modal from '../../components/Modal';
import { LoadingState, ErrorState, EmptyState } from '../../components/states';
import { fmtDate } from '../../utils/format';
import { fetchRequestApplicants } from '../../api/recruitment';
import { CV_RESULT_KIND, INTERVIEW_RESULT_KIND, REQUEST_STATE_KIND } from './util';

/* Phễu tuyển dụng của một đợt, đọc từ trái sang phải theo đúng thứ tự ứng viên
   đi qua. Định nghĩa từng mốc nằm ở backend (APPLICANT_GROUPS trong
   controllers/main.py) — cùng một domain dùng cho cả con số lẫn danh sách nên
   bấm vào số nào ra đúng người của số đó.

   Cột thứ 4 là tông màu: 'ok' cho mốc đi tiếp được, 'bad' cho mốc bị loại,
   bỏ trống cho con số trung tính (tổng đầu vào). */
export const APPLICANT_GROUPS = [
  ['cv',      'Tổng CV',    'cvCount', ''],
  ['cv_pass', 'CV pass',    'cvPass',  'ok'],
  ['fail_cv', 'CV fail',    'failCv',  'bad'],
  ['pv',      'PV',         'pvCount', ''],
  ['pv_pass', 'PV pass',    'pvPass',  'ok'],
  ['fail_pv', 'PV fail',    'failPv',  'bad'],
  ['onboard', 'Nhận việc',  'onboard', 'ok'],
  ['hired',   'Đã tuyển',   'hired',   'ok'],
];

/* Màu con số theo tông. Dùng chung với RequestTracking để hai chỗ không lệch. */
export const GROUP_COLOR = {
  ok: 'var(--green)',
  bad: 'var(--red-600)',
  '': 'var(--ink)',
};

const GROUP_LABEL = Object.fromEntries(APPLICANT_GROUPS.map(([k, l]) => [k, l]));

export default function ApplicantsModal({ req, group: group0, onClose }) {
  const [group, setGroup] = useState(group0 || 'cv');
  const [data, setData] = useState(null);
  const [err, setErr] = useState(null);

  const load = () => {
    setErr(null); setData(null);
    fetchRequestApplicants(req.id, group).then(setData).catch((e) => setErr(e.message));
  };
  useEffect(load, [req.id, group]);

  const jd = (data && data.jd) || {};
  const rows = (data && data.rows) || [];
  const cvLabels = (data && data.cvResultLabels) || {};
  const pvLabels = (data && data.interviewResultLabels) || {};

  /* Thông tin JD hiện dạng nhãn–giá trị; bỏ hẳn dòng rỗng thay vì hiện "—" cho
     kín bảng: phiếu tuyển thường bỏ trống nửa số ô, hiện hết thì khối JD dài
     gấp đôi danh sách ứng viên mà chẳng nói thêm điều gì. */
  const jdRows = [
    ['Mã phiếu', jd.code],
    ['Phòng ban', jd.depName],
    ['Người tạo phiếu', jd.requester],
    ['Ngày order', fmtDate(jd.dateRequest)],
    ['Số lượng cần tuyển', jd.qty],
    ['Deadline (ngày cần onboard)', fmtDate(jd.deadline)],
    ['Cấp bậc', jd.levelLabel],
    ['Lý do tuyển', jd.reasonLabel],
    ['Hình thức làm việc', jd.workTypeLabel],
    ['Mức lương dự kiến', jd.salary],
    ['Bằng cấp tối thiểu', jd.educationLabel],
    ['Kinh nghiệm tối thiểu', jd.experienceYears ? `${jd.experienceYears} năm` : ''],
    ['Ngoại ngữ', jd.languageRequirement],
  ].filter(([, v]) => v === 0 || !!v);

  return (
    <Modal onClose={onClose} lg>
      <div className="drawer-head" style={{ background: 'linear-gradient(120deg,var(--red-50),#fff)' }}>
        <div style={{ width: 56, height: 56, borderRadius: 14, background: 'var(--red-600)', color: '#fff', display: 'grid', placeItems: 'center', flexShrink: 0 }}>
          <Icon name="users" size={26} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <h2 style={{ margin: 0, fontSize: 21, fontWeight: 800, letterSpacing: '-.4px' }}>
              {req.jobTitle || jd.jobTitle || 'Phiếu tuyển dụng'}</h2>
            <Badge kind={REQUEST_STATE_KIND[jd.state || req.state] || 'gray'} dot>
              {jd.stateLabel || req.stateLabel || '—'}</Badge>
          </div>
          <div className="muted" style={{ fontSize: 13.5, marginTop: 3 }}>
            {GROUP_LABEL[group]} · {rows.length} ứng viên
          </div>
        </div>
        <div className="modal-x">
          <button className="icon-btn" onClick={onClose}><Icon name="x" size={20} /></button>
        </div>
      </div>

      <div className="filterbar" style={{ padding: '12px 24px', margin: 0, borderBottom: '1px solid var(--border)' }}>
        {APPLICANT_GROUPS.map(([key, label, countKey]) => (
          <button key={key} className={'chip' + (group === key ? ' active' : '')}
            onClick={() => setGroup(key)}>
            {label} <span className="ct">{req[countKey] || 0}</span>
          </button>
        ))}
      </div>

      <div style={{ padding: '18px 24px', maxHeight: '58vh', overflowY: 'auto' }}>
        {/* Khối JD — thu gọn được vì người mở popup phần lớn đến vì danh sách
            ứng viên, JD chỉ để đối chiếu khi cần. */}
        <details style={{ marginBottom: 18 }} open>
          <summary style={{ cursor: 'pointer', fontWeight: 700, fontSize: 13.5, marginBottom: 10 }}>
            Thông tin vị trí &amp; JD
          </summary>
          <div className="grid-2" style={{ rowGap: 14 }}>
            {jdRows.map(([k, v]) => (
              <div className="kv" key={k}><div className="k">{k}</div><div className="v">{v}</div></div>
            ))}
          </div>
          {jd.skillDescription && (
            <div style={{ marginTop: 14 }}>
              <div className="k" style={{ marginBottom: 4 }}>Kỹ năng yêu cầu</div>
              <div className="muted" style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{jd.skillDescription}</div>
            </div>
          )}
          {jd.jdDescription && (
            <div style={{ marginTop: 14 }}>
              <div className="k" style={{ marginBottom: 4 }}>Mô tả công việc (JD)</div>
              <div className="muted" style={{ fontSize: 13, whiteSpace: 'pre-wrap' }}>{jd.jdDescription}</div>
            </div>
          )}
          {jd.jdLink && (
            <div style={{ marginTop: 14 }}>
              <a className="btn btn-ghost btn-sm" href={jd.jdLink} target="_blank" rel="noreferrer">
                <Icon name="file" size={14} />Mở file JD</a>
            </div>
          )}
        </details>

        {err && <ErrorState message={err} onRetry={load} />}
        {!data && !err && <LoadingState label="Đang tải danh sách ứng viên…" />}
        {data && rows.length === 0 && (
          <EmptyState>Chưa có ứng viên nào ở nhóm “{GROUP_LABEL[group]}”.</EmptyState>
        )}
        {data && rows.length > 0 && (
          <div className="tbl-wrap tbl-scroll">
            <table className="tbl">
              <thead><tr>
                <th>Ứng viên</th><th>Liên hệ</th><th>Ngày nhận CV</th>
                <th>Bước hiện tại</th><th>Lọc CV</th><th>Kết quả PV</th>
                <th>Ngày nhận việc</th><th>CV</th>
              </tr></thead>
              <tbody>
                {rows.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <div className="nm">{a.name || '(chưa có tên)'}</div>
                      {a.employeeName && <div className="id">NV: {a.employeeCode || a.employeeName}</div>}
                    </td>
                    <td className="muted" style={{ fontSize: 12.5 }}>
                      {a.phone || '—'}{a.email ? <><br />{a.email}</> : null}
                    </td>
                    <td className="mono">{fmtDate(a.dateReceived)}</td>
                    <td><Badge kind="gray">{a.stage || '—'}</Badge></td>
                    <td>{a.cvResult
                      ? <Badge kind={CV_RESULT_KIND[a.cvResult] || 'gray'}>
                          {cvLabels[a.cvResult] || a.cvResult}</Badge>
                      : <span className="muted">—</span>}</td>
                    <td>{a.interviewResult
                      ? <Badge kind={INTERVIEW_RESULT_KIND[a.interviewResult] || 'gray'}>
                          {pvLabels[a.interviewResult] || a.interviewResult}</Badge>
                      : <span className="muted">—</span>}</td>
                    <td className="mono">{fmtDate(a.startDate) || '—'}</td>
                    <td>{a.cvFileUrl || a.cvLink
                      ? <a className="btn btn-ghost btn-sm" href={a.cvFileUrl || a.cvLink}
                          target="_blank" rel="noreferrer"><Icon name="file" size={13} />Xem</a>
                      : <span className="muted">—</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Modal>
  );
}
