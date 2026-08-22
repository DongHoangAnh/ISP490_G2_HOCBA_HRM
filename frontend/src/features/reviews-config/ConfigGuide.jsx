/* Tab "Hướng dẫn cấu hình": ngưỡng xếp loại + tham số, giải thích công thức
   bằng chính bộ câu hỏi HR đang cấu hình, và nhắc phiếu Nháp còn dùng cấu hình cũ.
   Owner: Việt.
   Spec: docs/superpowers/specs/2026-08-21-reviews-config-design.md */
import Icon from '../../components/Icon';

const inp = {
  width: '100%', padding: '8px 11px', borderRadius: 9,
  border: '1px solid var(--border-strong)', background: '#fff',
  fontSize: 13.5, color: 'var(--ink)', outline: 'none', fontFamily: 'inherit',
};
const th = {
  fontSize: 11, fontWeight: 700, color: 'var(--muted)',
  textTransform: 'uppercase', letterSpacing: '.3px', textAlign: 'left',
  padding: '8px 10px',
};
const td = { padding: '7px 10px', fontSize: 13.5, borderTop: '1px solid var(--border)' };

const GRADE_NOTE = {
  a: 'Vượt mong đợi — xét thưởng, đề bạt, giao việc thử thách hơn.',
  b: 'Hoàn thành tốt nhiệm vụ — duy trì, phát triển thêm thế mạnh.',
  c: 'Hoàn thành ở mức đạt — chốt 1–2 điểm cải thiện cho kỳ sau.',
  d: 'Chưa đạt — lập kế hoạch cải thiện có mốc thời gian.',
};

const AUTO_NOTE = {
  none: 'Quản lý tự chấm, đối chiếu 3 mốc mô tả hành vi của câu hỏi.',
  punctuality: 'Hệ thống chấm theo tỷ lệ buổi dạy / ngày công hợp lệ trong kỳ.',
  workload: 'Hệ thống chấm theo số buổi dạy so với chỉ tiêu của kỳ (chỉ giảng viên).',
  cert: 'Hệ thống chấm theo chứng chỉ đã xác minh trên hồ sơ (hết hạn → sắp hết hạn → còn hạn).',
};

function Card({ title, icon, children, tone }) {
  return (
    <div className="card" style={{ marginBottom: 18 }}>
      <div className="card-head" style={{ padding: '12px 16px', alignItems: 'center' }}>
        <div style={{
          width: 30, height: 30, borderRadius: 8, marginRight: 11,
          background: tone || 'var(--blue)', color: '#fff',
          display: 'grid', placeItems: 'center',
        }}>
          <Icon name={icon} size={15} />
        </div>
        <div className="t" style={{ fontSize: 15, fontWeight: 700 }}>{title}</div>
      </div>
      <div className="card-body" style={{ padding: 16 }}>{children}</div>
    </div>
  );
}

/* Điểm "mức giữa" của một câu hỏi — đúng công thức anchor_levels() ở backend. */
const midScore = (max) => Math.max(1, Math.floor((max + 1) / 2));

