# Mở file bằng Word để dựng sẵn mục lục (TOC) rồi lưu lại, và (tuỳ chọn)
# xuất PDF để soi bố cục.
#   powershell -NoProfile -File finish_word.ps1        # chỉ dựng TOC
#   powershell -NoProfile -File finish_word.ps1 -AsPdf # dựng TOC + xuất PDF
#
# Lưu ý: ExportAsFixedFormat hay treo khi Word chạy ẩn; script dùng SaveAs2
# (wdFormatPDF = 17) và luôn Quit trong finally để không bỏ lại WINWORD.EXE.
param([switch]$AsPdf)

$ErrorActionPreference = 'Stop'
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$doc  = Join-Path $here 'out\ISP490_G2_User_manual_Employee_v1.0.docx'
$pdf  = Join-Path $here 'out\ISP490_G2_User_manual_Employee_v1.0.pdf'

$w = New-Object -ComObject Word.Application
$w.Visible = $false
$w.DisplayAlerts = 0
try {
    $d = $w.Documents.Open($doc, $false, $false)
    foreach ($toc in $d.TablesOfContents) { $toc.Update() }
    $d.Fields.Update() | Out-Null
    $d.Repaginate()
    Write-Output ("pages: " + $d.ComputeStatistics(2))
    $d.Save()
    if ($AsPdf) {
        $d.SaveAs2($pdf, 17)
        Write-Output ("pdf: " + $pdf)
    }
    $d.Close($false)
} finally {
    $w.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($w) | Out-Null
}
