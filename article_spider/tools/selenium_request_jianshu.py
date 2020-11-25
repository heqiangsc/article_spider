from selenium import webdriver
from scrapy.selector import Selector
import time

#browser = webdriver.Chrome(executable_path="/Users/heqiang/data/src/chromedriver")
#browser.get('http://www.baidu.com/')

driver = webdriver.Chrome(executable_path="/Users/heqiang/data/src/chromedriver")
driver.set_window_size(1124, 850)  # 防止得到的WebElement的状态is_displayed为False，即不可见
driver.get("https://www.jianshu.com/")
time.sleep(6)
driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
time.sleep(6)
driver.execute_script("window.scrollTo(0,document.body.scrollHeight);")
time.sleep(5)
read_mores = driver.find_elements_by_xpath('//a[text()="阅读更多"]')

driver.execute_script("$(arguments[0]).click();", read_mores)
