"""Chụp toàn bộ 31 hình của User manual Employee.

    python shots_all.py             # chụp tất cả
    python shots_all.py fig-14 fig-15   # chụp lại vài hình

Mỗi hình bọc try/except: một hình hỏng không làm hỏng cả lượt, cuối lượt in
danh sách hình lỗi để chụp lại.
"""
import time
import traceback

from selenium.webdriver.common.by import By

from shots import (BASE, EMP, HR, close_all, driver_new, login, nav, btn,
                   shot, wanted, xp_click, scroll, scroll_in_modal, only)

FAILED = []


def step(key, fn):
    if not wanted(key):
        return
    try:
        fn()
    except Exception as e:                                   # noqa: BLE001
        FAILED.append(key)
        print('  !! %s — %s' % (key, e))
        traceback.print_exc(limit=1)


def search(d, text):
    """Gõ vào ô tìm kiếm ở topbar (lọc danh sách đang mở)."""
    box = d.find_element(By.CSS_SELECTOR, 'header.topbar input')
    box.clear()
    box.send_keys(text)
    time.sleep(1.6)


def open_row(d, n=1):
    xp_click(d, f'(//table//tbody/tr)[{n}]', wait=2.8)


def close_modal(d):
    close_all(d)


def drawer_tab(d, label):
    xp_click(d, f'//button[contains(@class,"tab") and '
                f'contains(normalize-space(.),"{label}")]', wait=2.0)


def open_emp(d, code):
    """Lọc theo mã rồi mở hồ sơ dòng đầu."""
    search(d, code)
    open_row(d)


def no_account_code(d):
    """Mã một NV chưa có tài khoản đăng nhập (để chụp form Tạo tài khoản)."""
    return d.execute_async_script("""
const done = arguments[arguments.length-1];
(async () => {
  const g = async (u) => (await fetch(u,{credentials:'same-origin'})).json();
  const emps = (await g('/hocba-hrm/api/employees')).employees;
  const accs = (await g('/hocba-hrm/api/accounts')).accounts;
  const has = new Set(accs.map(a => a.employeeId));
  const e = emps.find(x => !has.has(x.id) && x.code);
  done(e ? e.code : null);
})();""")


