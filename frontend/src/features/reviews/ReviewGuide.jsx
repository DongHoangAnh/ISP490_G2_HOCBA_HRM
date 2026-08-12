/* Tab "Hướng dẫn chấm điểm" của màn Đánh giá — tài liệu cho người chấm:
   quy trình, công thức, bảng quy đổi điểm, bộ tiêu chí, ví dụ tính tay.

   Mọi con số lấy từ API /reviews/guide (đọc ir.config_parameter + hằng số của
   model) chứ KHÔNG chép cứng: HR sửa trọng số hay ngưỡng xếp loại thì hướng dẫn
   đổi theo, không bao giờ dạy sai so với điểm hệ thống thực chấm.
   Nguồn nghiệp vụ: docs/CONG_THUC_DANH_GIA.md */
import { useState } from 'react';
import useFetch from '../../hooks/useFetch';
import { fetchReviewGuide } from '../../api/reviews';
import Icon from '../../components/Icon';
import Badge from '../../components/Badge';
import TblWrap from '../../components/TblWrap';
import { LoadingState, ErrorState } from '../../components/states';
import AnchorList from './AnchorList';
import { GRADE_KIND, AUTO_SOURCE_LABEL, unitLabel } from './util';

const round1 = (n) => Math.round(n * 10) / 10;

const GROUPS = [['teacher', 'Giảng viên'], ['office', 'Nhân viên văn phòng']];

/* Quy đổi chỉ số -> điểm theo bảng ngưỡng giảm dần — trùng _bucket() backend. */
const bucket = (value, table) =>
  (table.find((r) => value >= r.min) || table[table.length - 1]).score;

const gradeOf = (total, grades) =>
  grades.find((g) => total >= g.min) || grades[grades.length - 1];

function Section({ icon, title, sub, children }) {
  return (
    <section className="card" style={{ padding: '16px 18px', marginBottom: 14 }}>
      <div style={{ display: 'flex', gap: 9, alignItems: 'center', marginBottom: 4 }}>
        <Icon name={icon} size={17} />
        <h2 style={{ fontSize: 15, fontWeight: 800, margin: 0 }}>{title}</h2>
      </div>
      {sub && <p className="muted" style={{ fontSize: 12.5, margin: '0 0 12px' }}>{sub}</p>}
      {children}
    </section>
  );
}

/* Khối công thức — nền xám, chữ đều nét cho dễ đọc phép tính. */
function Formula({ children }) {
  return (
    <pre style={{
      margin: '0 0 10px', padding: '11px 14px', overflowX: 'auto',
      background: 'var(--surface-2)', border: '1px solid var(--border)',
      borderRadius: 10, fontSize: 12.5, lineHeight: 1.7,
      fontFamily: 'ui-monospace, SFMono-Regular, Menlo, Consolas, monospace',
    }}>{children}</pre>
  );
}

const STEPS = [
  ['Mở đợt đánh giá', 'HR / Admin',
    'Chọn nhóm và kỳ ở tab Giảng viên hoặc Nhân viên văn phòng rồi bấm "Mở đợt '
    + 'đánh giá" — hệ thống tạo phiếu Nháp cho toàn bộ nhân sự đang làm việc '
    + 'của nhóm. Bấm lại không tạo trùng, chỉ bổ sung người còn thiếu.'],
  ['Hệ thống tính chỉ số', 'Tự động',
    'Ngay lúc tạo phiếu, các tiêu chí có nguồn tự động được điền sẵn điểm đề '
    + 'xuất từ dữ liệu chấm công và chứng chỉ trong kỳ. Bấm "Tính lại chỉ số" '
    + 'trong phiếu để cập nhật khi dữ liệu thay đổi.'],
  ['Chấm điểm & nhận xét', 'Trưởng phòng · Giáo vụ · HR',
    'Bấm vào dòng nhân viên để mở phiếu, chấm 0–5 cho từng tiêu chí. Điểm đề '
    + 'xuất sửa đè được — khi sửa, hãy ghi lý do vào ô ghi chú của tiêu chí đó.'],
  ['Chốt phiếu', 'Người chấm',
    'Chốt được khi đã có ít nhất một tiêu chí khác 0 và đã nhập "Nhận xét của '
    + 'quản lý". Chốt xong, chỉ số và điểm bị đóng băng làm bằng chứng đánh giá.'],
  ['Công bố kết quả', 'Chỉ HR / Admin',
    'Nhân viên nhận thông báo trong app kèm tổng điểm và xếp loại. Muốn sửa sau '
    + 'khi chốt thì HR phải "Mở lại phiếu" — thao tác này có lưu vết.'],
];

