/* ============================================================
   Sắp xếp bảng dùng chung (Nhận việc / Nghỉ việc / Phòng ban). Owner: Tân.
   accessors: { [khoá cột]: (row) => giá trị so sánh }.
   Phần so sánh nằm ở utils/sortRows.js để test được không cần React.
   ============================================================ */
import { useState } from 'react';
import { sortRows } from '../utils/sortRows';

export default function useSort(accessors, initialKey = null, initialDir = 'asc') {
  const [sort, setSort] = useState({ key: initialKey, dir: initialDir });

  /* Bấm lại đúng cột đang sắp → đảo chiều; bấm cột khác → về tăng dần. */
  const toggle = (key) => setSort((p) => (p.key === key
    ? { key, dir: p.dir === 'asc' ? 'desc' : 'asc' }
    : { key, dir: 'asc' }));

  const apply = (rows) => sortRows(rows, accessors[sort.key], sort.dir);

  return { sortKey: sort.key, sortDir: sort.dir, toggle, apply };
}
