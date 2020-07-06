from gevent import monkey; monkey.patch_all()
import gevent
import requests
import datetime
import time
import dateutil.parser
from threading import Thread, RLock
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from sqlheper import SqlHelper
from proxy import ip
import os
from verification import getcode
from pyquery import PyQuery
import re
from chaojiying import getCodeChao


st = time.perf_counter()
week = time.strftime('%w')
sql = SqlHelper()

date0 = datetime.datetime.now()
date1 = date0 + datetime.timedelta(1)
date2 = str(date1).split(maxsplit=1)[0]

# datetime.datetime.strftime(item.get('create_time'), "%Y-%m-%d %H:%M")
# if week != '2':
# 当天的预约记录是否写进accomplish表里
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
            end_date,
            suss1,
            suss2,
            cookie,
            code,
            update_date
    from optioninfo inner join userinfo on optioninfo.number = userinfo.number
                    inner join accomplish on optioninfo.number = accomplish.number 
                    left join recordmsg on optioninfo.number = recordmsg.number where whether=1 and accomplish.date=%s
    """, [date2, ])

seatinfo1 = seatinfo

if not seatinfo:

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
                end_date,
                cookie,
                code,
                update_date
        from optioninfo inner join userinfo on optioninfo.number = userinfo.number
                         left join recordmsg on optioninfo.number = recordmsg.number
         where whether = 1
        """, [])

# else:
#
#     """周三预约"""
#     seatinfo = sql.get_list(
#         """
#         select start3 as start1,
#                 start4 as start2,
#                 end3 as end1,
#                 end4 as end2,
#                 seat1,
#                 seat2,
#                 seat3,
#                 floor,
#                 optioninfo.number,
#                 optioninfo.name,
#                 password,
#                 mutiple,
#                 email,
#                 t_m,
#                 times,
#                 end_date,
#                 suss1,
#                 suss2,
#                 cookie,
#                 code,
#                 update_date
#         from optioninfo inner join userinfo on optioninfo.number = userinfo.number
#                          left join recordmsg on optioninfo.number = recordmsg.number
#                         inner join accomplish on optioninfo.number = accomplish.number where whether=1 and accomplish.date=%s
#         """,
#         [date2])
#     seatinfo1 = seatinfo
#     if not seatinfo:
#         seatinfo = sql.get_list(
#             """
#             select start3 as start1,
#                     start4 as start2,
#                     end3 as end1,
#                     end4 as end2,
#                     seat1,
#                     seat2,
#                     seat3,
#                     floor,
#                     optioninfo.number,
#                     optioninfo.name,
#                     password,
#                     mutiple,
#                     email,
#                     t_m,
#                     times,
#                     end_date,
#                     cookie,
#                     code,
#                     update_date
#             from optioninfo inner join userinfo on optioninfo.number = userinfo.number
#                              left join recordmsg on optioninfo.number = recordmsg.number
#             where whether = 1
#             """,
#             [])

sql.close()
lock = RLock()