const PRINCIPLES = [
  ['Máy đề xuất, người quyết định',
    'Chỉ số tự động chỉ điền sẵn một con số khởi điểm. Quản lý là người chịu '
    + 'trách nhiệm về điểm cuối cùng và nên ghi lý do mỗi khi sửa đè.'],
  ['Không có dữ liệu thì không chấm',
    'Nhân viên mới, nghỉ thai sản, chưa có bản ghi chấm công… hệ thống để trống '
    + 'cho quản lý chấm tay chứ không quy về 0 điểm. Thiếu dữ liệu không đồng '
    + 'nghĩa với làm việc kém.'],
  ['Chỉ số là ảnh chụp tại thời điểm chốt',
    'Sau khi chốt, dữ liệu chấm công có sửa thì phiếu vẫn giữ nguyên con số cũ. '
    + 'Muốn tính lại phải nhờ HR mở lại phiếu.'],
  ['Trọng số được sao chép vào phiếu lúc tạo',
    'Sửa cấu hình tiêu chí hôm nay không làm đổi các phiếu đã chấm trước đó — '
    + 'nên đổi trọng số vào đầu kỳ, trước khi mở đợt.'],
];

/* Chấm cho đều tay — phần người chấm hay lúng túng nhất, đặt ngay dưới thang. */
const HOW_TO_PICK = [
  ['Luôn xuất phát từ mốc giữa',
    'Đọc mô tả mức "Đạt yêu cầu" trước và hỏi: nhân viên này có làm đúng như '
    + 'vậy không? Đúng thì chấm mốc giữa, rồi mới xét có bằng chứng để nhích '
    + 'lên hay phải hạ xuống. Đừng bắt đầu bằng cảm giác "người này khá" rồi '
    + 'tìm số cho khớp.'],
  ['Mỗi điểm phải gắn với một việc có thật trong kỳ',
    'Không nêu được ví dụ cụ thể thì đừng cho mức cao nhất, và cũng đừng cho '
    + 'mức thấp nhất. Không có bằng chứng nghĩa là chưa quan sát đủ, không phải '
    + 'nhân viên trung bình.'],
  ['Cho điểm cao nhất hoặc từ 2 trở xuống thì bắt buộc ghi chú',
    'Ô ghi chú của từng tiêu chí chính là thứ bảo vệ người chấm khi nhân viên '
    + 'thắc mắc, và là căn cứ để HR đối chiếu giữa các phòng.'],
  ['So với chuẩn của vị trí, không so nhân viên với nhau',
    'Cả phòng cùng tốt thì cả phòng cùng điểm cao — không có hạn ngạch cho mỗi '
    + 'mức. Xếp hạng nội bộ là việc của bước sau, không phải của ô điểm.'],
  ['Chấm cả kỳ, không chấm tháng cuối',
    'Mở lại ghi chú, email, biên bản họp trong kỳ trước khi bấm điểm — trí nhớ '
    + 'luôn nghiêng về chuyện vừa xảy ra.'],
];

const COMMON_MISTAKES = [
  ['Dồn hết về mức giữa cho an toàn',
    'Phiếu nào cũng 3–4 thì tổng điểm ai cũng na ná nhau, không chỉ ra được ai '
    + 'cần hỗ trợ và ai xứng đáng được thưởng — công sức chấm thành vô ích.'],
  ['Hiệu ứng hào quang',
    'Nhân viên giỏi chuyên môn nên tiêu chí nào cũng được điểm cao. Hãy chấm '
    + 'từng tiêu chí độc lập, đọc lại mô tả mốc trước mỗi dòng.'],
  ['Thiên vị chuyện mới xảy ra',
    'Một sự cố tuần trước kéo tụt cả kỳ, hoặc một thành tích sát ngày chấm che '
    + 'mất ba tháng trì trệ.'],
  ['Chấm theo quan hệ',
    'Thân thiết hay từng va chạm đều làm lệch điểm. Nếu thấy mình đang nghĩ về '
    + 'con người thay vì công việc, dừng lại và quay về mô tả mốc.'],
];

