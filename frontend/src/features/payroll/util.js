/* Payroll helpers — badge labels, state maps, date utils.
   Owner: Hùng. */

export const BATCH_STATE = {
  draft: ['Nháp', 'gray'],
  computed: ['Đã tính', 'blue'],
  manager_approved: ['QL duyệt', 'teal'],
  sent: ['Đã gửi', 'violet'],
  employees_confirmed: ['NV xác nhận', 'amber'],
  applied: ['Áp dụng', 'green'],
  paid: ['Đã trả', 'green'],
  cancelled: ['Huỷ', 'red'],
};

export const SLIP_STATE = {
  draft: ['Nháp', 'gray'],
  verify: ['Chờ duyệt', 'amber'],
  done: ['Hoàn tất', 'green'],
  cancel: ['Huỷ', 'red'],
};

export const batchState = (key) => BATCH_STATE[key] || ['?', 'gray'];
export const slipState = (key) => SLIP_STATE[key] || ['?', 'gray'];

export const CATEGORY_LABEL = {
  BASIC: 'Lương thời gian',
  COM: 'Hoa hồng',
  ALW: 'Phụ cấp',
  BONUS: 'Thưởng',
  GROSS: 'Tổng thu nhập',
  COMP: 'BH công ty đóng',
  DED: 'Khấu trừ',
  TAX: 'Thuế TNCN',
  NET: 'Thực lĩnh',
};

export const HIGHLIGHT_CODES = new Set(['GROSS', 'NET']);
export const MUTED_CATEGORIES = new Set(['COMP']);

export const currentMonth = () => String(new Date().getMonth() + 1).padStart(2, '0');
export const currentYear = () => String(new Date().getFullYear());

export const defaultBatchName = (m, y) => `Lương T${m}/${y}`;

export const firstOfMonth = (m, y) => `${y}-${String(m).padStart(2, '0')}-01`;
export const lastOfMonth = (m, y) => {
  const d = new Date(Number(y), Number(m), 0);
  return `${y}-${String(m).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

export const monthOptions = () =>
  Array.from({ length: 12 }, (_, i) => ({ value: String(i + 1), label: `Tháng ${i + 1}` }));

export const yearOptions = () => {
  const y = new Date().getFullYear();
  return [y - 1, y, y + 1].map((v) => ({ value: String(v), label: String(v) }));
};
