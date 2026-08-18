# Chạy 1 script seed trong container Odoo local.
#   .\tools\demo_seed\run.ps1 p0_clean.py
param([Parameter(Mandatory = $true)][string]$Script)

$container = 'isp490_g2_hocba_hrm-odoo-1'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Definition

# rm trước: docker cp vào thư mục ĐÃ tồn tại sẽ lồng thêm 1 cấp
# (/tmp/seed/demo_seed/...) và script cũ vẫn nằm nguyên chỗ cũ → chạy nhầm bản cũ.
# -u root: file do docker cp đẻ ra thuộc root, user odoo trong container xoá không nổi.
docker exec -u root $container rm -rf /tmp/seed | Out-Null
docker cp "$dir" "${container}:/tmp/seed" | Out-Null
# Lệnh phải nằm TRỌN 1 dòng: file .ps1 bị chuyển sang CRLF (git autocrlf) thì
# dấu "\" nối dòng của bash đứng trước CR không còn là nối dòng nữa → bash cắt
# thành nhiều lệnh và báo "--db_password: command not found".
$cmd = "odoo shell -d hocba_hrm --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo_password --addons-path=/mnt/extra-addons --no-http --log-level=warn < /tmp/seed/$Script"
docker exec $container bash -c $cmd 2>&1 | Where-Object { $_ -notmatch 'not installable, skipped|_sql_constraints|Some modules are not loaded' }
