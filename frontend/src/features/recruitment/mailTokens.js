/* Dịch qua lại giữa cú pháp Odoo `{{ object.* }}` và thẻ tiếng Việt `[Nhãn]`.

   HR không viết được biểu thức, nên form mail mẫu chỉ cho họ thấy `[Họ tên ứng
   viên]`. Việc dịch làm ở FRONTEND, ngay lúc mở và lúc lưu ⇒ DB vẫn lưu đúng cú
   pháp Odoo, luồng gửi mail và view backend không đổi gì.

   ⚠️ Dịch KHÔNG ĐƯỢC làm mất biểu thức gốc. Mẫu "Chào mừng" dùng
   `{{ object.partner_name or 'bạn' }}` — quy về dạng chuẩn `or ''` là ứng viên
   thiếu tên nhận mail "Chào mừng  đến với…" thay vì "Chào mừng bạn đến với…".
   Vì vậy mỗi thẻ mang theo biểu thức gốc trong `data-expr` và được trả lại
   nguyên vẹn khi lưu; chỉ thẻ HR mới chèn mới dùng dạng chuẩn. */

/* Dạng chuẩn dùng cho thẻ MỚI do HR chèn. `or ''` / `if ... else ''` để ứng
   viên thiếu dữ liệu thì ra chuỗi rỗng chứ không phải chữ "False". */
export const TOKENS = [
  { label: 'Họ tên ứng viên', code: "{{ object.partner_name or '' }}" },
  { label: 'Vị trí ứng tuyển', code: "{{ object.job_id.name if object.job_id else '' }}" },
  { label: 'Email ứng viên', code: "{{ object.email_from or '' }}" },
  { label: 'Số điện thoại', code: "{{ object.partner_phone or '' }}" },
  { label: 'Ngày phỏng vấn', code: "{{ object.interview_date.strftime('%d/%m/%Y') if object.interview_date else '' }}" },
  { label: 'Giờ phỏng vấn', code: "{{ object.interview_time or '' }}" },
];
const CODE_OF = Object.fromEntries(TOKENS.map((t) => [t.label, t.code]));

/* Nhận diện theo TÊN TRƯỜNG bên trong {{ }} chứ không so cả chuỗi: các mẫu seed
   viết biểu thức dài ngắn khác nhau, so cả chuỗi là trượt hết. */
const FIELD_MATCHERS = [
  [/object\.partner_name/, 'Họ tên ứng viên'],
  [/object\.job_id/, 'Vị trí ứng tuyển'],
  [/object\.email_from/, 'Email ứng viên'],
  [/object\.partner_phone/, 'Số điện thoại'],
  [/object\.interview_date/, 'Ngày phỏng vấn'],
  [/object\.interview_time/, 'Giờ phỏng vấn'],
];
const labelOf = (expr) => {
  for (const [re, label] of FIELD_MATCHERS) if (re.test(expr)) return label;
  return null;
};

const EXPR_RE = /\{\{[\s\S]*?\}\}/g;

/* ── Tiêu đề (ô input thường, không mang được thuộc tính) ──────────────────
   Dùng `memo` để nhớ biểu thức gốc theo nhãn, trả lại đúng bản gốc khi lưu. */

export const toFriendly = (s, memo) => (s || '').replace(EXPR_RE, (whole) => {
  const label = labelOf(whole);
  if (!label) return whole;              // biểu thức lạ: giữ nguyên, không nuốt
  if (memo && memo[label] === undefined) memo[label] = whole;
  return `[${label}]`;
});

export const toOdoo = (s, memo) => {
  let out = s || '';
  for (const t of TOKENS) {
    const original = memo && memo[t.label] ? memo[t.label] : t.code;
    out = out.split(`[${t.label}]`).join(original);
  }
  return out;
};

/* ── Import mail mẫu từ văn bản dán vào ────────────────────────────────────
   Mẫu mail Học Bá đang viết placeholder bằng tiếng Việt trong ngoặc vuông:
   [Tên ứng viên] · [TÊN VỊ TRÍ] · [ TÊN VỊ TRÍ] (có cả dấu cách thừa) ·
   [Tên vị trí tuyển dụng] · [giờ] · [thứ]. Nhận diện theo TỪ KHOÁ sau khi
   chuẩn hoá, không so khớp cứng — mỗi mẫu viết một kiểu.  */

const norm = (s) => s.toLowerCase().replace(/\s+/g, ' ').trim();

