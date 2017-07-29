# TIT-Push
**email push system based on spider, developed by scrapy and django**  

#### 程序说明
一个邮件推送系统，通过爬虫爬取教务处信息，然后推送到你的邮箱。

#### 使用方法
在titdjango/people文件下中打开views,配置MongoDB信息和EMAIL信息  
SMTP服务只要在你的邮箱中开启就可以了，然后输入邮箱帐号和SMTP服务的密码  
接下来在titdjango文件夹下运行  
python3 manage.py runserver  

然后在打开另一个终端，在titcrawler文件夹下运行run.sh，就可以运行爬虫程序。  
你可以在titcrawler/tit/spiders/jwc.py下配置爬虫的start_urls。  
邮件信息那里不需要配置。
