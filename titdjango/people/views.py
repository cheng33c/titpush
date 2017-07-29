import pymongo
import re
import smtplib
import datetime
import time

from django.shortcuts import render
from email.mime.text import MIMEText
from email.header import Header
from email.utils import parseaddr, formataddr

# Create your views here.

from_addr = 'terroristmechine@163.com'
password = 'nice88200438'
smtp_server = 'smtp.163.com'

MONGO_URL = 'localhost'
MONGO_DB = 'titjwc'
MONGO_TABLE = 'user'

client = pymongo.MongoClient(MONGO_URL)
db = client[MONGO_DB]

def Index(request):
    return render(request, 'register.html')

def Register(request):
    phonestate = None
    emailstate = None
    phone = ''
    email = ''
    level = ''
    #push_update_all_message()
    if request.method == 'POST':
        # Allow phone or email set Null
        phone = request.POST.get('phone', '')
        email = request.POST.get('email', '')
        level = request.POST.get('level', '')
        if phone == '' and email == '':
            phonestate = 'empty'
            emailstate = 'empty'
        elif level == '':
            print('级别不能为空')
        else:
            if phone != '':
                if db.user.find_one({"phone": phone}):
                    phonestate = 'wrong'
                else:
                    if re.match(r'[0-9]{11}', phone):
                        phonestate = 'right'
                    else:
                        phonestate = 'wrong'
            if email != '':
                if db.user.find_one({"email": email}):
                    emailstate = 'wrong'
                else:
                    if re.match(r'^(<\w[\s\w]+>\s)?(\w+[\w+.]*@\w+.(org|com|cn|com.cn|edu)$)', email):
                        emailstate = 'right'
                    else:
                        emailstate = 'wrong'
            if level == '老师':
                level = 'teacher'
            else:
                level = 'student'

        if phonestate == 'empty' and emailstate == 'empty':
            print('email 手机号不能都为空')
        else:
            if emailstate == 'right':
                print('email正确')
            else:
                print('email错误')

            if phonestate == 'right':
                print('手机号码正确')
            else:
                print('手机号码错误')

        if phonestate == 'wrong':
            phone = ''
        if emailstate == 'wrong':
            email = ''

    content = {
        'phone': phone,
        'email': email,
        'level': level,
    }
    state = {
        'phonestate': phonestate,
        'emailstate': emailstate,
    }
    if phonestate == 'right' or emailstate == 'right':
        save_to_mongo(content)
    return render(request, 'register.html', content, state)

def _format_addr(s):
    name, addr = parseaddr(s)
    return formataddr((Header(name, 'utf-8').encode(), addr))

#保存
def save_to_mongo(result):
    msg = MIMEText('你好，亲爱的老师或同学：\n欢迎使用tit push\n我们将会自动推送太原工业学院通知给你\n'
                   '热烈的欢迎并非常感谢你的使用：）\n'
                   '如果使用过程中有任何问题或有兴趣加入我们的开发，可以回复本邮箱向我们联系\n\n\n'
                   '                                        tit push小组', 'plain', 'utf-8')
    to_addr = result['email']
    msg['From'] = _format_addr('tit官方的<%s>' % from_addr)
    msg['To'] = _format_addr('给你 <%s>' % to_addr)
    msg['Subject'] = Header('tit push欢迎你的使用：）', 'utf-8').encode()
    try:
        if result['phone'] != '' or result['email'] != '':
            if db[MONGO_TABLE].insert(result):
                print('存储到MongoDB成功',result)
                push_message(result, msg)
                push_update_all_message(result)
    except Exception:
        print('存储到MongoDB错误',result)

# 新用户推送
def push_message(result,msg):
    if result['phone'] != '':
        push_phone(result['phone'],msg)
    if result['email'] != '':
        push_email(result['email'], msg)
        push_update_all_message(result)

# 推送更新消息
def push_new_message():
    now = datetime.datetime.now()
    for i in db.notice['pushed'].find(0):
        msg = ''
        if judge_day_illegal(i, now) == True:
            for c in i['content']:
                msg += c + '\n'
            msg = msg + '\n\n原链接来自:' + i['url']
            msg = MIMEText(msg, 'plain', 'utf-8')
            for j in db.user.find():
                to_addr = j['email']
                msg['From'] = _format_addr('tit官方的<%s>' % from_addr)
                msg['To'] = _format_addr('给你 <%s>' % to_addr)
                msg['Subject'] = Header(i['title'], 'utf-8').encode()
                push_email(j['email'], msg)
            # 防止邮箱被屏蔽
            time.sleep(1.2)

# 新用户组册推送一个月内所有消息
def push_update_all_message(result):

    now = datetime.datetime.now()
    print(result)
    level = result['level']
    print('push update all message')
    for i in db.notice.find():
        if level == 'student' and i['type'] == 'policy':
            continue
        msg = ''
        print('0')
        if judge_day_illegal(i, now) == True:
            for c in i['content']:
                msg += c + '\n'
            to_addr = result['email']
            msg = msg + '\n\n原链接来自:' + i['url']
            msg = MIMEText(msg, 'plain', 'utf-8')
            msg['From'] = _format_addr('tit push:<%s>' % from_addr)
            msg['To'] = _format_addr('<%s>' % to_addr)
            msg['Subject'] = Header(i['title'], 'utf-8').encode()
            push_email(result['email'], msg, 0)
            # 防止邮箱被屏蔽
            time.sleep(2)


def push_phone(phone,msg):
    pass

# 通用发送邮件
def push_email(email, msg, repeat_time):
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
        print('发送邮件错误,将重新发送')
        if repeat_time <= 3:
            push_email(email,msg, repeat_time + 1)


# 判断是否在一个月内
def judge_day_illegal(result,now):
    fuckdate = result['date'].split('/')
    y = int(fuckdate[0])
    m = int(fuckdate[1])
    d = int(fuckdate[2])
    print(y,m,d)
    if (now - datetime.datetime(y,m,d,0,0,0)).days > 30:
        return False
    else:
        return True