# ======================================================================
def run_hr(d):
    login(d, HR)

    # --- 1.4 mở module ---
    step('fig-01-workspace', lambda: shot(d, 'fig-01-workspace'))

    def _sidebar():
        d.set_window_size(1600, 1360)
        time.sleep(1.2)
        el = d.find_element(By.CSS_SELECTOR, 'aside.sidebar')
        el.screenshot(__import__('os').path.join(
            __import__('shots').IMG, 'fig-02-sidebar.png'))
        print('  shot fig-02-sidebar')
        d.set_window_size(1600, 1000)
        time.sleep(1.0)
    step('fig-02-sidebar', _sidebar)

    # --- 2.1 hồ sơ nhân viên ---
    def _emp_table():
        nav(d, 'Nhân viên')
        shot(d, 'fig-03-employees-table')
    step('fig-03-employees-table', _emp_table)

    def _emp_grid():
        nav(d, 'Nhân viên')
        btn(d, 'Thẻ')
        shot(d, 'fig-04-employees-grid')
        btn(d, 'Bảng')
    step('fig-04-employees-grid', _emp_grid)

    def _emp_form():
        nav(d, 'Nhân viên')
        btn(d, 'Thêm nhân viên', wait=2.4)
        shot(d, 'fig-05-employee-form')
        close_modal(d)
    step('fig-05-employee-form', _emp_form)

    def _drawer_info():
        nav(d, 'Nhân viên')
        open_emp(d, 'HB.04')
        shot(d, 'fig-06-drawer-info')
        close_modal(d)
    step('fig-06-drawer-info', _drawer_info)

    # --- 2.2 người phụ thuộc (HB.04 có 1 NPT) ---
    def _dependents():
        nav(d, 'Nhân viên')
        open_emp(d, 'HB.04')
        scroll_in_modal(d, 620)
        shot(d, 'fig-07-dependents')
        close_modal(d)
    step('fig-07-dependents', _dependents)

    def _dependent_form():
        nav(d, 'Nhân viên')
        open_emp(d, 'HB.04')
        scroll_in_modal(d, 620)
        btn(d, 'Thêm NPT', wait=2.0)
        shot(d, 'fig-08-dependent-form')
        close_modal(d)
        close_modal(d)
    step('fig-08-dependent-form', _dependent_form)

    # --- 2.3 chứng chỉ (HB.02 có 1 chứng chỉ) ---
    def _certs():
        nav(d, 'Nhân viên')
        open_emp(d, 'HB.02')
        scroll_in_modal(d, 900)
        shot(d, 'fig-09-certs')
        close_modal(d)
    step('fig-09-certs', _certs)

    def _cert_form():
        nav(d, 'Nhân viên')
        open_emp(d, 'HB.02')
        scroll_in_modal(d, 900)
        btn(d, 'Thêm chứng chỉ', wait=2.0)
        shot(d, 'fig-10-cert-form')
        close_modal(d)
        close_modal(d)
    step('fig-10-cert-form', _cert_form)

    # --- 2.4 tài sản (HB.01 có 1 tài sản) ---
    def _assets():
        nav(d, 'Nhân viên')
        open_emp(d, 'HB.01')
        drawer_tab(d, 'Tài sản')
        shot(d, 'fig-11-assets')
        close_modal(d)
    step('fig-11-assets', _assets)

    def _asset_form():
        nav(d, 'Nhân viên')
        open_emp(d, 'HB.01')
        drawer_tab(d, 'Tài sản')
        btn(d, 'Cấp phát', wait=2.0)
        shot(d, 'fig-12-asset-form')
        close_modal(d)
        close_modal(d)
    step('fig-12-asset-form', _asset_form)

    # --- 2.5 nhận việc ---
    step('fig-13-onboarding-list', lambda: (
        nav(d, 'Nhận việc'), shot(d, 'fig-13-onboarding-list')))

    def _steps():
        nav(d, 'Nhận việc')
        search(d, 'hà phi hùng')
        open_row(d)
        shot(d, 'fig-14-onboarding-steps')
        close_modal(d)
    step('fig-14-onboarding-steps', _steps)

    def _step_actions():
        nav(d, 'Nhận việc')
        search(d, 'hà phi hùng')
        open_row(d)
        scroll_in_modal(d, 900)
        shot(d, 'fig-15-step-actions')
        close_modal(d)
    step('fig-15-step-actions', _step_actions)

    def _tpl_picker():
        nav(d, 'Nhận việc')
        search(d, 'hà phi hùng')
        open_row(d)
        btn(d, 'Đổi quy trình', wait=2.6)
        shot(d, 'fig-16-template-picker')
        close_modal(d)
    step('fig-16-template-picker', _tpl_picker)

    # --- 2.6 cấu hình nhận việc ---
    step('fig-17-onb-config', lambda: (
        nav(d, 'Cấu hình nhận việc'), shot(d, 'fig-17-onb-config')))

    def _tpl_editor():
        nav(d, 'Cấu hình nhận việc')
        xp_click(d, '(//div[contains(@class,"card")][.//span]'
                    '[@draggable="true"])[1]', wait=2.4)
        shot(d, 'fig-18-onb-template-editor')
        close_modal(d)
    step('fig-18-onb-template-editor', _tpl_editor)

    # --- 2.7 thăng tiến (HB.01 có 2 mốc) ---
    def _promo():
        nav(d, 'Nhân viên')
        open_emp(d, 'HB.01')
        drawer_tab(d, 'Thăng tiến')
        time.sleep(2.0)
        shot(d, 'fig-19-promo-tab')
        close_modal(d)
    step('fig-19-promo-tab', _promo)

    # --- 2.8 lộ trình sự nghiệp (chọn NV một lần, cuộn chụp 3 hình) ---
    def _career():
        nav(d, 'Lộ trình sự nghiệp')
        box = d.find_element(
            By.XPATH, '//input[contains(@placeholder,"Tìm nhân viên theo")]')
        box.click()
        box.send_keys('HB.01')
        time.sleep(1.6)
        xp_click(d, '//div[@role="button"][contains(.,"HB.01")]', wait=3.6)
        for key, y in (('fig-20-career-top', 0),
                       ('fig-21-career-charts', 620),
                       ('fig-22-career-timeline', 1560)):
            if wanted(key):
                scroll(d, y)
                shot(d, key)
        scroll(d, 0)
    step('fig-20-career-top', _career)

    # --- 2.9 tài khoản ---
    step('fig-23-accounts', lambda: (
        nav(d, 'Tài khoản'), shot(d, 'fig-23-accounts')))

    def _account_form():
        nav(d, 'Nhân viên')
        code = no_account_code(d)
        if not code:
            raise RuntimeError('mọi NV đều đã có tài khoản')
        open_emp(d, code)
        drawer_tab(d, 'Tài khoản')
        btn(d, 'Tạo tài khoản', wait=2.0)
        shot(d, 'fig-24-account-form')
        close_modal(d)
        close_modal(d)
    step('fig-24-account-form', _account_form)

    # --- 2.10 phòng ban ---
    step('fig-25-departments', lambda: (
        nav(d, 'Phòng ban'), shot(d, 'fig-25-departments')))

    def _dept_form():
        nav(d, 'Phòng ban')
        xp_click(d, '(//table//tbody/tr//button[contains(.,"Sửa")])[1]',
                 wait=2.2)
        shot(d, 'fig-26-department-form')
        close_modal(d)
    step('fig-26-department-form', _dept_form)

    # --- 2.11 nghỉ việc (phía duyệt) ---
    step('fig-27-offboarding-managed', lambda: (
        nav(d, 'Nghỉ việc'), shot(d, 'fig-27-offboarding-managed')))


def run_emp(d):
    login(d, EMP)

    def _offb_form():
        nav(d, 'Nghỉ việc')
        btn(d, 'Nộp đơn nghỉ', wait=2.2)
        shot(d, 'fig-28-offboarding-form')
        close_modal(d)
    step('fig-28-offboarding-form', _offb_form)

    def _offb_mine():
        nav(d, 'Nghỉ việc')
        shot(d, 'fig-29-offboarding-mine')
    step('fig-29-offboarding-mine', _offb_mine)

    step('fig-30-profile', lambda: (
        nav(d, 'Hồ sơ của tôi'), shot(d, 'fig-30-profile')))

    def _profile_edit():
        nav(d, 'Hồ sơ của tôi')
        btn(d, 'Cập nhật thông tin', wait=2.2)
        shot(d, 'fig-31-profile-edit')
        close_modal(d)
    step('fig-31-profile-edit', _profile_edit)


HR_KEYS = tuple('fig-%02d' % i for i in range(1, 28))


def main():
    need_hr = not only or any(k.startswith(HR_KEYS) for k in only)
    need_emp = not only or any(k.startswith(('fig-28', 'fig-29', 'fig-30',
                                             'fig-31')) for k in only)
    d = driver_new()
    try:
        if need_hr:
            print('== HR Manager ==')
            run_hr(d)
        if need_emp:
            print('== Employee ==')
            run_emp(d)
    finally:
        d.quit()
    print('\nFAILED:', FAILED or 'none')


if __name__ == '__main__':
    main()
