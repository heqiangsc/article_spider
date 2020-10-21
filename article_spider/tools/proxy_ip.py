#!/usr/bin/env python
# encoding: utf-8

import time
import requests #用requests库来做简单的网络请求
import MySQLdb
from scrapy.selector import Selector
#从scrapy的settings中导入数据库配置
from article_spider.settings import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DBNAME

conn = MySQLdb.connect(host=MYSQL_HOST, user=MYSQL_USER, passwd=MYSQL_PASSWORD,
                       db=MYSQL_DBNAME, charset='utf8')
cursor = conn.cursor()


def clear_table():
    # 清空表内容
    cursor.execute('truncate table proxy_ip')
    conn.commit()


def crawl_ihuan_ip(pages):
    '''
    爬取一定页数上的所有代理ip,每爬完一页，就存入数据库
    :return:
    '''
    clear_table()
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64; rv:52.0) Gecko/20100101 Firefox/52.0"}
    cur_page = None
    for i in range(1, pages):
        response = requests.get(url='https://ip.ihuan.me/{0}'.format(cur_page), headers=headers)
        selector = Selector(text=response.text)
        all_trs = selector.css('div.table-responsive>table>tbody>tr')
        ip_list = []
        for tr in all_trs[1:]:
            ip = tr.xpath('td[1]/a/text()').extract_first()
            port = tr.xpath('td[2]/text()').extract_first()
            addr = tr.xpath('td[3]/a/text()').getall()
            operator = tr.xpath('td[4]/a/text()').extract_first()
            https = tr.xpath('td[5]/text()').extract_first()
            http = tr.xpath('td[6]/text()').extract_first()
            type = tr.xpath('td[7]/a/text()').extract_first()
            speed = tr.xpath('td[8]//text()').extract_first()
            if speed:
                speed = int(float(speed.split(u'秒')[0]) * 60)
            if addr:
                addr = ",".join(addr)

            ip_list.append((ip, port, addr, operator, https, http, type, speed))

        # 每页提取完后就存入数据库
        for ip_info in ip_list:
            sql = "insert into proxy_ip(ip, port, addr, operator, https, http, `type`, speed) VALUES('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', {7})".format(
                ip_info[0], ip_info[1], ip_info[2], ip_info[3], ip_info[4], ip_info[5], ip_info[6], ip_info[7]
            )
            cursor.execute( sql )
        conn.commit()
        time.sleep(3)
        cur_page = selector.css("ul.pagination>li:last-child>a::attr(href)").get()

# ip的管理类
class IPUtil(object):
    # noinspection SqlDialectInspection
    def get_random_ip(self):
        # 从数据库中随机获取一个可用的ip
        random_sql = """
              SELECT ip, port, type FROM proxy_ip
            ORDER BY RAND()
            LIMIT 1
            """

        result = cursor.execute(random_sql)
        for ip_info in cursor.fetchall():
            ip = ip_info[0]
            port = ip_info[1]
            ip_type = ip_info[2]

            judge_re = self.judge_ip(ip, port, ip_type)
            if judge_re:
                return "{2}://{0}:{1}".format(ip, port, str(ip_type).lower())
            else:
                return self.get_random_ip()

    def judge_ip(self, ip, port, ip_type):
        # 判断ip是否可用，如果通过代理ip访问百度，返回code200则说明可用
        # 若不可用则从数据库中删除
        print('begin judging ---->', ip, port, ip_type)
        http_url = "https://www.baidu.com"
        proxy_url = "{2}://{0}:{1}".format(ip, port, str(ip_type).lower())
        try:
            proxy_dict = {
                "http": proxy_url,
            }
            response = requests.get(http_url, proxies=proxy_dict)
        except Exception as e:
            print("invalid ip and port,cannot connect baidu")
            self.delete_ip(ip)
            return False
        else:
            code = response.status_code
            if code >= 200 and code < 300:
                print("effective ip")
                return True
            else:
                print("invalid ip and port,code is " + code)
                self.delete_ip(ip)
                return False

    # noinspection SqlDialectInspection
    def delete_ip(self, ip):
        # 从数据库中删除无效的ip
        delete_sql = """
            delete from proxy_ip where ip='{0}'
        """.format(ip)
        cursor.execute(delete_sql)
        conn.commit()
        return True

if __name__ == '__main__':
    #crawl_ihuan_ip(1000)
    ip = IPUtil()
    for i in range(20):
        print(ip.get_random_ip())