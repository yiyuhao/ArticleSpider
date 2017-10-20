# -*- coding: utf-8 -*-
from datetime import datetime

from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from tools.xici_ip_poll import XiciProxyIpPool
from ArticleSpider.utils.selenium_login_lagou import get_cookies
from ArticleSpider.utils.common import md5
from ArticleSpider.items import LagouJobItem, LagouJobItemLoader


class LagouSpider(CrawlSpider):

    def __init__(self):
        super(LagouSpider, self).__init__()
        # 代理ip池，在download middleware中随机获取ip
        self.ip_pool = XiciProxyIpPool()

    name = 'lagou'
    allowed_domains = ['www.lagou.com']
    start_urls = ['https://www.lagou.com/']

    # 覆盖默认配置
    custom_settings = {'DOWNLOADER_MIDDLEWARES': {
        'ArticleSpider.middlewares.RandomUserAgentMiddleware': 543,
        # 'ArticleSpider.middlewares.RandomProxyMiddleware': 544,
        'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    }}

    rules = (
        Rule(LinkExtractor(allow=r'zhaopin/.*'), follow=True),
        Rule(LinkExtractor(allow=r'gongsi/j\d+.html'), follow=True),
        Rule(LinkExtractor(allow=r'jobs/\d+.html'), callback='parse_job', follow=True),
    )

    # def parse_start_url(self, response):
    #     return []
    #
    # def process_results(self, response, results):
    #     return results

    def start_requests(self):
        """重写， 传入selenium获取到的cookie"""
        cookies = get_cookies()
        for url in self.start_urls:
            yield Request(url, dont_filter=True, cookies=cookies)

    def parse_job(self, response):
        """解析拉勾网的职位"""
        item_loader = LagouJobItemLoader(item=LagouJobItem(), response=response)
        item_loader.add_css("title", ".job-name::attr(title)")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", md5(response.url))
        item_loader.add_css("salary", ".job_request .salary::text")
        item_loader.add_xpath("job_city", "//*[@class='job_request']/p/span[2]/text()")
        item_loader.add_xpath("work_years", "//*[@class='job_request']/p/span[3]/text()")
        item_loader.add_xpath("degree_need", "//*[@class='job_request']/p/span[4]/text()")
        item_loader.add_xpath("job_type", "//*[@class='job_request']/p/span[5]/text()")

        item_loader.add_css("tags", '.position-label li::text')
        item_loader.add_css("publish_time", ".publish_time::text")
        item_loader.add_css("job_advantage", ".job-advantage p::text")
        item_loader.add_css("job_desc", ".job_bt div")
        item_loader.add_css("job_addr", ".work_addr")
        item_loader.add_css("company_name", "#job_company dt a img::attr(alt)")
        item_loader.add_css("company_url", "#job_company dt a::attr(href)")
        item_loader.add_value("crawl_time", datetime.now())

        job_item = item_loader.load_item()

        return job_item
