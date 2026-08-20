/* API domain Recruitment — Việt. Spec: docs/SPEC_API_RECRUITMENT.md */
import { hbGet, hbPost, hbUpload } from './client';

export const fetchCvList = () => hbGet('/hocba-hrm/api/recruitment/cv');
export const fetchApplicant = (id) =>
  hbGet(`/hocba-hrm/api/recruitment/applicant/${id}`);

export const createCv = (payload) =>
  hbPost('/hocba-hrm/api/recruitment/cv', payload);
export const updateApplicant = (id, payload) =>
  hbPost(`/hocba-hrm/api/recruitment/applicant/${id}`, payload);
export const changeStage = (id, stageId) =>
  hbPost(`/hocba-hrm/api/recruitment/applicant/${id}/stage`, { stageId });
export const uploadCvFile = (id, file) =>
  hbUpload(`/hocba-hrm/api/recruitment/applicant/${id}/cv-file`, file);
export const createEmployeeFromApplicant = (id) =>
  hbPost(`/hocba-hrm/api/recruitment/applicant/${id}/create-employee`, {});

/* Vị trí (hr.job) — dùng cho tab "Theo dõi tuyển dụng" và "Kho quản lý JD" */
export const fetchJobs = () => hbGet('/hocba-hrm/api/recruitment/jobs');
export const fetchJob = (id) => hbGet(`/hocba-hrm/api/recruitment/job/${id}`);
export const createJob = (payload) => hbPost('/hocba-hrm/api/recruitment/jobs', payload);
export const updateJob = (id, payload) =>
  hbPost(`/hocba-hrm/api/recruitment/job/${id}`, payload);

/* Phiếu yêu cầu tuyển dụng */
export const fetchRequests = () => hbGet('/hocba-hrm/api/recruitment/requests');
export const fetchRequest = (id) => hbGet(`/hocba-hrm/api/recruitment/request/${id}`);
export const createRequest = (payload) => hbPost('/hocba-hrm/api/recruitment/requests', payload);
export const updateRequest = (id, payload) =>
  hbPost(`/hocba-hrm/api/recruitment/request/${id}`, payload);
export const requestAction = (id, action, extra) =>
  hbPost(`/hocba-hrm/api/recruitment/request/${id}/action`, { action, ...extra });
/* Ứng viên của 1 phiếu theo nhóm trong phễu tuyển dụng
   (cv | cv_pass | fail_cv | pv | pv_pass | fail_pv | onboard | hired) — popup
   "xem chi tiết số ứng viên" ở tab Theo dõi tuyển dụng. Trả kèm khối JD. */
export const fetchRequestApplicants = (id, group) =>
  hbGet(`/hocba-hrm/api/recruitment/request/${id}/applicants?group=${group || 'cv'}`);

/* Mail mẫu tuyển dụng */
export const fetchMailTemplates = () => hbGet('/hocba-hrm/api/recruitment/mail-templates');
export const fetchMailTemplate = (id) => hbGet(`/hocba-hrm/api/recruitment/mail-template/${id}`);
export const createMailTemplate = (payload) => hbPost('/hocba-hrm/api/recruitment/mail-templates', payload);
export const updateMailTemplate = (id, payload) =>
  hbPost(`/hocba-hrm/api/recruitment/mail-template/${id}`, payload);
export const deleteMailTemplate = (id) =>
  hbPost(`/hocba-hrm/api/recruitment/mail-template/${id}/delete`, {});
export const sendMailTemplate = (id, applicantIds, override) =>
  hbPost(`/hocba-hrm/api/recruitment/mail-template/${id}/send`, { applicantIds, ...(override || {}) });
export const fetchMailLogs = () => hbGet('/hocba-hrm/api/recruitment/mail-logs');
export const previewMailTemplate = (id, applicantId) =>
  hbPost(`/hocba-hrm/api/recruitment/mail-template/${id}/preview`, { applicantId });

/* Ghi lịch sử mail đã gửi (qua Gmail redirect) — hiện ở tab Lịch sử gửi mail */
export const logSentMail = (logs) =>
  hbPost('/hocba-hrm/api/recruitment/mail/log-sent', { logs });

/* Cấu hình tuyển dụng (admin/HR) — stages + SLA + auto-close.
   Spec: docs/superpowers/specs/2026-07-23-recruitment-config-design.md */
export const fetchRecruitConfig = () => hbGet('/hocba-hrm/api/recruitment/config');
export const createRecruitStage = (payload) =>
  hbPost('/hocba-hrm/api/recruitment/config/stages', payload);
export const updateRecruitStage = (id, payload) =>
  hbPost(`/hocba-hrm/api/recruitment/config/stage/${id}`, payload);
export const deleteRecruitStage = (id) =>
  hbPost(`/hocba-hrm/api/recruitment/config/stage/${id}/delete`, {});
export const reorderRecruitStages = (ids) =>
  hbPost('/hocba-hrm/api/recruitment/config/stages/reorder', { ids });
export const saveRecruitSettings = (payload) =>
  hbPost('/hocba-hrm/api/recruitment/config/settings', payload);
export const saveSlotHours = (payload) =>
  hbPost('/hocba-hrm/api/recruitment/config/slot-hours', payload);

/* Lịch rảnh phỏng vấn (hb.interview.slot) */
export const fetchInterviewSlots = (from, to) =>
  hbGet(`/hocba-hrm/api/recruitment/interview-slots?from=${from}&to=${to}`);
export const createInterviewSlots = (userId, slots) =>
  hbPost('/hocba-hrm/api/recruitment/interview-slots', { userId, slots });
export const deleteInterviewSlot = (id) =>
  hbPost(`/hocba-hrm/api/recruitment/interview-slot/${id}/delete`, {});
export const bookInterviewSlot = (id, applicantId) =>
  hbPost(`/hocba-hrm/api/recruitment/interview-slot/${id}/book`, { applicantId });
/* Bỏ applicantId = gỡ hết ứng viên khỏi slot; truyền vào = chỉ gỡ ứng viên đó. */
export const unbookInterviewSlot = (id, applicantId) =>
  hbPost(`/hocba-hrm/api/recruitment/interview-slot/${id}/unbook`,
    applicantId ? { applicantId } : {});

/* Số phiếu yêu cầu đang chờ duyệt — badge cạnh menu Tuyển dụng.
   Chỉ người duyệt (HR/Admin/nhóm Tuyển dụng) mới ra số > 0. */
export const fetchRequestPendingCount = () =>
  hbGet('/hocba-hrm/api/recruitment/requests/pending-count');