/* §4 — bộ tiêu chí của một nhóm, kèm dòng tổng trọng số. */
function CriteriaTable({ rows, weightSum }) {
  return (
    <TblWrap>
      <table className="tbl tbl-prose">
        <thead>
          <tr>
            <th>Tiêu chí</th>
            <th style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>Trọng số</th>
            <th style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>Thang điểm</th>
            <th>Nguồn chấm</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.code}>
              <td>
                <div style={{ fontWeight: 600 }}>{c.name}</div>
                {c.guideline && (
                  <div className="muted" style={{ fontSize: 12, marginTop: 2 }}>
                    {c.guideline}
                  </div>
                )}
                {c.anchors.length > 0 && (
                  <details style={{ marginTop: 5 }}>
                    <summary style={{
                      cursor: 'pointer', fontSize: 12, fontWeight: 600,
                      color: 'var(--red-700, var(--ink))',
                    }}>Mốc chấm điểm: làm thế nào thì mấy điểm?</summary>
                    <div style={{ marginTop: 6 }}>
                      <AnchorList anchors={c.anchors} />
                    </div>
                  </details>
                )}
              </td>
              <td style={{ textAlign: 'right', fontWeight: 700 }}>{c.weight}%</td>
              <td style={{ textAlign: 'right' }}>0–{c.maxScore}</td>
              <td>
                {c.autoSource === 'none'
                  ? <Badge kind="gray">Quản lý chấm tay</Badge>
                  : <Badge kind="teal">
                    Tự động · {AUTO_SOURCE_LABEL[c.autoSource] || ''}
                  </Badge>}
              </td>
            </tr>
          ))}
          <tr>
            <td style={{ fontWeight: 700 }}>Tổng trọng số</td>
            <td style={{ textAlign: 'right', fontWeight: 800 }}>
              {round1(weightSum)}%
            </td>
            <td colSpan={2} className="faint" style={{ fontSize: 11.5 }}>
              {Math.abs(weightSum - 100) < 0.01
                ? 'Đủ 100% — chuẩn.'
                : 'Khác 100% vẫn chấm đúng: mẫu số của công thức là tổng trọng số thực tế.'}
            </td>
          </tr>
        </tbody>
      </table>
    </TblWrap>
  );
}

