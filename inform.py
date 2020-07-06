from sqlheper import SqlHelper
import time
import datetime
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr


sql = SqlHelper()


def inquire():
    t_date = datetime.datetime.now()
    date2 = str(t_date).split(maxsplit=1)[0]
    userinfo = sql.get_list("select number, name, email, t_m, times, end_date, money, whether from userinfo", [])
    for item in userinfo:
        if item.get('t_m') == 'times':
            if item['times'] <= 1:
                msg = '%s同学你好：预定座位次数不足了，若继续预约，请联系相关负责人！！！' % item.get("name")
                change(item, msg)
        elif item.get("t_m") == 'monthly':

            if str(item.get('end_date')) == date2:
                msg = '%s同学你好：预定座位时间到期，若继续预约，请联系相关负责人！！！' % item.get('name')
                change(item, msg)


def change(item, msg):
    sql.modify('update userinfo set whether=0 where number=%s', [item.get("number"), ])
    my_sender = ''  # 发件人邮箱账号
    # my_user = ''  # 收件人邮箱账号

    # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
    msg = MIMEText(msg, 'plain', 'utf-8')
    msg['From'] = formataddr(['Aaron', my_sender])  # 括号里的对应发件人邮箱昵称(可以为空)、发件人邮箱账号

    msg['To'] = formataddr([item.get("name"), item.get("email")])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号

    msg['Subject'] = '约座通知'  # 邮件的主题，也可以说是标题

    server = smtplib.SMTP_SSL('smtp.163.com', 465)  # 发送邮件服务器和端口号（qq服务器好像是smtp.163.com）
    server.login(my_sender, "")

    # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
    server.sendmail(my_sender, item.get("email"), msg.as_string())
    server.quit()  # 关闭连接

inquire()

