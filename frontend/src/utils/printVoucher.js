/* ============================================================
   printVoucher(voucher, company)
   Mở cửa sổ preview với dropdown chọn Thông tư:
     - TT200/2014: Mẫu 01-TT/02-TT (DN lớn)
     - TT133/2016: Mẫu 01-TT (DN vừa & nhỏ)
     - TT107/2017: Mẫu C40-BB (Hành chính sự nghiệp)
   User chọn template → preview thay đổi ngay → Ctrl+P / Save PDF.
   ============================================================ */
import { amountToWords, fmtVND } from './amountToWords';

/* ── Public API ────────────────────────────────────────────────────── */
export function printVoucher(voucher, company = {}) {
  const bodies = {
    tt200: renderTT200(voucher, company),
    tt133: renderTT133(voucher, company),
    tt107: renderTT107(voucher, company),
  };
  const html = buildPage(bodies, voucher);
  const w = window.open('', '_blank', 'width=920,height=760,toolbar=0,scrollbars=1');
  if (!w) { alert('Vui lòng cho phép popup — kiểm tra góc phải thanh địa chỉ trình duyệt.'); return; }
  w.document.write(html);
  w.document.close();
}

/* ── HTML page wrapper ─────────────────────────────────────────────── */
function buildPage(bodies, v) {
  const title = v.type === 'income' ? 'PHIẾU THU' : 'PHIẾU CHI';
  return `<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<title>${title} – ${esc(v.name || '')}</title>
<style>
/* ── Reset & base ── */
@page { size: A4 portrait; margin: 18mm 16mm 14mm 20mm; }
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Times New Roman',Times,serif;font-size:12.5pt;color:#000;background:#f3f4f6}

/* ── Control bar (hidden when printing) ── */
.ctrl-bar{
  background:#1d4ed8;color:#fff;
  display:flex;align-items:center;justify-content:space-between;
  padding:10px 20px;gap:12px;flex-wrap:wrap;
}
.ctrl-left{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.ctrl-label{font-family:sans-serif;font-size:13px;font-weight:600;white-space:nowrap}
.tpl-sel{
  font-family:sans-serif;font-size:13px;padding:6px 12px;
  border-radius:8px;border:none;background:#fff;color:#1d4ed8;
  font-weight:600;min-width:280px;cursor:pointer;
}
.print-btn{
  background:#fff;color:#1d4ed8;border:2px solid #fff;
  border-radius:8px;padding:7px 20px;font-size:13px;
  font-family:sans-serif;font-weight:700;cursor:pointer;white-space:nowrap;
}
.print-btn:hover{background:#dbeafe}

/* ── Voucher paper ── */
.tpl-wrap{background:#fff;max-width:780px;margin:18px auto;padding:22mm 20mm 18mm;box-shadow:0 2px 16px #0002}

/* ── Shared: header ── */
.hdr{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8pt}
.org-name{font-weight:bold;font-size:12pt}
.org-info{font-size:11pt;line-height:1.6}
.form-ref{text-align:right;font-size:10.5pt;line-height:1.6;max-width:220pt}
.form-ref .form-no{font-weight:bold;font-size:11.5pt}

/* ── Shared: fields table ── */
.fields{width:100%;border-collapse:collapse;margin-bottom:10pt}
.fields td{padding:5pt 0;font-size:12pt;vertical-align:bottom}
.lbl{white-space:nowrap;width:1%;padding-right:5pt;font-weight:normal}
.dotline{
  border-bottom:1px dotted #333;width:100%;
  display:block;min-height:16pt;line-height:16pt;padding:0 3pt;
}
.amount{font-weight:bold;font-size:13pt}

/* ── Shared: signature section ── */
.sig-section{margin-top:22pt}
.sig-date{text-align:right;font-size:11.5pt;font-style:italic;margin-bottom:14pt}
.sig-row{display:flex;justify-content:space-between;text-align:center}
.sig-row.five .sig-box{flex:1;padding:0 3pt}
.sig-row.three .sig-box{flex:1;padding:0 6pt}
.sig-box .sig-title{font-weight:bold;font-size:11pt}
.sig-box .sig-note{font-size:9.5pt;font-style:italic;color:#444;min-height:36pt;margin:2pt 0 0}
.sig-box .sig-line{border-top:1px solid #000;display:block;width:75%;margin:0 auto;padding-top:2pt;font-size:10pt;font-style:italic}

/* ── Shared: footer ── */
.footer-note{margin-top:14pt;font-size:8.5pt;color:#666;border-top:1px solid #ccc;padding-top:4pt}

/* ── TT200 specific ── */
/*
  Title block: 3 cột chính xác theo mẫu chuẩn BTC:
  [spacer 20%] [PHIẾU THU căn giữa 45%] [Quyển số/Số/Nợ/Có căn trái 35%]
*/
.tt200 .tb200{
  display:flex;align-items:flex-start;
  margin:10pt 0 8pt;
}
.tt200 .tb200-spacer{flex:0 0 20%}           /* vùng trống bên trái */
.tt200 .tb200-left{flex:0 0 45%;text-align:center}
.tt200 .tb200-left h1{font-size:15pt;font-weight:bold;letter-spacing:1pt}
.tt200 .tb200-left .tb200-date{font-size:11.5pt;font-style:italic;margin-top:4pt}
.tt200 .tb200-right{flex:0 0 35%;text-align:left;font-size:11pt;line-height:1.9;padding-left:8pt}
/* inline-pair: Số tiền + Viết bằng chữ cùng dòng */
.tt200 .dotline-inline{
  border-bottom:1px dotted #333;display:inline-block;
  min-width:80pt;line-height:16pt;padding:0 3pt;vertical-align:bottom;
}
.tt200 .dotline-kembali{
  border-bottom:1px dotted #333;display:inline-block;
  min-width:160pt;line-height:16pt;padding:0 3pt;vertical-align:bottom;
}

/* ── TT133 specific ── */
.tt133 .title-wrap{
  display:flex;justify-content:space-between;align-items:flex-start;
  margin:8pt 0 10pt;
}
.tt133 .title-left h1{font-size:18pt;font-weight:bold;letter-spacing:2pt}
.tt133 .title-left .title-date{font-size:11pt;margin-top:4pt;font-style:italic}
.tt133 .title-right{text-align:right;font-size:11pt;line-height:1.8}
.tt133 .inline-pair td{padding:5pt 0;vertical-align:bottom}
.tt133 .inline-pair .dotline-inline{
  border-bottom:1px dotted #333;display:inline-block;
  min-width:140pt;line-height:16pt;padding:0 3pt;vertical-align:bottom;
}
.tt133 .kembali-row{font-size:12pt;padding-top:6pt}
.tt133 .dotline-inline-short{
  border-bottom:1px dotted #333;display:inline-block;
  min-width:100pt;line-height:16pt;padding:0 3pt;vertical-align:bottom;
}

/* ── TT107 specific ── */
.tt107 .hdr-107{display:flex;justify-content:space-between;margin-bottom:10pt}
.tt107 .title-block-107{
  display:flex;margin:8pt 0 10pt;
}
.tt107 .title-center{flex:1;text-align:center}
.tt107 .title-center h1{font-size:18pt;font-weight:bold}
.tt107 .title-center .title-date{font-size:11pt;font-style:italic;margin-top:4pt}
.tt107 .title-center .title-so{font-size:11pt;margin-top:4pt}
.tt107 .title-right-107{text-align:right;font-size:11pt;line-height:1.8;min-width:120pt}
.tt107 .received{
  border:1px solid #ccc;padding:8pt 10pt;margin-top:14pt;font-size:11.5pt;
}
.tt107 .received .rec-row{margin-bottom:5pt}
.tt107 .dotline-rec{
  border-bottom:1px dotted #333;display:inline-block;
  min-width:200pt;line-height:16pt;padding:0 3pt;vertical-align:bottom;
}

/* ── Print media ── */
@media print {
  body{background:#fff}
  .ctrl-bar{display:none!important}
  .tpl-wrap{box-shadow:none;margin:0;padding:0;max-width:none}
}
</style>
</head>
<body>

<!-- Control bar -->
<div class="ctrl-bar no-print">
  <div class="ctrl-left">
    <span class="ctrl-label">📋 Mẫu theo Thông tư:</span>
    <select id="tpl-select" class="tpl-sel">
      <option value="tt200" selected>TT 200/2014 — Doanh nghiệp lớn (Mẫu 01-TT / 02-TT)</option>
      <option value="tt133">TT 133/2016 — Doanh nghiệp vừa &amp; nhỏ (Mẫu 01-TT)</option>
      <option value="tt107">TT 107/2017 — Hành chính sự nghiệp (Mẫu C40-BB)</option>
    </select>
  </div>
  <button class="print-btn" onclick="window.print()">🖨️ In / Lưu PDF</button>
</div>

<!-- Template containers -->
<div id="tpl-tt200" class="tpl-wrap">${bodies.tt200}</div>
<div id="tpl-tt133" class="tpl-wrap" hidden>${bodies.tt133}</div>
<div id="tpl-tt107" class="tpl-wrap" hidden>${bodies.tt107}</div>

<script>
  document.getElementById('tpl-select').addEventListener('change', function() {
    var v = this.value;
    ['tt200','tt133','tt107'].forEach(function(id) {
      document.getElementById('tpl-' + id).hidden = (id !== v);
    });
  });
</script>
</body>
</html>`;
}

