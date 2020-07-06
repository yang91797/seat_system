from gevent import monkey; monkey.patch_all()
import gevent
import requests
import datetime
import time
from threading import Thread, RLock
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from sqlheper import SqlHelper
from proxy import ip
import os

st = time.perf_counter()
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
                email,
                t_m,
                times,
                end_date
        from optioninfo inner join userinfo on optioninfo.number = userinfo.number where whether = 1
        """,
        [])

sql.close()
lock = RLock()


class Order(object):
    base_url = 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx'
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'record')
    agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1'

    def __init__(self):
        self.proxy = None  # {'http': 'http://58.254.220.116:53579', 'https': 'https://58.254.220.116:53579'}
        self.all_cookie_dict = {}
        date = datetime.datetime.now() + datetime.timedelta(1)
        self.date = str(date).split(maxsplit=1)[0]  # 预约日期
        self.start = []  # 预约时间段
        self.end = []
        self.seat = []  # 预选座位列表
        self.user = None  # 用户账号
        self.username = None  # 用户姓名
        self.email = None  # 用户邮箱
        self.info = None  # 用户信息
        self.floor = None       # 用户选座楼层
        self.number = 0  # 执行程序次数
        self.max_number = 20
        self.timeout = (3, 5)  # 超时时间
        self.sql = SqlHelper()
        self.no_choice = ['西101', '西201', '东202']
        self.way = None  # 用户购买方式
        self.g = []  # 协程
        self.flag = True
        self.h = 5
        self.m = 30
        self.ip_index = 0
        self.t_start = 0
        self.t_end = 0
        self.flag1 = True
        self.seat_list = []

    def get_proxy(self):
        # ip = ip_dict['data'][0]['IP']
        self.proxy = ip.get_proxy()
        return self.proxy

    def top_speed_seat(self):
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

        print(self.seat_list)

        for i in self.seat_list:
            self.flag = True
            seat_msg = {'devId': i['devId'], 'labId': i['labId'], 'kindId': i['kindId'], 'title': i['seat_name']}

            while self.flag:
                now = datetime.datetime.now()
                if now.hour >= self.h and now.minute >= self.m or now.hour > self.h:
                    result = self.get_seat(seat_msg)
                    if result:
                        return 'ok'

    def vie_seat(self):
        """
        快速抢座
        :return:
        """
        seat_info = self.sql.get_list('select seat_name, kindName, devId, labId, kindId from seatinfo where kindName=%s order by devId desc', [self.floor])     # 倒序抢
        # seat_info = self.sql.get_list(
        #     'select seat_name, kindName, devId, labId, kindId from seatinfo where kindName=%s',
        #     [self.floor])
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                'Host': 'seat.hhit.edu.cn',
                'Upgrade-Insecure-Requests': '1',
                'Connection': 'close'
            },
            proxies=self.proxy
        )
        self.all_cookie_dict.update(index.cookies.get_dict())

        # 1544887217867

    def login(self, user):
        login = requests.get(
            url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/login.aspx',
            timeout=self.timeout,
            params={
                'act': 'login',
                'id': user,
                'pwd': user,
                'role': '512',
                'aliuserid': '',
                'schoolcode': '',
                'wxuserid': '',
                '_nocache': ''
            },
            headers={
                'Host': 'seat.hhit.edu.cn',
                'Referer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                'Connection': 'close'
            },
            proxies=self.proxy,
            cookies=self.all_cookie_dict
        )
        self.all_cookie_dict.update(login.cookies.get_dict())
        warning = "We're working to restore all services as soon as possible"
        print(login, '????')
        if warning in login.text and self.number < 10:
            self.number += 1
            self.get_proxy()
            foo(self, self.info)

        msg = login.json()
        if login.status_code == 200:
            print('登录成功')
            return 'ok'
        else:
            t = str(datetime.datetime.now())
            info = '%s: %s: %s' % (self.username, msg, t)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
            self.for_func(foo, info)

    def get_floor(self):
        """
        获得楼层
        :return:
        """
        floor = requests.get(
            url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/room.aspx',
            timeout=self.timeout,
            params={
                'classkind': '8',
                'date': self.date,
                'start': self.start,
                'end': self.end,
                'act': 'get_rm_sta',
                '_nocache': ''
            },
            headers={
                'Host': 'seat.hhit.edu.cn',
                'Refer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                'Connection': 'close'
            },
            cookies=self.all_cookie_dict,
            proxies=self.proxy
        )
        floor_dic = floor.json()
        if floor_dic['msg'] == 'ok':
            for item in floor_dic['data']:
                yield item

    def get_room(self, rooms, room_name):
        choice_room = None
        for room in rooms:
            if room['name'] not in self.no_choice:
                choice_room = room

                response = requests.get(
                    url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/device.aspx',
                    timeout=self.timeout,
                    params={
                        'right': 'detail',
                        'fr_all_day': 'false',
                        'room_id': choice_room['id'],
                        'name': choice_room['name'],
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
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                        'Connection': 'close'
                    },
                    proxies=self.proxy,
                    cookies=self.all_cookie_dict
                )

                if response.status_code == 200:
                    info_dic = response.json()

                    if info_dic['msg'] == 'ok':
                        for info in info_dic['data']:
                            yield info

                            # seat_info = {'seat_name': info['name'], 'kindName': info['kindName'], 'devId': info['devId'], 'labId': info['labId'], 'kindId': info['kindId']}
                            # self.save_seat(seat_info)
                            # print(seat_info)
                            # if self.seat_index == len(self.seat): break

    def get_seat(self, seat):
        start = self.date + ' %s' % self.start
        end = self.date + ' %s' % self.end

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
                '_nocache': ''
            },
            headers={
                'Host': 'seat.hhit.edu.cn',
                'Referer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                'Connection': 'close'

            },
            proxies=self.proxy,
            cookies=self.all_cookie_dict
        )

        print(response.text)
        msg = response.json()['msg']
        time = str(datetime.datetime.now())

        if msg == '操作成功！':
            info = '%s同学你好：%s : %s' % (self.username, seat['title'], time)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
            self.g.append(gevent.spawn(self.send_email, self.email, info))
            # self.send_email(self.email, info)
            self.g.append(gevent.spawn(self.change, times=True))

            return 'ok'

        elif '已有预约' in msg:
            info = '%s同学：该时间段内已有预约：%s: %s' % (self.username, seat['title'], time)
            print(info)
            # self.msg(info)
            self.g.append(gevent.spawn(self.msg, info))
            return 'ok'
        elif '未登录' in msg:
            info = '%s未登录或密码错误:座位号%s ：%s ' % (self.username, seat['title'], time)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
            return 'ok'
        else:
            info = '%s:座位号：%s     %s : %s' % (self.username, seat['title'], msg, time)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
        self.flag = False

    def msg(self, message):
        date = str(datetime.datetime.now()).split(maxsplit=1)[0]
        path = os.path.join(self.path, '%smsg.text' % date)
        with open(path, mode='a+', encoding='utf-8') as f:
            f.write(message + '\n')

    def send_email(self, my_user, content, ):
        my_sender = 'Aaron5718@163.com'  # 发件人邮箱账号
        # my_user = '573812718@qq.com'  # 收件人邮箱账号

        # 三个参数：第一个为文本内容，第二个 plain 设置文本格式，第三个 utf-8 设置编码
        msg = MIMEText(content, 'plain', 'utf-8')
        msg['From'] = formataddr(['Aaron', my_sender])  # 括号里的对应发件人邮箱昵称(可以为空)、发件人邮箱账号

        msg['To'] = formataddr([self.username, my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号

        msg['Subject'] = '选座结果'  # 邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL('smtp.163.com', 465)  # 发送邮件服务器和端口号（qq服务器好像是smtp.163.com）
        server.login(my_sender, "19941113yxd")

        # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.sendmail(my_sender, my_user, msg.as_string())
        server.quit()  # 关闭连接

    def change(self, times=None, whether=None):
        if times and self.way == 'times':
            lock.acquire()
            self.sql.modify('update userinfo set times=times-1 where number=%s', [self.user])
            lock.release()
        elif whether:
            self.sql.modify('update userinfo set whether=0 where number=%s', [self.user])

    def for_func(self, func, msg):
        if self.number < self.max_number:
            self.number += 1
            func(self, self.info)
        else:
            self.g.append(gevent.spawn(self.send_email, '573812718@qq.com', msg))
            time.sleep(3)
            self.number = 10
            func(self, u)

    def save_seat(self, seat_info):
        self.sql.modify('insert into seatinfo(seat_name,kindName,devId,labId,kindId) values(%s, %s, %s, %s, %s)',
                        [seat_info['seat_name'], seat_info['kindName'], seat_info['devId'], seat_info['labId'],
                         seat_info['kindId']])

    def __del__(self):

        self.sql.close()


def main(u):
    obj = Order()
    obj.info = u
    obj.seat.extend([u['seat1'], u['seat2'], u['seat3']])
    obj.user = u['number']
    obj.email = u['email']
    obj.username = u['name']
    obj.floor = u['floor']
    if u['t_m'] == 'times':
        obj.way = 'times'
        if u['times'] <= 1:
            msg = '%s同学你好：预定座位次数不足了，若继续预约，请联系相关负责人！！！' % u['name']
            obj.g.append(gevent.spawn(obj.send_email, u['email'], msg))
            obj.g.append(gevent.spawn(obj.msg, msg))
            obj.g.append(gevent.spawn(obj.change, whether=1))
    elif u['t_m'] == 'monthly':
        obj.way = 'monthly'
        if str(u['end_date'] + datetime.timedelta(1)) == obj.date:
            msg = '%s同学你好：预定座位时间到期，若继续预约，请联系相关负责人！！！' % u['name']
            obj.g.append(gevent.spawn(obj.send_email, u['email'], msg))
            obj.g.append(gevent.spawn(obj.msg, msg))
            obj.g.append(gevent.spawn(obj.change, whether=True))

    login(obj, u)


def login(obj, u):
    try:
        obj.index()
        if not obj.login(obj.user):
            return
        foo(obj, u)
    except requests.exceptions.ReadTimeout as e:
        info = '%s预约超时：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.for_func(login, info)

    except requests.exceptions.ConnectTimeout as e:
        info = '%s链接超时：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.for_func(login, info)

    except requests.exceptions.ProxyError as e:
        info = '%sip失效%s：%s: %s' % (u['name'], obj.proxy, e, str(datetime.datetime.now()))
        print(info)
        obj.g.append(gevent.spawn(obj.msg, info))
        obj.get_proxy()
        # foo(obj, u)
        obj.for_func(login, info)
    except requests.exceptions.ConnectionError:
        info = '%s同学链接出现故障，%s' % (u['name'], str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.for_func(login, info)
    except Exception as e:
        info = '%s同学登录出现错误：%s，%s' % (u['name'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.for_func(login, info)


def foo(obj, u):
    try:
        # obj.get_proxy()
        for item in times(u):

            obj.start = item[0]
            obj.end = item[1]

            res_top_speed = obj.top_speed_seat()
            if res_top_speed:
                print('极速抢座成功')
                print(time.perf_counter() - st)
                continue

            # 快速抢座
            result = obj.vie_seat()
            if result:
                print('快速抢座成功')
                continue

            # 按顺序抢座
            rooms = obj.get_floor()
            seats = obj.get_room(rooms, u['floor'])
            for seat in seats:
                if obj.get_seat(seat):
                    break

        print(time.perf_counter() - st)
    except requests.exceptions.ReadTimeout as e:
        info = '%s预约超时：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.for_func(foo, info)

    except requests.exceptions.ConnectTimeout as e:
        info = '%s链接超时：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.for_func(foo, info)
    except requests.exceptions.ProxyError as e:
        info = '%sip失效%s：%s: %s' % (u['name'], obj.proxy, e, str(datetime.datetime.now()))
        print(info)
        obj.g.append(gevent.spawn(obj.msg, info))
        obj.get_proxy()
        # foo(obj, u)
        obj.for_func(foo, info)
    except requests.exceptions.ConnectionError:
        info = '%s同学链接出现故障，%s' % (u['name'], str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        obj.for_func(foo, info)
    except Exception as e:
        info = '%s同学系统出错啦：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        msg = '%s同学你好：选座出现未知错误，将尽快修复！！！' % u['name']
        obj.for_func(foo, msg)
    gevent.joinall(obj.g)


def times(userinfo):

    start_list = []
    end_list = []
    start_list.extend([userinfo['start1'], userinfo['start2']])
    end_list.extend([userinfo['end1'], userinfo['end2']])
    start_list = [i for i in start_list if i]
    end_list = [i for i in end_list if i]
    for i, start in enumerate(start_list):
        yield start, end_list[i]


if __name__ == '__main__':
    thread_list = []
    for u in seatinfo:
        t = Thread(target=main, args=(u,))
        thread_list.append(t)
        t.start()

    for t in thread_list:
        t.join()
