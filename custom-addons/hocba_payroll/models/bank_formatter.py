"""
Bank file formatters — Strategy Pattern.
FUNC-PR-003: Mỗi ngân hàng là 1 concrete strategy.

    Usage:
        formatter = BankFormatterRegistry.get('VCB')
        rows = formatter.build_rows(payslips, description_tpl)
        file_bytes = formatter.export_xlsx(rows)
"""
import io
import logging
import re
import unicodedata

from odoo import _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

try:
    import openpyxl
    from openpyxl.styles import Font, Alignment, numbers
except ImportError:
    openpyxl = None
    _logger.warning('openpyxl not installed — bank file export will fail.')


# ── Helpers ──────────────────────────────────────────────────
def _remove_diacritics(text):
    """Remove Vietnamese diacritics: Nguyễn → Nguyen."""
    if not text:
        return ''
    nfkd = unicodedata.normalize('NFKD', text)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))


def _to_uppercase_no_diacritics(text):
    """NGUYEN VAN A — required by VCB."""
    return _remove_diacritics(text).upper()


# ═════════════════════════════════════════════════════════════
# Abstract base (Strategy interface)
# ═════════════════════════════════════════════════════════════
class BaseBankFormatter:
    """Base class for all bank formatters."""

    code = ''           # e.g. 'VCB'
    name = ''           # e.g. 'Vietcombank'
    headers = []        # list[str] — column headers

    def validate_account(self, acc_number, regex=None):
        """Validate account number format."""
        if not acc_number:
            return False
        if regex and not re.match(regex, acc_number.strip()):
            return False
        return True

    def build_row(self, stt, acc_number, emp_name, amount, description, **kw):
        """Build a single data row — override per bank."""
        raise NotImplementedError

    def build_rows(self, payslips, description_tpl, account_regex=None):
        """Build all rows from a set of payslips.

        Returns:
            (list[dict], list[str])  — rows, warnings
        """
        rows = []
        warnings = []
        stt = 1
        for slip in payslips:
            net = self._get_net_amount(slip)
            if net <= 0:
                warnings.append(
                    _('Payslip %(ref)s có Net = 0 hoặc âm — đã bỏ qua.',
                      ref=slip.number or slip.name)
                )
                continue

            bank_account = self._get_employee_bank(slip.employee_id)
            if not bank_account or not bank_account.acc_number:
                continue  # already validated in wizard

            acc_number = bank_account.acc_number.strip()
            emp_name = slip.employee_id.name or ''
            emp_code = getattr(slip.employee_id, 'x_employee_code', '') or ''
            month = slip.date_to.strftime('%m') if slip.date_to else ''
            year = slip.date_to.strftime('%Y') if slip.date_to else ''

            desc = (description_tpl or 'Luong T{month}/{year}').format(
                month=month, year=year, employee_code=emp_code,
            )

            row = self.build_row(
                stt=stt,
                acc_number=acc_number,
                emp_name=emp_name,
                amount=int(net),
                description=desc,
                employee_code=emp_code,
            )
            rows.append(row)
            stt += 1

        return rows, warnings

    def export_xlsx(self, rows):
        """Generate XLSX bytes from rows."""
        if openpyxl is None:
            raise ValidationError(_('Thư viện openpyxl chưa được cài đặt.'))

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = self.code

        # Header row
        header_font = Font(bold=True)
        for col_idx, header in enumerate(self.headers, start=1):
            cell = ws.cell(row=1, column=col_idx, value=header)
            cell.font = header_font

        # Data rows
        for row_idx, row_data in enumerate(rows, start=2):
            for col_idx, key in enumerate(self._column_keys(), start=1):
                val = row_data.get(key, '')
                cell = ws.cell(row=row_idx, column=col_idx, value=val)
                if isinstance(val, (int, float)):
                    cell.number_format = '#,##0'
                    cell.alignment = Alignment(horizontal='right')

        # Auto-width
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 3, 40)

        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def _column_keys(self):
        """Return ordered keys matching self.headers."""
        raise NotImplementedError

    @staticmethod
    def _get_net_amount(payslip):
        """Read NET amount from payslip lines."""
        net_line = payslip.line_ids.filtered(lambda l: l.code == 'NET')
        return net_line[0].amount if net_line else 0.0

    @staticmethod
    def _get_employee_bank(employee):
        """Get employee bank account — compatible with Community (no bank_account_id)."""
        if hasattr(employee, 'bank_account_id') and employee.bank_account_id:
            return employee.bank_account_id
        partner = employee.address_home_id or employee.work_contact_id
        if partner and partner.bank_ids:
            return partner.bank_ids[0]
        return None


# ═════════════════════════════════════════════════════════════
# Concrete: Vietcombank (VCB)
# ═════════════════════════════════════════════════════════════
class VCBFormatter(BaseBankFormatter):
    code = 'VCB'
    name = 'Vietcombank'
    headers = ['STT', 'Số tài khoản', 'Tên người nhận', 'Số tiền', 'Nội dung']

    def build_row(self, stt, acc_number, emp_name, amount, description, **kw):
        return {
            'stt': stt,
            'acc_number': acc_number,
            'emp_name': _to_uppercase_no_diacritics(emp_name),   # BR-PR-015
            'amount': amount,
            'description': description,
        }

    def _column_keys(self):
        return ['stt', 'acc_number', 'emp_name', 'amount', 'description']


# ═════════════════════════════════════════════════════════════
# Concrete: Techcombank (TCB)
# ═════════════════════════════════════════════════════════════
class TCBFormatter(BaseBankFormatter):
    code = 'TCB'
    name = 'Techcombank'
    headers = ['Account Number', 'Beneficiary Name', 'Amount', 'Currency', 'Remark', 'Bank Code']

    def build_row(self, stt, acc_number, emp_name, amount, description, **kw):
        return {
            'acc_number': acc_number,
            'emp_name': emp_name.upper(),    # BR-PR-016: giữ dấu TV, viết hoa
            'amount': amount,
            'currency': 'VND',
            'description': description[:100],  # VR-009: max 100 chars
            'bank_code': '',
        }

    def _column_keys(self):
        return ['acc_number', 'emp_name', 'amount', 'currency', 'description', 'bank_code']


# ═════════════════════════════════════════════════════════════
# Registry (simple factory)
# ═════════════════════════════════════════════════════════════
class BankFormatterRegistry:
    """Registry for bank formatter strategies."""

    _formatters = {
        'VCB': VCBFormatter,
        'TCB': TCBFormatter,
    }

    @classmethod
    def get(cls, code):
        """Return an instance of the formatter for the given bank code."""
        formatter_cls = cls._formatters.get(code)
        if not formatter_cls:
            raise ValidationError(
                _('Không tìm thấy formatter cho ngân hàng "%(code)s".', code=code)
            )
        return formatter_cls()

    @classmethod
    def register(cls, code, formatter_cls):
        """Register a new formatter (for extensibility)."""
        cls._formatters[code] = formatter_cls

    @classmethod
    def available_codes(cls):
        return list(cls._formatters.keys())
