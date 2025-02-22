import json
import time
import websocket
from env import needProxy, proxyPort, proxyHost
from util import getHumanReadTime

try:
    import thread
except ImportError:
    import _thread as thread


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
            print(self.cache)
            # globalVar['btcP'] = btcP(self.cache)
            # data = busd(self.cache)
            # data.sort(key=compare, reverse=True)
            # try:
            #     dealData(data[0]['s'])
            # except Exception as e:
            #     print(e)
        else:
            print(message)

    def on_error(self, ws, error):
        print(ws)
        print(error)

    def on_close(self, ws, close_status_code, close_msg):
        print("### 关闭WebSocket ###")
        print('关闭时间：', getHumanReadTime(), close_status_code, close_msg)
        print(ws)
        # self.listenStreams()

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
                                http_proxy_port=proxyPort, proxy_type="http")
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
    # webSocketListener = WebSocketListener('!miniTicker@arr')
    webSocketListener = WebSocketListener('btcusdt@kline_1m')
    webSocketListener.listen()


main()