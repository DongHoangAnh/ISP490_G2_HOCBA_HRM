/* Stub màn chưa nối API — mỗi thành viên thay bằng feature của mình
   theo docs/QUY_UOC_FRONTEND.md §3 (ownership) */
export default function ComingSoon({ title, owner, api }) {
  return (
    <div className="content fade-in">
      <div className="card" style={{ padding: 36, textAlign: 'center' }}>
        <div style={{ fontSize: 17, fontWeight: 800, marginBottom: 8 }}>{title}</div>
        <p className="muted" style={{ margin: 0 }}>
          Màn này đang chờ <b>{owner}</b> viết spec + nối API <code>{api}</code>.
          <br />Xem quy ước: <code>docs/QUY_UOC_FRONTEND.md</code> · mẫu chuẩn: màn Nhân viên.
        </p>
      </div>
    </div>
  );
}
