# -*- coding: utf-8 -*-
import codecs
import json

from scrapy.pipelines.images import ImagesPipeline
from scrapy.exporters import JsonItemExporter
from twisted.enterprise import adbapi

import MySQLdb
import MySQLdb.cursors


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class ArticleImagePipeline(ImagesPipeline):
    """优先获取image path"""

    def item_completed(self, results, item, info):
        if 'front_image_url' in item:
            for __, value in results:
                item['front_image_path'] = value['path']
        return item


class JsonWithEncodingPipeline(object):
    def __init__(self):
        self.file = codecs.open('article.json', 'w', encoding='utf-8')

    def process_item(self, item, spider):
        lines = json.dumps(dict(item), ensure_ascii=False) + '\n'
        self.file.write(lines)
        return item

    def spider_closed(self, spider):
        self.file.close()


class JsonExporterPipeline(object):
    """调用scrapy提供的json_exporter导出json文件"""

    def __init__(self):
        self.file = open('article_exporter.json', 'wb')
        self.exporter = JsonItemExporter(self.file, encoding='utf-8', ensure_ascii=False)
        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        self.file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)
        return item


class MysqlTwistedPipeline(object):
    def __init__(self, db_pool):
        self.db_pool = db_pool

    @classmethod
    def from_settings(cls, settings):
        params = dict(
            host=settings['MYSQL_HOST'],
            database=settings['MYSQL_DATABASE'],
            user=settings['MYSQL_USER'],
            password=settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )

        db_pool = adbapi.ConnectionPool('MySQLdb', **params)

        return cls(db_pool)

    def process_item(self, item, spider):
        """async SQL insert with Twisted"""
        query = self.db_pool.runInteraction(self.do_insert, item)
        query.addErrback(self.handle_error, item, spider)

    def do_insert(self, cursor, item):
        """
            根据不同item构建不同sql，执行具体的插入
        """

        insert_sql, sql_params = item.sql
        cursor.execute(insert_sql, sql_params)

    def handle_error(self, failure, item, spider):
        """处理异步插入的异常"""
        print(failure)
