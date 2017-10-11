# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import re
from datetime import datetime

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join


def create_date_convert(value):
    try:
        create_date = datetime.strptime(value, '%Y/%m/%d').date()
    except ValueError:
        create_date = datetime.now().date()
    return create_date


def numbers_convert(value):
    # 获取数字的正则表达式
    p = '.*?(\d+).*'
    match = re.match(p, value)
    return int(match.group(1)) if match else 0


def tags_convert(value):
    if '评论' not in value:
        return value


class ArticleItemLoader(ItemLoader):
    """custom item loader"""
    default_output_processor = TakeFirst()


class JobboleArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field(input_processor=MapCompose(create_date_convert))
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    front_image_url = scrapy.Field(output_processor=lambda x: x)
    front_image_path = scrapy.Field()
    praise_nums = scrapy.Field(input_processor=MapCompose(numbers_convert))
    fav_nums = scrapy.Field(input_processor=MapCompose(numbers_convert))
    comment_nums = scrapy.Field(input_processor=MapCompose(numbers_convert))
    tags = scrapy.Field(input_processor=MapCompose(tags_convert),
                        output_processor=Join(', '))
    content = scrapy.Field()


class ZhihuQuestionItem(scrapy.Item):
    """知乎的问题 item"""

    zhihu_id = scrapy.Field()
    topics = scrapy.Field()
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    # 通过页面无法获取
    # create_time = scrapy.Field()
    # update_time = scrapy.Field()
    answer_num = scrapy.Field()
    comments_num = scrapy.Field()
    watch_user_num = scrapy.Field()
    click_num = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()


class ZhihuAnswerItem(scrapy.Item):
    """知乎的答案 item"""

    zhihu_id = scrapy.Field()
    url = scrapy.Field()
    question_id = scrapy.Field()
    author_id = scrapy.Field()
    content = scrapy.Field()
    praise_num = scrapy.Field()
    comments_num = scrapy.Field()
    create_time = scrapy.Field()
    update_time = scrapy.Field()
    crawl_time = scrapy.Field()
    crawl_update_time = scrapy.Field()
