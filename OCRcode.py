import requests
import urllib
import base64
from pyquery import PyQuery
import re
import time
from multiprocessing import Queue
from sqlheper import SqlHelper


class Baidu:
    q = Queue(4)
    number = 0

    def __init__(self, user, proxy=None, sql=None):
        self.timeout = 3
        self.proxy = proxy
        self.sql = SqlHelper()
        self.user = user
        self.number += 1

    def get_token(self):
        sql = self.sql.get_one("select client_id, client_secret from ipurl", [])
        print(sql)
        res = requests.post(
            url="https://aip.baidubce.com/oauth/2.0/token",
            timeout=self.timeout,
            params={
                "grant_type": "client_credentials",
                "client_id": sql.get("client_id"),
                "client_secret": sql.get("client_secret")
            }

        )
        print(res.text)
        res_json = res.json()
        access_token = res_json.get("access_token")
        print(access_token, len(access_token))
        self.sql.modify("update ipurl set value = %s", [access_token])

    def webimage(self):

        filepath = "./code/%s.jpg" % self.user
        access_token = self.sql.get_one("select value from ipurl", []).get("value")

        with open(filepath, mode='rb') as f:
            image = f.read()

        image = str(base64.b64encode(image), 'utf-8')

        res = requests.post(
            url="https://aip.baidubce.com/rest/2.0/ocr/v1/webimage",
            params={
                "access_token": access_token
            },
            timeout=self.timeout,
            data={
                "image": image
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        res_json = res.json()
        print(res_json)
        error_code = res_json.get("error_code")
        if not error_code:
            words = res_json.get("words_result")[0].get("words")
            print(words)
            if '\u4e00' <= words <= '\u9fa5':        # 判断是否为汉字
                baiduText = requests.get(
                    url="https://www.baidu.com/s?ie=utf8&oe=utf8&tn=98010089_dg&ch=11&wd=%s" % words,
                    timeout=5,
                    headers={
                        'Host': 'www.baidu.com',
                        'Upgrade-Insecure-Requests': '1',
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6799.400 QQBrowser/10.3.2908.400'
                    },
                    proxies=self.proxy,
                )
                doc = PyQuery(baiduText.text)
                res = doc("#content_left .c-container")
                res.find('script').remove()
                res.find('style').remove()
                text = res.text()
                texts = re.split('[,|。|!\[|\]|\\n]', text)

                for line in texts:
                    if len(line) == len(words) + 1:
                        res_line = list(line)
                        for t in words:
                            if t in res_line:
                                res_line.remove(t)
                            if len(res_line) == 1:
                                print("百度结果验证码：", res_line[0])
                                return res_line[0]
                return

                                # self.sql.modify("update recordmsg set code=%s where number=%s",
                                #                 [res_line[0], self.user])

            return words

        elif error_code == 17:
            print("请求量超限额")
        elif error_code == 111:
            self.get_token()
            return self.webimage()
        elif error_code == 18:
            return self.webimage()



if __name__ == '__main__':
    baidu = Baidu(2016120453)
    baidu.get_token()
    user = 2016120451
    # baidu.webimage()
