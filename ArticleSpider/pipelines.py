# -*- coding: utf-8 -*-

from scrapy.pipelines.images import ImagesPipeline

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


class ArticlespiderPipeline(object):
    def process_item(self, item, spider):
        return item


class ArticleImagePipeline(ImagesPipeline):
    """优先获取image path"""
    def item_completed(self, results, item, info):
        for __, value in results:
            item['front_image_path'] = value['path']
        return item
