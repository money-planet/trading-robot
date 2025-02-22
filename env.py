# 环境变量

needProxy = True

proxyHost = '127.0.0.1'
proxyPort = 7890

proxies = {
    "http": 'http://' + proxyHost + ':' + str(proxyPort),
    "https": 'http://' + proxyHost + ':' + str(proxyPort),
}

host = 'api.binance.com'
