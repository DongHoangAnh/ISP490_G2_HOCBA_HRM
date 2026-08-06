/* ============================================================
   Chuyển số tiền VND → chữ tiếng Việt.
   Chuẩn: viết hoa chữ cái đầu, kết thúc "đồng" (TT200 §01-TT).
   Chỉ xử lý VND (số nguyên dương), tối đa 999 tỷ tỷ.
   ============================================================ */

const DIGITS = ['không', 'một', 'hai', 'ba', 'bốn', 'năm', 'sáu', 'bảy', 'tám', 'chín'];

function readGroup3(a, b, c, showZeroHundred) {
  const parts = [];
  if (a > 0) {
    parts.push(DIGITS[a], 'trăm');
  } else if (showZeroHundred) {
    parts.push('không', 'trăm');
  }
  if (b > 0) {
    parts.push(b === 1 ? 'mười' : DIGITS[b] + ' mươi');
    if (c === 1) parts.push('mốt');
    else if (c === 5) parts.push('lăm');
    else if (c > 0) parts.push(DIGITS[c]);
  } else if (c > 0) {
    if (a > 0 || showZeroHundred) parts.push('lẻ');
    parts.push(DIGITS[c]);
  }
  return parts.join(' ');
}

export function amountToWords(n) {
  n = Math.abs(Math.floor(n || 0));
  if (n === 0) return 'Không đồng';
  const units = ['', 'nghìn', 'triệu', 'tỷ', 'nghìn tỷ', 'triệu tỷ'];
  const groups = [];
  let tmp = n;
  while (tmp > 0) { groups.push(tmp % 1000); tmp = Math.floor(tmp / 1000); }
  const segs = [];
  for (let i = groups.length - 1; i >= 0; i--) {
    const g = groups[i];
    if (g === 0) continue;
    const a = Math.floor(g / 100), b = Math.floor((g % 100) / 10), c = g % 10;
    const word = readGroup3(a, b, c, i < groups.length - 1);
    segs.push(units[i] ? `${word} ${units[i]}` : word);
  }
  const raw = segs.join(' ').replace(/\s+/g, ' ').trim();
  return raw.charAt(0).toUpperCase() + raw.slice(1) + ' đồng';
}

export function fmtVND(n) {
  return new Intl.NumberFormat('vi-VN').format(n || 0);
}
