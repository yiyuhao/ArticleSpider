# coding: utf-8
from time import sleep

import requests


class ProxyIpPool:
    def __init__(self):
        
        # 订单号
        tid = 559757171400635
        # 提取数量
        num = 5
        # 速度(多少秒内)
        delay = 3
        # 不过滤24小时内提取过的
        category = 2
    
        # 提取api
        self.api = 'http://tvp.daxiangdaili.com/ip/?tid={tid}&num={num}&operator=1&delay={delay}&category={category}&protocol=https'.format(
            tid=tid, num=num, delay=delay, category=category)
        
        # ip列表
        self.ip_pool = []
    
    def _pull_ips(self):
        """通过api获取代理ip"""
        try:
            ips = requests.get(self.api).text
            self.ip_pool = ips.split('\r\n')
            assert self.ip_pool
        except:
            # api有1秒提取限制，出错时重新获取
            sleep(1)
            self._pull_ips()

    def get_random_ip(self):
        """获取一个代理ip"""
        if not self.ip_pool:
            self._pull_ips()
        return 'https://{}'.format(self.ip_pool.pop())


if __name__ == '__main__':
    ip_pool = ProxyIpPool()
    a = ip_pool.get_random_ip()
    b = ip_pool.get_random_ip()
