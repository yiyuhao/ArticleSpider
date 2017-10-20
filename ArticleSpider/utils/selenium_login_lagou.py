# coding: utf-8
#
# 当前文件夹下需放入驱动文件: chromedriver.exe
#

import os
from time import sleep

from selenium import webdriver


def get_cookies():
    """登录拉勾并返回登录后的cookie"""
    # 启动selenium
    this_dir = os.path.abspath(os.path.dirname(__file__))
    browser = webdriver.Chrome(os.path.join(this_dir, 'chromedriver.exe'))
    # 登录
    browser.get('https://passport.lagou.com/login/login.html')
    browser.find_element_by_css_selector('div.left_area div.form_body form input[type=text]').send_keys('13880992332')
    browser.find_element_by_css_selector('div.left_area div.form_body form input[type=password]').send_keys('Popkart88')
    browser.find_element_by_css_selector('div.left_area div.form_body form input[type=submit]').click()
    sleep(5)
    # get cookies
    cookies = browser.get_cookies()
    browser.close()
    return cookies
