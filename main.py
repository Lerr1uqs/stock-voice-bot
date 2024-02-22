import pyttsx3
from datetime import datetime as Datetime
from datetime import time as dttime
import time
import pandas as pd
from ashare import ashare
import config
from typing import Dict, List

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

codename = pd.read_csv("storage/codename.csv")

def monitor(stock_minutes_data: Dict[str, pd.DataFrame]):

    for stock in config.STOCK_LIST:

        data = ashare.api.query_prices_untilnow(
            security=stock,
            frequency="1minute",
            count=1
        )

        history = stock_minutes_data[stock]

        if data.iloc[-1].index != history.iloc[-1].index:

            stock_minutes_data[stock] = pd.concat(
                [history, data], axis=0
            )
            now = stock_minutes_data[stock]
            # close_pctchg  = now["close"].pct_change()
            # volume_pctchg = now["volume"].pct_change()

            close_is_min = now["close"].iloc[-1] == now["close"].min()
            close_is_max = now["close"].iloc[-1] == now["close"].max()

            name = codename[codename["ts_code"] == stock, "name"].iloc[0]

            if close_is_max:
                text_to_speech(f"{name} reach its high")
            elif close_is_min:
                text_to_speech(f"{name} reach its low")

        else:
            continue
    
    # 20s轮询一次
    elapse = 20 - Datetime.now().time().second
    time.sleep(elapse)

def is_trader_period(t: dttime) -> bool:
    return ASTOCK_MORNING_START <= t <= ASTOCK_MORNING_END or \
            ASTOCK_AFTERNOON_START <= t <= ASTOCK_AFTERNOON_END

while True:

    time.sleep(60)
    now = Datetime.now()
    nows = now.strftime(r"%Y%m%d")
    
    isopen = CALANDER.loc[CALANDER['cal_date'] == nows, 'is_open'].values[0]
    
    if isopen:
        # 一天之内
        stock_minutes_data: Dict[str, pd.DataFrame] = {}
        columns = ["open" ,"close", "high", "low", "volume"]
        
        for stock in config.STOCK_LIST:
            stock_minutes_data[stock] = pd.DataFrame(columns=columns)

        while ASTOCK_MORNING_START <= now.time() <= ASTOCK_AFTERNOON_END:
            if is_trader_period(Datetime.now().time()):
                monitor(stock_minutes_data)
            else:
                time.sleep(20)
        
        # 收盘了
        print("收盘")


