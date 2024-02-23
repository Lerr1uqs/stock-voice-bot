import pyttsx3
from datetime import datetime as Datetime
from datetime import time as dttime
import time
import pandas as pd
from ashare import ashare
import config
from typing import Dict, List, NoReturn
from abc import abstractmethod
from loguru import logger
import collections
collections.Callable = collections.abc.Callable

ASTOCK_MORNING_START   = dttime(hour=9, minute=30, second=0)
ASTOCK_MORNING_END     = dttime(hour=11, minute=30, second=0)

ASTOCK_AFTERNOON_START = dttime(hour=13, minute=0, second=0)
ASTOCK_AFTERNOON_END   = dttime(hour=15, minute=0, second=0)

CALANDER: pd.DataFrame = pd.read_csv("./storage/calander.csv")
engine = pyttsx3.init()

def text_to_speech(text):
    # 初始化语音引擎
    
    # 将文本输入到引擎
    engine.say(text)
    
    # 等待语音播放完成
    engine.runAndWait()

from qywxbot import qywx as wx
bot = wx.Bot()

def log(text) -> None:
    text_to_speech(text=text)
    bot.send_msg(content=text)
    

codename = pd.read_csv("storage/codename.csv")

def is_trader_period(t: dttime) -> bool:

    if config.enable_test:
        # 无视时间测试
        return True
        
    return ASTOCK_MORNING_START <= t <= ASTOCK_MORNING_END or \
            ASTOCK_AFTERNOON_START <= t <= ASTOCK_AFTERNOON_END

class ApiClient:

    def __init__(self, stocks: List[str]) -> None:
        self.stocks = stocks

    @abstractmethod
    def on_data(self, datas: Dict[str, pd.DataFrame]):
        '''
        datas为各个注册的股票的最新的数据
        '''
        pass

class ApiServer:

    def register_client(self, client: ApiClient):
        self.client = client

    @property
    def trading_period(self):
        now = Datetime.now()
        return is_trader_period(now.time())

    def fetching(self):
        '''
        日内的交易时间会fetching 否则则会退出
        '''

        while self.trading_period:

            start = time.time()

            datas = {}
            for stock in self.client.stocks:
                data = ashare.api.query_data_in_day(
                    security=stock
                )
                # 这里只会拿到当天的数据
                datas[stock] = data

            # 回调函数
            self.client.on_data(datas)
            
            end = time.time()

            elapse = end - start

            time.sleep(60-elapse)
            
    def run_forever(self) -> NoReturn:
        while True:
            time.sleep(10)

class Monitor(ApiClient):
    def on_data(self, datas: Dict[str, pd.DataFrame]):
        
        logger.debug("on_data trigger")

        for stock in config.STOCK_LIST:
            now = datas[stock]

            close_is_min = now["close"].iloc[-1] == now["close"].min()
            close_is_max = now["close"].iloc[-1] == now["close"].max()

            # TODO 要处理这种转换很麻烦 需要标准化
            prefix = stock[0:2]
            code = stock[2:]
            stock = code + "." + prefix.upper()

            name = codename[codename["ts_code"] == stock]["name"].iloc[0]

            if close_is_max:
                log(f"{name} reach it's high {now['close'].max()}")
            elif close_is_min:
                log(f"{name} reach it's low {now['close'].min()}")
            else:
                pass
                # text_to_speech("sleep")

server = ApiServer()
server.register_client(Monitor(config.STOCK_LIST))

def isopen() -> bool:

    if config.enable_test:
        return True
    
    now = Datetime.now()
    nows = now.strftime(r"%Y%m%d")
    
    return CALANDER.loc[CALANDER['cal_date'].astype(str) == nows, 'is_open'].values[0]

if config.enable_test:
    logger.warning("testing now")

while True:
    
    if isopen():
        # 一天之内
        # stock_minutes_data: Dict[str, pd.DataFrame] = {}
        # columns = ["open" ,"close", "high", "low", "volume"]
        
        # for stock in config.STOCK_LIST:
        #     stock_minutes_data[stock] = pd.DataFrame(columns=columns)

        server.fetching()
        
        logger.info("收盘")

    time.sleep(60)

