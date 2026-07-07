/* Xuất file Excel (.xlsx) thuần client — không phụ thuộc thư viện ngoài.
   Đóng gói một ZIP "store" (không nén) chứa XML tối thiểu của Office OpenXML.
   downloadXlsx(filename, sheetName, headers, rows, opts):
     - headers: mảng string tiêu đề cột
     - rows: mảng các hàng; mỗi hàng là mảng giá trị (number → ô số, còn lại → text)
     - opts (tuỳ chọn):
         · colStyles: mảng theo chỉ số cột { headerFill, valueFill } — mã màu '#RRGGBB'
           (hoặc null/undefined = không tô, để trắng). Tô nền ô tiêu đề / ô giá trị.
         · lastRowIsTotal: true → hàng cuối in đậm (dòng "Tổng"). */

const enc = new TextEncoder();

/* ---- CRC32 (bảng tra cứu) ---- */
const CRC_TABLE = (() => {
  const t = new Uint32Array(256);
  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xedb88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c >>> 0;
  }
  return t;
})();

function crc32(bytes) {
  let c = 0xffffffff;
  for (let i = 0; i < bytes.length; i++) c = CRC_TABLE[(c ^ bytes[i]) & 0xff] ^ (c >>> 8);
  return (c ^ 0xffffffff) >>> 0;
}

function xmlEscape(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&apos;');
}

function colLetter(i) {
  let s = '';
  i += 1;
  while (i > 0) { const r = (i - 1) % 26; s = String.fromCharCode(65 + r) + s; i = Math.floor((i - 1) / 26); }
  return s;
}

function numCell(ref, value, s) {
  // numFmt "#,##0": số hiện đầy đủ (232,000,000) thay vì E+08, vẫn tính được.
  return `<c r="${ref}" s="${s}"><v>${value}</v></c>`;
}
function textCell(ref, value, s) {
  return `<c r="${ref}"${s ? ` s="${s}"` : ''} t="inlineStr"><is><t xml:space="preserve">${xmlEscape(value ?? '')}</t></is></c>`;
}
function formulaCell(ref, f, s) {
  // Ô công thức: Excel tự tính khi mở (workbook.calcPr fullCalcOnLoad).
  return `<c r="${ref}" s="${s}"><f>${xmlEscape(f)}</f></c>`;
}
function isFormula(v) { return v != null && typeof v === 'object' && typeof v.f === 'string'; }

/* Tạo ô công thức để chèn vào `rows`. Vd một ô SUM cả cột (để Excel tự cộng
   hàng Tổng thay vì tính sẵn trong JS): sumFormula(colIndex, firstRow, lastRow). */
export function sumFormula(colIndex, firstRow, lastRow) {
  const L = colLetter(colIndex);
  return { f: `SUM(${L}${firstRow}:${L}${lastRow})` };
}

function normHex(hex) {
  return String(hex).replace('#', '').toUpperCase().slice(0, 6).padEnd(6, '0');
}

/* Bộ đăng ký style động: dùng chung một bảng fill/font/border, sinh cellXfs theo
   nhu cầu thực tế (dedup) rồi xuất styles.xml. Cho phép tô nền từng ô (fill màu)
   để người dùng cấu hình màu tiêu đề / màu giá trị từng cột khi in. */
