/* Helper định dạng dùng chung — không tự format tay trong component
   (quy ước §5c). */

export const hbVND = (n) => (n || 0).toLocaleString('vi-VN');

export function fmtDate(s) {
  if (!s || s === '—') return '—';
  const [y, m, d] = s.split('-');
  return `${d}/${m}/${y}`;
}

export function hbInitials(name) {
  const p = (name || '').trim().split(/\s+/);
  return ((p[p.length - 2]?.[0] || '') + (p[p.length - 1]?.[0] || '')).toUpperCase();
}

const HB_AV = ['av-a', 'av-b', 'av-c', 'av-d', 'av-e', 'av-f'];
export const hbAvCls = (id) => HB_AV[(id || 0) % HB_AV.length];

/* Mapping "kind" màu badge — bộ giá trị chuẩn (quy ước §6) */
export function hbStatusKind(key) {
  return ({
    probation: 'amber', official: 'green', intern: 'blue', parttime: 'violet',
    ctv: 'violet', advisor: 'teal', exiting: 'red', resigned: 'gray',
  })[key] || 'gray';
}

export function hbTypeKind(t) {
  return ({ Offline: 'teal', Online: 'blue', CTV: 'violet' })[t] || 'gray';
}

export const HB_RESULT = {
  draft: ['Chưa đánh giá', 'gray'],
  pass: ['Đạt', 'green'],
  fail: ['Không đạt', 'red'],
  extend: ['Gia hạn', 'amber'],
};

export const HB_CERT = {
  valid: ['Còn hạn', 'green'],
  expiring: ['Sắp hết hạn', 'amber'],
  expired: ['Hết hạn', 'red'],
  none: ['—', 'gray'],
};