/* ── Renderer: TT200/2014 — Doanh nghiệp lớn ──────────────────────── */
function renderTT200(v, c) {
  const isIncome = v.type === 'income';
  const { d, m, y } = splitDate(v.date);
  const formNo  = isIncome ? '01-TT' : '02-TT';
  const title   = isIncome ? 'PHIẾU THU' : 'PHIẾU CHI';
  const pLabel  = isIncome ? 'Họ và tên người nộp tiền' : 'Họ và tên người nhận tiền';
  const rLabel  = isIncome ? 'Lý do nộp' : 'Lý do chi';
  const sigLbl  = isIncome ? 'nộp' : 'nhận';
  const lien    = isIncome ? 'người nộp tiền' : 'người nhận tiền';
  const words   = amountToWords(v.amount);

  return `
<div class="voucher tt200">
  <!-- Header -->
  <div class="hdr">
    <div class="org-info">
      <div>Đơn vị: <strong>${esc(c.name || '.......................')}</strong></div>
      <div>Địa chỉ: ${esc(c.address || '.......................')}</div>
      ${c.phone ? `<div>ĐT: ${esc(c.phone)}</div>` : ''}
    </div>
    <div class="form-ref">
      <div class="form-no">Mẫu số ${formNo}</div>
      <div>(Ban hành theo Thông tư số 200/2014/TT-BTC</div>
      <div>Ngày 22/12/2014 của Bộ Tài chính)</div>
    </div>
  </div>

  <!-- Title block: [spacer 20%] | [PHIẾU THU 45%] | [Quyển số/Số/Nợ/Có 35%] -->
  <div class="tb200">
    <div class="tb200-spacer"></div>
    <div class="tb200-left">
      <h1>${title}</h1>
      <div class="tb200-date">
        Ngày <u>&nbsp;${d}&nbsp;</u> tháng <u>&nbsp;${m}&nbsp;</u> năm <u>&nbsp;${y}&nbsp;</u>
      </div>
    </div>
    <div class="tb200-right">
      <div>Quyển số: .................</div>
      <div>Số: <strong>${esc(v.name || '.............')}</strong></div>
      <div>Nợ: .................</div>
      <div>Có: .................</div>
    </div>
  </div>

  <!-- Content fields -->
  <table class="fields">
    <tr>
      <td class="lbl">${pLabel}:</td>
      <td><span class="dotline">${esc(v.partnerName)}</span></td>
    </tr>
    <tr>
      <td class="lbl">Địa chỉ:</td>
      <td><span class="dotline">${esc(v.partnerAddress)}</span></td>
    </tr>
    <tr>
      <td class="lbl">${rLabel}:</td>
      <td><span class="dotline">${esc(v.memo)}</span></td>
    </tr>
    <!-- Số tiền + Viết bằng chữ cùng 1 dòng (chuẩn TT200) -->
    <tr>
      <td class="lbl" style="white-space:nowrap;vertical-align:bottom">Số tiền:</td>
      <td style="vertical-align:bottom;padding:5pt 0">
        <span class="dotline-inline amount">${fmtVND(v.amount)}</span>
        <span style="font-size:11pt;font-weight:normal">&ensp;(Viết bằng chữ):</span>
        <span class="dotline-inline">${esc(words)}</span>
      </td>
    </tr>
    <!-- Dòng trống — overflow chữ -->
    <tr><td colspan="2"><span class="dotline">&nbsp;</span></td></tr>
    <!-- Kèm theo + Chứng từ gốc cùng 1 dòng (chuẩn TT200) -->
    <tr>
      <td colspan="2" style="padding-top:5pt">
        Kèm theo:
        <span class="dotline-kembali">&nbsp;</span>
        Chứng từ gốc: <strong>${v.attachmentCount || 0}</strong>
      </td>
    </tr>
  </table>

  <div class="sig-section">
    <div class="sig-date">Ngày&nbsp;<u>&nbsp;${d}&nbsp;</u>&nbsp;tháng&nbsp;<u>&nbsp;${m}&nbsp;</u>&nbsp;năm&nbsp;<u>&nbsp;${y}&nbsp;</u></div>
    <div class="sig-row five">
      ${box('Giám đốc',        '(Ký, họ tên, đóng dấu)')}
      ${box('Kế toán trưởng',  '(Ký, họ tên)')}
      ${box('Thủ quỹ',         '(Ký, họ tên)')}
      ${box(`Người ${sigLbl} tiền`, '(Ký, họ tên)')}
      ${box('Người lập phiếu', '(Ký, họ tên)')}
    </div>
  </div>

  <div class="footer-note">
    Phiếu được lập thành 3 liên: 1 liên lưu gốc · 1 liên giao ${lien} · 1 liên lưu kế toán.
    In từ phần mềm HRM HọcBá. Số phiếu: ${esc(v.name || '—')}.
  </div>
</div>`;
}

