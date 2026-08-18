# Dựng lại toàn bộ dữ liệu demo trên DB local hocba_hrm.
#   .\tools\demo_seed\seed_all.ps1
# ⚠️ p0_clean.py XOÁ SẠCH dữ liệu nghiệp vụ. Chỉ chạy trên DB local.
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Definition

$phases = @(
    'p0_clean.py',
    'p1_org.py',
    'p2_profile.py',
    'p3_attendance.py',
    'p4_timeoff.py',
    'p5_payroll.py',
    'p5b_fix_rules.py',
    'p5c_fix_categories.py',
    'p5d_fix_base_rule.py',
    'p6_recruitment.py',
    'p7_reviews_career.py',
    'p8_service_finance.py',
    'p9_finalize.py',
    'p10_fix_probation_profile.py',
    'p11_onboarding_queue.py'
)

foreach ($p in $phases) {
    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "  $p"
    Write-Host ("=" * 60)
    & "$dir\run.ps1" $p
}
