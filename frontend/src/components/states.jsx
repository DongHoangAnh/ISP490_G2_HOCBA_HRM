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
