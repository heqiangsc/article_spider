from selenium import webdriver
from scrapy.selector import Selector
import time

#browser = webdriver.Chrome(executable_path="/Users/heqiang/data/src/chromedriver")
#browser.get('http://www.baidu.com/')

driver = webdriver.Chrome(executable_path="/Users/heqiang/data/src/chromedriver")
driver.set_window_size(1124, 850)  # 防止得到的WebElement的状态is_displayed为False，即不可见
driver.get("http://www.weibo.com/login.php")
time.sleep(5)
# 自动点击并输入用户名
driver.find_element_by_xpath('//*[@id="loginname"]').clear()
driver.find_element_by_xpath('//*[@id="loginname"]').send_keys("")
driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[2]/div/input').clear()

time.sleep(2)
# 自动点击并输入登录的密码
driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[2]/div/input').send_keys("")
driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()

# 输入验证码
driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[3]/div/input').send_keys(
    input("输入验证码： "))

time.sleep(1)
driver.find_element_by_xpath('//*[@id="pl_login_form"]/div/div[3]/div[6]/a').click()