export default function ConfigGuide({
  data, grading, setGrading, onSaveGrading, saving, groupRows,
}) {
  const g = grading;
  const setG = (field, val) => setGrading({ ...g, [field]: val });

  // Ví dụ tính tay: lấy chính bộ câu hỏi của tab Giảng viên đang mở, giả sử
  // người chấm cho tất cả ở "mức giữa" — HR thấy ngay cấu hình của mình cho ra
  // bao nhiêu điểm, thay vì phải tin một ví dụ chép cứng.
  const rows = (groupRows || []).filter((r) => r.active && r.maxScore > 0);
  const wSum = rows.reduce((s, r) => s + r.weight, 0);
  const acc = rows.reduce((s, r) => s + (midScore(r.maxScore) / r.maxScore) * r.weight, 0);
  const total = wSum ? (acc / wSum) * 100 : 0;
  const grade = total >= g.gradeA ? 'A' : total >= g.gradeB ? 'B'
    : total >= g.gradeC ? 'C' : 'D';

  const drafts = (data.draftCount || {});
  const draftTotal = (drafts.teacher || 0) + (drafts.office || 0);

  return (
    <div style={{ maxWidth: 980 }}>
      {draftTotal > 0 && (
        <div className="card" style={{
          marginBottom: 18, padding: '12px 16px', display: 'flex', gap: 10,
          alignItems: 'flex-start', borderLeft: '3px solid var(--gold-600)',
        }}>
          <Icon name="alertTriangle" size={17} />
          <div style={{ fontSize: 13.5, lineHeight: 1.6 }}>
            Còn <b>{draftTotal} phiếu Nháp</b> (giảng viên {drafts.teacher || 0},
            văn phòng {drafts.office || 0}) đang dùng cấu hình cũ. Phiếu đã tạo
            giữ nguyên trọng số và thang điểm lúc mở đợt — muốn áp cấu hình vừa
            sửa thì <b>mở đợt đánh giá mới</b> ở màn Đánh giá nhân viên.
          </div>
        </div>
      )}

      <Card title="Ngưỡng xếp loại & tham số" icon="target" tone="var(--green)">
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 14 }}>
          {[
            ['gradeA', 'A — Xuất sắc từ'], ['gradeB', 'B — Tốt từ'],
            ['gradeC', 'C — Đạt từ'],
          ].map(([field, label]) => (
            <label key={field} style={{ display: 'grid', gap: 5 }}>
              <span style={th}>{label}</span>
              <input type="number" min="1" max="100" step="1" style={inp}
                value={g[field]}
                onChange={(e) => setG(field, Number(e.target.value || 0))} />
            </label>
          ))}
          <label style={{ display: 'grid', gap: 5 }}>
            <span style={th}>Chỉ tiêu buổi dạy / quý</span>
            <input type="number" min="1" step="1" style={inp}
              value={g.sessionsTarget}
              onChange={(e) => setG('sessionsTarget', Number(e.target.value || 0))} />
          </label>
        </div>
        <div className="muted" style={{ fontSize: 12.5, marginTop: 10, lineHeight: 1.6 }}>
          Dưới ngưỡng C là loại D. Ngưỡng phải giảm dần (A &gt; B &gt; C &gt; 0).
          Ngưỡng dùng chung cho cả hai nhóm, và <b>áp dụng ngay</b> cho phiếu
          Nháp — phiếu đã chốt/công bố giữ nguyên kết quả cũ.
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: 12 }}>
          <tbody>
            {[
              ['a', `TOTAL ≥ ${g.gradeA}`], ['b', `${g.gradeB} ≤ TOTAL < ${g.gradeA}`],
              ['c', `${g.gradeC} ≤ TOTAL < ${g.gradeB}`], ['d', `TOTAL < ${g.gradeC}`],
            ].map(([k, cond]) => (
              <tr key={k}>
                <td style={{ ...td, width: 44, fontWeight: 800 }}>{k.toUpperCase()}</td>
                <td style={{ ...td, width: 210 }}>{cond}</td>
                <td style={{ ...td, color: 'var(--muted)' }}>{GRADE_NOTE[k]}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div style={{ marginTop: 14 }}>
          <button className="btn btn-primary" onClick={onSaveGrading} disabled={saving}>
            <Icon name="checkCircle" size={16} className="mr-s" />
            {saving ? 'Đang lưu…' : 'Lưu ngưỡng & tham số'}
          </button>
        </div>
      </Card>

      <Card title="Công thức tính tổng điểm" icon="calculator">
        <div style={{
          fontFamily: 'ui-monospace, monospace', fontSize: 13, background: 'var(--surface-2)',
          padding: '10px 14px', borderRadius: 10, lineHeight: 1.8,
        }}>
          TOTAL = Σ( điểm chấm ÷ điểm tối đa × trọng số ) ÷ Σ trọng số × 100
        </div>
        <div className="muted" style={{ fontSize: 13, margin: '10px 0 14px', lineHeight: 1.65 }}>
          Chia cho tổng trọng số thực tế (thay vì cho 100 cố định) nên điểm vẫn
          về thang 100 kể cả khi bộ câu hỏi tạm lệch. Câu hỏi <b>để 0 điểm vẫn
          được tính là 0</b>, không phải bỏ qua — người chấm không được sót dòng nào.
        </div>
        <div style={{ fontSize: 12.5, fontWeight: 700, marginBottom: 6 }}>
          Ví dụ theo bộ câu hỏi đang mở, giả sử chấm tất cả ở mức giữa:
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={th}>Câu hỏi</th>
              <th style={{ ...th, textAlign: 'right', width: 110 }}>Điểm giả định</th>
              <th style={{ ...th, textAlign: 'right', width: 100 }}>Trọng số</th>
              <th style={{ ...th, textAlign: 'right', width: 110 }}>Đóng góp</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={r.id || 'new' + i}>
                <td style={td}>{r.name || <span className="faint">(chưa đặt tên)</span>}</td>
                <td style={{ ...td, textAlign: 'right' }}>
                  {midScore(r.maxScore)} / {r.maxScore}
                </td>
                <td style={{ ...td, textAlign: 'right' }}>{r.weight}%</td>
                <td style={{ ...td, textAlign: 'right' }}>
                  {((midScore(r.maxScore) / r.maxScore) * r.weight).toFixed(1)}
                </td>
              </tr>
            ))}
            <tr>
              <td style={{ ...td, fontWeight: 800 }} colSpan={2}>
                Tổng điểm → xếp loại
              </td>
              <td style={{ ...td, textAlign: 'right', fontWeight: 800 }}>{wSum}%</td>
              <td style={{ ...td, textAlign: 'right', fontWeight: 800 }}>
                {total.toFixed(1)} — loại {grade}
              </td>
            </tr>
          </tbody>
        </table>
      </Card>

      <Card title="Nguồn chấm của mỗi câu hỏi" icon="settings" tone="var(--gold-600)">
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody>
            {(data.autoSources || []).map((s) => (
              <tr key={s.key}>
                <td style={{ ...td, width: 240, fontWeight: 600 }}>{s.label}</td>
                <td style={{ ...td, color: 'var(--muted)' }}>{AUTO_NOTE[s.key]}</td>
              </tr>
            ))}
          </tbody>
        </table>
        <div className="muted" style={{ fontSize: 12.5, marginTop: 10, lineHeight: 1.6 }}>
          Câu hỏi tự động vẫn cho quản lý sửa đè điểm; bảng quy đổi của chúng
          (% đúng giờ → điểm, khối lượng, chứng chỉ) cố định trong hệ thống, xem
          chi tiết ở tab "Hướng dẫn chấm điểm" của màn Đánh giá.
        </div>
      </Card>

      <Card title="Cách viết câu hỏi và mốc chấm" icon="book" tone="var(--muted)">
        <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13.5, lineHeight: 1.85 }}>
          <li><b>Tổng trọng số mỗi nhóm phải bằng 100</b> — lệch thì hệ thống không cho lưu.</li>
          <li>Điểm tối đa mỗi câu từ {data.maxScoreMin} đến {data.maxScoreMax}. Thang 5 hoặc 10 dễ chấm nhất.</li>
          <li>Mốc mô tả <b>hành vi quan sát được</b>, không dùng lời khen chung chung — hai quản lý khác nhau chấm cùng một người phải ra kết quả gần nhau.</li>
          <li>Mốc giữa là "đạt yêu cầu của vị trí" — chuẩn để so lên hoặc xuống; các mức xen giữa cố ý không mô tả riêng.</li>
          <li>Bỏ câu hỏi thì <b>tắt</b>, đừng đổi nó thành câu khác: phiếu cũ vẫn tham chiếu tới câu hỏi đó.</li>
        </ul>
      </Card>
    </div>
  );
}
