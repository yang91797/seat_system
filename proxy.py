import time
import requests
from sqlheper import SqlHelper
import datetime
import os
from bs4 import BeautifulSoup


sql = SqlHelper()

url = sql.get_one('select url from ipurl', []).get('url')
# url = 'http://ip.11jsq.com/index.php/api/entry?method=proxyServer.generate_api_url&packid=7&fa=5&fetch_key=&groupid=0&qty=100&time=1&pro=&city=&port=1&format=json&ss=5&css=&dt=1&specialTxt=3&specialJson='

print(url)

count = 0


def getIp(count):

    try:
        res = requests.get(
            url="http://http.zhiliandaili.cn/Users-whiteIpAddNew.html?appid=3802&appkey=a2792cf6bf201ec00878b40de918cfcb&whiteip=47.105.44.64,47.100.57.249,49.94.143.215",
            timeout=5
        )
        response = requests.get(
            url=url,
            timeout=10,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6799.400 QQBrowser/10.3.2908.400',
                'Upgrade-Insecure-Requests': '1'
            }
        )
        ip_dict = response.json()
        print(ip_dict)
        date = str(datetime.datetime.now()).split(maxsplit=1)[0]
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'record')
        path = os.path.join(path, '%smsg.text' % date)
        with open(path, mode='a+', encoding='utf-8') as f:
            f.write(str(ip_dict) + '\n')
        return ip_dict['data']
    except Exception as e:
        print(e)
        if count <= 5:
            count += 1
            getIp(count)


ip_dict = getIp(count)


class Proxy:

    def __init__(self):
        self.ip_index = 0
        self.t_start = 0
        self.t_end = 0
        self.proxy = None
        self.number = 0

    def get_proxy(self):
        try:
            ip = ip_dict[self.ip_index]['IP']

            self.proxy = {
                'http': 'http://%s' % ip,
                'https': 'https://%s' % ip
            }
            # whether = requests.get(
            #     url="https://www.baidu.com/s?ie=utf8&oe=utf8&tn=98010089_dg&ch=11&wd=ip",
            #     timeout=3,
            #     headers={
            #         'Host': 'www.baidu.com',
            #         'Upgrade-Insecure-Requests': '1',
            #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.26 Safari/537.36 Core/1.63.6799.400 QQBrowser/10.3.2908.400'
            #     },
            #     proxies=self.proxy,
            # )
            # soup = BeautifulSoup(whether.text, 'lxml')
            # for li in soup.select(".c-span21 .c-gap-right"):
            #     if ip.split(':')[0] in li.get_text():
            #         print(ip, "ip可用")
            #         return self.proxy
            #     else:
            #         ip_dict.pop(self.ip_index)
            #         self.get_proxy()

            self.ip_index += 1
            if self.ip_index >= len(ip_dict):
                self.ip_index = 0
        except Exception:
            if self.number <= 10:
                self.number += 1
                self.get_proxy()
            else:
                self.proxy = None

        return self.proxy


ip = Proxy()




