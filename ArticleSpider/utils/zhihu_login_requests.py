# coding: utf-8

try:
    import http.cookiejar as cookielib
except:
    import cookielib
import re
import shutil
import time

import requests

from ArticleSpider.utils.zheye import zheye

# 初始化session及cookies
session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies.txt')

# load cookies
try:
    session.cookies.load(ignore_discard=True)
except:
    print('cookie未能加载')


# headers
headers = {
    'HOST': 'www.zhihu.com',
    'Referer': 'https://www.zhihu.com',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36'
}


def get_xsrf():
    """获取xsrf, 作为post提交 """
    response = session.get('https://www.zhihu.com', headers=headers)
    r = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)
    return r.group(1) if r else ''


def get_captcha_position():
    """获取图片验证码并返回倒立汉字的坐标"""

    random_num = str(int(time.time() * 1000))
    captcha_url = 'https://www.zhihu.com/captcha.gif?r={random_num}&type=login&lang=cn'.format(random_num=random_num)
    response = session.get(captcha_url, headers=headers, stream=True)
    # 成功返回
    if response.status_code == 200:
        with open('pic_captcha.gif', 'wb') as f:
            response.raw.decode_content = True
            # 将类文件对象保存为文件f
            shutil.copyfileobj(response.raw, f)

    # 使用'者也'进行验证码识别并返回坐标
    z = zheye()
    positions = z.Recognize('pic_captcha.gif')

    # 处理坐标，变为可以post的格式: [[y, x], [y, x]]
    p = [list(t) for t in positions]
    for i in range(len(p)):
        for j, num in enumerate(p[i]):
            # post回去的图片为200*44，因此坐标也裁剪一半
            num = num / 2
            # 保留4位小数
            p[i][j] = float('%.4f' % num)
        # y, x --> x, y
        p[i][0], p[i][1] = p[i][1], p[i][0]
    # 交换坐标顺序(将第一个倒立汉字坐标放在第一位), 比较p[0]与p[-1]可以避免只有一个倒立汉字的情况
    if p[0][0] > p[-1][0]:
        p.reverse()

    return str(p)


def zhihu_login(account, password):
    """知乎登录"""

    if re.match('^1\d{10}', account):
        print('手机号码登录')
        url = 'https://www.zhihu.com/login/phone_num'
        data = {
            '_xsrf': get_xsrf(),
            'phone_num': account,
            'password': password,
            'captcha': '{"img_size":[200, 44], "input_points":%s}' % get_captcha_position(),
            'captcha_type': 'cn'
        }
    elif '@' in account:
        print('邮箱登陆')
        url = 'https://www.zhihu.com/login/email'
        data = {
            '_xsrf': get_xsrf(),
            'email': account,
            'password': password,
            'captcha': '{"img_size":[200, 44], "input_points":%s}' % get_captcha_position(),
            'captcha_type': 'cn'
        }
    else:
        raise ValueError('Invalid account')

    r = session.post(url, data=data, headers=headers)

    session.cookies.save()


def is_login():
    """通过访问个人中心获取返回状态码来判断是否登陆"""

    res = session.get('https://www.zhihu.com/inbox', headers=headers, allow_redirects=False)
    return True if res.status_code == 200 else False


def index():
    """登录成功后通过cookie请求知乎首页"""

    if not is_login():
        zhihu_login('390999999@qq.com', 'Password')

    response = session.get('https://www.zhihu.com', headers=headers)
    with open('index_page.html', 'wb') as f:
        f.write(response.text.encode())
    print('OK')


if __name__ == '__main__':
    index()
