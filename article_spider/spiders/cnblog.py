import re
import scrapy
import datetime
from scrapy.http import Request
from urllib import parse

from article_spider.items import CnBlogArticleItem, ArticleItemLoader
from article_spider.utils.common import get_md5

class CnBlogSpider(scrapy.Spider):
    name = "cnblog"
    allowed_domains = ["www.cnblogs.com"]
    start_urls = ['https://www.cnblogs.com/pick/']

    def parse(self, response):
        """
        1. 获取文章列表页中的文章url并交给scrapy下载后并进行解析
        2. 获取下一页的url并交给scrapy进行下载， 下载完成后交给parse
        """
        # 解析列表页中的所有文章url并交给scrapy下载后并进行解析
        post_nodes = response.xpath('//*[@id="post_list"]/article')
        for post_node in post_nodes:
            post_url = post_node.css("::attr(href)").extract_first("")
            yield Request(url=parse.urljoin(response.url, post_url), callback=self.parse_detail)

        # 提取下一页并交给scrapy进行下载
        next_url = response.xpath('//*[@id="paging_block"]/div/a//@href')[-1].extract()
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)

    def parse_detail(self, response):
        # 通过item loader加载item
        #cb_post_title_url span
        item_loader = ArticleItemLoader(item=CnBlogArticleItem(), response=response)
        item_loader.add_css("title", "#cb_post_title_url span::text")
        item_loader.add_value("url", response.url)
        item_loader.add_value("url_object_id", get_md5(response.url))
        item_loader.add_css("create_date", "#post-date::text")
        item_loader.add_css("fav_nums", "#post_view_count::text")
        item_loader.add_css("comment_nums", "#post_comment_count::text")
        ##item_loader.add_css("fav_nums", ".bookmark-btn::text")
        ##item_loader.add_css("tags", "p.entry-meta-hide-on-mobile a::text")
        item_loader.add_css("content", "#cnblogs_post_body")
        item_loader.add_css("content_image_url", "#cnblogs_post_body>p>img::attr(src)")
        item_loader.add_value("content_replace_flag", 0)
        article_item = item_loader.load_item()

        yield article_item
