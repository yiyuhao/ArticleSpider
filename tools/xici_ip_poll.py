import re
import requests
from time import sleep

import MySQLdb
from scrapy.selector import Selector


class XiciProxyIpPool:
    def __init__(self):
        # 连接db
        self.conn = MySQLdb.connect(host='localhost', user='root', password='root', database='article_spider', charset='utf8')
        self.cursor = self.conn.cursor()

    def crawl_ips(self):
        """爬取西刺的免费ip代理"""

        # 最终结果
        ip_list = []

        # headers
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:56.0) Gecko/20100101 Firefox/56.0'}

        # 爬取2000页
        for page in range(1, 2000):
            # 缓慢爬取
            sleep(2)

            # 发起request
            req = requests.get('http://www.xicidaili.com/nn/{page}'.format(page=page), headers=headers)

            selector = Selector(text=req.text)
            all_trs = selector.css('#ip_list tr')

            # 去掉tr表头
            for tr in all_trs[1:]:
                all_texts = tr.css('td::text').extract()
                # 代理ip
                ip = all_texts[0]
                # 端口
                port = all_texts[1]
                # http or https?
                proxy_type = all_texts[5] if 'HTTP' in all_texts[5] else all_texts[4]
                # 速度
                speed = tr.css('.bar::attr(title)').extract_first()
                if speed:
                    speed = float(speed.split('秒')[0])
                # 插入db的一行数据
                line = (ip, port, proxy_type, speed)

                # 判断解析正确
                try:
                    assert re.match('\d+\.\d+\.\d+\.\d+', ip) is not None, '解析出的ip存在问题: {}'.format(ip)
                    assert re.match('HTTPS*', proxy_type) is not None, 'type存在问题: {}'.format(proxy_type)
                    assert re.match('\d+\.\d+', str(speed)) is not None, 'speed存在问题: {}'.format(str(speed))
                    ip_list.append(line)
                except:
                    print('解析存在问题: ', line, '当前是第{}页'.format(page))

                # 插入数据库
                try:
                    self.insert_db(line)
                except:
                    print('error to insert a line: ', line)

    def insert_db(self, line):
        """爬取的数据插入数据库"""
        self.cursor.execute("""
                       INSERT INTO proxy_ips(ip, port, proxy_type, speed)
                       VALUES('{ip}', '{port}', '{proxy_type}', {speed})""".format(ip=line[0], port=line[1],
                                                                                   proxy_type=line[2], speed=line[3]))
        self.conn.commit()

    def get_random_ip(self):
        """
            从数据库中随机获取代理ip
            :return  (str)  'http://110.1.1.1:80'
        """

        sql = """SELECT ip, port FROM proxy_ips
                 WHERE proxy_type='HTTP' and speed < 1
                 ORDER BY RAND()
                 LIMIT 1"""
        db_has_ip = self.cursor.execute(sql)
        # 数据库没有指定要求的ip则爬取
        if not db_has_ip:
            try:
                self.crawl_ips()
            except:
                pass
            self.get_random_ip()
        for line in self.cursor.fetchall():
            ip = 'http://{ip}:{port}'.format(ip=line[0], port=line[1])
            if self.ip_is_effective(ip):
                return ip
            else:
                self.delete_ip(ip=line[0])
                self.get_random_ip()

    @staticmethod
    def ip_is_effective(ip):
        """检查ip是否可用"""
        try:
            res = requests.get('http://www.baidu.com', proxies={'http': ip})
        except:
            print('invalid ip and port')
            return False
        else:
            code = res.status_code
            return True if 200 <= code < 300 else False

    def delete_ip(self, ip):
        """数据库中删除无效ip"""
        sql = """
            DELETE FROM proxy_ips 
            WHERE ip='{}'""".format(ip)
        self.cursor.execute(sql)
        self.conn.commit()


if __name__ == '__main__':
    ip_pool = XiciProxyIpPool()
    # ip = ip_pool.get_random_ip()
    ip_pool.crawl_ips()
