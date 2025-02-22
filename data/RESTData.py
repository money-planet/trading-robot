import hashlib
import hmac
import json

import requests

from env import needProxy, proxies, host


def getSignature(msg, secret_key):
    return hmac.new(bytes(secret_key, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()


def getRequest(host, method, msg='', signature='', headers=None):
    if needProxy:
        return requests.get(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=headers, proxies=proxies)
    else:
        return requests.get(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=headers)


def postRequest(host, method, msg, signature='', headers=None):
    if needProxy:
        return requests.post(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=headers, proxies=proxies)
    else:
        return requests.post(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=headers)


def deleteRequest(host, method, msg, signature='', headers=None):
    if needProxy:
        return requests.delete(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=headers, proxies=proxies)
    else:
        return requests.delete(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=headers)


def simpleGet(url):
    if needProxy:
        response = requests.get(url, proxies=proxies)
    else:
        response = requests.get(url)
    return response


def getKline(host, symbol, interval, startTime, endTime, limit='1000'):
    method = '/api/v3/klines'
    msg = '&'.join(['symbol=' + symbol, 'interval=' + interval, 'limit=' + limit, 'startTime=' + startTime, 'endTime=' + endTime])
    response = simpleGet('https://' + host + method + '?' + msg)
    content = json.loads(response.content)
    return content

kline = getKline(host, 'BTCUSDT', '15m', '1738392678521', '1740192678521')
print(kline)