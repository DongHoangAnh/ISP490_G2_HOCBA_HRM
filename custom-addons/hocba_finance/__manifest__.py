{
    'name': 'Học Bá — Tài chính (Quản lý dòng tiền)',
    'version': '19.0.1.0.0',
    'category': 'Accounting/Finance',
    'summary': 'Sổ quản lý dòng tiền độc lập: phiếu thu/chi, quỹ theo phòng ban, báo cáo Thu−Chi',
    'description': """
Module quản lý dòng tiền (cash-flow ledger) cho Học Bá Education.
- Phiếu thu / phiếu chi với quy trình Nháp → Duyệt → Ghi sổ.
- Quỹ tiền theo phòng ban; số dư cập nhật khi ghi sổ.
- Danh mục mục thu/chi; chiều phân tích theo phòng ban.
- Nạp thu qua nhập tay hoặc API/JSON (idempotent theo external_ref).
- Báo cáo Thu − Chi = Lãi/Lỗ, theo thời gian / phòng ban / mục / số dư quỹ.
Thuần cash basis, độc lập các module khác. Xem docs/superpowers/specs/2026-07-11-finance-cashflow.md.
""",
    'author': 'Học Bá / ISP490_G2',
    'license': 'LGPL-3',
    'depends': ['base', 'hr', 'mail'],
    'data': [
        'security/finance_security.xml',
        'security/ir.model.access.csv',
        'security/finance_rules.xml',
        'data/ir_sequence_data.xml',
        'data/fin_category_data.xml',
        'views/fund_views.xml',
        'views/fin_category_views.xml',
        'views/fin_voucher_views.xml',
        'views/fin_report_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': True,
}
