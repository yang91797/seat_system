from gevent import monkey; monkey.patch_all()
import gevent
import requests
from bs4 import BeautifulSoup
import datetime
import pymysql
from threading import Thread, RLock
import smtplib
from email.mime.text import MIMEText
from email.utils import formataddr
from sqlheper import SqlHelper
import os


sql = SqlHelper()
count = sql.get_one('select count(id) as count from seatinfo', [])
seatinfo = sql.get_list(
    'select * from seatinfo inner join userinfo on seatinfo.usr = userinfo.number where whether = 1',
    [])

sql.close()
lock = RLock()


class Order(object):
    base_url = 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx'
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'record')
    agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3 like Mac OS X) AppleWebKit/602.1.50 (KHTML, like Gecko) CriOS/56.0.2924.75 Mobile/14E5239e Safari/602.1'

    def __init__(self):
        self.proxy = None  # {'http': '183.232.113.51:80'}
        self.all_cookie_dict = {}
        date = datetime.datetime.now() + datetime.timedelta(1)
        self.date = str(date).split(maxsplit=1)[0]  # 预约日期
        self.start = None  # 预约时间段
        self.end = None
        self.user = None  # 用户账号
        self.email = None  # 用户邮箱
        self.obj = None  # 实例化对象
        self.seat = None  # 预选座位列表
        self.info = None  # 用户信息
        self.number = 0  # 执行程序次数
        self.timeout = 5  # 超时时间
        self.sql = SqlHelper()
        self.get_info()
        self.no_choice = ['西101', '西201', '东202']
        self.way = None     # 用户购买方式
        self.g = []         # 协程

    def get_proxy(self):
        response = requests.get(
            url='http://127.0.0.1:5000/get'
        )
        self.proxy = {
            'http': 'http://%s' % response.text
        }
        return self.proxy

    def get_info(self):
        pass

    def vie_seat(self):
        """
        快速抢座
        :return:
        """
        dev_filter = requests.get(
            url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/device.aspx',
            timeout=self.timeout,
            params={
                'classkind': '8',
                'name': self.seat,
                'pctrNeed': '10',
                'act': 'dev_filter',
                '_nocache': ''
            },
            headers={
                'User-Agent': self.agent,
                'Host': 'seat.hhit.edu.cn',
                'Referer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
            },
            proxies=self.proxy,
            cookies=self.all_cookie_dict
        )
        dev_filter = dev_filter.json()

        if dev_filter['msg'] == 'ok':
            dev_id = dev_filter['data']['devs'][0]['id']

            title = requests.get(
                url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/device.aspx',
                timeout=self.timeout,
                params={
                  'date': self.date.replace('-', ''),
                    'dev_id': dev_id,
                    'act': 'get_rsv_sta',
                    '_nocache': ''
                },
                headers={
                    'User-Agent': self.agent,
                    'Host': 'seat.hhit.edu.cn',
                    'Referer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx'
                },
                proxies=self.proxy,
                cookies=self.all_cookie_dict
            )

            title = title.json()
            seat = {'devId': dev_id, 'labId': title['data'][0]['labId'], 'kindId': title['data'][0]['kindId'], 'title': title['data'][0]['devName']}
            return self.get_seat(seat)

    def index(self):
        index = requests.get(
            url=self.base_url,
            timeout=self.timeout,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
                'Host': 'seat.hhit.edu.cn',
                'Upgrade-Insecure-Requests': '1',
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'
            },
            proxies=self.proxy,
            cookies=self.all_cookie_dict
        )
        self.all_cookie_dict.update(login.cookies.get_dict())

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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'

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
            if room['name'] == room_name:
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
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'

                    },
                    proxies=self.proxy,
                    cookies=self.all_cookie_dict
                )

                if response.status_code == 200:
                    info_dic = response.json()

                    if info_dic['msg'] == 'ok':
                        for info in info_dic['data']:
                            yield info
                            # if self.seat_index == len(self.seat): break

    def get_seat(self, seat):

        # for seat in seats:
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
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'

            },
            proxies=self.proxy,
            cookies=self.all_cookie_dict
        )

        print(response.text)
        msg = response.json()['msg']
        time = str(datetime.datetime.now())

        if msg == '操作成功！':
            info = '%s预定成功：%s : %s' % (self.user, seat['title'], time)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
            self.g.append(gevent.spawn(self.send_email, self.email, info))
            # self.send_email(self.email, info)
            self.g.append(gevent.spawn(self.change))
            return 'ok'

        elif '已有预约' in msg:
            info = '%s该时间段内已有预约：%s: %s' % (self.user, seat['title'], time)
            print(info)
            # self.msg(info)
            self.g.append(gevent.spawn(self.msg, info))
            return 'ok'
        elif '密码输入有误' in msg:
            info = '%s: %s: %s: %s' % (self.user, seat['title'], msg, time)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))
            return 'ok'
        else:
            info = '%s:%s: %s : %s' % (self.user, seat['title'], msg, time)
            print(info)
            self.g.append(gevent.spawn(self.msg, info))

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

        # msg['To'] = formataddr(['', my_user])  # 括号里的对应收件人邮箱昵称、收件人邮箱账号

        msg['Subject'] = '选座结果'  # #邮件的主题，也可以说是标题

        server = smtplib.SMTP_SSL('smtp.163.com', 465)  # 发送邮件服务器和端口号（qq服务器好像是smtp.163.com）
        server.login(my_sender, "19951113yxd")

        # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
        server.sendmail(my_sender, [my_user, '573812718@qq.com'], msg.as_string())
        server.quit()  # 关闭连接

    def change(self):
        if self.way == 'times':
            lock.acquire()
            self.sql.modify('update userinfo set times=times-1 where number=%s', [self.user])
            lock.release()

    def __del__(self):

        self.sql.close()


def main(u):

    obj = Order()
    obj.obj = obj
    obj.info = u
    foo(obj, u)


def foo(obj, u):

    if u['t_m'] == 'times':
        obj.way = 'times'
        if u['times'] <= 1:
            obj.send_email(u['email'], '%s预定座位次数不足了，请马上充值' % u['usr'])

    elif u['t_m'] == 'monthly':
        obj.way = 'monthly'
        if str(u['end_date']) == obj.date:
            obj.send_email(u['email'], '%s预定座位时间快到期，请联系相关负责人进行充值' % u['usr'])

    try:
        #     obj.get_proxy()
        obj.start = u['start']
        obj.end = u['end']

        obj.seat = u['seat']
        obj.user = u['usr']
        obj.email = u['email']
        obj.index()
        obj.login(obj.user)
        result = obj.vie_seat()
        if result:
            print('快速抢座成功')
            return
        rooms = obj.get_floor()
        seats = obj.get_room(rooms, u['floor'])
        for seat in seats:
            if obj.get_seat(seat):
                gevent.joinall(obj.g)
                break
    except requests.exceptions.ReadTimeout as e:
        info = '%s超时：%s: %s' % (u['usr'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        foo(obj, u)
    except requests.exceptions.ConnectTimeout as e:
        info = '%s超时：%s: %s' % (u['usr'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        foo(obj, u)
    except Exception as e:
        info = '%s出错啦：%s: %s' % (u['usr'], e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        if obj.number < 20:
            obj.number += 1
            foo(obj, u)
        else:
            obj.send_email(u['email'], '%s选座出错啦' % u['usr'])


if __name__ == '__main__':
    for u in seatinfo:
        t = Thread(target=main, args=(u, ))
        t.start()