/* Thứ tự có ý nghĩa: cụm dài xét trước cụm ngắn. */
const IMPORT_RULES = [
  [/(họ tên|tên).*(ứng viên|uv)|^ứng viên$/, 'Họ tên ứng viên'],
  [/vị trí/, 'Vị trí ứng tuyển'],
  [/ngày.*(phỏng vấn|pv)|^ngày$/, 'Ngày phỏng vấn'],
  [/giờ|thời gian.*(phỏng vấn|pv)/, 'Giờ phỏng vấn'],
  [/email|thư điện tử/, 'Email ứng viên'],
  [/số điện thoại|sđt|điện thoại/, 'Số điện thoại'],
];

/* KHÔNG đụng vào: đây là chữ thật trong mail, không phải chỗ điền. */
const IMPORT_SKIP = [/học bá/, /^thứ$/];

/* Đổi `[...]` trong văn bản dán vào thành thẻ `[Nhãn]` chuẩn.
   Trả về { text, matched: [[gốc, nhãn]], skipped: [gốc] } để hiện bảng đối
   chiếu cho người dùng tự kiểm — không im lặng đổi dữ liệu của họ. */
export const bracketsToTokens = (raw) => {
  const matched = [];
  const skipped = [];
  const text = (raw || '').replace(/\[([^\]\n]{1,60})\]/g, (whole, inner) => {
    const n = norm(inner);
    if (IMPORT_SKIP.some((re) => re.test(n))) { skipped.push(whole); return whole; }
    for (const [re, label] of IMPORT_RULES) {
      if (re.test(n)) { matched.push([whole, label]); return `[${label}]`; }
    }
    skipped.push(whole);
    return whole;
  });
  return { text, matched, skipped };
};

const esc = (s) => (s || '')
  .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');

/* Văn bản thường (dán từ Word/Gmail/Excel) → HTML mail.
   Dòng trống ngăn đoạn ⇒ <p>; xuống dòng đơn trong đoạn ⇒ <br>. */
export const textToHtml = (text) => {
  const blocks = (text || '').replace(/\r\n?/g, '\n').split(/\n{2,}/)
    .map((b) => b.trim()).filter(Boolean);
  const body = blocks
    .map((b) => `  <p>${esc(b).split('\n').join('<br>')}</p>`)
    .join('\n');
  return '<div style="font-family: Arial, sans-serif; font-size: 14px;'
    + ' line-height: 1.8; color: #333333;">\n' + body + '\n</div>';
};

/* ── Nội dung (contentEditable, mang được data-expr) ───────────────────────── */

const TOKEN_STYLE = 'background:#fef3c7;border-radius:4px;padding:0 4px;'
  + 'font-weight:600;white-space:nowrap;';

/* `expr` là biểu thức Odoo gốc; bỏ trống ⇒ dùng dạng chuẩn của nhãn. */
export const tokenSpan = (label, expr) =>
  `<span class="mail-token" data-expr="${encodeURIComponent(expr || CODE_OF[label] || '')}"`
  + ` style="${TOKEN_STYLE}">[${label}]</span>`;

/* HTML trong DB → nội dung hiển thị cho HR soạn. */
export const storedToEditor = (html) => (html || '').replace(EXPR_RE, (whole) => {
  const label = labelOf(whole);
  return label ? tokenSpan(label, whole) : whole;
});

/* Nội dung soạn thảo → HTML đúng cú pháp Odoo để lưu.
   Ưu tiên data-expr (biểu thức gốc), thiếu thì mới dùng dạng chuẩn theo nhãn.
   Trình duyệt có thể cắt/nhân bản span khi HR gõ chen vào giữa nên gỡ theo thẻ,
   không đòi khớp cặp chính xác. */
export const editorToStored = (html) => {
  let out = (html || '').replace(
    /<span class="mail-token"([^>]*)>([\s\S]*?)<\/span>/g,
    (whole, attrs, inner) => {
      const m = /data-expr="([^"]*)"/.exec(attrs);
      if (m) {
        try { return decodeURIComponent(m[1]); } catch { /* rơi xuống dưới */ }
      }
      const lm = /^\[(.+)\]$/.exec(inner.trim());
      return (lm && CODE_OF[lm[1]]) || inner;
    });
  // Thẻ HR gõ tay hoặc dán từ ô Tiêu đề sang — không có span bọc.
  out = toOdoo(out);
  return out;
};
