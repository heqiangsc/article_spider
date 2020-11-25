# -*- coding: utf-8 -*-

# Scrapy settings for article_spider project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html
import os

BOT_NAME = 'article_spider'

SPIDER_MODULES = ['article_spider.spiders']
NEWSPIDER_MODULE = 'article_spider.spiders'


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'article_spider (+http://www.yourdomain.com)'

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Configure maximum concurrent requests performed by Scrapy (default: 16)
#CONCURRENT_REQUESTS = 32

# Configure a delay for requests for the same website (default: 0)
# See https://docs.scrapy.org/en/latest/topics/settings.html#download-delay
# See also autothrottle settings and docs
#DOWNLOAD_DELAY = 3
# The download delay setting will honor only one of:
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable cookies (enabled by default)
COOKIES_ENABLED = True

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#   'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
#   'Accept-Language': 'en',
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    'article_spider.middlewares.ArticleSpiderSpiderMiddleware': 543,
#}

# Enable or disable downloader middlewares
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
DOWNLOADER_MIDDLEWARES = {
   'article_spider.middlewares.ArticleSpiderDownloaderMiddleware': 543,
   'article_spider.middlewares.RandomUserAgentMiddleware': 1,

}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    'scrapy.extensions.telnet.TelnetConsole': None,
#}

# Configure item pipelines
# See https://docs.scrapy.org/en/latest/topics/item-pipeline.html
ITEM_PIPELINES = {
    #'article_spider.pipelines.ArticleSpiderPipeline': 300,
    #'article_spider.pipelines.JsonWithEncodingPipeline': 1,
    #'scrapy.pipelines.images.ImagesPipeline': 1,
    'article_spider.pipelines.GridFSFilesPipeline': 1,
    'article_spider.pipelines.GridFSImagesPipeline': 2,
    #'article_spider.pipelines.ArticleImagePipeline': 1,
    'article_spider.pipelines.ImageMysqlTwistedPipeline': 3,
    'article_spider.pipelines.ArticleContentReplacePipeline': 4,
    'article_spider.pipelines.MysqlTwistedPipeline': 300,

}

IMAGES_URLS_FIELD = "content_image_url"
project_dir = os.path.abspath(os.path.dirname(__file__))
IMAGES_STORE = os.path.join(project_dir, 'images')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
print (os.path.join(BASE_DIR, 'article_spider'))

#
# IMAGES_MIN_HEIGHT = 100
# IMAGES_MIN_WIDTH = 100

# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 5
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 60
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
# Enable showing throttling stats for every response received:
AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = 'httpcache'
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = 'scrapy.extensions.httpcache.FilesystemCacheStorage'


MYSQL_HOST = "127.0.0.1"
MYSQL_DBNAME = "article_spider"
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"

SQL_DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
SQL_DATE_FORMAT = "%Y-%m-%d"

#MONGO_URI = "127.0.0.1:27017"
#MONGO_DATABASE = "article_spider"

MONGO_URI = "mongodb://localhost:27017/scrapy_files"


#IMAGES_STORE="mongodb://127.0.0.1:27017/scrapy_files"
#MONGO_IMAGE_DATABASE = "scrapy_files"
#PIPELINE_MONGODB_ENABLED=True

IMAGES_THUMBS = {
    'small': (50, 50),
    'big': (100, 100),
}