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
    early_leave: ['Về sớm', 'amber'],
    forget: ['Quên chấm', 'red'],
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

export function firstDayOfMonth() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-01`;
}

export function lastDayOfMonth() {
  const d = new Date();
  const last = new Date(d.getFullYear(), d.getMonth() + 1, 0);
  return `${last.getFullYear()}-${String(last.getMonth() + 1).padStart(2, '0')}-${String(last.getDate()).padStart(2, '0')}`;
}

/* Công ngày: 1.0 -> '1 công', 0.5 -> '½ công', 0/null -> '—'. */
export function fmtCredit(v) {
  if (v >= 1) return '1 công';
  if (v >= 0.5) return '½ công';
  return '—';
}
