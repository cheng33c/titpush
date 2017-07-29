# -*- coding: utf-8 -*-
import scrapy
import pymongo
import time
import datetime
import smtplib

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from pyquery import PyQuery as pq
from tit.settings import *
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]


from_addr = 'terroristmechine@163.com'
password = 'nice88200438'
smtp_server = 'smtp.163.com'

#browser = webdriver.PhantomJS(service_args=SERVICE_AGES)
browser = webdriver.Chrome()
browser.set_window_size(1400,900)
wait = WebDriverWait(browser, 10)

class JwcSpider(scrapy.Spider):
    name = "jwc"
    allowed_domains = ["http://jwc.tit.edu.cn/"]

    start_urls = ['http://jwc.tit.edu.cn/list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1022',
                  'http://jwc.tit.edu.cn/list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1107',
                  'http://jwc.tit.edu.cn/list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1108',
                  'http://jwc.tit.edu.cn/list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1106',]

    def parse(self, response):
        for url in self.start_urls:
            try:
                browser.get(url)
            except TimeoutException:
                self.parse(response)

            type = 'notpolicy'
            if url == 'http://jwc.tit.edu.cn/list.jsp?urltype=tree.TreeTempUrl&wbtreeid=1108':
                type = 'policy'
            self.get_urls(type)
        browser.close()

    def get_urls(self, type):
        baseurl = 'http://jwc.tit.edu.cn'
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.winstyle1129870260_54098 ')))
        html = browser.page_source
        doc = pq(html)
        url_part = doc('.winstyle1129870260_54098 .f54098').items()
        title_part = doc('.winstyle1129870260_54098 .f54098').items()
        date_part = doc('.winstyle1129870260_54098 .timestyle1129870260_54098').items()



        for u, t, d in zip(url_part, title_part, date_part):
            url = baseurl + u.attr('href')

            if db.notice.find_one({"url": url}):
                print(url + '已经爬取，不再重复爬取.')
                continue

            if self.judge_day_illegal(d) == False:
                print(url + '日期超过一个月，不再爬取')
                continue

            content = self.parse_html(url)
            result = {
                'url': url,
                'title': t.text(),
                'date': d.text(),
                'content': content,
                'pushed': 0,
                'type': type
            }
            self.parse_html(baseurl + u.attr('href'))
            print(result)
            self.save_to_mongo(result)

    def save_to_mongo(self, result):
        try:
            if db[MONGO_TABLE].insert(result):
                print('存储到MongoDB成功', result)
        except Exception:
            print('存储到MongoDB错误', result)

    def parse_html(self, url):
        try:
            browser.get(url)
        except TimeoutException:
            self.parse_html(url)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.winstyle1129870260_54099')))
        html = browser.page_source
        doc = pq(html)
        if doc.find('.MsoNormal'):
            content_part = doc('.MsoNormal').items()
        else:
            content_part = doc('.contentstyle1129870260_54099').items()
        content = []
        for c in content_part:
            content.append(c.text())
        return content

    def judge_day_illegal(self, dd):
        date = dd.text().split('/')
        y = int(date[0])
        m = int(date[1])
        d = int(date[2])
        if (datetime.datetime.now()-datetime.datetime(y,m,d,0,0,0)).days > 30:
            return False
        return True

    # 推送更新消息
    def push_new_message(self):
        now = datetime.datetime.now()
        for i in db.notice['pushed'].find(0):
            msg = ''
            if self.judge_day_illegal(i, now) == True:
                for c in i['content']:
                    msg += c + '\n'
                msg = msg + '\n\n原链接来自:' + i['url']
                msg = MIMEText(msg, 'plain', 'utf-8')
                for j in db.user.find():
                    to_addr = j['email']
                    msg['From'] = self._format_addr('tit官方的<%s>' % from_addr)
                    msg['To'] = self._format_addr('给你 <%s>' % to_addr)
                    msg['Subject'] = Header(i['title'], 'utf-8').encode()
                    self.push_email(j['email'], msg)
                # 防止邮箱被屏蔽
                time.sleep(1.2)

    def push_email(email, msg):
        to_addr = email
        try:
            server = smtplib.SMTP(smtp_server, 25)  # SMTP协议默认端口是25
            server.starttls()
            server.set_debuglevel(1)
            server.login(from_addr, password)
            server.sendmail(from_addr, [to_addr], msg.as_string())
            server.quit()
            print('发送邮件成功')
        except Exception:
            print('发送邮件错误')

    def _format_addr(s):
        name, addr = parseaddr(s)
        return formataddr((Header(name, 'utf-8').encode(), addr))