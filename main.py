from scrapy.cmdline import execute

import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
execute(["scrapy", "crawl", "cnblog"])
#executeIMAGES_IMAGES_STORESTORE(["scrapy", "crawl", "proxy_ip"])