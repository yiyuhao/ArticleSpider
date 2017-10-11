# -*- coding: utf-8 -*-

import json
import re

import scrapy

from ArticleSpider.utils.zheye import zheye


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    headers = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36'
    }

    def parse(self, response):
        pass

    def parse_detail(self, response):
        pass

    def start_requests(self):
        """访问登陆页面，以获取xsrf"""
        return [scrapy.Request('https://www.zhihu.com/#signin', headers=self.headers, callback=self.login)]

    def login(self, response):
        """访问登录页面拿到xsrf，再请求验证码"""
        # regex获取xsrf
        r = re.match('.*name="_xsrf" value="(.*?)"', response.text, re.DOTALL)
        assert r, "The xsrf doesn't exist in zhihu login page. Check whether the response is valid."
        xsrf = r.group(1)

        import time
        random_num = str(int(time.time() * 1000))
        captcha_url = 'https://www.zhihu.com/captcha.gif?r={random_num}&type=login&lang=cn'.format(
            random_num=random_num)
        yield scrapy.Request(captcha_url, headers=self.headers, meta={'xsrf': xsrf},
                             callback=self.login_after_captcha)

    def login_after_captcha(self, response):
        """请求到验证码后，再进行识别，最终提交登陆post请求"""
        with open('captcha.jpg', 'wb') as f:
            f.write(response.body)
            f.close()

        # 使用'者也'进行验证码识别并返回坐标
        z = zheye()
        positions = z.Recognize('captcha.jpg')

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

        # 提交登录表单
        url = 'https://www.zhihu.com/login/phone_num'
        data = {
            '_xsrf': response.meta['xsrf'],
            'phone_num': '13880992332',
            'password': 'Popkart88',
            'captcha': '{"img_size":[200, 44], "input_points":%s}' % str(p),
            'captcha_type': 'cn'
        }

        yield scrapy.FormRequest(url=url, formdata=data, headers=self.headers, callback=self.check_login)

    def check_login(self, response):

        """验证服务器的返回数据判断是否登陆成功"""
        text_json = json.loads(response.text)
        if text_json.get('msg') == '登录成功':
            for url in self.start_urls:
                yield scrapy.Request(url, headers=self.headers, dont_filter=True)
