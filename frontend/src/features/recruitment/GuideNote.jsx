/* Khối hướng dẫn thao tác, đặt CUỐI tab — để người mới không phải hỏi hoặc mở
   tài liệu ngoài. Dùng chung cho các tab tuyển dụng (Offer & Nhận việc, Danh
   sách PV…) nên chỉnh khoảng cách / kiểu dáng ở đây là cả bộ đổi theo.

   Nội dung phải mô tả ĐÚNG hành vi hiện tại của hệ thống (luật đẩy bước ở
   MAIL_STAGE_RULES, hr_applicant.write, endpoint create-employee). Sửa luật thì
   sửa cả bước tương ứng trong `steps` — hướng dẫn sai còn hại hơn không có.

   props: title · steps [[tiêu đề, nội dung JSX]] · note (dòng ghi chú cuối). */
import Icon from '../../components/Icon';

export default function GuideNote({ title, steps, note }) {
  return (
    <div className="card" style={{
      marginTop: 26, padding: '14px 16px',
      borderLeft: '3px solid var(--red-600)',
    }}>
      <div style={{ display: 'flex', gap: 7, alignItems: 'center', marginBottom: 10 }}>
        <Icon name="help-circle" size={15} />
        <span style={{ fontWeight: 700, fontSize: 13 }}>{title}</span>
      </div>
      <ol className="muted" style={{
        margin: 0, paddingLeft: 20, fontSize: 12.5, lineHeight: 1.7,
        display: 'flex', flexDirection: 'column', gap: 7,
      }}>
        {steps.map(([stepTitle, body]) => (
          <li key={stepTitle}>
            <b style={{ color: 'var(--ink)' }}>{stepTitle}.</b> {body}
          </li>
        ))}
      </ol>
      {note && (
        <div className="muted" style={{ fontSize: 12, marginTop: 10, lineHeight: 1.6 }}>
          {note}
        </div>
      )}
    </div>
  );
}
