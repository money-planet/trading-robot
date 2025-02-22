项目分为四个模块：

1. 行情数据获取，主要获取K线数据（高开低收成交量当前价）
2. 账户操作，开仓平仓止盈止损
3. 行情分析，各个时间周期是趋势行情还是震荡行情，多头还是空头，振幅如何，根据振幅可以选择合适的合约倍数
4. 概率计算，此时开仓面临的振幅风险是多少，多少价格开仓合适开仓成功的概率是多少，大概要等多久，多少价格平仓合适平仓成功的概率是多少，大概要多久时间

对应代码目录分别是：

1. data
2. transaction
3. analysis
4. probability

# 行情数据获取

## 遇到的开发大坑，卡了很久的进度

1. 币安的API在国内被墙了，要用代理才能请求到，websocket接口的`self.ws.run_forever(sslopt={"check_hostname": False}, http_proxy_host=proxyHost,
http_proxy_port=proxyPort, proxy_type="http")`这一句的`proxy_type`现在是必传的参数了，不传就会报`Only http, socks4, socks5 proxy protocols are supported`错误
2. UTC K线，Stream 名称: <symbol>@kline_<interval>，symbol必须是小写，比如`BTCUSDT`，就拿不到数据，必须`btcusdt`才行
3. K线数据，GET /api/v3/klines，symbol必须是大写，比如`BTCUSDT`，才能拿到数据，`btcusdt`不行
4. K线数据，GET /api/v3/klines，最大限制是1000根K线，怎么拿到更久远的历史数据呢？ 通过循环请求，分批次获取历史数据。例如，你可以根据时间范围（如每 1000 根 K 线对应的时间段）逐步请求数据，然后将数据拼接起来。

用的是币安的接口，币安API：
https://www.binance.com/zh-CN/binance-api

币安现货API的websocket接口：
https://developers.binance.com/docs/zh-CN/binance-spot-api-docs/web-socket-streams

比较常用的接口：

全市场所有Symbol的精简Ticker：!miniTicker@arr
{
    "e": "24hrMiniTicker",  // 事件类型
    "E": 1672515782136,     // 事件时间
    "s": "BNBBTC",          // 交易对
    "c": "0.0025",          // 最新成交价格
    "o": "0.0010",          // 24小时前开始第一笔成交价格
    "h": "0.0025",          // 24小时内最高成交价
    "l": "0.0010",          // 24小时内最低成交加
    "v": "10000",           // 成交量
    "q": "18"               // 成交额
}
主要用于获取所有交易对，刚扫了一下目前有272个，如果有更简单的接口，可以替换掉这个。如果不需要跟踪新币和下架的币的话，这个接口每天调用一次即可

UTC K线：<symbol>@kline_<interval>
{
  "e": "kline",          // 事件类型
  "E": 1672515782136,    // 事件时间
  "s": "BNBBTC",         // 交易对
  "k": {
    "t": 1672515780000,  // 这根K线的起始时间
    "T": 1672515839999,  // 这根K线的结束时间
    "s": "BNBBTC",       // 交易对
    "i": "1m",           // K线间隔
    "f": 100,            // 这根K线期间第一笔成交ID
    "L": 200,            // 这根K线期间末一笔成交ID
    "o": "0.0010",       // 这根K线期间第一笔成交价
    "c": "0.0020",       // 这根K线期间末一笔成交价
    "h": "0.0025",       // 这根K线期间最高成交价
    "l": "0.0015",       // 这根K线期间最低成交价
    "v": "1000",         // 这根K线期间成交量
    "n": 100,            // 这根K线期间成交数量
    "x": false,          // 这根K线是否完结（是否已经开始下一根K线）
    "q": "1.0000",       // 这根K线期间成交额
    "V": "500",          // 主动买入的成交量
    "Q": "0.500",        // 主动买入的成交额
    "B": "123456"        // 忽略此参数
  }
}

