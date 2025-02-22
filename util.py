import time

def getTime():
    return str(int(time.time() * 1000))


def getHumanReadTime():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
