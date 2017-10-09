# -*- coding: utf-8 -*-
from urllib import parse

import scrapy
from scrapy.http import Request
from ArticleSpider.items import JobboleArticleItem, ArticleItemLoader
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

        # 通过item loader加载item
        item_loader = ArticleItemLoader(item=JobboleArticleItem(), response=response)
        item_loader.add_css('title', '.entry-header h1::text')
        item_loader.add_css('create_date', '.entry-meta-hide-on-mobile::text')
        item_loader.add_value('url', response.url)
        item_loader.add_value('url_object_id', md5(response.url))
        item_loader.add_value('front_image_url', [response.meta.get('front_image_url', '')])
        item_loader.add_css('praise_nums', 'span.vote-post-up h10::text')
        item_loader.add_css('fav_nums', 'span.bookmark-btn::text')
        item_loader.add_css('comment_nums', 'a[href="#article-comment"] span::text')
        item_loader.add_css('tags', 'p.entry-meta-hide-on-mobile a::text')
        item_loader.add_css('content', 'div.entry')
        item = item_loader.load_item()

        yield item
