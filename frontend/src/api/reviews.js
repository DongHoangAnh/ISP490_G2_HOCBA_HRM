/* API domain Đánh giá nhân viên — Việt.
   Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md */
import { hbGet, hbPost } from './client';

export const fetchReviews = ({ group, periodType, year, index }) =>
  hbGet(`/hocba-hrm/api/reviews?group=${group}&periodType=${periodType}`
    + `&year=${year}&index=${index}`);

export const fetchReview = (id) => hbGet(`/hocba-hrm/api/reviews/${id}`);

/* Nội dung tab Hướng dẫn chấm điểm: ngưỡng xếp loại, bộ tiêu chí, bảng quy đổi
   chỉ số tự động — lấy từ cấu hình đang chạy để không lệch với điểm thực chấm. */
export const fetchReviewGuide = () => hbGet('/hocba-hrm/api/reviews/guide');

export const createReview = (payload) =>
  hbPost('/hocba-hrm/api/reviews', payload);

export const saveReview = (id, payload) =>
  hbPost(`/hocba-hrm/api/reviews/${id}`, payload);

export const reviewAction = (id, action) =>
  hbPost(`/hocba-hrm/api/reviews/${id}/action`, { action });

export const bulkOpenReviews = (payload) =>
  hbPost('/hocba-hrm/api/reviews/bulk-open', payload);

/* ---- Màn Cấu hình đánh giá (HR Manager/Admin) ----
   Spec: docs/superpowers/specs/2026-08-21-reviews-config-design.md */

export const fetchReviewConfig = () => hbGet('/hocba-hrm/api/reviews/config');

/* Lưu CẢ BỘ câu hỏi của một nhóm — BE chặn cứng tổng trọng số 100 nên không
   có endpoint sửa lẻ từng câu. */
export const saveReviewCriteria = (group, criteria) =>
  hbPost('/hocba-hrm/api/reviews/config/criteria', { group, criteria });

export const saveReviewGrading = (payload) =>
  hbPost('/hocba-hrm/api/reviews/config/grading', payload);
