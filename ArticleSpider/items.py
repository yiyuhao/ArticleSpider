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

    @property
    def sql(self):
        insert_sql = """
            INSERT INTO jobbole_article(title, create_date, url, url_object_id, front_image_url, front_image_path,
                                        comment_nums, fav_nums, praise_nums, tags, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        params = (self['title'], self['create_date'], self['url'], self['url_object_id'],
                  self['front_image_url'], self['front_image_path'], self['comment_nums'],
                  self['fav_nums'], self['praise_nums'], self['tags'], self['content'])

        return insert_sql, params


class ZhihuQuestionItem(scrapy.Item):
    """知乎的问题 item"""

    zhihu_id = scrapy.Field()
    topics = scrapy.Field(output_processor=Join(', '))
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    # 通过页面无法获取
    # create_time = scrapy.Field()
    # update_time = scrapy.Field()
    answer_num = scrapy.Field(input_processor=MapCompose(numbers_convert))
    comments_num = scrapy.Field(input_processor=MapCompose(numbers_convert))
    watch_user_num = scrapy.Field(output_processor=lambda x: int(x[0]))
    click_num = scrapy.Field(output_processor=lambda x: int(x[1]))
    crawl_time = scrapy.Field()

    # crawl_update_time = scrapy.Field()

    @property
    def sql(self):
        insert_sql = """
                INSERT INTO zhihu_question(zhihu_id, topics, url, title, content, answer_num, comments_num,
                                           watch_user_num, click_num, crawl_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""

        params = (self['zhihu_id'], self['topics'], self['url'], self['title'],
                  self['content'], self['answer_num'], self['comments_num'],
                  self['watch_user_num'], self['click_num'], self['crawl_time'])

        return insert_sql, params


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

    # crawl_update_time = scrapy.Field()

    @property
    def sql(self):
        insert_sql = """
                    INSERT INTO zhihu_answer(zhihu_id, url, question_id, author_id, content, praise_num, 
                                             comments_num, create_time, update_time, crawl_time)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE content=VALUES(content), comments_num=VALUES(comments_num), 
                                            praise_num=VALUES(praise_num), content=VALUES(update_time)
                    """

        params = (self['zhihu_id'], self['url'], self['question_id'], self['author_id'],
                  self['content'], self['praise_num'], self['comments_num'],
                  self['create_time'], self['update_time'], self['crawl_time'])

        return insert_sql, params


def remove_splash(value):
    """去掉工作城市的斜线"""

    return value.replace("/", "")


def handle_jobaddr(value):
    addr_list = value.split("\n")
    addr_list = [item.strip() for item in addr_list if item.strip() != "查看地图"]
    return "".join(addr_list)


class LagouJobItemLoader(ItemLoader):
    """自定义item loader"""

    default_output_processor = TakeFirst()


class LagouJobItem(scrapy.Item):
    """拉勾网职位信息"""

    title = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    salary = scrapy.Field()
    job_city = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    work_years = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    degree_need = scrapy.Field(
        input_processor=MapCompose(remove_splash),
    )
    job_type = scrapy.Field()
    publish_time = scrapy.Field()
    job_advantage = scrapy.Field()
    job_desc = scrapy.Field()
    job_addr = scrapy.Field(
        input_processor=MapCompose(handle_jobaddr),
    )
    company_name = scrapy.Field()
    company_url = scrapy.Field()
    tags = scrapy.Field(
        input_processor=Join(",")
    )
    crawl_time = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into lagou_job(title, url, url_object_id, salary, job_city, work_years, degree_need,
            job_type, publish_time, job_advantage, job_desc, job_addr, company_name, company_url,
            tags, crawl_time) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE salary=VALUES(salary), job_desc=VALUES(job_desc)
        """
        params = (
            self["title"], self["url"], self["url_object_id"], self["salary"], self["job_city"],
            self["work_years"], self["degree_need"], self["job_type"],
            self["publish_time"], self["job_advantage"], self["job_desc"],
            self["job_addr"], self["company_name"], self["company_url"],
            self["job_addr"], self["crawl_time"],
        )

        return insert_sql, params
