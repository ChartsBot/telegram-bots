from binance.client import Client
from pprint import pprint
import os

import datetime

clef = os.environ.get('BINANCE_API_KEY')
secret = os.environ.get('BINANCE_API_SECRET')

client = Client(clef, secret)

t_from = 1604660400000
to = 1604745000000

new_from = 1602154752000
new_to = 1604746752000

Client.KLINE_INTERVAL_30MINUTE
#
# candles = client.get_klines(symbol='XRPUSDT', interval="1h", startTime=t_from, endTime=new_to)
#
# pprint(candles)

import pandas as pd


def datteeesss(t_from, t_to):
    time_diff = round((t_to - t_from) / (1000 * 60))
    frequency = str(5) + 'min'

    time_start = datetime.datetime.fromtimestamp(round(t_from / 1000) + 1)
    time_end = datetime.datetime.fromtimestamp(round(t_to / 1000) + 1)

    pprint(time_start)
    pprint(time_end)
    pprint(frequency)

    date_list = pd.date_range(start=time_start, end=time_end, freq=frequency).to_pydatetime().tolist()
    pprint(date_list)


def get_price(ticker, client):
    return client.get_ticker(symbol=ticker)


t = """[{'address': '0x1755baa7b6017da5a96d553c2213dfbee140396c',
 'holdersCount': 4,
 'issuancesCount': 0,
 'lastUpdated': 1607020578,
 'owner': '0x924f7008ff73c825b711370344fd069fc348ef00',
 'price': False,
 'totalSupply': '8000000000000000000'}]
"""

import json
# import src.libraries.requests_util as requests_util


if __name__ == '__main__':
    pass
    # res = get_price("btcusdt".upper(), client)
    # pprint(res)
    # res = requests_util.get_balance_wallet_request("0xd08517cd0372cD12B710a554F5025cFD419B43fF")
    # for token in res['tokens']:
    #     if token['balance'] != 0:
    #         token_owned_raw = float(token['balance'])
    #         maybe_token_descr = token['tokenInfo']
    #         if maybe_token_descr is not None:
    #             if 'decimals' in maybe_token_descr:
    #                 pprint("yeah")
    #             else:
    #                 pprint("nah")
    #                 pprint(maybe_token_descr)
    # res = ''
