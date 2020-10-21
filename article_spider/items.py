# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import datetime
import re

import scrapy
from scrapy.loader import ItemLoader
from scrapy.loader.processors import MapCompose, TakeFirst, Join
from article_spider.utils.common import extract_num
from article_spider.settings import SQL_DATETIME_FORMAT, SQL_DATE_FORMAT
from w3lib.html import remove_tags


class ArticleSpiderItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass


def add_cnblogs(value):
    return value+"-heyi"

def date_convert(value):
    try:
        create_date = datetime.datetime.strptime(value, "%Y/%m/%d").date()
    except Exception as e:
        create_date = datetime.datetime.now().date()

    return create_date


def get_nums(value):
    match_re = re.match(".*?(\d+).*", value)
    if match_re:
        nums = int(match_re.group(1))
    else:
        nums = 0

    return nums

def return_value(value):
    return value


def remove_comment_tags(value):
    #去掉tag中提取的评论
    if "评论" in value:
        return ""
    else:
        return value


def get_second(value):
    if "秒" in value:
        return float(value[0, len(value) - len("秒")-1]) * 60
    else:
        return float(value) * 60

class ArticleItemLoader(ItemLoader):
    #自定义itemloader
    default_output_processor = TakeFirst()

class CnBlogArticleItem(scrapy.Item):
    title = scrapy.Field()
    create_date = scrapy.Field()
    url = scrapy.Field()
    url_object_id = scrapy.Field()
    content_image_url = scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    content_image_path = scrapy.Field(
        output_processor=MapCompose(return_value)
    )
    content_replace_flag = scrapy.Field()
    comment_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    fav_nums = scrapy.Field(
        input_processor=MapCompose(get_nums)
    )
    #tags = scrapy.Field(
    #    input_processor=MapCompose(remove_comment_tags),
    #    output_processor=Join(",")
    #)
    content = scrapy.Field()

    def get_insert_sql(self):
        insert_sql = """
            insert into cnblogs_article(title, url, create_date, fav_nums,  comment_nums,  content, 
            content_image_url, content_image_path, content_replace_flag)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON DUPLICATE KEY UPDATE url=VALUES(url)
        """

        fron_image_url = ""
        # content = remove_tags(self["content"])

        #if self["front_image_url"]:
        #    fron_image_url = self["front_image_url"][0]

        params = (self["title"], self["url"], self["create_date"], self["fav_nums"], self["comment_nums"],
                  self["content"], '', '', self["content_replace_flag"])
        return insert_sql, params

    def get_image_insert_sql(self):
        insert_sql = """
            insert into image_file(url, image_download_url, image_url)
            VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE image_download_url=VALUES(image_download_url)
        """
        params = [];
        if self["content_image_url"]  and self["content_image_path"] and len(self["content_image_url"]) == len(self["content_image_path"]) :
           cnt = 0
           for image_url in self["content_image_url"] :
               params.append((self["url"], image_url, self["content_image_path"][cnt]))
               cnt+=1
        return insert_sql, params
