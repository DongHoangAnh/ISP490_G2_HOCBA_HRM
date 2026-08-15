/* Sắp xếp bảng phía client — dùng chung cho các màn danh sách.

   Dữ liệu các màn này đã tải hết về SPA (không phân trang phía server) nên sắp
   xếp ngay ở client là đủ và không tốn thêm request.

   Cách dùng:
     const sort = useSort();                       // mặc định: giữ thứ tự server
     const rows = sort.apply(filtered, {           // map key → hàm lấy giá trị
       name: (r) => r.employeeName,
       date: (r) => r.requestDate,
     });
     <SortTh sort={sort} k="name">Nhân viên</SortTh>
*/
import { useState } from 'react';

/* So sánh 2 giá trị bất kỳ: rỗng luôn xuống cuối (bất kể chiều sắp xếp),
   số so theo số, còn lại so chuỗi theo tiếng Việt (có dấu đúng thứ tự). */
function cmp(a, b) {
  const ea = a === null || a === undefined || a === '' || a === '—';
  const eb = b === null || b === undefined || b === '' || b === '—';
  if (ea || eb) return ea && eb ? 0 : (ea ? 1 : -1);
  if (typeof a === 'number' && typeof b === 'number') return a - b;
  if (typeof a === 'boolean' && typeof b === 'boolean') return (a ? 1 : 0) - (b ? 1 : 0);
  return String(a).localeCompare(String(b), 'vi', { numeric: true });
}

export function useSort(initialKey = null, initialDir = 'asc') {
  const [st, setSt] = useState({ key: initialKey, dir: initialDir });

  /* Bấm lại cùng cột → đảo chiều; lần thứ 3 → bỏ sắp xếp, về thứ tự gốc. */
  const toggle = (key) => setSt((s) => {
    if (s.key !== key) return { key, dir: 'asc' };
    if (s.dir === 'asc') return { key, dir: 'desc' };
    return { key: null, dir: 'asc' };
  });

  const apply = (rows, getters) => {
    const get = st.key && getters[st.key];
    if (!get) return rows;
    const sign = st.dir === 'asc' ? 1 : -1;
    // Sort trên bản sao: mảng gốc là state/props, sort tại chỗ sẽ đổi cả nguồn.
    return [...rows].sort((a, b) => sign * cmp(get(a), get(b)));
  };

  return { key: st.key, dir: st.dir, toggle, apply };
}

/* <th> bấm được. Giữ nguyên mọi prop khác (style width…) của th thường. */
export function SortTh({ sort, k, children, className = '', ...rest }) {
  const active = sort.key === k;
  return (
    <th {...rest}
      className={('th-sort ' + className).trim() + (active ? ' active' : '')}
      onClick={() => sort.toggle(k)}
      title="Bấm để sắp xếp"
      aria-sort={active ? (sort.dir === 'asc' ? 'ascending' : 'descending') : 'none'}>
      <span className="th-sort-in">
        {children}
        <span className="th-arrow">{active ? (sort.dir === 'asc' ? '▲' : '▼') : '↕'}</span>
      </span>
    </th>
  );
}