function createStyleRegistry() {
  const fillColors = [];              // hex (không '#'); fillId = index + 2 (0=none,1=gray125)
  function fillId(hex) {
    if (!hex) return 0;
    const norm = normHex(hex);
    let i = fillColors.indexOf(norm);
    if (i < 0) { fillColors.push(norm); i = fillColors.length - 1; }
    return i + 2;
  }
  const xfs = [];
  const xfMap = new Map();
  function xf(numFmtId, fontId, fillIdx, borderId, align) {
    const key = `${numFmtId}|${fontId}|${fillIdx}|${borderId}|${align || 0}`;
    let i = xfMap.get(key);
    if (i == null) { i = xfs.length; xfs.push({ numFmtId, fontId, fillId: fillIdx, borderId, align }); xfMap.set(key, i); }
    return i;
  }
  xf(0, 0, 0, 0, 0);                  // xf 0 = mặc định trơn
  function build() {
    const fonts = '<fonts count="2"><font><sz val="11"/><name val="Calibri"/></font>'
      + '<font><b/><sz val="11"/><name val="Calibri"/></font></fonts>';
    const fills = `<fills count="${2 + fillColors.length}"><fill><patternFill patternType="none"/></fill>`
      + '<fill><patternFill patternType="gray125"/></fill>'
      + fillColors.map((h) => `<fill><patternFill patternType="solid"><fgColor rgb="FF${h}"/></patternFill></fill>`).join('')
      + '</fills>';
    const borders = '<borders count="2"><border/>'
      + '<border><left style="thin"><color rgb="FFBFBFBF"/></left><right style="thin"><color rgb="FFBFBFBF"/></right>'
      + '<top style="thin"><color rgb="FFBFBFBF"/></top><bottom style="thin"><color rgb="FFBFBFBF"/></bottom></border></borders>';
    const cellXfs = xfs.map((x) => {
      const a = [`numFmtId="${x.numFmtId}"`, `fontId="${x.fontId}"`, `fillId="${x.fillId}"`, `borderId="${x.borderId}"`, 'xfId="0"'];
      if (x.numFmtId) a.push('applyNumberFormat="1"');
      if (x.fontId) a.push('applyFont="1"');
      if (x.fillId > 1) a.push('applyFill="1"');
      if (x.borderId) a.push('applyBorder="1"');
      if (x.align) a.push('applyAlignment="1"');
      const inner = x.align ? '<alignment horizontal="center" vertical="center" wrapText="1"/>' : '';
      return `<xf ${a.join(' ')}>${inner}</xf>`;
    }).join('');
    return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
      + '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
      + '<numFmts count="1"><numFmt numFmtId="164" formatCode="#,##0"/></numFmts>'
      + fonts + fills + borders
      + '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
      + `<cellXfs count="${xfs.length}">${cellXfs}</cellXfs>`
      + '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>';
  }
  return { fillId, xf, build };
}

/* Độ rộng hiển thị của một giá trị (số dài kèm dấu phẩy '#,##0'). */
function displayLen(v) {
  if (isFormula(v)) return 0;                         // ô công thức: bề rộng do ô số khác quyết định
  if (typeof v === 'number' && Number.isFinite(v)) {
    const digits = Math.round(v).toString().replace('-', '').length;
    const seps = Math.floor((digits - 1) / 3);       // số dấu phẩy phân nhóm nghìn
    return digits + seps + (v < 0 ? 1 : 0);
  }
  return String(v ?? '').length;
}

/* <cols>: tự canh bề rộng mỗi cột theo nội dung dài nhất → tránh số bị "####". */
function colsXml(headers, rows) {
  const n = headers.length;
  const cols = [];
  for (let c = 0; c < n; c++) {
    let max = displayLen(headers[c]);
    for (const row of rows) if (c < row.length) max = Math.max(max, displayLen(row[c]));
    const width = Math.min(60, Math.max(8, max + 2));  // +2 đệm, kẹp 8..60
    cols.push(`<col min="${c + 1}" max="${c + 1}" width="${width}" customWidth="1"/>`);
  }
  return `<cols>${cols.join('')}</cols>`;
}

