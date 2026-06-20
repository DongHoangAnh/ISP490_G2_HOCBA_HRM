from odoo import models, fields


class HbFormulaHelpWizard(models.TransientModel):
    _name = 'hb.formula.help.wizard'
    _description = 'Hướng dẫn hàm công thức'

    info = fields.Html(string='Thông tin', default='', readonly=True)

    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res['info'] = self._build_help_html()
        return res

    @staticmethod
    def _build_help_html():
        rows = [
            ('Mã rule',
             'Ghi trực tiếp mã slug của rule để lấy giá trị đã tính.',
             '<code>luong_thoi_gian * 0.08</code>'),
            ('IF(điều_kiện, đúng, sai)',
             'Nếu điều kiện đúng trả về giá trị đúng, ngược lại trả về giá trị sai.',
             '<code>IF(tong_thu_nhap > 0, tong_thu_nhap - khau_tru_nv, 0)</code>'),
            ('SUM(a, b)',
             'Cộng tất cả các rule từ mã <b>a</b> đến mã <b>b</b> theo thứ tự sequence (bao gồm cả a và b).',
             '<code>SUM(luong_thoi_gian, thuong_khac)</code>'),
            ('MAX(a, b)',
             'Trả về giá trị lớn nhất trong các tham số.',
             '<code>MAX(tong_thu_nhap - khau_tru_nv, 0)</code>'),
            ('MIN(a, b)',
             'Trả về giá trị nhỏ nhất trong các tham số.',
             '<code>MIN(luong_thoi_gian, 5000000)</code>'),
            ('ABS(x)',
             'Trả về giá trị tuyệt đối (bỏ dấu âm).',
             '<code>ABS(bhxh_8_nv)</code>'),
            ('ROUND(x, y)',
             'Làm tròn số. y = 1: làm tròn lên, y = 0: làm tròn xuống.',
             '<code>ROUND(luong_thoi_gian * 0.08, 1)</code>'),
        ]

        html = '<table class="table table-sm table-bordered">'
        html += '<thead class="table-light"><tr>'
        html += '<th style="width:30%">Hàm</th>'
        html += '<th style="width:40%">Mô tả</th>'
        html += '<th style="width:30%">Ví dụ</th>'
        html += '</tr></thead><tbody>'
        for name, desc, example in rows:
            html += f'<tr><td><b>{name}</b></td><td>{desc}</td><td>{example}</td></tr>'
        html += '</tbody></table>'

        html += '<div class="mt-2 text-muted small">'
        html += 'Toán tử hỗ trợ: <code>+ - * / > &lt; >= &lt;= == !=</code>'
        html += '</div>'

        return html
