/* 3 trạng thái màn hình bắt buộc — quy ước §5b */

export function LoadingState({ label = 'Đang tải dữ liệu…' }) {
  return (
    <div className="content fade-in">
      <div className="empty">{label}</div>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="content fade-in">
      <div className="empty">
        Không tải được dữ liệu ({message}).{' '}
        {onRetry && <button className="btn btn-ghost" onClick={onRetry}>Thử lại</button>}
      </div>
    </div>
  );
}

export function EmptyState({ children }) {
  return <div className="empty">{children}</div>;
}

/* Skeleton giả hàng bảng — dùng cho lần tải đầu của các panel (useFetch.loading). */
export function TableSkeleton({ rows = 6 }) {
  return (
    <div className="fade-in" style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: '6px 0' }}>
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="skeleton" style={{ height: 38, borderRadius: 10 }}></div>
      ))}
    </div>
  );
}
