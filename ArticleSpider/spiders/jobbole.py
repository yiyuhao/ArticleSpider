# -*- coding: utf-8 -*-
import re
from datetime import datetime
from urllib import parse

import scrapy
from ArticleSpider.items import JobboleArticleItem
from scrapy.http import Request
from ArticleSpider.utils.common import md5


class JobboleSpider(scrapy.Spider):
    name = 'jobbole'
    allowed_domains = ['blog.jobbole.com']
    start_urls = ['http://blog.jobbole.com/all-posts/']

    def parse(self, response):
        """
        1、获取文章列表页中的文章url并进行解析
        2、获取下一页的url并交给downloader进行下载
        :param response:
        :return:
        """
        # 获取列表页中所有文章url
        post_nodes = response.css('#archive .floated-thumb .post-thumb a')
        for node in post_nodes:
            img_url = node.css('img::attr(src)').extract_first('')
            url = node.css('::attr(href)').extract_first('')
            yield Request(url=parse.urljoin(response.url, url), meta={'front_image_url': img_url}, callback=self.extract_article)

        # 获取下一页的url
        next_page_url = response.css('.next.page-numbers::attr(href)').extract_first('')
        if next_page_url:
            yield Request(url=parse.urljoin(response.url, next_page_url), callback=self.parse)

    def extract_article(self, response):
        """提取文章具体字段(标题 日期 内容等)"""

        item = JobboleArticleItem()

        # 获取数字的正则表达式
        pattern_get_int = '.*?(\d+).*'

        # ##########通过xpath提取########## #

        # # 文章标题
        # title = title = response.xpath('//div[@class="entry-header"]/h1/text()').extract_first('')
        # # 发表日期(2000-01-01)
        # create_date = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/text()').extract_first('').replace('·',
        #                                                                                                   '').strip()
        # # 点赞数
        # praise_nums = int(response.xpath('//span[contains(@class, "vote-post-up")]/h10/text()').extract_first(''))
        # # 收藏数
        # fav_nums = response.xpath('//span[contains(@class, "bookmark-btn")]/text()').extract_first('')
        # match = re.match(pattern_get_int, fav_nums)
        # fav_nums = int(match.group(1)) if match else 0
        # # 评论数
        # comment_nums = response.xpath(
        #     '//a[@href="#article-comment"]//span[contains(@class, "btn-bluet-bigger")]/text()').extract_first('')
        # match = re.match(pattern_get_int, comment_nums)
        # comment_nums = int(match.group(1)) if match else 0
        # # 正文内容
        # content = response.xpath('//div[@class="entry"]').extract_first('')
        # # 标签   (list)   ['职场', '面试']
        # tags = response.xpath('//p[@class="entry-meta-hide-on-mobile"]/a/text()').extract()
        # tags = [t for t in tags if '评论' not in t]

        # ##########通过CSS选择器提取########## #

        # 封面图
        front_image_url = response.meta.get('front_image_url', '')

        # 题目
        title = response.css('.entry-header h1::text').extract_first('')

        # 发表日期(2000-01-01)
        create_date = response.css('.entry-meta-hide-on-mobile::text').extract_first('').replace('·', '').strip()

        # 点赞数
        praise_nums = int(response.css('span.vote-post-up h10::text').extract_first(''))

        # 收藏数
        fav_nums = response.css('span.bookmark-btn::text').extract_first('')
        match = re.match(pattern_get_int, fav_nums)
        fav_nums = int(match.group(1)) if match else 0

        # 评论数
        comment_nums = response.css('a[href="#article-comment"] span::text').extract_first('')
        match = re.match(pattern_get_int, comment_nums)
        comment_nums = int(match.group(1)) if match else 0

        # 正文内容
        content = response.css('div.entry').extract_first('')

        # tags  (list)   ['职场', '面试']
        tags = response.css('p.entry-meta-hide-on-mobile a::text').extract()
        tags = ', '.join([t for t in tags if '评论' not in t])

        # 传入item
        item['url'] = response.url
        item['url_object_id'] = md5(response.url)
        item['front_image_url'] = [front_image_url]
        # 在pipelines中处理image path
        # item['front_image_path'] = front_image_path
        item['title'] = title
        try:
            create_date = datetime.strptime(create_date, '%Y/%m/%d').date()
        except ValueError:
            create_date = datetime.now().date()
        item['create_date'] = create_date
        item['praise_nums'] = praise_nums
        item['fav_nums'] = fav_nums
        item['comment_nums'] = comment_nums
        item['content'] = content
        item['tags'] = tags
        yield item
