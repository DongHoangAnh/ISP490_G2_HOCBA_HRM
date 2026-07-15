/* API domain Tài chính (dòng tiền) — module hocba_finance.
   Spec: docs/superpowers/specs/2026-07-11-finance-cashflow.md */
import { hbGet, hbPost } from './client';

const qs = (o) => {
  const p = Object.entries(o).filter(([, v]) => v != null && v !== '');
  return p.length ? '?' + p.map(([k, v]) => `${k}=${encodeURIComponent(v)}`).join('&') : '';
};

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
