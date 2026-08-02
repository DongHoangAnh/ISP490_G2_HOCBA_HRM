/* Nhãn & màu dùng chung cho màn Đánh giá. Công thức: docs/CONG_THUC_DANH_GIA.md */

export const GRADE_LABEL = {
  a: 'A — Xuất sắc',
  b: 'B — Tốt',
  c: 'C — Đạt',
  d: 'D — Cần cải thiện',
};

export const GRADE_KIND = { a: 'green', b: 'blue', c: 'gold', d: 'red' };

/* Ngưỡng xếp loại — TRÙNG mặc định backend (ir.config_parameter
   hocba_reviews.grade_a/b/c). Chỉ dùng để hiện xếp loại tạm thời ngay khi
   người chấm bấm điểm; con số chính thức luôn do backend tính lại khi lưu. */
export const gradeOf = (total) =>
  (total >= 85 ? 'a' : total >= 70 ? 'b' : total >= 55 ? 'c' : 'd');

export const STATE_LABEL = {
  none: 'Chưa có phiếu',
  draft: 'Đang chấm',
  confirmed: 'Đã chốt',
  published: 'Đã công bố',
};

export const STATE_KIND = {
  none: 'gray', draft: 'amber', confirmed: 'teal', published: 'green',
};

export const PERIOD_TYPES = [
  ['quarter', 'Quý'],
  ['half', 'Nửa năm'],
  ['year', 'Năm'],
];

/* Số kỳ hợp lệ trong năm theo loại kỳ. */
export const periodCount = (type) =>
  (type === 'year' ? 1 : type === 'half' ? 2 : 4);

export const periodLabel = (type, index, year) => {
  if (type === 'year') return `Năm ${year}`;
  if (type === 'half') return `Nửa năm ${index}/${year}`;
  return `Quý ${index}/${year}`;
};

/* Nhãn nguồn chấm tự động — hiện trong drawer để người chấm hiểu điểm ở đâu ra. */
export const AUTO_SOURCE_LABEL = {
  punctuality: 'Tỷ lệ đúng giờ',
  workload: 'Khối lượng giảng dạy',
  cert: 'Chuẩn chứng chỉ',
};

/* Đơn vị đếm khác nhau giữa 2 nhóm — dùng cho nhãn chỉ số. */
export const unitLabel = (group) =>
  (group === 'teacher' ? 'buổi dạy' : 'ngày công');
