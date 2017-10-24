# coding: utf-8
from datetime import datetime
from elasticsearch_dsl import DocType, Date, Nested, Boolean, \
    analyzer, InnerObjectWrapper, Completion, Keyword, Text, Integer

from elasticsearch_dsl.analysis import CustomAnalyzer as _CustomAnalyzer
from elasticsearch_dsl.connections import connections

# 连接本地elasticsearch
connections.create_connection(hosts=['localhost'])


class CustomAnalyzer(_CustomAnalyzer):
    """自定义analysis规避es_dsl Model init报错问题"""
    def get_analysis_definition(self):
        return {}


ik_analyzer = CustomAnalyzer('ik_max_word', filter=['lowercase'])


class JobboleEsModel(DocType):
    """伯乐在线文章类型"""
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer='ik_max_word')
    create_date = Date()
    url = Keyword()
    url_object_id = Keyword()
    front_image_url = Keyword()
    front_image_path = Keyword()
    praise_nums = Integer()
    fav_nums = Integer()
    comment_nums = Integer()
    tags = Text(analyzer='ik_max_word')
    content = Text(analyzer='ik_max_word')

    class Meta:
        index = 'jobbole'
        doc_type = 'article'


class ZhihuQuestionEsModel(DocType):
    suggest = Completion(analyzer=ik_analyzer)
    zhihu_id = Keyword()
    topics = Text(analyzer='ik_max_word')
    url = Keyword()
    title = Text(analyzer='ik_max_word')
    content = Text(analyzer='ik_max_word')
    create_time = Date()
    update_time = Date()
    answer_num = Integer()
    comments_num = Integer()
    watch_user_num = Integer()
    click_num = Integer()
    crawl_time = Date()
    crawl_update_time = Date()

    class Meta:
        index = 'zhihu_question'
        doc_type = 'article'


class ZhihuAnswerEsModel(DocType):
    suggest = Completion(analyzer=ik_analyzer)
    zhihu_id = Keyword()
    url = Keyword()
    question_id = Keyword()
    author_id = Keyword()
    content = Text(analyzer='ik_max_word')
    praise_num = Integer()
    comments_num = Integer()
    create_time = Date()
    update_time = Date()
    crawl_time = Date()

    class Meta:
        index = 'zhihu_answer'
        doc_type = 'article'
        

class LagouEsModel(DocType):
    suggest = Completion(analyzer=ik_analyzer)
    title = Text(analyzer='ik_max_word')
    url = Keyword()
    url_object_id = Keyword()
    salary = Keyword()
    job_city = Text(analyzer='ik_max_word')
    work_years = Keyword()
    degree_need = Text(analyzer='ik_max_word')
    job_type = Text(analyzer='ik_max_word')
    publish_time = Keyword()
    job_advantage = Keyword()
    job_desc = Text(analyzer='ik_max_word')
    job_addr = Keyword()
    company_name = Keyword()
    company_url = Keyword()
    tags = Text(analyzer='ik_max_word')
    crawl_time = Date()

    class Meta:
        index = 'lagou'
        doc_type = 'job'

if __name__ == '__main__':
    JobboleEsModel.init()
    ZhihuQuestionEsModel.init()
    ZhihuAnswerEsModel.init()
    LagouEsModel.init()
