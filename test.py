import requests
import json

def test(content):
    content = {"content": content}
    # content = content.encode("utf8")
    # print(content)
    # content = content.encode("utf8")
    content = json.dumps(content, ensure_ascii=False,).encode("utf-8")
    # content = str(content)

    print(content)
    res = requests.post(
        url='http://192.168.3.46:8000/wxapi/test/',
        params={
            "access_token": "dwldkwldkwdw",
        },
        data=content

    )
    print(res.text)


def str_to_hex(s):
    return ' '.join([hex(ord(c)).replace('0x', '') for c in s])


li = [i*i for i in range(1, 11)]
print(li)

import os
os.rm