/* Bảng ngưỡng "chỉ số ≥ X → n điểm". */
function BucketTable({ head, rows, unit = '%' }) {
  return (
    <TblWrap>
      <table className="tbl tbl-prose">
        <thead>
          <tr>
            <th>{head}</th>
            <th style={{ textAlign: 'right' }}>Điểm</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((r, i) => (
            <tr key={r.min}>
              {/* Dòng cuối là ngưỡng sàn (min = 0) — diễn đạt "dưới X" cho dễ đọc. */}
              <td>{i > 0 && i === rows.length - 1
                ? `Dưới ${rows[i - 1].min}${unit}`
                : `Từ ${r.min}${unit} trở lên`}</td>
              <td style={{ textAlign: 'right', fontWeight: 700 }}>{r.score}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </TblWrap>
  );
}

/* Kịch bản mẫu của 2 nhóm. Điểm chấm tay ghi theo MÃ tiêu chí để ví dụ kể được
   một câu chuyện có cao có thấp; tiêu chí không nêu tên thì mặc định 4. */
const EXAMPLE = {
  teacher: {
    who: 'cô Nguyễn Thị A — giảng viên',
    period: 'Quý 3',
    sessions: 58,
    violated: 3,
    manual: {},
    manualNote: 'Các tiêu chí định tính quản lý chấm 4/5.',
    reading: 'Điểm bị kéo xuống chủ yếu ở tiêu chí chuyên cần — đây chính là '
      + 'điểm cải thiện cụ thể, đo được, để trao đổi với giáo viên cho kỳ sau.',
  },
  office: {
    who: 'anh Trần Văn B — nhân viên văn phòng',
    period: 'Nửa năm 2',
    units: 118,
    late: 4,
    early: 2,
    manual: { o_result: 5, o_potential: 3 },
    manualNote: 'Quản lý chấm: Kết quả công việc 5/5 (vượt mục tiêu đã thống '
      + 'nhất đầu kỳ), Tiềm năng phát triển 3/5, các tiêu chí còn lại 4/5.',
    reading: 'Tiêu chí trọng số lớn nhất kéo cả phiếu: chỉ riêng KPI 5/5 đã góp '
      + '35 điểm. Ngược lại, chuyên cần 3/5 làm mất 8 điểm — đủ để tụt một bậc '
      + 'xếp loại nếu tổng đang sát ngưỡng.',
  },
};

/* §7 — ví dụ tính tay, chấm trên CHÍNH bộ tiêu chí đang cấu hình.
   Kịch bản cố định, điểm tự động suy ra từ bảng quy đổi thật → ví dụ luôn khớp
   với kết quả hệ thống sẽ cho nếu HR nhập đúng dữ liệu đó. */
function WorkedExample({ d, group }) {
  const rows = d.criteria[group] || [];
  const ex = EXAMPLE[group];
  if (!rows.length) return null;

  const teacher = group === 'teacher';
  const quarter = d.periods.find((p) => p.type === 'quarter') || { sessionTarget: 60 };
  /* Giảng viên đếm buổi dạy vi phạm; văn phòng đếm ngày trễ + ngày về sớm. */
  const units = teacher ? ex.sessions : ex.units;
  const bad = teacher ? ex.violated : ex.late + ex.early;
  const punctualPct = units ? (units - bad) / units * 100 : 0;
  const workloadPct = quarter.sessionTarget
    ? ex.sessions / quarter.sessionTarget * 100 : 0;
  /* 2 chứng chỉ còn hạn = nhánh cuối của bảng quy đổi chứng chỉ. */
  const certScore = d.autoTables.cert[d.autoTables.cert.length - 1].score;

  const sampleScore = (c) => {
    if (c.autoSource === 'punctuality') return bucket(punctualPct, d.autoTables.punctuality);
    if (c.autoSource === 'workload') return bucket(workloadPct, d.autoTables.workload);
    if (c.autoSource === 'cert') return certScore;
    return ex.manual[c.code] ?? 4;   // tiêu chí định tính — quản lý tự chấm
  };

  const lines = rows.map((c) => {
    const score = Math.min(sampleScore(c), c.maxScore);
    const ratio = c.maxScore ? score / c.maxScore : 0;
    return { ...c, score, ratio, acc: ratio * c.weight };
  });
  const wsum = lines.reduce((s, l) => s + (l.maxScore > 0 ? l.weight : 0), 0);
  const accSum = lines.reduce((s, l) => s + l.acc, 0);
  const total = wsum ? round1(accSum / wsum * 100) : 0;
  const grade = gradeOf(total, d.grades);

  return (
    <>
      <p style={{ fontSize: 12.5, margin: '0 0 10px' }}>
        <b>Tình huống:</b> {ex.who}, kỳ đánh giá {ex.period}.{' '}
        {teacher ? (
          <>
            Trong kỳ có <b>{ex.sessions} buổi dạy</b> chấm công, trong đó{' '}
            <b>{ex.violated} buổi vi phạm</b> (chấm công ngoài cửa sổ giờ hoặc
            sai vị trí), hồ sơ có <b>2 chứng chỉ đã xác minh còn hạn</b>.
          </>
        ) : (
          <>
            Trong kỳ có <b>{ex.units} ngày công</b>, trong đó{' '}
            <b>{ex.late} ngày đi trễ</b> và <b>{ex.early} ngày về sớm</b> (không
            trùng ngày nào).
          </>
        )}{' '}
        {ex.manualNote}
      </p>
      <Formula>
        {teacher
          ? (`Đúng giờ  : (${ex.sessions} − ${ex.violated}) / ${ex.sessions} × 100 = ${round1(punctualPct)}%`
            + `  → ${bucket(punctualPct, d.autoTables.punctuality)} điểm\n`
            + `Khối lượng: ${ex.sessions} / ${round1(quarter.sessionTarget)} buổi × 100 = ${round1(workloadPct)}%`
            + `  → ${bucket(workloadPct, d.autoTables.workload)} điểm\n`
            + `Chứng chỉ : 2 chứng chỉ còn hạn                → ${certScore} điểm`)
          : (`Ngày công đạt : ${units} − (${ex.late} trễ + ${ex.early} về sớm) = ${units - bad} ngày\n`
            + `Đúng giờ      : ${units - bad} / ${units} × 100 = ${round1(punctualPct)}%`
            + `  → ${bucket(punctualPct, d.autoTables.punctuality)} điểm`)}
      </Formula>
      <TblWrap>
        <table className="tbl tbl-prose">
          <thead>
            <tr>
              <th>Tiêu chí</th>
              <th style={{ textAlign: 'right' }}>Trọng số</th>
              <th style={{ textAlign: 'right' }}>Điểm</th>
              <th style={{ textAlign: 'right' }}>Tỷ lệ đạt</th>
              <th style={{ textAlign: 'right' }}>Tỷ lệ × trọng số</th>
            </tr>
          </thead>
          <tbody>
            {lines.map((l) => (
              <tr key={l.code}>
                <td>
                  {l.name}{' '}
                  <span className="faint" style={{ fontSize: 11 }}>
                    ({l.autoSource === 'none' ? 'chấm tay' : 'tự động'})
                  </span>
                </td>
                <td style={{ textAlign: 'right' }}>{l.weight}%</td>
                <td style={{ textAlign: 'right' }}>{l.score}/{l.maxScore}</td>
                <td style={{ textAlign: 'right' }}>{round1(l.ratio * 100)}%</td>
                <td style={{ textAlign: 'right' }}>{round1(l.acc)}</td>
              </tr>
            ))}
            <tr>
              <td style={{ fontWeight: 700 }}>Cộng</td>
              <td style={{ textAlign: 'right', fontWeight: 700 }}>{round1(wsum)}%</td>
              <td colSpan={2}></td>
              <td style={{ textAlign: 'right', fontWeight: 800 }}>{round1(accSum)}</td>
            </tr>
          </tbody>
        </table>
      </TblWrap>
      <Formula>
        {`TỔNG = ${round1(accSum)} / ${round1(wsum)} × 100 = ${total} điểm`}
      </Formula>
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap' }}>
        <span style={{ fontSize: 12.5 }}>Kết quả:</span>
        <Badge kind={GRADE_KIND[grade.key] || 'gray'}>{grade.label}</Badge>
        <span className="muted" style={{ fontSize: 12.5 }}>{ex.reading}</span>
      </div>
    </>
  );
}

export default function ReviewGuide() {
  const [group, setGroup] = useState('teacher');      // bộ tiêu chí ở mục 5
  const [example, setExample] = useState('teacher');  // ví dụ tính tay ở mục 7
  const { data: d, err, loading, reload } = useFetch(
    fetchReviewGuide, [], 'reviews:guide');

  if (err) return <ErrorState message={err} onRetry={reload} />;
  if (loading || !d) return <LoadingState label="Đang tải hướng dẫn chấm điểm…" />;

  const rule = d.punctualRule[group];

  return (
    <div style={{ maxWidth: 960 }}>
      <Section icon="list" title="1. Một đợt đánh giá chạy thế nào"
        sub="Năm bước, mỗi bước một người chịu trách nhiệm.">
        <div style={{ display: 'grid', gap: 9 }}>
          {STEPS.map(([title, who, desc], i) => (
            <div key={title} style={{ display: 'flex', gap: 11, alignItems: 'flex-start' }}>
              <div style={{
                flex: '0 0 26px', width: 26, height: 26, borderRadius: '50%',
                background: 'var(--red-600)', color: '#fff', fontWeight: 800,
                fontSize: 13, display: 'flex', alignItems: 'center',
                justifyContent: 'center', marginTop: 1,
              }}>{i + 1}</div>
              <div>
                <div style={{ display: 'flex', gap: 7, alignItems: 'center', flexWrap: 'wrap' }}>
                  <span style={{ fontWeight: 700, fontSize: 13.5 }}>{title}</span>
                  <Badge kind="gray">{who}</Badge>
                </div>
                <div className="muted" style={{ fontSize: 12.5, marginTop: 2 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section icon="calculator" title="2. Công thức tính tổng điểm"
        sub="Ý tưởng một câu: mỗi tiêu chí được giao sẵn một số điểm tối đa (chính là trọng số của nó); chấm được bao nhiêu phần của thang thì lấy bấy nhiêu phần số điểm đó.">
        <div style={{
          padding: '11px 14px', marginBottom: 12, fontSize: 12.5,
          background: 'var(--red-50)', borderRadius: 11,
          border: '1px solid var(--red-100, var(--border))',
        }}>
          Ví dụ tiêu chí <b>trọng số 25%</b>, thang 0–5, người chấm cho{' '}
          <b>4 điểm</b>: nhân viên đạt 4/5 = <b>80%</b> của tiêu chí đó, nên tiêu
          chí này góp <b>80% × 25 = 20 điểm</b> vào tổng. Chấm 5/5 thì góp trọn
          25 điểm, chấm 0 thì góp 0. Làm vậy với mọi tiêu chí rồi cộng lại là ra
          tổng điểm.
        </div>

        <div style={{ fontWeight: 700, fontSize: 13.5, marginBottom: 7 }}>
          Các thành phần trong công thức
        </div>
        <TblWrap>
          <table className="tbl tbl-prose">
            <thead>
              <tr>
                <th style={{ width: 130 }}>Thành phần</th>
                <th>Là gì</th>
                <th style={{ width: 190 }}>Ví dụ</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ fontWeight: 700 }}>Điểm chấm</td>
                <td className="muted">Con số người chấm bấm cho một tiêu chí.</td>
                <td>4</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700 }}>Điểm tối đa</td>
                <td className="muted">
                  Thang của tiêu chí đó, mặc định 5. Xem cột "Thang điểm" ở mục 5.
                </td>
                <td>5</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700 }}>Tỷ lệ đạt</td>
                <td className="muted">
                  Điểm chấm chia cho điểm tối đa — nhân viên đạt được bao nhiêu
                  phần của tiêu chí này. Luôn nằm giữa 0 và 1.
                </td>
                <td>4 / 5 = 0,8 (tức 80%)</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700 }}>Trọng số</td>
                <td className="muted">
                  Tiêu chí này quan trọng cỡ nào, tính bằng % của cả bài đánh
                  giá. Cũng chính là <b>số điểm tối đa</b> nó góp vào tổng 100.
                </td>
                <td>25%</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700 }}>Σ (xích ma)</td>
                <td className="muted">
                  Ký hiệu "cộng tất cả lại" — cộng qua toàn bộ tiêu chí của phiếu.
                </td>
                <td>6 tiêu chí cộng lại</td>
              </tr>
              <tr>
                <td style={{ fontWeight: 700 }}>Tổng điểm</td>
                <td className="muted">
                  Kết quả cuối trên thang 100, dùng để tra xếp loại ở mục 3.
                </td>
                <td>82,0 → loại B</td>
              </tr>
            </tbody>
          </table>
        </TblWrap>

        <div style={{ fontWeight: 700, fontSize: 13.5, margin: '14px 0 7px' }}>
          Viết thành công thức
        </div>
        <Formula>
          {'Bước 1 — tỷ lệ đạt của một tiêu chí:\n'
            + '    tỷ lệ đạt = điểm chấm / điểm tối đa        (0 → 1)\n\n'
            + 'Bước 2 — cộng qua tất cả tiêu chí, quy về thang 100:\n'
            + '              Σ (tỷ lệ đạt × trọng số)\n'
            + '    TỔNG =  ───────────────────────── × 100\n'
            + '                   Σ trọng số'}
        </Formula>
        <p className="muted" style={{ fontSize: 12.5, margin: 0 }}>
          <b>Vì sao phải chia cho Σ trọng số?</b> Mẫu số là tổng trọng số{' '}
          <b>thực tế</b> của phiếu chứ không phải 100 cố định. Khi HR tắt bớt một
          tiêu chí, nhân viên không bị mất điểm oan: bỏ tiêu chí trọng số 5 thì
          phần còn lại được chia trên 95, không phải 100. Nếu tổng trọng số đúng
          bằng 100 thì phép chia này không đổi gì cả.
        </p>
      </Section>

      <Section icon="award" title="3. Bảng quy đổi xếp loại"
        sub="Ngưỡng lấy từ cấu hình hệ thống — HR đổi ngưỡng thì bảng này đổi theo.">
        <TblWrap>
          <table className="tbl tbl-prose">
            <thead>
              <tr>
                <th>Xếp loại</th>
                <th>Khoảng điểm</th>
                <th>Đọc hiểu &amp; hành động</th>
              </tr>
            </thead>
            <tbody>
              {d.grades.map((g) => (
                <tr key={g.key}>
                  <td><Badge kind={GRADE_KIND[g.key] || 'gray'}>{g.label}</Badge></td>
                  <td style={{ whiteSpace: 'nowrap', fontWeight: 600 }}>
                    {g.max == null
                      ? `Từ ${round1(g.min)} điểm trở lên`
                      : `${round1(g.min)} → dưới ${round1(g.max)}`}
                  </td>
                  <td className="muted" style={{ fontSize: 12.5 }}>{g.meaning}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TblWrap>
      </Section>

      <Section icon="target" title={`4. Chọn điểm nào trên thang 0–${d.scaleMax}?`}
        sub="Phần quan trọng nhất khi chấm tay: mỗi mức nghĩa là gì, và làm sao để hai quản lý khác nhau chấm ra kết quả gần nhau.">
        <TblWrap>
          <table className="tbl tbl-prose">
            <thead>
              <tr>
                <th style={{ width: 60 }}>Điểm</th>
                <th style={{ width: 140 }}>Mức</th>
                <th>Chọn khi nào</th>
              </tr>
            </thead>
            <tbody>
              {d.scale.map((s) => (
                <tr key={s.score}>
                  <td style={{ fontWeight: 800, fontSize: 15 }}>{s.score}</td>
                  <td style={{ fontWeight: 600 }}>
                    {s.label}
                    {s.key === 'zero' && (
                      <div style={{ marginTop: 3 }}>
                        <Badge kind="amber">Cẩn thận</Badge>
                      </div>
                    )}
                  </td>
                  <td className="muted" style={{ fontSize: 12.5 }}>{s.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TblWrap>
        <p className="muted" style={{ fontSize: 12.5, margin: '10px 0 4px' }}>
          Mô tả trên là nghĩa chung của từng mức. Còn <b>hành vi cụ thể</b> ứng
          với mức cao nhất / đạt yêu cầu / không đạt thì mỗi tiêu chí một khác —
          xem phần "Mốc chấm điểm" của từng tiêu chí ở mục 5, hoặc bấm ngay
          trong phiếu khi đang chấm.
        </p>

        <div style={{ fontWeight: 700, fontSize: 13.5, margin: '14px 0 7px' }}>
          Năm thói quen giúp chấm đều tay
        </div>
        <div style={{ display: 'grid', gap: 9 }}>
          {HOW_TO_PICK.map(([title, desc], i) => (
            <div key={title} style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
              <div style={{
                flex: '0 0 22px', width: 22, height: 22, borderRadius: 7,
                background: 'var(--surface-2)', border: '1px solid var(--border)',
                fontWeight: 800, fontSize: 12, display: 'flex',
                alignItems: 'center', justifyContent: 'center',
              }}>{i + 1}</div>
              <div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{title}</div>
                <div className="muted" style={{ fontSize: 12.5 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>

        <div style={{ fontWeight: 700, fontSize: 13.5, margin: '16px 0 7px' }}>
          Bốn lỗi hay gặp
        </div>
        <div style={{ display: 'grid', gap: 9 }}>
          {COMMON_MISTAKES.map(([title, desc]) => (
            <div key={title} style={{ display: 'flex', gap: 9, alignItems: 'flex-start' }}>
              <Icon name="alertTriangle" size={15} />
              <div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>{title}</div>
                <div className="muted" style={{ fontSize: 12.5 }}>{desc}</div>
              </div>
            </div>
          ))}
        </div>
      </Section>

      <Section icon="star" title="5. Bộ tiêu chí và trọng số"
        sub="Hai bộ tách riêng cho hai nhóm nhân sự. Mở &quot;Mốc chấm điểm&quot; ở từng tiêu chí để xem hành vi nào ứng với mức nào.">
        <div style={{ display: 'flex', gap: 7, marginBottom: 11 }}>
          {GROUPS.map(([id, l]) => (
            <button key={id} type="button"
              className={'btn btn-sm ' + (group === id ? 'btn-primary' : 'btn-ghost')}
              onClick={() => setGroup(id)}>{l}</button>
          ))}
        </div>
        <CriteriaTable rows={d.criteria[group] || []}
          weightSum={d.weightSum[group] || 0} />
      </Section>

      <Section icon="chart" title="6. Chỉ số tự động quy ra điểm thế nào"
        sub="Ba tiêu chí được hệ thống chấm sẵn từ dữ liệu vận hành. Người chấm vẫn sửa đè được.">
        <div style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 700, fontSize: 13.5, marginBottom: 3 }}>
            6.1. Chuyên cần &amp; đúng giờ
          </div>
          <p className="muted" style={{ fontSize: 12.5, margin: '0 0 8px' }}>
            Nguồn: {rule.source}. {rule.okWhen} Tỷ lệ đúng giờ ={' '}
            số {rule.unit} đạt / tổng số {rule.unit} trong kỳ × 100.
          </p>
          <BucketTable head="Tỷ lệ đúng giờ trong kỳ"
            rows={d.autoTables.punctuality} />
          <div style={{
            marginTop: 8, padding: '9px 13px', fontSize: 12.5,
            background: 'var(--surface-2)', border: '1px solid var(--border)',
            borderRadius: 10,
          }}>
            <b>Không có {unitLabel(group)} nào trong kỳ</b> → hệ thống bỏ trống,
            không chấm 0. Người chấm tự quyết định (nhân viên mới, nghỉ dài hạn…).
          </div>
        </div>

        <div style={{ marginBottom: 16 }}>
          <div style={{ fontWeight: 700, fontSize: 13.5, marginBottom: 3 }}>
            6.2. Khối lượng giảng dạy <span className="faint">(chỉ giảng viên)</span>
          </div>
          <p className="muted" style={{ fontSize: 12.5, margin: '0 0 8px' }}>
            Chỉ tiêu {d.params.teacherSessionsTarget} buổi mỗi quý, quy đổi theo
            độ dài kỳ:{' '}
            {d.periods.map((p) => `${p.label.toLowerCase()} ${round1(p.sessionTarget)} buổi`)
              .join(' · ')}. Tỷ lệ = số buổi dạy thực tế / chỉ tiêu của kỳ × 100.
          </p>
          <BucketTable head="Tỷ lệ hoàn thành chỉ tiêu" rows={d.autoTables.workload} />
        </div>

        <div>
          <div style={{ fontWeight: 700, fontSize: 13.5, marginBottom: 3 }}>
            6.3. Chuẩn chứng chỉ <span className="faint">(chỉ giảng viên)</span>
          </div>
          <p className="muted" style={{ fontSize: 12.5, margin: '0 0 8px' }}>
            Chỉ đếm chứng chỉ <b>đã xác minh</b> trên hồ sơ nhân viên. Chứng chỉ
            hết hạn trong vòng {d.params.certAlertDays} ngày tới được coi là
            &quot;sắp hết hạn&quot;. Xét từ trên xuống, gặp trường hợp đúng đầu
            tiên thì lấy điểm đó.
          </p>
          <TblWrap>
            <table className="tbl tbl-prose">
              <thead>
                <tr>
                  <th>Trường hợp</th>
                  <th style={{ textAlign: 'right' }}>Điểm</th>
                  <th>Ý nghĩa</th>
                </tr>
              </thead>
              <tbody>
                {d.autoTables.cert.map((r) => (
                  <tr key={r.score}>
                    <td>{r.when}</td>
                    <td style={{ textAlign: 'right', fontWeight: 700 }}>{r.score}</td>
                    <td className="muted" style={{ fontSize: 12.5 }}>{r.note}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </TblWrap>
        </div>
      </Section>

      <Section icon="book" title="7. Ví dụ tính tay"
        sub="Chấm thử trên chính bộ tiêu chí đang cấu hình ở mục 5 — mỗi nhóm một tình huống.">
        <div style={{ display: 'flex', gap: 7, marginBottom: 11 }}>
          {GROUPS.map(([id, l]) => (
            <button key={id} type="button"
              className={'btn btn-sm ' + (example === id ? 'btn-primary' : 'btn-ghost')}
              onClick={() => setExample(id)}>{l}</button>
          ))}
        </div>
        <WorkedExample d={d} group={example} />
      </Section>

      <Section icon="info" title="8. Nguyên tắc khi vận hành">
        <div style={{ display: 'grid', gap: 10 }}>
          {PRINCIPLES.map(([title, desc]) => (
            <div key={title}>
              <div style={{ fontWeight: 700, fontSize: 13 }}>{title}</div>
              <div className="muted" style={{ fontSize: 12.5 }}>{desc}</div>
            </div>
          ))}
        </div>
      </Section>
    </div>
  );
}
