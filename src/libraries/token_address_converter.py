
import os
import sys

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots/src')

import json
from pprint import pprint
import requests

gecko_uniswap_list = requests.get("https://tokens.coingecko.com/uniswap/all.json").json()


def convert_ticker_address(ticker: str):
    for gecko_ticker in gecko_uniswap_list['tokens']:
        if gecko_ticker['symbol'] == ticker.upper():
            return gecko_ticker
    return None

if __name__ == '__main__':
    res = convert_ticker_address('weth')
    if res:
        pprint('gotcha')
    pprint(res)
    pprint(res['address'].lower())