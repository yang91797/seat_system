#!/usr/bin/env python
# coding:utf-8

import requests
from hashlib import md5
import json


class Chaojiying_Client(object):

    def __init__(self, username, password, soft_id):
        self.username = username
        password = password.encode('utf8')
        self.timeout = (3, 20)
        self.password = md5(password).hexdigest()
        self.soft_id = soft_id
        self.base_params = {
            'user': self.username,
            'pass2': self.password,
            'softid': self.soft_id,
        }
        self.headers = {
            'Connection': 'Keep-Alive',
            'User-Agent': 'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0)',
        }

    def PostPic(self, im, codetype):
        """
        im: 图片字节
        codetype: 题目类型 参考 http://www.chaojiying.com/price.html
        """
        params = {
            'codetype': codetype,
        }
        params.update(self.base_params)
        files = {'userfile': ('ccc.jpg', im)}
        r = requests.post('http://upload.chaojiying.net/Upload/Processing.php', timeout=self.timeout, data=params,
                          files=files, headers=self.headers)
        return r.json()

    def ReportError(self, im_id):
        """
        im_id:报错题目的图片ID
        """
        params = {
            'id': im_id,
        }
        params.update(self.base_params)
        r = requests.post('http://upload.chaojiying.net/Upload/ReportError.php', tiomeout=self.timeout,
                          data=params, headers=self.headers)
        return r.json()


def getCodeChao(userNumbaer):
    chaojiying = Chaojiying_Client('Aaron5738', 'jtcqXKKDf5K5MDC', '900871')  # 用户中心>>软件ID 生成一个替换 96001

    path = "code/%s.jpg" % userNumbaer
    im = open(path, 'rb').read()  # 本地图片文件路径 来替换 a.jpg 有时WIN系统须要//
    result = chaojiying.PostPic(im, 6004)
    # print(result)  # 1902 验证码类型  官方网站>>价格体系 3.4+版 print 后要加()

    return result


if __name__ == '__main__':
    getCodeChao("2016120453")
