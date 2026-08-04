/* Đọc file mail mẫu do HR chọn → văn bản thuần, để đưa vào cùng luồng với ô dán.
   Dự án không có thư viện parse tài liệu nào và cũng không nên thêm, nên .docx
   được mở bằng API sẵn có của trình duyệt: .docx là file ZIP, giải nén
   word/document.xml bằng DecompressionStream rồi bóc chữ ra. */

export const ACCEPT = '.txt,.md,.eml,.html,.htm,.docx';

const decodeEntities = (s) => (s || '')
  .replace(/&lt;/g, '<').replace(/&gt;/g, '>')
  .replace(/&quot;/g, '"').replace(/&#39;/g, "'")
  .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&');   // &amp; cuối cùng, không thì hỏng chuỗi

/* HTML → văn bản: thẻ khối thành xuống dòng để giữ bố cục đoạn. */
const htmlToText = (html) => decodeEntities((html || '')
  .replace(/<(script|style)[\s\S]*?<\/\1>/gi, '')
  .replace(/<br\s*\/?>/gi, '\n')
  .replace(/<\/(p|div|tr|li|h[1-6])>/gi, '\n\n')
  .replace(/<[^>]+>/g, ''))
  .replace(/\n{3,}/g, '\n\n')
  .trim();

async function inflateRaw(bytes) {
  const ds = new DecompressionStream('deflate-raw');
  const buf = await new Response(new Blob([bytes]).stream().pipeThrough(ds)).arrayBuffer();
  return new Uint8Array(buf);
}

/* Lấy 1 entry trong file ZIP qua bảng thư mục trung tâm (đáng tin hơn quét
   local header, vì local header có thể để size = 0 và ghi ở data descriptor). */
async function zipEntry(buf, wanted) {
  const dv = new DataView(buf);
  let eocd = -1;
  const min = Math.max(0, buf.byteLength - 22 - 65536);
  for (let i = buf.byteLength - 22; i >= min; i--) {
    if (dv.getUint32(i, true) === 0x06054b50) { eocd = i; break; }
  }
  if (eocd < 0) throw new Error('File .docx không hợp lệ.');
  let p = dv.getUint32(eocd + 16, true);
  const count = dv.getUint16(eocd + 10, true);
  const dec = new TextDecoder();
  for (let n = 0; n < count; n++) {
    if (dv.getUint32(p, true) !== 0x02014b50) break;
    const method = dv.getUint16(p + 10, true);
    const compSize = dv.getUint32(p + 20, true);
    const nameLen = dv.getUint16(p + 28, true);
    const extraLen = dv.getUint16(p + 30, true);
    const cmtLen = dv.getUint16(p + 32, true);
    const localOff = dv.getUint32(p + 42, true);
    const name = dec.decode(new Uint8Array(buf, p + 46, nameLen));
    if (name === wanted) {
      const lnLen = dv.getUint16(localOff + 26, true);
      const leLen = dv.getUint16(localOff + 28, true);
      const start = localOff + 30 + lnLen + leLen;
      const raw = new Uint8Array(buf, start, compSize);
      const out = method === 0 ? raw : await inflateRaw(raw);
      return dec.decode(out);
    }
    p += 46 + nameLen + extraLen + cmtLen;
  }
  throw new Error('Không tìm thấy nội dung trong file .docx.');
}

/* XML của Word → văn bản: mỗi <w:p> là một đoạn, <w:br> là xuống dòng. */
const docxXmlToText = (xml) => decodeEntities(xml
  .replace(/<w:br[^>]*\/?>/g, '\n')
  .replace(/<\/w:p>/g, '\n\n')
  .replace(/<[^>]+>/g, ''))
  .replace(/\n{3,}/g, '\n\n')
  .trim();

/* File → văn bản thuần. Ném Error với thông báo tiếng Việt nếu không đọc được. */
export async function readMailFile(file) {
  const name = (file.name || '').toLowerCase();
  if (name.endsWith('.docx')) {
    if (typeof DecompressionStream === 'undefined')
      throw new Error('Trình duyệt này không mở được .docx — hãy lưu sang .txt rồi thử lại.');
    return docxXmlToText(await zipEntry(await file.arrayBuffer(), 'word/document.xml'));
  }
  const text = await file.text();
  if (name.endsWith('.html') || name.endsWith('.htm')) return htmlToText(text);
  if (name.endsWith('.doc'))
    throw new Error('File .doc (Word cũ) không đọc được — hãy lưu lại thành .docx hoặc .txt.');
  return text;                                   // .txt · .md · .eml
}
