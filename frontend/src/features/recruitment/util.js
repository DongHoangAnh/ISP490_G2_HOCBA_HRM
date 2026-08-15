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
/* Tiềm năng đi chung màu đỏ với Fail: cả hai đều là "không nhận lần này",
   khác nhau ở chỗ Tiềm năng còn giữ hồ sơ cho đợt sau. */
export const INTERVIEW_RESULT_KIND = { pass: 'green', fail: 'red', potential: 'red' };

/* Link tuyển dụng công khai: BE trả đường dẫn tương đối (/jobs/detail/...) →
   ghép origin hiện tại thành URL tuyệt đối để copy đi truyền thông. */
export const publicJobUrl = (u) => (u ? new URL(u, window.location.origin).href : '');

/* Copy text vào clipboard — fallback execCommand cho ngữ cảnh không có
   navigator.clipboard (http không secure-context). */
export async function copyText(text) {
  try { await navigator.clipboard.writeText(text); return true; }
  catch {
    const ta = document.createElement('textarea');
    ta.value = text; document.body.appendChild(ta); ta.select();
    try { return document.execCommand('copy'); }
    catch { return false; }
    finally { document.body.removeChild(ta); }
  }
}
