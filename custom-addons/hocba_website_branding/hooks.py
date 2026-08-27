# -*- coding: utf-8 -*-
"""Phần branding KHÔNG khai báo được bằng XML: ảnh nhị phân (logo) và ngôn ngữ.

Chạy một lần lúc cài module. Viết theo kiểu chạy lại nhiều lần cũng không sao
(idempotent) để lỡ có `-i` lại thì không hỏng gì.
"""
import base64
import logging

from odoo.tools import file_open

_logger = logging.getLogger(__name__)

LOGO_PATH = 'hocba_website_branding/static/src/img/logo_hocba.png'


def _install_vietnamese(env):
    """Bật vi_VN và đặt làm ngôn ngữ duy nhất của website công khai."""
    lang = env['res.lang'].with_context(active_test=False).search(
        [('code', '=', 'vi_VN')], limit=1)
    if not lang:
        _logger.warning('Không tìm thấy res.lang vi_VN — bỏ qua bước ngôn ngữ.')
        return None
    if not lang.active:
        # Wizard này mới nạp bản dịch của các module; set active=True suông thì
        # ngôn ngữ bật nhưng giao diện vẫn tiếng Anh.
        env['base.language.install'].create({
            'lang_ids': [(6, 0, [lang.id])],
            'overwrite': False,
        }).lang_install()
        _logger.info('Đã cài ngôn ngữ vi_VN.')
    return lang


def _set_logo(record, b64_logo, label):
    """Ghi logo rồi ĐỌC LẠI để chắc chắn.

    Field Binary của Odoo lưu qua ir.attachment; đã gặp trường hợp ghi xong
    commit êm ru mà dữ liệu không nằm lại trong DB, nên phải verify.
    """
    record.write({'logo': b64_logo})
    record.invalidate_recordset(['logo'])
    written = record.logo
    if not written:
        _logger.error('Ghi logo cho %s KHÔNG thành công (đọc lại ra rỗng).', label)
        return False
    _logger.info('Logo %s: %s byte.', label, len(base64.b64decode(written)))
    return True


def post_init_hook(env):
    with file_open(LOGO_PATH, 'rb') as fh:
        b64_logo = base64.b64encode(fh.read())

    company = env.ref('base.main_company', raise_if_not_found=False)
    if company:
        _set_logo(company, b64_logo, 'công ty')

    website = env.ref('website.default_website', raise_if_not_found=False)
    if not website:
        _logger.warning('Không có website mặc định — bỏ qua logo/ngôn ngữ website.')
        return

    _set_logo(website, b64_logo, 'website')

    lang = _install_vietnamese(env)
    if lang:
        # Website chỉ phục vụ tiếng Việt → ẩn luôn bộ chọn ngôn ngữ ở footer.
        website.write({
            'language_ids': [(6, 0, [lang.id])],
            'default_lang_id': lang.id,
        })
        _logger.info('Website dùng ngôn ngữ duy nhất: vi_VN.')
