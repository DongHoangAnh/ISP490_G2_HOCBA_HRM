/* Mốc mô tả hành vi của một tiêu chí (thang BARS): "được mấy điểm khi làm gì".
   Dùng chung cho tab Hướng dẫn (đọc trước khi chấm) và drawer chấm điểm (đối
   chiếu ngay lúc bấm) — cùng một nguồn chữ nên hai chỗ không thể nói khác nhau.
   Nội dung: trường anchor_top/mid/low của hb.review.criteria. */

/* anchors: [{score, text}] xếp từ mức cao xuống thấp. */
export default function AnchorList({ anchors, current }) {
  if (!anchors || !anchors.length) return null;
  return (
    <div style={{ display: 'grid', gap: 6 }}>
      {anchors.map((a) => {
        const hit = current === a.score;
        return (
          <div key={a.score} style={{
            display: 'flex', gap: 9, alignItems: 'flex-start',
            padding: '6px 9px', borderRadius: 9,
            background: hit ? 'var(--red-50)' : 'transparent',
            border: '1px solid ' + (hit ? 'var(--red-100, var(--border))' : 'transparent'),
          }}>
            <span style={{
              flex: '0 0 auto', minWidth: 22, height: 22, padding: '0 6px',
              borderRadius: 7, fontSize: 11.5, fontWeight: 800,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              background: 'var(--surface-2)', border: '1px solid var(--border)',
            }}>{a.score}đ</span>
            <span style={{ fontSize: 12.5, lineHeight: 1.5 }}>{a.text}</span>
          </div>
        );
      })}
      <div className="faint" style={{ fontSize: 11.5 }}>
        Các mức xen giữa là khoảng giữa hai mốc liền kề — dùng khi nhân viên rõ
        ràng hơn mốc dưới nhưng chưa đạt đủ mốc trên.
      </div>
    </div>
  );
}
