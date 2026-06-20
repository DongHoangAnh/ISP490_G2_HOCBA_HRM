/* API domain Payroll — Hùng.
   Spec: custom-addons/hocba_payroll/resource/spec/ */
import { hbGet, hbPost } from './client';

const g = (url) => hbGet(url).then((r) => r.data);
const p = (url, body) => hbPost(url, body).then((r) => r.data);

// ── Batch ───────────────────────────────────────────────
export const fetchBatches = () =>
  g('/hocba-hrm/api/payroll/batch');
export const fetchBatch = (id) =>
  g(`/hocba-hrm/api/payroll/batch/${id}`);
export const createBatch = (payload) =>
  p('/hocba-hrm/api/payroll/batch', payload);
export const generatePayslips = (batchId) =>
  p(`/hocba-hrm/api/payroll/batch/${batchId}/generate`, {});
export const closeBatch = (batchId) =>
  p(`/hocba-hrm/api/payroll/batch/${batchId}/close`, {});

// ── Payslip ─────────────────────────────────────────────
export const fetchPayslips = (params) =>
  g('/hocba-hrm/api/payroll/payslip?' + new URLSearchParams(params));
export const fetchEmployeePayroll = (params) =>
  g('/hocba-hrm/api/payroll/employee-payroll?' + new URLSearchParams(params));
export const fetchPayslip = (id) =>
  g(`/hocba-hrm/api/payroll/payslip/${id}`);
export const computePayslip = (id) =>
  p(`/hocba-hrm/api/payroll/payslip/${id}/compute`, {});
export const confirmPayslip = (id) =>
  p(`/hocba-hrm/api/payroll/payslip/${id}/confirm`, {});
export const resetPayslip = (id, reason) =>
  p(`/hocba-hrm/api/payroll/payslip/${id}/reset`, { reason });

// ── Work Entry ──────────────────────────────────────────
export const fetchWorkEntries = (params) =>
  g('/hocba-hrm/api/payroll/work-entry?' + new URLSearchParams(params));
export const createWorkEntry = (payload) =>
  p('/hocba-hrm/api/payroll/work-entry', payload);
export const bulkCreateWorkEntries = (entries) =>
  p('/hocba-hrm/api/payroll/work-entry/bulk-create', { entries });

// ── Bank File ───────────────────────────────────────────
export const fetchBankFiles = (params) =>
  g('/hocba-hrm/api/payroll/bank-file?' + new URLSearchParams(params));
export const generateBankFile = (payload) =>
  p('/hocba-hrm/api/payroll/bank-file/generate', payload);
export const markBankFileUploaded = (id) =>
  p(`/hocba-hrm/api/payroll/bank-file/${id}/upload`, {});
export const markBankFileConfirmed = (id) =>
  p(`/hocba-hrm/api/payroll/bank-file/${id}/confirm`, {});

// ── Salary Structure (read-only list) ────────────────────
export const fetchSalaryStructures = () =>
  g('/hocba-hrm/api/payroll/salary-structure');

// ── Salary Rule ──────────────────────────────────────────
export const fetchRuleCategories = () =>
  g('/hocba-hrm/api/payroll/salary-rule-category');
export const createRuleCategory = (payload) =>
  p('/hocba-hrm/api/payroll/salary-rule-category', payload);
export const updateRuleCategory = (id, payload) =>
  p(`/hocba-hrm/api/payroll/salary-rule-category/${id}`, payload);
export const deleteRuleCategory = (id) =>
  p(`/hocba-hrm/api/payroll/salary-rule-category/${id}/delete`, {});
export const fetchSalaryRules = (params) =>
  g('/hocba-hrm/api/payroll/salary-rule?' + new URLSearchParams(params));
export const createSalaryRule = (payload) =>
  p('/hocba-hrm/api/payroll/salary-rule', payload);
export const updateSalaryRule = (id, payload) =>
  p(`/hocba-hrm/api/payroll/salary-rule/${id}`, payload);
export const deleteSalaryRule = (id) =>
  p(`/hocba-hrm/api/payroll/salary-rule/${id}/delete`, {});
export const reorderSalaryRules = (order) =>
  p('/hocba-hrm/api/payroll/salary-rule/reorder', { order });

export const fetchBankFormats = () =>
  g('/hocba-hrm/api/payroll/bank-format');
export const createBankFormat = (payload) =>
  p('/hocba-hrm/api/payroll/bank-format', payload);
export const updateBankFormat = (id, payload) =>
  p(`/hocba-hrm/api/payroll/bank-format/${id}`, payload);
export const deleteBankFormat = (id) =>
  p(`/hocba-hrm/api/payroll/bank-format/${id}/delete`, {});
export const fetchContract = (id) =>
  g(`/hocba-hrm/api/payroll/contract/${id}`);
