import { useState, useEffect } from 'react';

export const PAGE_SIZE = 10;

/* Cắt trang cho một mảng đã lọc sẵn.
   `deps` là các state lọc/tìm kiếm — đổi là về trang 1, không thì lọc còn 3
   dòng trong khi đang đứng trang 5 sẽ ra màn hình trống.
   ⚠️ Giữ độ dài mảng `deps` cố định giữa các lần render (quy tắc hook React).
   Trả về thẳng bộ prop cho <Pagination {...pg} />, `pg.rows` là dòng của trang. */
export function usePaged(rows, deps = [], size = PAGE_SIZE) {
  const [page, setPage] = useState(1);
  useEffect(() => { setPage(1); }, deps);
  const total = rows.length;
  const pageCount = Math.max(1, Math.ceil(total / size));
  const cur = Math.min(page, pageCount);   // xoá bớt dòng → kẹp về trang cuối
  return {
    rows: rows.slice((cur - 1) * size, cur * size),
    page: cur, pageCount, total, pageSize: size, onPage: setPage,
  };
}

/* Phân trang client-side dùng chung. Ẩn khi chỉ có 1 trang. */
export default function Pagination({ page, pageCount, total, pageSize, onPage }) {
  if (pageCount <= 1) return null;
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);

  // Cửa sổ số trang gọn: 1 2 … (p-1) p (p+1) … (n-1) n
  const nums = [];
  const add = (n) => { if (n >= 1 && n <= pageCount && !nums.includes(n)) nums.push(n); };
  add(1); add(2);
  add(page - 1); add(page); add(page + 1);
  add(pageCount - 1); add(pageCount);
  nums.sort((a, b) => a - b);

  const items = [];
  let prev = 0;
  for (const n of nums) {
    if (n - prev > 1) items.push('gap' + n);
    items.push(n);
    prev = n;
  }

  return (
    <div className="pager">
      <div className="pager-info">{from}–{to} / {total}</div>
      <div className="pager-nav">
        <button className="pager-btn" disabled={page <= 1} onClick={() => onPage(page - 1)} aria-label="Trang trước">‹</button>
        {items.map((it) =>
          typeof it === 'number'
            ? <button key={it} className={'pager-btn' + (it === page ? ' active' : '')} onClick={() => onPage(it)}>{it}</button>
            : <span key={it} className="pager-gap">…</span>
        )}
        <button className="pager-btn" disabled={page >= pageCount} onClick={() => onPage(page + 1)} aria-label="Trang sau">›</button>
      </div>
    </div>
  );
}
