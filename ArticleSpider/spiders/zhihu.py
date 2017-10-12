# -*- coding: utf-8 -*-

import json
import re
from datetime import datetime
from urllib import parse

import scrapy

from ArticleSpider.items import ZhihuAnswerItem, ZhihuQuestionItem
from ArticleSpider.items import ArticleItemLoader
from ArticleSpider.utils.zheye import zheye


class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    allowed_domains = ['www.zhihu.com']
    start_urls = ['http://www.zhihu.com/']

    # question的第一页answer url
    start_answer_url = 'https://www.zhihu.com/api/v4/questions/{question_id}/answers' \
                       '?sort_by=default&include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2' \
                       'Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2' \
                       'Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2' \
                       'Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2' \
                       'Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2' \
                       'Creview_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2' \
                       'Cvoting%2Cis_thanked%2Cis_nothelp%2Cupvoted_followees%3Bdata%5B%2A%5D.mark_infos' \
                       '%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%3F%28type%3D' \
                       'best_answerer%29%5D.topics&limit={limit}&offset={offset}'

    headers = {
        'HOST': 'www.zhihu.com',
        'Referer': 'https://www.zhihu.com',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.104 Safari/537.36'
    }

    def parse(self, response):
        """
            extract and track all urls
            如果url格式为/question/xxx 就下载后直接进入解析函数
        """
        all_urls = response.css('a::attr(href)').extract()
        all_urls = [parse.urljoin(response.url, url) for url in all_urls]

        # 过滤掉<a href='javascript:'>等
        all_urls = filter(lambda x: True if x.startswith('https') else False, all_urls)

        # 提取question_url及question_id
        patt = re.compile('(.*zhihu\.com/question/(\d+))(/|$).*')
        for url in all_urls:
            r = patt.match(url)
            if r:
                # 如果提取到question页面
                request_url = r.group(1)
                question_id = r.group(2)

                yield scrapy.Request(request_url, meta={'question_id': question_id}, headers=self.headers,
                                     callback=self.parse_question)
            else:
                # 不是question页面则进一步跟踪
                yield scrapy.Request(url, headers=self.headers)

    def parse_question(self, response):
        """
            extract item from question url: like
            https://www.zhihu.com/question/66461942
        """

        if "QuestionHeader-title" in response.text:
            # 处理新版本
            # question_item_loader
            question_id = int(response.meta.get('question_id'))
            il = ArticleItemLoader(item=ZhihuQuestionItem(), response=response)
            il.add_value('zhihu_id', question_id)
            il.add_css('topics', 'div.QuestionHeader-topics .Popover div::text')
            il.add_value('url', response.url)
            il.add_css('title', 'h1.QuestionHeader-title::text')
            il.add_css('content', 'div.QuestionHeader-detail div div span')
            # il.add_css('create_time', '')
            # il.add_css('update_time', '')
            il.add_css('answer_num', '.List-headerText span::text')
            il.add_css('comments_num', '.QuestionHeader-Comment button::text')
            il.add_css('watch_user_num', '.NumberBoard-value::text')
            il.add_css('click_num', '.NumberBoard-value::text')
            il.add_value('crawl_time', datetime.now().date())
            # il.add_css('crawl_update_time', '')

            item = il.load_item()

            yield scrapy.Request(self.start_answer_url.format(question_id=question_id, limit=20, offset=0),
                                 headers=self.headers,
                                 callback=self.parse_answer)
            yield item
        else:
            # 处理旧版本
            print('有旧版本页面: %s' % response.url)

    def parse_answer(self, response):
        """extract item from answer"""

        ans_json = json.loads(response.text)
        is_end = ans_json['paging']['is_end']
        next_url = ans_json['paging']['next']

        # 提取answer具体信息
        for answer in ans_json['data']:
            answer_item = ZhihuAnswerItem()
            answer_item['zhihu_id'] = answer['id']
            answer_item['url'] = answer['url']
            answer_item['question_id'] = answer['question']['id']
            answer_item['author_id'] = answer['author']['id'] if 'id' in answer['author'] else None
            answer_item['content'] = answer['content'] if 'content' in answer else None
            answer_item['praise_num'] = answer['voteup_count']
            answer_item['comments_num'] = answer['comment_count']
            # 将str格式timestamp转换为datetime
            answer_item['create_time'] = datetime.fromtimestamp(float(answer['created_time']))
            answer_item['update_time'] = datetime.fromtimestamp(float(answer['updated_time']))
            answer_item['crawl_time'] = datetime.now()

            yield answer_item

        # 跟踪下一页评论
        if not is_end:
            yield scrapy.Request(next_url, headers=self.headers, callback=self.parse_answer)

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
        else:
            raise AssertionError()
