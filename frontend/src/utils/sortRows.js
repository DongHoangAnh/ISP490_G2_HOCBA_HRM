/* Phần so sánh thuần của useSort — tách khỏi hook để test được không cần React. */

const isBlank = (v) => v === null || v === undefined || v === '' || v === '—';

/* Số so theo số; chuỗi so theo tiếng Việt (localeCompare 'vi') để "Đ" không rơi
   sau "E" như khi so sánh mã Unicode thô. */
export function cmpVal(a, b) {
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  return String(a).localeCompare(String(b), 'vi', { numeric: true, sensitivity: 'base' });
}

/* Trả về MẢNG MỚI (không sửa mảng gốc — rows thường là data từ state).
   Ô trống luôn nằm cuối ở CẢ hai chiều: đảo chiều là để đổi thứ tự dữ liệu có
   thật, không phải để dồn một đống dấu "—" lên đầu bảng. */
export function sortRows(rows, get, dir = 'asc') {
  if (!get) return rows;
  const sign = dir === 'desc' ? -1 : 1;
  return [...rows].sort((x, y) => {
    const a = get(x), b = get(y);
    const na = isBlank(a), nb = isBlank(b);
    if (na || nb) return na && nb ? 0 : (na ? 1 : -1);
    return sign * cmpVal(a, b);
  });
}