function sheetXml(headers, rows, colStyles, lastRowIsTotal, reg) {
  const cs = (i) => colStyles[i] || {};
  const lines = [];
  // Header: đậm (font 1) + border + căn giữa/wrap (align 1) + màu nền tuỳ cột.
  const head = headers.map((h, c) => {
    const s = reg.xf(0, 1, reg.fillId(cs(c).headerFill), 1, 1);
    return textCell(colLetter(c) + '1', String(h), s);
  }).join('');
  lines.push(`<row r="1">${head}</row>`);
  rows.forEach((row, r) => {
    const isTotal = lastRowIsTotal && r === rows.length - 1;
    const font = isTotal ? 1 : 0;    // hàng tổng in đậm
    const cells = row.map((v, c) => {
      const fill = reg.fillId(cs(c).valueFill);
      const ref = colLetter(c) + (r + 2);
      if (isFormula(v)) {
        return formulaCell(ref, v.f, reg.xf(164, font, fill, 1, 0));
      }
      if (typeof v === 'number' && Number.isFinite(v)) {
        return numCell(ref, v, reg.xf(164, font, fill, 1, 0));
      }
      return textCell(ref, v, reg.xf(0, font, fill, 1, 0));
    }).join('');
    lines.push(`<row r="${r + 2}">${cells}</row>`);
  });
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">${colsXml(headers, rows)}<sheetData>${lines.join('')}</sheetData></worksheet>`;
}

/* ---- ZIP (phương thức store, không nén) ---- */
function buildZip(files) {
  const enc2 = (s) => enc.encode(s);
  const local = [];
  const central = [];
  let offset = 0;

  const u16 = (n) => [n & 0xff, (n >>> 8) & 0xff];
  const u32 = (n) => [n & 0xff, (n >>> 8) & 0xff, (n >>> 16) & 0xff, (n >>> 24) & 0xff];

  for (const f of files) {
    const nameBytes = enc2(f.name);
    const dataBytes = typeof f.data === 'string' ? enc2(f.data) : f.data;
    const crc = crc32(dataBytes);
    const size = dataBytes.length;

    const lh = [
      ...u32(0x04034b50), ...u16(20), ...u16(0), ...u16(0), ...u16(0), ...u16(0),
      ...u32(crc), ...u32(size), ...u32(size), ...u16(nameBytes.length), ...u16(0),
    ];
    local.push(Uint8Array.from(lh), nameBytes, dataBytes);

    const ch = [
      ...u32(0x02014b50), ...u16(20), ...u16(20), ...u16(0), ...u16(0), ...u16(0), ...u16(0),
      ...u32(crc), ...u32(size), ...u32(size), ...u16(nameBytes.length), ...u16(0), ...u16(0),
      ...u16(0), ...u16(0), ...u32(0), ...u32(offset),
    ];
    central.push(Uint8Array.from(ch), nameBytes);

    offset += lh.length + nameBytes.length + size;
  }

  const cdSize = central.reduce((n, a) => n + a.length, 0);
  const eocd = Uint8Array.from([
    ...u32(0x06054b50), ...u16(0), ...u16(0), ...u16(files.length), ...u16(files.length),
    ...u32(cdSize), ...u32(offset), ...u16(0),
  ]);

  const parts = [...local, ...central, eocd];
  const total = parts.reduce((n, a) => n + a.length, 0);
  const out = new Uint8Array(total);
  let p = 0;
  for (const a of parts) { out.set(a, p); p += a.length; }
  return out;
}

export function downloadXlsx(filename, sheetName, headers, rows, opts = {}) {
  const safeSheet = xmlEscape((sheetName || 'Sheet1').slice(0, 31));
  const reg = createStyleRegistry();
  // Dựng sheet trước (đăng ký style dùng), rồi mới build styles.xml.
  const sheetData = sheetXml(headers, rows, opts.colStyles || [], !!opts.lastRowIsTotal, reg);
  const stylesXml = reg.build();
  const files = [
    {
      name: '[Content_Types].xml',
      data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>`,
    },
    {
      name: '_rels/.rels',
      data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`,
    },
    {
      name: 'xl/workbook.xml',
      data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="${safeSheet}" sheetId="1" r:id="rId1"/></sheets><calcPr fullCalcOnLoad="1"/></workbook>`,
    },
    {
      name: 'xl/_rels/workbook.xml.rels',
      data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>`,
    },
    { name: 'xl/styles.xml', data: stylesXml },
    { name: 'xl/worksheets/sheet1.xml', data: sheetData },
  ];

  const zip = buildZip(files);
  const blob = new Blob([zip], {
    type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename.endsWith('.xlsx') ? filename : filename + '.xlsx';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
