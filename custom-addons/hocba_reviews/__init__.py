from . import models
from . import controllers

from .models.hb_review_criteria import seed_default_anchors


def post_init_hook(env):
    """Cài mới: điền thang mô tả hành vi cho bộ tiêu chí mặc định.

    Để ở hook thay vì trong file data vì data đang noupdate=1 (giữ trọng số HR
    đã sửa) — thêm field vào record cũ trong đó sẽ không bao giờ được áp dụng.
    """
    seed_default_anchors(env)
