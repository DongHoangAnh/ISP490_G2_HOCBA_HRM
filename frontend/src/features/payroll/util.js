/* Payroll helpers — badge labels, state maps, date utils.
   Owner: Hùng. */

export const BATCH_STATE = {
  draft: ['Nháp', 'gray'],
  verify: ['Đang xác nhận', 'amber'],
  close: ['Hoàn tất', 'green'],
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
  phu_cap: 'Phụ cấp',
  thuong: 'Thưởng',
  tong_thu_nhap: 'Tổng thu nhập',
  giam_tru: 'Giảm trừ',
  khau_tru_nv: 'Khấu trừ NV',
  thue_tncn: 'Thuế TNCN',
  thuc_lanh: 'Thực lĩnh',
  bh_phan_cong_ty: 'BH công ty đóng',
};

export const HIGHLIGHT_CODES = new Set(['tong_thu_nhap', 'thuc_lanh']);
export const MUTED_CATEGORIES = new Set(['bh_phan_cong_ty']);

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
