"""Chụp ảnh minh hoạ cho User manual module Employee bằng Selenium.

    python shots.py            # chụp tất cả
    python shots.py fig-03 fig-14   # chụp lại vài hình

Ảnh ra `img/<key>.png`, đúng key mà build.py gọi. App phải đang chạy —
stack Neon: docker compose -f docker-compose.yml -f docker-compose.onl.yml up -d odoo
(→ http://localhost:8070). Tài khoản test: xem docs/DB_TEST_DATA.md.
"""
import os
import sys
import time

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, 'img')
BASE = os.environ.get('HB_BASE', 'http://localhost:8070')
PWD = 'Hocba@2026'
HR = 'test_hrmanager@hocba.vn'
EMP = 'test_employee@hocba.vn'
SIZE = (1600, 1000)

only = set(sys.argv[1:])


def wanted(key):
    return not only or any(key.startswith(p) for p in only)


def driver_new():
    o = Options()
    o.add_argument('--window-size=%d,%d' % SIZE)
    o.add_argument('--hide-scrollbars')
    o.add_argument('--force-device-scale-factor=1')
    o.add_argument('--disable-blink-features=AutomationControlled')
    d = webdriver.Chrome(options=o)
    d.set_window_size(*SIZE)
    return d


def login(d, user):
    d.get(BASE + '/web/session/logout')
    time.sleep(1)
    d.get(BASE + '/web/login')
    time.sleep(2)
    d.find_element(By.ID, 'login').clear()
    d.find_element(By.ID, 'login').send_keys(user)
    pw = d.find_element(By.ID, 'password')
    pw.clear()
    pw.send_keys(PWD)
    pw.send_keys(Keys.ENTER)
    time.sleep(4)
    d.get(BASE + '/hocba-hrm')
    time.sleep(5)


def xp_click(d, xpath, wait=1.6):
    els = [e for e in d.find_elements(By.XPATH, xpath) if e.is_displayed()]
    if not els:
        raise RuntimeError('not found: ' + xpath)
    d.execute_script('arguments[0].scrollIntoView({block:"center"});', els[0])
    time.sleep(0.25)
    els[0].click()
    time.sleep(wait)
    return els[0]


def close_all(d):
    """Đóng mọi modal đang mở (Modal.jsx đóng bằng phím Escape)."""
    for _ in range(4):
        if not d.find_elements(By.CSS_SELECTOR, '.overlay'):
            return
        d.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
        time.sleep(0.8)
    # vẫn kẹt → nạp lại SPA cho sạch
    d.get(BASE + '/hocba-hrm')
    time.sleep(5)


def nav(d, label):
    """Bấm mục sidebar theo nhãn (nhãn có thể kèm badge số việc cần xử lý)."""
    close_all(d)
    xp_click(d, f'//nav//button[starts-with(normalize-space(.),"{label}")]',
             wait=2.8)


def btn(d, label, wait=1.6):
    xp_click(d, f'//button[contains(normalize-space(.),"{label}")]', wait)


def shot(d, key):
    os.makedirs(IMG, exist_ok=True)
    path = os.path.join(IMG, key + '.png')
    d.save_screenshot(path)
    print('  shot', key)


def scroll(d, y):
    d.execute_script(f'window.scrollTo(0,{y});')
    time.sleep(0.6)


def scroll_in_modal(d, y):
    d.execute_script(
        'const m=[...document.querySelectorAll("div")].filter('
        'e=>e.scrollHeight>e.clientHeight+40 && e.clientHeight>200);'
        'if(m.length) m[m.length-1].scrollTop=arguments[0];', y)
    time.sleep(0.6)


def esc(d):
    d.find_element(By.TAG_NAME, 'body').send_keys('')
    time.sleep(1)


def row_click(d, n=1):
    """Mở dòng thứ n của bảng đầu tiên trên màn."""
    xp_click(d, f'(//table//tbody/tr)[{n}]', wait=2.6)
