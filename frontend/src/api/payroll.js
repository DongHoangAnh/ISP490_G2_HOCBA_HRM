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
export const closeBatchByPeriod = (month, year) =>
  p('/hocba-hrm/api/payroll/batch/close-by-period', { month, year });

// ── Payslip ─────────────────────────────────────────────
export const fetchPayslips = (params) =>
  g('/hocba-hrm/api/payroll/payslip?' + new URLSearchParams(params));
export const fetchEmployeePayroll = (params) =>
  g('/hocba-hrm/api/payroll/employee-payroll?' + new URLSearchParams(params));
export const fetchSalaryHistory = (params) =>
  g('/hocba-hrm/api/payroll/salary-history?' + new URLSearchParams(params));
export const fetchPayslip = (id) =>
  g(`/hocba-hrm/api/payroll/payslip/${id}`);
export const computePayslip = (id) =>
  p(`/hocba-hrm/api/payroll/payslip/${id}/compute`, {});
export const confirmPayslip = (id) =>
  p(`/hocba-hrm/api/payroll/payslip/${id}/confirm`, {});
export const resetPayslip = (id, reason) =>
  p(`/hocba-hrm/api/payroll/payslip/${id}/reset`, { reason });
export const computeAllPayslips = (month, year) =>
  p('/hocba-hrm/api/payroll/compute-all', { month, year });
export const fetchComputeStatus = (month, year) =>
  g(`/hocba-hrm/api/payroll/compute-status?month=${month}&year=${year}`);

// ── Bank File / Transfer ─────────────────────────────────
export const fetchBankFiles = (params) =>
  g('/hocba-hrm/api/payroll/bank-file?' + new URLSearchParams(params));
export const generateBankFile = (payload) =>
  p('/hocba-hrm/api/payroll/bank-file/generate', payload);
export const createTransferFile = (month, year, bankCodes) =>
  p('/hocba-hrm/api/payroll/transfer-file', { month, year, bank_codes: bankCodes });
export const markBankFileUploaded = (id) =>
  p(`/hocba-hrm/api/payroll/bank-file/${id}/upload`, {});
export const markBankFileConfirmed = (id) =>
  p(`/hocba-hrm/api/payroll/bank-file/${id}/confirm`, {});
export const fetchTransferList = (params) =>
  g('/hocba-hrm/api/payroll/transfer-list?' + new URLSearchParams(params));

// ── Unified Config Aggregation ─────────────────────────────
export const fetchPayrollConfigAll = () =>
  g('/hocba-hrm/api/payroll/config-all');

// ── Salary Rule ──────────────────────────────────────────
export const fetchRuleCategories = () =>
  g('/hocba-hrm/api/payroll/salary-rule-category');
export const createRuleCategory = (payload) =>
  p('/hocba-hrm/api/payroll/salary-rule-category', payload);
export const updateRuleCategory = (id, payload) =>
  p(`/hocba-hrm/api/payroll/salary-rule-category/${id}`, payload);
export const fetchSalaryStructures = () =>
  g('/hocba-hrm/api/payroll/salary-structure');
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
export const fetchLookupSources = () =>
  g('/hocba-hrm/api/payroll/lookup-sources');

export const fetchBankFormats = () =>
  g('/hocba-hrm/api/payroll/bank-format');
export const createBankFormat = (payload) =>
  p('/hocba-hrm/api/payroll/bank-format', payload);
export const updateBankFormat = (id, payload) =>
  p(`/hocba-hrm/api/payroll/bank-format/${id}`, payload);
export const deleteBankFormat = (id) =>
  p(`/hocba-hrm/api/payroll/bank-format/${id}/delete`, {});

// ── Payslip messages (chatter) ──────────────────────────
export const fetchPayslipMessages = (id) =>
  g(`/hocba-hrm/api/payroll/payslip/${id}/messages`);

// ── Send payslip mail (Odoo SMTP fallback) ───────────────
export const sendPayslipMail = (payslipIds) =>
  p('/hocba-hrm/api/payroll/payslip/send-mail', { payslip_ids: payslipIds });

// ── Mark payslips as sent (after EmailJS) ────────────────
export const markPayslipsSent = (payslipIds) =>
  p('/hocba-hrm/api/payroll/payslip/mark-sent', { payslip_ids: payslipIds });

// ── Employee self-confirm & my payslips (authenticated) ──
export const fetchMyPayslips = () =>
  g('/hocba-hrm/api/payroll/my-payslips');

export const employeeConfirmPayslip = (slipId, action, feedback) =>
  p(`/hocba-hrm/api/payroll/payslip/${slipId}/employee-confirm`, { action, feedback });

// ── HR reset confirmation ────────────────────────────────
export const resetPayslipConfirm = (slipId) =>
  p(`/hocba-hrm/api/payroll/payslip/${slipId}/reset-confirm`, {});

export const bulkResetPayslipConfirm = (payload) =>
  p('/hocba-hrm/api/payroll/payslip/bulk-reset-confirm', payload);

// ── Mail template config ────────────────────────────────
export const fetchMailTemplate = () =>
  g('/hocba-hrm/api/payroll/mail-template');
export const saveMailTemplate = (payload) =>
  p('/hocba-hrm/api/payroll/mail-template', payload);

// ── Confirm Period Config ───────────────────────────────
export const fetchConfirmConfig = () =>
  g('/hocba-hrm/api/payroll/confirm-config');
export const saveConfirmConfig = (payload) =>
  p('/hocba-hrm/api/payroll/confirm-config', payload);

// ── EmailJS config ──────────────────────────────────────
export const fetchEmailjsConfig = () =>
  g('/hocba-hrm/api/payroll/emailjs-config');
export const saveEmailjsConfig = (payload) =>
  p('/hocba-hrm/api/payroll/emailjs-config', payload);

// ── Sale Salary Levels (KPI-based) ──────────────────────
export const fetchSaleSalaryLevels = () =>
  g('/hocba-hrm/api/payroll/sale-salary-level');
export const createSaleSalaryLevel = (payload) =>
  p('/hocba-hrm/api/payroll/sale-salary-level', payload);
export const updateSaleSalaryLevel = (id, payload) =>
  p(`/hocba-hrm/api/payroll/sale-salary-level/${id}`, payload);
export const deleteSaleSalaryLevel = (id) =>
  p(`/hocba-hrm/api/payroll/sale-salary-level/${id}/delete`, {});

// ── Role & Position Allowance Config ────────────────────
export const fetchRoleAllowanceConfigs = () =>
  g('/hocba-hrm/api/payroll/role-allowance-config');
export const createRoleAllowanceConfig = (payload) =>
  p('/hocba-hrm/api/payroll/role-allowance-config', payload);
export const deleteRoleAllowanceConfig = (id) =>
  p(`/hocba-hrm/api/payroll/role-allowance-config/${id}/delete`, {});

// ── Bulk Bonus & Penalty Assignment Wizard ──────────────
export const applyBulkBonusPenalty = (batchId, payload) =>
  p(`/hocba-hrm/api/payroll/batch/${batchId}/bulk-bonus-penalty`, payload);

