/* Helper riêng feature attendance (feature-local theo quy ước §4). */

/* ISO datetime -> 'HH:MM' (giờ local đã do BE quy đổi). */
export function fmtTime(iso) {
  if (!iso) return '—';
  const t = (iso.split('T')[1] || '').slice(0, 5);
  return t || '—';
}

/* statusKey -> [nhãn, kind badge] (kind theo bộ chuẩn quy ước §6). */
export function attStatus(key) {
  return ({
    on_time: ['Đúng giờ', 'green'],
    late: ['Đi muộn', 'amber'],
    none: ['Chưa chấm', 'gray'],
  })[key] || ['—', 'gray'];
}

/* Tháng hiện tại dạng 'YYYY-MM' cho input month mặc định. */
export function currentMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
}

/* Hôm nay dạng 'YYYY-MM-DD' cho input date mặc định. */
export function today() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}