class Order(object):
    base_url = 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx'
    agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1'
    date_msg = str(datetime.datetime.now()).split(maxsplit=1)[0]
    path = os.path.join(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'record'), '%smsg.text' % date_msg)

    def __init__(self):
        self.proxy = None  # {'http': 'http://58.254.220.116:53579', 'https': 'https://58.254.220.116:53579'}
        self.f = open(self.path, mode='a+', encoding='utf-8')
        date = datetime.datetime.now() + datetime.timedelta(1)
        self.date = str(date).split(maxsplit=1)[0]  # 预约日期
        self.start = []  # 预约时间段
        self.end = []
        self.seat = []  # 预选座位列表
        self.user = None  # 用户账号
        self.username = None  # 用户姓名
        self.password = None
        self.all_cookie_dict = {}
        self.email = None  # 用户邮箱
        self.info = None  # 用户信息
        self.floor = None       # 用户选座楼层
        self.number = 0  # 执行程序次数
        self.max_number = 5
        self.timeout = (3, 10)  # 超时时间
        self.sql = SqlHelper()
        self.no_choice = ['西101', '西201', '东202']
        self.way = None  # 用户购买方式
        self.while_times = 0
        self.g = []  # 协程
        self.flag = True
        self.h = 5
        self.m = 30
        self.seat_index = 0         # 顺序预约的次数
        self.top = True             # 是否快速抢座
        self.flag1 = True
        self.seat_list = []
        self.seatTime = 0   # 第几个时间段
        self.auth = 13
        self.ind = 0
        self.codeTimes = 0
        self.seat_time = []
        self.flag2 = True

    def get_proxy(self):
        # ip = ip_dict['data'][0]['IP']
        stTime = time.perf_counter() - st
        if stTime >= 180:
            self.proxy = None
        else:
            # self.proxy = None
            self.proxy = ip.get_proxy()
        print("%sip:" % self.username, self.proxy)
        return self.proxy

    def top_speed_seat(self, m):
        """
        极速抢座
        :return:
        """
        seat = self.sql.get_list(
            'select seat_name, kindName, devId, labId, kindId from seatinfo where seat_name in(%s, %s, %s)',
            [self.seat[0], self.seat[1], self.seat[2]])

        index = 0
        while self.flag1:
            for st in seat:
                if st.get('seat_name') == self.seat[index]:
                    self.seat_list.append(st)
                    if len(self.seat_list) == len(seat):
                        self.flag1 = False
                        break
                    index += 1

        #print(self.seat_list, self.username)

        for i in self.seat_list:
            self.flag = True
            seat_msg = {'devId': i['devId'], 'labId': i['labId'], 'kindId': i['kindId'], 'title': i['seat_name']}
            # now_time = datetime.datetime.now()
            # if now_time.hour <= self.h and now_time.minute <= 28 or now_time.hour < self.h:
            #     self.get_seat(seat_msg)
            #     return "ok"
            # else:
            while self.flag:
                now = datetime.datetime.now()
                if self.while_times == 0 and now.hour <= self.h and now.minute <= 29 and now.second <= 20:
                    time.sleep(10)
                    self.while_times += 1
                if now.hour >= self.h and now.minute >= self.m or now.hour >= self.h and now.minute >= 29 and now.second >= 35 or now.hour > self.h:
                    # if now.hour == self.h and now.minute == 29 and now.second == 25:
                    #     time.sleep(0.85)
                    if not self.codeTimes:
                        self.codeTimes += 1
                        self.code()
                        self.getCode()
                    result = self.get_seat(seat_msg, m)
                    if result:
                        return 'ok'

    def vie_seat(self):
        """
        快速抢座
        :return:
        """
        if not self.info.get("mutiple"):
            seat_info = self.sql.get_list(
                'select seat_name, kindName, devId, labId, kindId from seatinfo where kindName=%s order by devId desc',
                [self.floor])  # 倒序抢
        else:
            seat_info = self.sql.get_list(
                'select seat_name, kindName, devId, labId, kindId from seatinfo where kindName=%s',
                [self.floor])

        for i in seat_info:
            seat = {'devId': i.get('devId'), 'labId': i.get('labId'), 'kindId': i.get('kindId'),
                    'title': i.get('seat_name')}
            if self.get_seat(seat):
                return True

    def index(self):
        index = requests.get(
            url=self.base_url,
            timeout=self.timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Mobile Safari/537.36',
                'Host': 'seat.hhit.edu.cn',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'close'
            },
            proxies=self.proxy,
            allow_redirects=False
        )
        self.all_cookie_dict.update(index.cookies.get_dict())

        # 1544887217867

    def logins(self, user):
        # self.code()
        # self.getCode()
        login_res = requests.get(
            url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/login.aspx',
            timeout=self.timeout,
            params={
                'act': 'login',
                # 'number': self.auth,
                'id': user,
                'pwd': self.password,
                'role': '512',
                'aliuserid': '',
                'schoolcode': '',
                'wxuserid': '',
                '_nocache': ''
            },
            headers={
                'Host': 'seat.hhit.edu.cn',
                'Referer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Mobile Safari/537.36',
                'Connection': 'close',
                "X-Requested-With": "XMLHttpRequest"
            },
            proxies=self.proxy,
            cookies=self.all_cookie_dict
        )
        self.all_cookie_dict.update(login_res.cookies.get_dict())
        warning = "We're working to restore all services as soon as possible"
        print(login_res.text, self.username, '????')
        msg = login_res.text
        t = str(datetime.datetime.now())
        info = '%s: %s: %s' % (self.username, msg, t)
        print(info)
        print(self.auth, user, self.password)
        self.g.append(gevent.spawn(self.msg, info))
        if warning in msg and self.number < 10:
            self.number += 1
            self.get_proxy()
            return foo(self, self.info)
        elif '不在白名单内或者IP已经过了有效期失效不能访问' in msg:
            self.get_proxy()
            return self.for_func(login, info)
        elif '验证码不正确' in msg or '验证码超时' in msg:

            # return self.for_func(login, info)
            return login(self, self.info, session=True)
        elif "密码输入有误" in msg:
            return

        if 'ok' in msg:

            if not self.info.get("cookie"):
                self.sql.modify("insert into recordmsg(number, name, cookie, code) values(%s, %s, %s, %s)", [self.user, self.username, str(self.all_cookie_dict), self.auth])
            else:
                self.sql.modify("update recordmsg set cookie=%s where number=%s", [str(self.all_cookie_dict), self.user])
            return 'ok'

        else:

            return self.for_func(login, info)

    def get_floor(self):
        """
        获得楼层
        :return:
        """
        room = ["西104", "西204", "西301", "西303", "西401", "西403", "西501", "西504"]
        floor_list = []
        for item in room:
            floor = self.sql.get_one('select seat_name, kindName, devId, labId, kindId, roomId from seatinfo where kindName=%s', [item])
            floor_list.append(floor)
        return floor_list

    def get_room(self, rooms, room_name):

        for room in rooms:

            response = requests.get(
                url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/device.aspx',
                timeout=self.timeout,
                params={
                    'right': 'detail',
                    'fr_all_day': 'false',
                    'room_id': room.get("roomId"),
                    'name': room.get("kindName"),
                    'open_start': '600',
                    'open_end': '2201',
                    'classkind': '8',
                    'date': self.date,
                    'start': self.start,
                    'end': self.end,
                    'act': 'get_rsv_sta',
                    'fr_start': self.start,
                    'fr_end': self.end,
                    '_nocache': ''
                },
                headers={
                    'Host': 'seat.hhit.edu.cn',
                    'Referer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Mobile Safari/537.36',
                    'Connection': 'close'
                },
                proxies=self.proxy,
                cookies=self.all_cookie_dict
            )

            # print(response.text)
            if response.status_code == 200:
                try:
                    info_dic = response.json()
                except Exception as e:
                    print("出错啦", e)
                    return

                if room.get("kindName") == "西104":
                    for info in reversed(info_dic['data']):
                        if not info.get("ts"):
                            #print(info)
                            yield info  # 倒序抢
                else:
                    for info in info_dic['data']:
                        if not info.get("ts"):
                           # print(info)
                            yield info

                            # else:
                            #
                            #     for item in info.get("ts"):
                            #
                            #         print(item.get("start"))
                            #         print(item.get("end"))
                            #         timeArray = time.strptime(item.get("end"), "%Y-%m-%d %H:%M")
                            #         timeStamp = int(time.mktime(timeArray))
                            #         print(timeStamp)


                            # seat_info = {'seat_name': info['name'], 'kindName': info['kindName'], 'devId': info['devId'], 'labId': info['labId'], 'kindId': info['kindId']}
                            # self.save_seat(seat_info)
                            # print(seat_info)
                            # if self.seat_index == len(self.seat): break

    def get_seat(self, seat, i):
        start = self.date + ' %s' % self.start
        end = self.date + ' %s' % self.end
        self.flag = False
        if not self.flag2:
            print(self.flag2, "$$")
            return
        response = requests.get(
            url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/reserve.aspx',
            timeout=self.timeout,
            params={
                'dev_id': seat['devId'],
                'lab_id': seat['labId'],
                'room_id': '',
                'kind_id': seat['kindId'],
                'type': 'dev',
                'prop': '',
                'test_id': '',
                'resv_id': '',
                'term': '',
                'min_user': '',
                'max_user': '',
                'mb_list': '',
                'test_name': '',
                'start': start,
                'end': end,
                'memo': '',
                'act': 'set_resv',
                '_nocache': '',
                'number': self.auth
            },
            headers={
                'Host': 'seat.hhit.edu.cn',
                'Referer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Mobile Safari/537.36',
                'Connection': 'close'

            },
            proxies=self.proxy,
            cookies=self.all_cookie_dict
        )
        print(self.all_cookie_dict)
        # print(response.text)
        msg = response.json()['msg']
        now_time = datetime.datetime.now()
        time_str = str(now_time)

        if msg == '操作成功！':
            info = '%s同学你好：%s : %s' % (self.username, seat['title'], time_str)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
            sendMsg = "%s:座位号:%s" % (self.username, seat['title'])
            self.g.append(gevent.spawn(self.send_email, self.email, sendMsg))
            # self.send_email(self.email, info)
            # self.g.append(gevent.spawn(self.change, times=True, accomplished=True))
            self.change(times=True, accomplished=True)
            print(i, len(self.seat_time), "%")
            if i == len(self.seat_time) - 1:
                self.flag2 = False
            return 'ok'

        elif '已有预约' in msg:
            info = '%s同学：该时间段内已有预约：%s: %s' % (self.username, seat['title'], time_str)
            print(info)
            # self.msg(info)
            self.g.append(gevent.spawn(self.msg, info))
            self.change(times=True, accomplished=True)
            print(i, len(self.seat_time), "%%")
            if i == len(self.seat_time) - 1:
                self.flag2 = False
            return 'ok'
        elif '未登录' in msg:
            info = '%s未登录或密码错误:座位号%s ：%s ' % (self.username, seat['title'], time_str)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
            return login(self, self.info, session=True)
        elif "[05:30]方可预约" in msg:
            info = "%s:座位号:%s:%s:%s" % (self.username, seat['title'], msg, time_str)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
            # if now_time.hour <= self.h and now_time.minute <= 28 or now_time.hour < self.h:
            #     print("当前时间小于5点29")
            #     return "ok"
            if now_time.hour <= self.h and now_time.minute == 29 and now_time.second < 59:
                sleep = 59 - now_time.second
                print(sleep, "???")
                time.sleep(sleep + 0.4)
            return foo(self, self.info)

        elif "验证码超时" in msg or "验证码不正确" in msg:
            info = "%s:%s:%s:%s" % (self.username, msg, self.auth, time_str)
            self.g.append(gevent.spawn(self.msg, info))
            print(info)
            self.code()
            self.getCode()
            return foo(self, self.info)

        else:
            info = '%s:座位号：%s     %s : %s' % (self.username, seat['title'], msg, time_str)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))

    def code(self):
        # http://seat.hhit.edu.cn/ClientWeb/pro/page/image.aspx????
        res = requests.get(
            url='http://seat.hhit.edu.cn/ClientWeb/pro/page/image.aspx?',
            timeout=self.timeout,
            headers={
                'Host': 'seat.hhit.edu.cn',
                'Referer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
                'User-Agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Mobile Safari/537.36'
            },
            proxies=self.proxy,
            cookies=self.all_cookie_dict
        )
        codepath = 'code/%s.jpg' % self.user
        with open(codepath, 'wb') as f:
            f.write(res.content)

    def getCode(self):
        cid, result = getcode(self.user)
        print(type(cid), cid, result)
        if result == '看不清' or str(cid) == "-3003":
            return self.code()
        elif '\u4e00' <= result <= '\u9fa5' and len(result) > 1:

            baiduText = requests.get(
                url="https://www.baidu.com/s?ie=utf8&oe=utf8&tn=98010089_dg&ch=11&wd=%s" % result,
                timeout=5,
                headers={
                    'Host': 'www.baidu.com',
                    'Upgrade-Insecure-Requests': '1',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6799.400 QQBrowser/10.3.2908.400'
                },
            )
            doc = PyQuery(baiduText.text)
            res = doc("#content_left .c-container")
            res.find('script').remove()
            res.find('style').remove()
            text = res.text()
            texts = re.split('[,|。|!\[|\]|\\n]', text)

            for line in texts:
                if len(line) == len(result) + 1:
                    res_line = list(line)
                    for t in result:
                        if t in res_line:
                            res_line.remove(t)
                        if len(res_line) == 1:
                            print("百度结果验证码：", res_line[0])
                            self.auth = res_line[0]
                            self.sql.modify("update recordmsg set code=%s where number=%s", [res_line[0], self.user])
                            return

        else:
            self.auth = result.upper()
            self.sql.modify("update recordmsg set code=%s where number=%s", [self.auth, self.user])
            return

    def msg(self, message):
        self.f.write(message + '\n')

    def send_email(self, my_user, content, ):
        my_sender = 'Aaron5718@163.com'  # 发件人邮箱账号
        # my_user = '573812718@qq.com'  # 收件人邮箱账号

        # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = formataddr(['Aaron', my_sender])  # 括号里的对应发件人邮箱昵称(可以为空)、发件人邮箱账号

        msg['To'] = formataddr([self.username, my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号

        msg['Subject'] = '选座'  # 邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL('smtp.163.com', 465)  # 发送邮件服务器和端口号（qq服务器好像是smtp.163.com）
        server.login(my_sender, "19941113yxd")

        # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.sendmail(my_sender, my_user, msg.as_string())
        server.quit()  # 关闭连接

    def change(self, times=None, whether=None, accomplish=None, accomplished=None):

        if times and self.way == 'times':
            lock.acquire()
            self.sql.modify('update userinfo set times=times-1 where number=%s', [self.user])
            lock.release()
        elif whether:

            self.sql.modify('update userinfo set whether=0 where number=%s', [self.user, ])

        if accomplish and not self.seatTime:
            self.sql.modify("insert into accomplish(number, name, date) values(%s, %s, %s) ", [self.user, self.username, self.date])

        if accomplished and not self.seatTime:

            self.sql.modify("update accomplish set suss1=1 where date=%s and number=%s ", [self.date, self.user])
        elif accomplished and self.seatTime:

            self.sql.modify("update accomplish set suss2=1 where date=%s and number=%s", [self.date, self.user])

    def for_func(self, func, msg):
        if self.number < self.max_number:
            self.number += 1
            func(self, self.info)
        else:
            time.sleep(2)
            self.number = 0
            func(self, self.info)

    def save_seat(self, seat_info):
        self.sql.modify('insert into seatinfo(seat_name,kindName,devId,labId,kindId) values(%s, %s, %s, %s, %s)',
                        [seat_info['seat_name'], seat_info['kindName'], seat_info['devId'], seat_info['labId'],
                         seat_info['kindId']])

    def __del__(self):
        self.sql.close()
        self.f.close()


def main(u):
    obj = Order()
    obj.info = u
    obj.seat.extend([u['seat1'], u['seat2'], u['seat3']])
    obj.user = u['number']
    obj.email = u['email']
    obj.username = u['name']
    obj.floor = u['floor']
    obj.get_proxy()     # 更换ip
    if not seatinfo1:
        obj.change(accomplish=True)
        # obj.g.append(gevent.spawn(obj.change, accomplish=True))
    if u["password"]:
        obj.password = u['password']
    else:
        obj.password = u['number']
    obj.all_cookie_dict = {'user': obj.user, 'pwd': obj.password}
    if u['t_m'] == 'times':
        obj.way = 'times'
        obj.g.append(gevent.spawn(obj.change, times=True))

    login(obj, u)


def login(obj, u, session=None):
    """
    :param obj: 对象
    :param u: 用户信息
    :param session: cookie过期
    :return:
    """
    try:

        # now_time = datetime.datetime.now()
        # if now_time.hour <= obj.h and now_time.minute <= 28 or now_time.hour < obj.h or session or not u.get("cookie") or not u.get("code"):
        #
        #     if now_time.hour <= obj.h and now_time.minute <= 28 or now_time.hour < obj.h:
        #         if u.get("update_date"):
        #             update_date = str(u.get("update_date")).split(maxsplit=1)[0]
        #             now_date = str(date0).split(maxsplit=1)[0]
        #             if update_date == now_date:
        #                 return
        #     obj.index()
        #     if obj.logins(obj.user):
        #         obj.code()
        #         obj.getCode()
        #         foo(obj, u)
        #         return
        # else:
        #
        #     obj.all_cookie_dict.update(eval(u.get("cookie")))
        #     obj.auth = u.get("code")
        #     foo(obj, u)
        obj.index()
        if obj.logins(obj.user):
            # obj.code()
            # obj.getCode()
            foo(obj, u)
            return

    except requests.exceptions.ReadTimeout as e:
        info = '%s登录超时：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.get_proxy()
        return obj.for_func(login, info)

    except requests.exceptions.ConnectTimeout as e:
        info = '%s链接超时：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.get_proxy()
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        return obj.for_func(login, info)

    except requests.exceptions.ProxyError as e:
        info = '%sip失效%s：%s: %s' % (u['name'], obj.proxy, e, str(datetime.datetime.now()))
        print(info)
        obj.g.append(gevent.spawn(obj.msg, info))
        obj.get_proxy()
        # foo(obj, u)
        return obj.for_func(login, info)
    except requests.exceptions.ConnectionError:
        info = '%s同学链接出现故障，%s' % (u['name'], str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        return obj.for_func(login, info)
    # except Exception as e:
    #     info = '%s同学登录出现错误：%s，%s' % (u['name'], e, str(datetime.datetime.now()))
    #     obj.g.append(gevent.spawn(obj.msg, info))
    #     print(info)
    #     obj.for_func(login, info)


def foo(obj, u, flag=None):
    try:
        seat_time = times(u)
        obj.seat_time = seat_time
        rooms = obj.get_floor()
        if not flag:
            obj.ind = 0
        for i, item in enumerate(seat_time):
            if not obj.flag2:
                print(obj.flag2, "**")
                return
            if u.get("suss1") and i == 0:
                continue
            elif u.get("suss2") and i == 1:
                continue
            obj.seatTime = i
            obj.start = item[0]
            obj.end = item[1]

            if obj.top:
                res_top_speed = obj.top_speed_seat(i)
                obj.ind += 1
                print(obj.ind)
                if obj.ind > len(seat_time):
                    obj.top = False
                if res_top_speed:
                    print('极速抢座成功')
                    print(time.perf_counter() - st)
                    continue

            # # 快速抢座
            # result = obj.vie_seat()
            # if result:
            #     print('快速抢座成功')
            #     continue

            # 按顺序抢座
            seats = obj.get_room(rooms, u['floor'])
            for seat in seats:
                if not obj.flag2:
                    print(obj.flag2, "&&")
                    return
                obj.seat_index += 1
                if obj.get_seat(seat, i):
                        break
                print(obj.seat_index)
                if obj.seat_index >= 5:
                    obj.seat_index = 0
                    print(obj.seat_index)
                    print("循环")
                    return foo(obj, u, flag=True)
        gevent.joinall(obj.g)
        print(time.perf_counter() - st)
    except requests.exceptions.ReadTimeout as e:
        info = '%s预约超时：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.get_proxy()
        return obj.for_func(foo, info)

    except requests.exceptions.ConnectTimeout as e:
        info = '%s链接超时：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.get_proxy()
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        return obj.for_func(foo, info)
    except requests.exceptions.ProxyError as e:
        info = '%sip失效%s：%s: %s' % (u['name'], obj.proxy, e, str(datetime.datetime.now()))
        print(info)
        obj.g.append(gevent.spawn(obj.msg, info))
        obj.get_proxy()
        # foo(obj, u)
        return obj.for_func(foo, info)
    except requests.exceptions.ConnectionError:
        info = '%s同学链接出现故障，%s' % (u['name'], str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        return obj.for_func(foo, info)
    # except Exception as e:
    #     info = '%s同学系统出错啦：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
    #     obj.g.append(gevent.spawn(obj.msg, info))
    #     print(info)
    #     msg = '%s同学你好：选座出现未知错误，将尽快修复！！！' % u['name']
    #     obj.for_func(foo, msg)


def times(userinfo):

    start_list = []
    end_list = []
    start_list.extend([userinfo['start1'], userinfo['start2']])
    end_list.extend([userinfo['end1'], userinfo['end2']])
    start_list = [i for i in start_list if i]
    end_list = [i for i in end_list if i]
    seat_time = []
    for i, start in enumerate(start_list):
        seat_time.append([start, end_list[i]])
    return seat_time


if __name__ == '__main__':
    thread_list = []
    for u in seatinfo:

        if u.get("start1") and u.get("start2") and u.get("suss1") and u.get("suss2"):
            continue
        elif not u.get("start2") and u.get("suss1"):
            continue

        t = Thread(target=main, args=(u,))
        thread_list.append(t)
        t.start()

    for t in thread_list:
        t.join()


