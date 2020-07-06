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

st = time.perf_counter()
week = time.strftime('%w')
sql = SqlHelper()

date1 = datetime.datetime.now() + datetime.timedelta(1)
date2 = str(date1).split(maxsplit=1)[0]

# datetime.datetime.strftime(item.get('create_time'), "%Y-%m-%d %H:%M")
# if week != '2':
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
            code
    from optioninfo inner join userinfo on optioninfo.number = userinfo.number
                    inner join accomplish on optioninfo.number = accomplish.number 
                    left join recordmsg on optioninfo.number = recordmsg.number where whether=1 and accomplish.date=%s
    """, [date2])

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
                code
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
#                 code
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
#                     code
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
        self.no_choice = []
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
        self.ower_times = 0
        self.ower_true = False

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

    def get_floor(self):
        """
        获得楼层
        :return:
        """
        # floor = requests.get(
        #     url='http://seat.hhit.edu.cn/ClientWeb/pro/ajax/room.aspx',
        #     timeout=self.timeout,
        #     params={
        #         'classkind': '8',
        #         'date': self.date,
        #         'start': self.start,
        #         'end': self.end,
        #         'act': 'get_rm_sta',
        #         '_nocache': ''
        #     },
        #     headers={
        #         'Host': 'seat.hhit.edu.cn',
        #         'Refer': 'http://seat.hhit.edu.cn/ClientWeb/m/ic2/Default.aspx',
        #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
        #         'Connection': 'close'
        #     },
        #     cookies=self.all_cookie_dict,
        #     proxies=self.proxy
        # )
        # floor_dic = floor.json()
        # if floor_dic['msg'] == 'ok':
        #     for item in floor_dic['data']:
        #         yield item



        room = ["西104", '西101', '西201', '东202', '西201', "西204", "西301", "西303", "西401", "西403", "西501", "西504"]
        floor_list = []
        for item in room:
            floor = self.sql.get_one('select seat_name, kindName, devId, labId, kindId, roomId from seatinfo where kindName=%s', [item])
            floor_list.append(floor)
        return floor_list

    def get_room(self, rooms):
        date = datetime.datetime.now()
        self.date = str(date).split(maxsplit=1)[0]  # 预约日期
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

            if response.status_code == 200:
                info_dic = response.json()
                for info in info_dic['data']:
                    # self.save_seat(info)                # 保存房间信息
                    # print(info)
                    title = info.get("title")
                    for item in info.get("ts"):
                        owner = item.get("owner")
                        start = item.get("start")
                        end = item.get("end")
                        info = "%s:%s:%s:%s" % (title, owner, start, end)
                        print(info)
                        self.g.append(gevent.spawn(self.msg, info))
                        if self.ower_times >= 5:
                            return

                        if "杨旭东" in owner:
                            self.ower_true = True
                            self.ower_times += 1
                        elif self.ower_true:
                            self.ower_times += 1

    def msg(self, message):
        self.f.write(message + '\n')

    def save_seat(self, info):
        seat_info = {'seat_name': info['name'], 'kindName': info['kindName'], 'devId': info['devId'],
                     'labId': info['labId'], 'kindId': info['kindId'], "roomId": info["roomId"]}
        print(seat_info)
        self.sql.modify('insert into seatinfo(seat_name,kindName,devId,labId,kindId,roomId) values(%s,%s,%s,%s,%s,%s)',
                        [seat_info['seat_name'], seat_info['kindName'], seat_info['devId'], seat_info['labId'],
                         seat_info['kindId'], seat_info["roomId"]])

    def __del__(self):
        self.sql.close()
        self.f.close()


def main():
    obj = Order()
    obj.get_proxy()
    foo(obj)


def foo(obj):
    try:
        rooms = obj.get_floor()
        seats = obj.get_room(rooms)

        gevent.joinall(obj.g)
        print(time.perf_counter() - st)
    except requests.exceptions.ReadTimeout as e:
        info = '预约超时：%s: %s' % (e, str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        foo(obj)

    except requests.exceptions.ConnectTimeout as e:
        info = '链接超时：%s: %s' % (e, str(datetime.datetime.now()))
        obj.get_proxy()
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        foo(obj)
    except requests.exceptions.ProxyError as e:
        info = 'ip失效%s：%s: %s' % (obj.proxy, e, str(datetime.datetime.now()))
        print(info)
        obj.g.append(gevent.spawn(obj.msg, info))
        obj.get_proxy()
        # foo(obj, u)
        foo(obj)
    except requests.exceptions.ConnectionError:
        info = '同学链接出现故障，%s' % (str(datetime.datetime.now()))
        obj.g.append(gevent.spawn(obj.msg, info))
        print(info)
        foo(obj)
    # except Exception as e:
    #     info = '%s同学系统出错啦：%s: %s' % (u['name'], e, str(datetime.datetime.now()))
    #     obj.g.append(gevent.spawn(obj.msg, info))
    #     print(info)
    #     msg = '%s同学你好：选座出现未知错误，将尽快修复！！！' % u['name']
    #     obj.for_func(foo, msg)


if __name__ == '__main__':
    main()


