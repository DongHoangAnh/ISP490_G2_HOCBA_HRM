/* Helper riêng feature Recruitment — map key Selection -> "kind" màu badge
   (bộ chuẩn quy ước §6). */
export const CV_RESULT_KIND = {
  pass: 'green', fail: 'red', potential: 'amber', contact_later: 'blue',
};
export const CALL_STATUS_KIND = {
  agree: 'green', refuse: 'red', potential: 'amber', contact_later: 'gray',
};

/* Trạng thái phiếu yêu cầu tuyển dụng */
export const REQUEST_STATE_KIND = {
  draft: 'gray', submitted: 'amber', recruiting: 'green', closed: 'blue', refused: 'red',
};

/* Tham gia PV (đã đến / không đến) + kết quả phỏng vấn */
export const ATTENDANCE_KIND = { present: 'green', absent: 'red' };
export const INTERVIEW_RESULT_KIND = { pass: 'green', fail: 'red', potential: 'amber' };
