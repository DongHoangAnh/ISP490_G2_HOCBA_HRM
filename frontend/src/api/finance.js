/* API domain Tài chính (dòng tiền) — module hocba_finance.
   Spec: docs/superpowers/specs/2026-07-11-finance-cashflow.md
   Nâng cấp: CRUD Quỹ/Mục + fields TT200 */
import { hbGet, hbPost, hbPut, hbDelete } from './client';

const qs = (o) => {
  const p = Object.entries(o).filter(([, v]) => v != null && v !== '');
  return p.length ? '?' + p.map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&') : '';
};

/* ── Voucher APIs (existing) ──────────────────────────────────────────── */
export const fetchFinanceContext = () =>
  hbGet('/hocba-hrm/api/finance/context');

export const fetchVouchers = (filters = {}) =>
  hbGet('/hocba-hrm/api/finance/vouchers' + qs(filters));

export const createVoucher = (payload) =>
  hbPost('/hocba-hrm/api/finance/voucher', payload);

export const voucherAction = (id, action) =>
  hbPost(`/hocba-hrm/api/finance/voucher/${id}/action`, { action });

export const fetchSummary = (filters = {}) =>
  hbGet('/hocba-hrm/api/finance/summary' + qs(filters));

/* ── Fund CRUD (mới — chỉ Kế toán/BGĐ) ──────────────────────────────── */
export const createFund = (payload) =>
  hbPost('/hocba-hrm/api/finance/fund', payload);

export const updateFund = (id, payload) =>
  hbPut(`/hocba-hrm/api/finance/fund/${id}`, payload);

export const deleteFund = (id) =>
  hbDelete(`/hocba-hrm/api/finance/fund/${id}`);

/* ── Category CRUD (mới — chỉ Kế toán/BGĐ) ──────────────────────────── */
export const createCategory = (payload) =>
  hbPost('/hocba-hrm/api/finance/category', payload);

export const updateCategory = (id, payload) =>
  hbPut(`/hocba-hrm/api/finance/category/${id}`, payload);

export const deleteCategory = (id) =>
  hbDelete(`/hocba-hrm/api/finance/category/${id}`);
