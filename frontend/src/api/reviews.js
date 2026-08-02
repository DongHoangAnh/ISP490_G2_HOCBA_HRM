/* API domain Đánh giá nhân viên — Việt.
   Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md */
import { hbGet, hbPost } from './client';

export const fetchReviews = ({ group, periodType, year, index }) =>
  hbGet(`/hocba-hrm/api/reviews?group=${group}&periodType=${periodType}`
    + `&year=${year}&index=${index}`);

export const fetchReview = (id) => hbGet(`/hocba-hrm/api/reviews/${id}`);

export const createReview = (payload) =>
  hbPost('/hocba-hrm/api/reviews', payload);

export const saveReview = (id, payload) =>
  hbPost(`/hocba-hrm/api/reviews/${id}`, payload);

export const reviewAction = (id, action) =>
  hbPost(`/hocba-hrm/api/reviews/${id}/action`, { action });

export const bulkOpenReviews = (payload) =>
  hbPost('/hocba-hrm/api/reviews/bulk-open', payload);