/* ── Renderer: TT133/2016 — Doanh nghiệp vừa và nhỏ ───────────────── */
function renderTT133(v, c) {
  const isIncome = v.type === 'income';
  const { d, m, y } = splitDate(v.date);
  const title  = isIncome ? 'PHIẾU THU' : 'PHIẾU CHI';
  const pLabel = isIncome ? 'Họ và tên người nộp tiền' : 'Họ và tên người nhận tiền';
  const rLabel = isIncome ? 'Lý do nộp' : 'Lý do chi';
  const sigLbl = isIncome ? 'nộp' : 'nhận';
  const lien   = isIncome ? 'người nộp tiền' : 'người nhận tiền';
  const words  = amountToWords(v.amount);

  return `
<div class="voucher tt133">
  <div class="hdr">
    <div class="org-info">
      <div>Đơn vị: <strong>${esc(c.name || '.......................')}</strong></div>
      <div>Địa chỉ: ${esc(c.address || '.......................')}</div>
    </div>
    <div class="form-ref">
      <div class="form-no">Mẫu số 01 - TT</div>
      <div>(Ban hành theo Thông tư số 133/2016/TT-BTC</div>
      <div>ngày 26/8/2016 của Bộ Tài chính)</div>
    </div>
  </div>

  <div class="title-wrap">
    <div class="title-left">
      <h1>${title}</h1>
      <div class="title-date">Ngày .... tháng .... năm ....</div>
    </div>
    <div class="title-right">
      <div>Quyển số: .................</div>
      <div>Số: <strong>${esc(v.name || '.............')}</strong></div>
      <div>Nợ: .................</div>
      <div>Có: .................</div>
    </div>
  </div>

  <table class="fields">
    <tr>
      <td class="lbl">${pLabel}:</td>
      <td><span class="dotline">${esc(v.partnerName)}</span></td>
    </tr>
    <tr>
      <td class="lbl">Địa chỉ:</td>
      <td><span class="dotline">${esc(v.partnerAddress)}</span></td>
    </tr>
    <tr>
      <td class="lbl">${rLabel}:</td>
      <td><span class="dotline">${esc(v.memo)}</span></td>
    </tr>
    <tr class="inline-pair">
      <td class="lbl" style="white-space:nowrap;vertical-align:bottom">Số tiền:</td>
      <td style="vertical-align:bottom;padding:5pt 0">
        <span class="dotline-inline amount">${fmtVND(v.amount)}</span>
        &ensp;<span style="font-size:11pt">(Viết bằng chữ):</span>&ensp;
        <span class="dotline-inline">${esc(words)}</span>
      </td>
    </tr>
    <tr>
      <td colspan="2"><span class="dotline">&nbsp;</span></td>
    </tr>
    <tr>
      <td colspan="2" class="kembali-row">
        Kèm theo:
        <span class="dotline-inline-short">&nbsp;</span>
        &ensp;Chứng từ gốc: <strong>${v.attachmentCount || 0}</strong>
      </td>
    </tr>
  </table>

  <div class="sig-section">
    <div class="sig-date">Ngày&nbsp;<u>&nbsp;${d}&nbsp;</u>&nbsp;tháng&nbsp;<u>&nbsp;${m}&nbsp;</u>&nbsp;năm&nbsp;<u>&nbsp;${y}&nbsp;</u></div>
    <div class="sig-row five">
      ${box('Giám đốc',        '(Ký, họ tên, đóng dấu)')}
      ${box('Kế toán trưởng',  '(Ký, họ tên)')}
      ${box('Thủ quỹ',         '(Ký, họ tên)')}
      ${box(`Người ${sigLbl} tiền`, '(Ký, họ tên)')}
      ${box('Người lập phiếu', '(Ký, họ tên)')}
    </div>
  </div>

  <div class="footer-note">
    Phiếu được lập thành 3 liên: 1 liên lưu gốc · 1 liên giao ${lien} · 1 liên lưu kế toán.
    In từ phần mềm HRM HọcBá. Số phiếu: ${esc(v.name || '—')}.
  </div>
</div>`;
}

