{
    'name': 'Đánh giá nhân viên Học Bá',
    'version': '19.0.1.0.0',
    'author': 'Học Bá Education',
    'license': 'LGPL-3',
    'category': 'Human Resources/Appraisal',
    'summary': 'Đánh giá định kỳ giảng viên & nhân viên văn phòng — tiêu chí có '
               'trọng số, chỉ số tự động từ chấm công/chứng chỉ, xếp loại A/B/C/D',
    'description': '''
        Đánh giá nhân viên định kỳ (quý / nửa năm / năm) cho Học Bá Education.
        - 2 bộ tiêu chí tách theo nhóm: Giảng viên và Nhân viên văn phòng
        - Chấm thang 5 mức có trọng số, tổng điểm quy về thang 100, xếp loại A/B/C/D
        - Tự động chấm 4 chỉ số từ dữ liệu vận hành: chuyên cần buổi dạy/ngày công,
          khối lượng giảng dạy, chuẩn chứng chỉ
        - Luồng Nháp -> Đã chốt -> Đã công bố, thông báo cho nhân viên khi công bố
        Spec: docs/superpowers/specs/2026-07-26-performance-review-design.md
        Công thức: docs/CONG_THUC_DANH_GIA.md
    ''',
    'depends': [
        'hr_holidays',
        'hocba_employees',
        'hocba_attendance',
        'hocba_notify',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/hb_review_criteria_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
