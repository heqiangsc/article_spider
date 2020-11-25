
import scrapy
from scrapy.http import Request
from urllib import parse

from article_spider.items import  ArticleItemLoader
from article_spider.utils.common import get_md5


class JianShuSpider(scrapy.Spider):
    name = "jianshu"
    allowed_domains = ["jianshu.com"]
    start_urls = ['https://www.jianshu.com/']

    #rules = (
    #    Rule(LinkExtractor(allow=r'.*/p/[0-9a-z]{12}.*'), callback='parse_detail', follow=True),
    #)


    def parse(self, response):
        """
        1. 获取文章列表页中的文章url并交给scrapy下载后并进行解析
        2. 获取下一页的url并交给scrapy进行下载， 下载完成后交给parse
        """
        # 解析列表页中的所有文章url并交给scrapy下载后并进行解析
        post_nodes = response.css('a.title')
        for post_node in post_nodes:
            post_url = post_node.css("::attr(href)").extract_first("")
           # yield Request(url=parse.urljoin(response.url, post_url), callback=self.parse_detail)

        # 提取下一页并交给scrapy进行下载
        next_url = response.xpath('//*[@id="paging_block"]/div/a//@href')[-1].extract()
        if next_url:
            yield Request(url=parse.urljoin(response.url, next_url), callback=self.parse)
'''
    def parse_detail(self, response):
        try:
            item_loader = ArticleItemLoader(item=JianShuArticleItem(), response=response)
            item_loader.add_xpath("title", "//h1[@class='_1RuRku']/text()")
            item_loader.add_value("url", response.url)
            item_loader.add_value("url_object_id", get_md5(response.url))
            item_loader.add_xpath("create_date", "//div[@class='s-dsoj']/time/text()")
            item_loader.add_xpath("author", "//span[@class='FxYr8x']/a/text()")
            #item_loader.add_xpath("fav_nums", "#post_view_count::text")
            #item_loader.add_xpath("comment_nums", "#post_comment_count::text")
            item_loader.add_xpath("content", "//article[@class='_2rhmJa']")
            item_loader.add_value("content_image_url", "//img[@class='_13D2Eh']/@src")
            item_loader.add_value("content_replace_flag", 0)
            article_item = item_loader.load_item()

            yield article_item
        except Exception as e:
            print(e)
      pass
'''