/* ── Renderer: TT107/2017 — Hành chính sự nghiệp (C40-BB) ─────────── */
function renderTT107(v, c) {
  const isIncome = v.type === 'income';
  const { d, m, y } = splitDate(v.date);
  const title  = isIncome ? 'PHIẾU THU' : 'PHIẾU CHI';
  const pLabel = isIncome ? 'Họ và tên người nộp tiền' : 'Họ và tên người nhận tiền';
  const words  = amountToWords(v.amount);

  return `
<div class="voucher tt107">
  <div class="hdr-107">
    <div class="org-info">
      <div>Đơn vị: <strong>${esc(c.name || '.......................')}</strong></div>
      <div>Mã QHNS: .................</div>
    </div>
    <div class="form-ref" style="text-align:right;font-size:10.5pt;line-height:1.6">
      <div><strong>Mẫu C40-BB</strong></div>
      <div>(Ban hành theo Thông tư số 107/2017/TT-BTC</div>
      <div>ngày 10/10/2017 của Bộ Tài chính)</div>
    </div>
  </div>

  <div class="title-block-107">
    <div class="title-center">
      <h1>${title}</h1>
      <div class="title-date">Ngày .... tháng .... năm ....</div>
      <div class="title-so">Số: <strong>${esc(v.name || '.............')}</strong></div>
    </div>
    <div class="title-right-107">
      <div>Quyển số: ........</div>
      <div style="margin-top:12pt">Nợ: .................</div>
      <div>Có: .................</div>
    </div>
  </div>

  <table class="fields">
    <tr>
      <td class="lbl">${pLabel}:</td>
      <td><span class="dotline">${esc(v.partnerName)}</span></td>
    </tr>
    <tr>
      <td class="lbl">Địa chỉ:</td>
      <td><span class="dotline">${esc(v.partnerAddress)}</span></td>
    </tr>
    <tr>
      <td class="lbl">Nội dung:</td>
      <td><span class="dotline">${esc(v.memo)}</span></td>
    </tr>
    <tr>
      <td class="lbl">Số tiền:</td>
      <td>
        <span class="dotline">
          <strong>${fmtVND(v.amount)}</strong>
          <span style="font-size:11pt;font-weight:normal"> ....................(loại tiền)</span>
        </span>
      </td>
    </tr>
    <tr>
      <td class="lbl">(viết bằng chữ):</td>
      <td><span class="dotline">${esc(words)}</span></td>
    </tr>
    <tr>
      <td class="lbl">Kèm theo:</td>
      <td><span class="dotline">${v.attachmentCount || 0} chứng từ gốc</span></td>
    </tr>
  </table>

  <div class="sig-section" style="margin-top:18pt">
    <div class="sig-row three">
      ${box('Thủ trưởng đơn vị', '(Ký, họ tên, đóng dấu)')}
      ${box('Kế toán trưởng',    '(Ký, họ tên)')}
      ${box('Người lập',         '(Ký, họ tên)')}
    </div>
  </div>

  <div class="received">
    <div class="rec-row">
      Đã nhận đủ số tiền:&nbsp; &ndash; Bằng số:
      <span class="dotline-rec"><strong>${fmtVND(v.amount)}</strong> đồng</span>
    </div>
    <div class="rec-row">
      <span style="opacity:0">Đã nhận đủ số tiền:</span>&nbsp; &ndash; Bằng chữ:
      <span class="dotline-rec">${esc(words)}</span>
    </div>
  </div>

  <div class="footer-note">
    In từ phần mềm HRM HọcBá. Số phiếu: ${esc(v.name || '—')}.
  </div>
</div>`;
}

/* ── Shared helpers ─────────────────────────────────────────────────── */
function box(title, note) {
  return `<div class="sig-box">
    <div class="sig-title">${title}</div>
    <div class="sig-note">${note}</div>
    <span class="sig-line">&nbsp;</span>
  </div>`;
}

function splitDate(ds) {
  if (!ds) return { d: '......', m: '......', y: '......' };
  const dt = new Date(ds);
  return { d: dt.getDate(), m: dt.getMonth() + 1, y: dt.getFullYear() };
}

function esc(s) {
  return String(s || '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}
