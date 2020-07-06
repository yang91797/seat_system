from gevent import monkey; monkey.patch_all()
import time
from threading import Thread, RLock
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from sqlheper import SqlHelper
import datetime
import os

week = time.strftime('%w')
sql = SqlHelper()

if week != '2':
    seatinfo = sql.get_list(
        """
        select start1,
                start2,
                end1,
                end2,
                seat1,
                seat2,
                seat3,
                floor,
                optioninfo.number,
                optioninfo.name,
                password,
                mutiple,
                email,
                t_m,
                times,
                end_date
        from optioninfo inner join userinfo on optioninfo.number = userinfo.number where whether = 1
        """,
        [])
else:

    """周三预约"""
    seatinfo = sql.get_list(
        """
        select start3 as start1,
                start4 as start2,
                end3 as end1,
                end4 as end2,
                seat1,
                seat2,
                seat3,
                floor,
                optioninfo.number,
                optioninfo.name,
                password,
                mutiple,
                email,
                t_m,
                times,
                end_date
        from optioninfo inner join userinfo on optioninfo.number = userinfo.number where whether = 1
        """,
        [])

sql.close()
lock = RLock()


def send_email(username, my_user, content):
    my_sender = 'Aaron5718@163.com'  # 发件人邮箱账号
    # my_user = '573812718@qq.com'  # 收件人邮箱账号

    # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
    msg = MIMEText(content, 'plain', 'utf-8')
    msg['From'] = formataddr(['Aaron', my_sender])  # 括号里的对应发件人邮箱昵称(可以为空)、发件人邮箱账号

    msg['To'] = formataddr([username, my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号

    msg['Subject'] = '预约座位服务通知'  # 邮件的主题，也可以说是标题

    server = smtplib.SMTP_SSL('smtp.163.com', 465)  # 发送邮件服务器和端口号（qq服务器好像是smtp.163.com）
    server.login(my_sender, "19941113yxd")

    # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
    server.sendmail(my_sender, my_user, msg.as_string())
    server.quit()  # 关闭连接


def msg(message):
        date = str(datetime.datetime.now()).split(maxsplit=1)[0]
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'record')
        path = os.path.join(path, '%smsg.text' % date)

        with open(path, mode='a+', encoding='utf-8') as f:
            f.write(message + '\n')


def main(user):
    content = "%s同学你好，由于服务器压力，今天约座系统有一些更新，有些问题要在实际环境中才知道是否存在，注意关注明天的预约动态噢" % user.get("name")
    print(content)
    send_email(user.get("name"), user.get("email"), content)
    msg(content)


if __name__ == '__main__':
    # thread_list = []
    for user in seatinfo:
        main(user)
        # t = Thread(target=main, args=(user,))
        # thread_list.append(t)
        # t.start()

    # for t in thread_list:
    #     t.join()
