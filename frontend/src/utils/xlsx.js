/* Xuất file Excel (.xlsx) thuần client — không phụ thuộc thư viện ngoài.
   Đóng gói một ZIP "store" (không nén) chứa XML tối thiểu của Office OpenXML.
   downloadXlsx(filename, sheetName, headers, rows):
     - headers: mảng string tiêu đề cột
     - rows: mảng các hàng; mỗi hàng là mảng giá trị (number → ô số, còn lại → text). */

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

function cellXml(ref, value) {
  if (typeof value === 'number' && Number.isFinite(value)) {
    return `<c r="${ref}"><v>${value}</v></c>`;
  }
  return `<c r="${ref}" t="inlineStr"><is><t xml:space="preserve">${xmlEscape(value ?? '')}</t></is></c>`;
}

function sheetXml(headers, rows) {
  const lines = [];
  const head = headers.map((h, c) => cellXml(colLetter(c) + '1', String(h))).join('');
  lines.push(`<row r="1">${head}</row>`);
  rows.forEach((row, r) => {
    const cells = row.map((v, c) => cellXml(colLetter(c) + (r + 2), v)).join('');
    lines.push(`<row r="${r + 2}">${cells}</row>`);
  });
  return `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>${lines.join('')}</sheetData></worksheet>`;
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

export function downloadXlsx(filename, sheetName, headers, rows) {
  const safeSheet = xmlEscape((sheetName || 'Sheet1').slice(0, 31));
  const files = [
    {
      name: '[Content_Types].xml',
      data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>`,
    },
    {
      name: '_rels/.rels',
      data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>`,
    },
    {
      name: 'xl/workbook.xml',
      data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="${safeSheet}" sheetId="1" r:id="rId1"/></sheets></workbook>`,
    },
    {
      name: 'xl/_rels/workbook.xml.rels',
      data: `<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>`,
    },
    { name: 'xl/worksheets/sheet1.xml', data: sheetXml(headers, rows) },
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
