"""
这个策略专门快进快出币安涨幅榜第一名：
0: 行情好的时候这个策略才会赚钱
1. 涨幅榜第一名新上的时候，现价买入，挂单涨20%卖出
2. 60分钟后如果没卖掉，现价卖出
3. 如果上新时已经持有仓位，且当前仓位是盈利的则立即卖出，买入新的榜一，否则等待30分钟后卖出
"""
import requests
import json
import time
import hmac
import hashlib
from decimal import *
import websocket
from config import config

try:
    import thread
except ImportError:
    import _thread as thread

getcontext().prec = 8

needProxy = False

proxyHost = '127.0.0.1'
proxyPort = 1087

proxies = {
    "http": 'http://' + proxyHost + ':' + str(proxyPort),
    "https": 'http://' + proxyHost + ':' + str(proxyPort),
}


def getTime():
    return str(int(time.time() * 1000))


def getHumanReadTime():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def getSignature(msg):
    return hmac.new(bytes(config['secret_key'], 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()


def getRequest(host, method, msg='', signature=''):
    if needProxy:
        return requests.get(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=config['headers'], proxies=proxies)
    else:
        return requests.get(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=config['headers'])


def postRequest(host, method, msg, signature):
    if needProxy:
        return requests.post(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=config['headers'], proxies=proxies)
    else:
        return requests.post(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=config['headers'])


def deleteRequest(host, method, msg, signature):
    if needProxy:
        return requests.delete(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=config['headers'], proxies=proxies)
    else:
        return requests.delete(
            'https://' + host + method + '?' + msg + '&signature=' + signature,
            headers=config['headers'])


def simpleGet(url):
    if needProxy:
        response = requests.get(url, proxies=proxies)
    else:
        response = requests.get(url)
    return response


def get24hTop10():
    def busd(data):
        res = []
        for d in data:
            if d['symbol'][-4:] == 'BUSD':
                res.append(d)
        return res

    def compare(a):
        return float(a['priceChangePercent'])

    method = '/api/v3/ticker/24hr'
    response = simpleGet('https://' + config['host'] + method)
    content = json.loads(response.content)
    data = busd(content)
    data.sort(key=compare, reverse=True)
    return data[:10]


def getKline(symbol, interval, limit='10'):
    method = '/api/v3/klines'
    msg = '&'.join(['symbol=' + symbol, 'interval=' + interval, 'limit=' + limit])
    response = simpleGet('https://' + config['host'] + method + '?' + msg)
    content = json.loads(response.content)
    return content


def getListenKey(self):
    method = '/api/v3/userDataStream'
    timestamp = str(getTime())
    msg = '&'.join(
        ['timestamp=' + timestamp])
    signature = getSignature(msg)
    response = postRequest(config['host'], method, msg, signature)
    content = json.loads(response.content)
    print('获取listenKey')
    return content['listenKey']


def order(symbol, side, _type, option):
    print('symbol: ', symbol, ' ,side: ', side, ', type: ', _type, ', option: ', option)
    method = '/api/v3/order'
    timestamp = str(getTime())
    params = ['symbol=' + symbol, 'side=' + side, 'type=' + _type,
              'timestamp=' + timestamp] + option
    msg = '&'.join(params)
    print(msg)
    signature = getSignature(msg)
    response = postRequest(config['host'], method, msg, signature)
    content = json.loads(response.content)
    print(content, "status: ", response.status_code)
    return content


def getQuantityStepSize(symbol):
    method = "/api/v3/exchangeInfo"
    response = simpleGet('https://' + config['host'] + method + '?symbol=' + symbol)
    content = json.loads(response.content)
    filters = content['symbols'][0]['filters']
    for f in filters:
        if f['filterType'] == 'LOT_SIZE':
            print('quantityStepSize: ', float(f['stepSize']))
            return Decimal(f['stepSize'])


def getPriceStepSize(symbol):
    method = "/api/v3/exchangeInfo"
    response = simpleGet('https://' + config['host'] + method + '?symbol=' + symbol)
    content = json.loads(response.content)
    filters = content['symbols'][0]['filters']
    for f in filters:
        if f['filterType'] == 'PRICE_FILTER':
            print('priceStepSize: ', Decimal(f['tickSize']))
            return Decimal(f['tickSize'])


def getOrder(symbol, orderId):
    method = '/api/v3/order'
    timestamp = str(getTime())
    params = ['symbol=' + symbol, 'orderId=' + str(orderId), 'timestamp=' + timestamp]
    msg = '&'.join(params)
    signature = getSignature(msg)
    response = getRequest(config['host'], method, msg, signature)
    content = json.loads(response.content)
    print(content)
    return content


def getPrice(symbol):
    method = '/api/v3/ticker/price'
    response = simpleGet('https://' + config['host'] + method + '?symbol=' + symbol)
    content = json.loads(response.content)
    print(content)
    return Decimal(content['price'])


def getBalance(symbol):
    method = '/api/v3/account'
    timestamp = str(getTime())
    params = ['timestamp=' + timestamp]
    msg = '&'.join(params)
    signature = getSignature(msg)
    response = getRequest(config['host'], method, msg, signature)
    content = json.loads(response.content)
    for x in content['balances']:
        if x['asset'] == symbol:
            print('locked: ', Decimal(x['locked']), ' free: ', Decimal(x['free']))
            sum = Decimal(x['locked']) + Decimal(x['free'])
            print('总数: ', sum)
            if symbol == 'SHIBBUSD':
                sum -= 1
            return sum
    return 0


def deleteAllOrder(symbol):
    method = '/api/v3/openOrders'
    timestamp = str(getTime())
    params = ['timestamp=' + timestamp, 'symbol=' + symbol]
    msg = '&'.join(params)
    signature = getSignature(msg)
    response = deleteRequest(config['host'], method, msg, signature)
    content = json.loads(response.content)
    print('删除所有挂单', "status: ", response.status_code)
    print(content)


def getPosition(symbol, price):
    if symbol != '':
        balance = getBalance(symbol[:-4])
        print(symbol[:-4], ' 个数:', balance)
        if balance * price > 10:
            return balance
    return 0


def deleteAllPosition(symbol, price):
    position = getPosition(symbol, price)
    if position > 0:
        deleteAllOrder(symbol)
        stepSize = getQuantityStepSize(symbol)
        order(symbol, 'SELL', 'MARKET', ['quantity=' + str(int(position / stepSize) * stepSize)])


globalVar = {
    'old': '',
    'price': 0,
    'btcP': 0,
    '24hrTop1Record': [],
    'transactTime': float(getTime()),
}


def buyChoice(symbol):
    if len(globalVar['24hrTop1Record']) <= 3:
        return buy(symbol, 200, 0.2)
    else:
        return buy(symbol, 20, 0.01)


def buy(symbol, busdAmount, percentage):
    res = order(symbol, 'BUY', 'MARKET', ['quoteOrderQty=' + str(busdAmount), 'newOrderRespType=RESULT'])
    avgPrice = Decimal(res['cummulativeQuoteQty']) / Decimal(res['executedQty'])
    print('买入均价:', avgPrice)
    globalVar['price'] = avgPrice
    stepSize = getQuantityStepSize(symbol)
    priceStepSize = getPriceStepSize(symbol)
    order(symbol, 'SELL', 'LIMIT',
          ['timeInForce=GTC',
           'quantity=' + str(int(Decimal(res['executedQty']) * Decimal(0.999) / stepSize) * stepSize),
           'price=' + str(int(avgPrice * Decimal(1 + percentage) / priceStepSize) * priceStepSize)])
    return res


def deleteExpiredTop1():
    record = globalVar['24hrTop1Record']
    res = []
    for r in record:
        if float(getTime()) - r['time'] < 8 * 3600 * 1000:
            res.append(r)
    globalVar['24hrTop1Record'] = res


def dealData(newTop1):
    if globalVar['old'] == '':
        globalVar['old'] = newTop1
        return
    print(globalVar['24hrTop1Record'])
    if globalVar['old'] != newTop1:
        deleteExpiredTop1()
        price = getPrice(globalVar['old'])
        deleteAllPosition(globalVar['old'], price)
        res = buyChoice(newTop1)
        globalVar['transactTime'] = float(res['transactTime'])
        globalVar['old'] = newTop1
        globalVar['24hrTop1Record'].append({"symbol": newTop1, "time": float(getTime())})
    elif float(getTime()) - globalVar['transactTime'] > 15 * 60 * 1000:
        price = getPrice(globalVar['old'])
        deleteAllPosition(globalVar['old'], price)
        globalVar['transactTime'] = float(getTime())


class WebSocketListener(object):

    def __init__(self, streamName):
        self.listenTime = time.time()
        self.ws = None
        self.streamName = streamName
        self.cache = None   # k线数据
        self.onMessageTime = time.time()

    def on_message(self, ws, message):
        def busd(data):
            res = []
            for d in data:
                # 排除掉了新币
                if d['s'][-4:] == 'BUSD' and float(d['x']) != 0:
                    res.append(d)
            return res

        def btcP(data):
            for d in data:
                if d['s'] == 'BTCBUSD':
                    return float(d['P'])

        def compare(a):
            return float(a['P'])

        def find(data, s):
            for y in data:
                if y['s'] == s:
                    return True
            return False

        def updateCache(data):
            if self.cache is not None:
                for x in self.cache:
                    if not find(data, x['s']):
                        message['data'].append(x)
            self.cache = message['data']

        s = int(time.strftime("%S", time.localtime()))
        if s % 5 != 0:
            return

        # 大于23小时重连（每24小时服务器会断开连接）
        if (time.time() - self.listenTime) / 3600 > 23:
            ws.close()
            return

        message = json.loads(message)
        if message['stream'] == '!ticker@arr':
            updateCache(message['data'])
            globalVar['btcP'] = btcP(self.cache)
            data = busd(self.cache)
            data.sort(key=compare, reverse=True)
            try:
                dealData(data[0]['s'])
            except Exception as e:
                print(e)
        else:
            print(message)

    def on_error(self, ws, error):
        print(ws)
        print(error)

    def on_close(self, ws):
        print("### 关闭WebSocket ###")
        print('关闭时间：', getHumanReadTime())
        print(ws)
        self.listenStreams()

    def on_open(self, ws):
        print("### 开启WebSocket ###")
        print('开启时间：', getHumanReadTime())
        print(ws)

    def listenStreams(self):
        print('before 监听WebSocket')
        streamNames = '/'.join([self.streamName])
        self.listenTime = time.time()
        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp("wss://stream.binance.com:9443/stream?streams=" + streamNames,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_open=self.on_open,
                                         on_close=self.on_close)
        print('after 监听WebSocket')
        if needProxy:
            self.ws.run_forever(sslopt={"check_hostname": False}, http_proxy_host=proxyHost,
                                http_proxy_port=proxyPort)
        else:
            self.ws.run_forever(sslopt={"check_hostname": False})

    def listenOnThread(self):
        def run():
            self.listenStreams()

        thread.start_new_thread(run, ())

    def listen(self):
        self.listenStreams()

    def close(self):
        self.ws.close()


def main():
    webSocketListener = WebSocketListener('!ticker@arr')
    webSocketListener.listen()


main()
