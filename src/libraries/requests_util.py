import requests
import pprint
import time
import json

from binance.client import Client
from dataclasses import dataclass
from cachetools import cached, TTLCache
import os
import sys

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots/src')

from libraries.util import float_to_str, pretty_number, keep_significant_number_float
import libraries.time_util as time_util
import libraries.web3_calls as web3_util
import libraries.general_end_functions as general_end_functions
import libraries.token_address_converter as token_addy_converter
import libraries.util as util
import yfinance as yf

from web3 import Web3

API_KEY_ETHEXPLORER = os.environ.get('API_KEY_ETHEXPLORER')
clef = os.environ.get('BINANCE_API_KEY')
secret = os.environ.get('BINANCE_API_SECRET')

client_binance = Client(clef, secret)

jwt = os.environ.get('JWT')

query_get_latest = """
query {  
    mints(first: $AMOUNT, where: {pair_in: $PAIR}, orderBy: timestamp, orderDirection: desc) {
        transaction {
          id
          timestamp
          __typename
        }
        pair {
          token0 {
            id
            symbol
            __typename
          }
          token1 {
            id
            symbol
            __typename
          }
          __typename
        }
        to
        liquidity
        amount0
        amount1
        amountUSD
        __typename
  }
  burns(first: $AMOUNT, where: {pair_in: $PAIR}, orderBy: timestamp, orderDirection: desc) {
    transaction {
      id
      timestamp
      __typename
    }
    pair {
      token0 {
        id
        symbol
        __typename
      }
      token1 {
        id
        symbol
        __typename
      }
      __typename
    }
    sender
    liquidity
    amount0
    amount1
    amountUSD
    __typename
  }
  swaps(first: $AMOUNT, where: {pair_in: $PAIR}, orderBy: timestamp, orderDirection: desc) {
    transaction {
      id
      timestamp
      __typename
    }
    id
    pair {
      token0 {
        id
        symbol
        __typename
      }
      token1 {
        id
        symbol
        __typename
      }
      __typename
    }
    amount0In
    amount0Out
    amount1In
    amount1Out
    amountUSD
    to
    __typename
  }
}

"""

url_price_full = "https://api.coingecko.com/api/v3/simple/price?ids=$ID&vs_currencies=usd&include_market_cap=true&include_24hr_vol=true&include_24hr_change=true"

url_price_old = "https://api.coingecko.com/api/v3/coins/$ID/market_chart?vs_currency=usd&days=$DAYS&interval=daily"

url_eth_price_gecko = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"

get_address_endpoint = "https://visitly.azurewebsites.net/api/pairs/ERC-20/"

etherscan_api_key = os.environ.get('ETH_API_KEY')

ethexplorer_holder_base_url = "https://ethplorer.io/service/service.php?data="

url_graphex_backend = "https://chartex.pro/api/history?symbol=$EXCHANGE%3A$SYMBOL&resolution=$RESOLUTION&from=$TFROM&to=$TTO"

gecko_chart_url = "https://api.coingecko.com/api/v3/coins/$TOKEN/market_chart/range?vs_currency=usd&from=$T_FROM&to=$T_TO"

symbol_chartex = {
    'ROT': 'ROT.5AE9E2',
    'SAV3': 'SAV3',
    'HOT': 'HOT.4D5DDC',
    '7ADD': '7ADD.A2DF92',
    'COIN': 'COIN.CFA850'
}

ticker_hardcoded = {
    'COIN': '0xE61fDAF474Fac07063f2234Fb9e60C1163Cfa850'
}

# Graph QL requests
query_eth = '''query blocks {
    t1: blocks(first: 1, orderBy: timestamp, orderDirection: desc, where: {timestamp_gt: %d, timestamp_lt: %d}) {
            number
    }
    t2: blocks(first: 1, orderBy: timestamp, orderDirection: desc, where: {timestamp_gt: %d, timestamp_lt: %d}) {
            number
    }
    tnow: blocks(first: 1, orderBy: timestamp, orderDirection: desc, where: {timestamp_lt: %d}) {
            number
    }
}'''

query_uni = '''query blocks {
    t1: token(id: "CONTRACT", block: {number: NUMBER_T1}) {
        derivedETH
    }
    t2: token(id: "CONTRACT", block: {number: NUMBER_T2}) {
        derivedETH
    }
    tnow: token(id: "CONTRACT", block: {number: NUMBER_TNOW}) {
        derivedETH
    }
    b1: bundle(id: "1", block: {number: NUMBER_T1}) {
        ethPrice
    }
    b2: bundle(id: "1", block: {number: NUMBER_T2}) {
        ethPrice
    }
    bnow: bundle(id: "1", block: {number: NUMBER_TNOW}) {
        ethPrice
    }
}
'''

query_eth_now = '''
query blocks {
    tnow: blocks(first: 1, orderBy: timestamp, orderDirection: desc, where: {timestamp_lt: %d}) {
            number
    }
}
'''

query_uni_now = '''query blocks {
    tnow: token(id: "CONTRACT", block: {number: NUMBER_TNOW}) {
        derivedETH
    }
    bnow: bundle(id: "1", block: {number: NUMBER_TNOW}) {
        ethPrice
    }
}
'''

req_graphql_vol24h_rot = '''{
  pairHourDatas(
    where: {hourStartUnix_gt: TIMESTAMP_MINUS_24_H, pair: "PAIR_CHANGE"})
    {
    hourlyVolumeUSD
  }
}'''


# t_from and t_to should be in epoch seconds.
# Resolution should be 1, 5, 15, 30, 60, 240, 720, 1D
def create_url_request_graphex(symbol, resolution, t_from, t_to, exchange):
    return url_graphex_backend \
        .replace('$EXCHANGE', exchange) \
        .replace("$SYMBOL", symbol) \
        .replace("$RESOLUTION", str(resolution)) \
        .replace("$TFROM", str(t_from)) \
        .replace("$TTO", str(t_to))


def get_gecko_chart(token_name, t_from, t_to):
    print("token: " + token_name + "f_from: " + str(t_from) + " - t_to: " + str(t_to))
    gecko_url_updated = gecko_chart_url.replace("$TOKEN", token_name) \
        .replace("$T_FROM", str(t_from)) \
        .replace("$T_TO", str(t_to))
    pprint.pprint(gecko_url_updated)
    res = requests.get(gecko_url_updated)
    return res


def get_binance_chart_data(token_name, t_from, t_to):
    delta = round(t_to - t_from)
    if delta < 6 * 3600:
        res = "1m"
    elif delta < 13 * 3600:
        res = "5m"
    elif delta < 24 * 3600 + 100:
        res = "5m"
    elif delta < 24 * 3600 * 7 + 100:
        res = "1h"
    elif delta < 24 * 3600 * 30 + 100:
        res = "6h"
    elif delta < 24 * 3600 * 500 + 100:
        res = "1d"
    else:
        res = "2d"

    t_from_ms = t_from * 1000
    t_to_ms = t_to * 1000
    print("token: " + token_name + "f_from: " + str(t_from) + " - t_to: " + str(t_to) + " - resolution = " + str(res))

    candles = client_binance.get_klines(symbol=token_name, interval=res, startTime=t_from_ms, endTime=t_to_ms)
    return candles


def get_stock_data(ticker, resolution: str, t_from, t_to):
    period = int((round(t_to - t_from) / (3600 * 24)))
    period_str = str(period) + 'd'
    pprint.pprint(period_str)
    msft = yf.Ticker(ticker)

    # get historical market data
    hist = msft.history(period=period_str, interval=resolution, prepost=True)
    return hist


def get_graphex_data(token, resolution, t_from, t_to, exchange='UNISWAP'):
    if token in symbol_chartex:
        symbol = symbol_chartex.get(token)
    else:
        symbol = token
    url = create_url_request_graphex(symbol, resolution, t_from, t_to, exchange)
    name = 'cookie'
    header = {name: jwt}
    resp = requests.get(url, headers=header)
    return resp


def get_price_raw_now(graphql_client_eth, graphql_client_uni, token_contract):  # TODO: use web3 for it to be faster
    now = int(time.time())

    updated_eth_query = query_eth_now % now
    res_eth_query = graphql_client_eth.execute(updated_eth_query)
    json_resp_eth = json.loads(res_eth_query)

    latest_block = int(json_resp_eth['data']['tnow'][0]['number'])

    query_uni_updated = query_uni_now.replace("CONTRACT", token_contract) \
        .replace("NUMBER_TNOW", str(latest_block))

    res_uni_query = graphql_client_uni.execute(query_uni_updated)
    json_resp_uni = json.loads(res_uni_query)

    try:
        token_per_eth_now = float(json_resp_uni['data']['tnow']['derivedETH'])
    except KeyError:  # trying again, as sometimes the block that we query has not yet been indexed. For that, we read
        # the error message returned by uniswap and work on the last indexed block that is return in the error message
        last_block_indexed = str(res_uni_query).split('indexed up to block number ')[1][0:8]
        query_uni_updated = query_uni_now.replace("CONTRACT", token_contract) \
            .replace("NUMBER_TNOW", str(last_block_indexed))
        res_uni_query = graphql_client_uni.execute(query_uni_updated)
        json_resp_uni = json.loads(res_uni_query)
        token_per_eth_now = float(json_resp_uni['data']['tnow']['derivedETH'])

    eth_price_now = float(json_resp_uni['data']['bnow']['ethPrice'])

    token_price_now_usd = token_per_eth_now * eth_price_now

    return token_per_eth_now, token_price_now_usd


# from graphqlclient import GraphQLClient
# graphql_client_uni_2 = GraphQLClient('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2')
# graphql_client_eth = GraphQLClient('https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks')
def get_price_raw(graphql_client_eth, graphql_client_uni, token_contract):
    now = int(time.time())

    before_7d = now - 3600 * 24 * 7
    before_7d_high = before_7d + 600

    before_1d = now - 3600 * 24
    before_1d_high = before_1d + 600

    updated_eth_query = query_eth % (before_7d, before_7d_high, before_1d, before_1d_high, now)
    res_eth_query = graphql_client_eth.execute(updated_eth_query)
    json_resp_eth = json.loads(res_eth_query)

    block_from_7d = int(json_resp_eth['data']['t1'][0]['number'])
    block_from_1d = int(json_resp_eth['data']['t2'][0]['number'])
    latest_block = int(json_resp_eth['data']['tnow'][0]['number'])

    query_uni_updated = query_uni.replace("CONTRACT", token_contract.lower()) \
        .replace("NUMBER_T1", str(block_from_7d)) \
        .replace("NUMBER_T2", str(block_from_1d)) \
        .replace("NUMBER_TNOW", str(latest_block))

    res_uni_query = graphql_client_uni.execute(query_uni_updated)
    json_resp_uni = json.loads(res_uni_query)

    try:
        token_per_eth_now = float(json_resp_uni['data']['tnow']['derivedETH'])
    except KeyError:  # trying again, as sometimes the block that we query has not yet been indexed. For that, we read
        # the error message returned by uniswap and work on the last indexed block that is return in the error message
        # TODO: work with regex as block numbers can be < 10000000
        last_block_indexed = str(res_uni_query).split('indexed up to block number ')[1][0:8]
        query_uni_updated = query_uni.replace("CONTRACT", token_contract) \
            .replace("NUMBER_T1", str(block_from_7d)) \
            .replace("NUMBER_T2", str(block_from_1d)) \
            .replace("NUMBER_TNOW", str(last_block_indexed))
        res_uni_query = graphql_client_uni.execute(query_uni_updated)
        json_resp_uni = json.loads(res_uni_query)
        token_per_eth_now = float(json_resp_uni['data']['tnow']['derivedETH'])

    try:
        token_per_eth_7d = float(json_resp_uni['data']['t1']['derivedETH']) if 'derivedETH' in json_resp_uni['data'][
            't1'] else 0.0
    except TypeError:
        token_per_eth_7d = None
    try:
        token_per_eth_1d = float(json_resp_uni['data']['t2']['derivedETH']) if 'derivedETH' in json_resp_uni['data'][
            't2'] else 0.0
    except TypeError:
        token_per_eth_1d = None

    eth_price_7d = float(json_resp_uni['data']['b1']['ethPrice'])
    eth_price_1d = float(json_resp_uni['data']['b2']['ethPrice'])
    eth_price_now = float(json_resp_uni['data']['bnow']['ethPrice'])

    token_price_7d_usd = token_per_eth_7d * eth_price_7d if token_per_eth_7d is not None else None
    token_price_1d_usd = token_per_eth_1d * eth_price_1d if token_per_eth_1d is not None else None
    token_price_now_usd = token_per_eth_now * eth_price_now

    return (
        token_per_eth_7d, token_price_7d_usd, token_per_eth_1d, token_price_1d_usd, token_per_eth_now,
        token_price_now_usd)


@cached(cache=TTLCache(maxsize=1024, ttl=60))
def get_supply_cap_raw(contract_addr, decimals):
    base_addr = 'https://api.etherscan.io/api?module=stats&action=tokensupply&contractaddress=' + contract_addr + '&apikey=' + etherscan_api_key
    supply_cap = float(requests.post(base_addr).json()['result']) / decimals
    return supply_cap


# return price 7 days ago, price 1 day ago, volume last 24h
@cached(cache=TTLCache(maxsize=1024, ttl=60))
def get_volume_24h(graphclient_uni, pair_contract):
    now = int(time.time())
    yesterday = now - 3600 * 24
    print("yesterday = " + str(yesterday))
    updated_req = req_graphql_vol24h_rot.replace("TIMESTAMP_MINUS_24_H", str(yesterday)).replace("PAIR_CHANGE",
                                                                                                 pair_contract.lower())
    res = graphclient_uni.execute(updated_req)
    json_resp_eth = json.loads(res)

    all_values = json_resp_eth['data']['pairHourDatas']

    amount = 0
    for value in all_values:
        amount += round(float(value['hourlyVolumeUSD']))

    return amount


@cached(cache=TTLCache(maxsize=1024, ttl=300))
def get_number_holder_token(token):
    url = ethexplorer_holder_base_url + token
    res = requests.get(url).json()
    try:
        holders = res['pager']['holders']['records']
    except KeyError:
        holders = -1
    return int(holders)


# cache weather data for no longer than ten minutes
@cached(cache=TTLCache(maxsize=1024, ttl=3600))
def get_token_contract_address(token_ticker):
    if util.is_checksumaddr(token_ticker):
        return token_ticker
    elif token_ticker == "eth" or token_ticker == "ETH":
        return "0x0000000000000000000000000000000000000000"
    elif token_ticker.upper() in ticker_hardcoded:
        return ticker_hardcoded[token_ticker.upper()]
    maybe_res = token_addy_converter.convert_ticker_address(token_ticker)
    if maybe_res:
        return maybe_res['address'].lower()
    url = get_address_endpoint + token_ticker
    pprint.pprint("start getting contract from token" + token_ticker)
    res = requests.get(url).json()
    for i in res:
        if 'token1' in i:
            if 'symbol' in i['token1']:
                if i['token1']['symbol'].lower() == token_ticker.lower():
                    if 'id' in i['token1']:
                        pprint.pprint("done getting contract from token")
                        return i['token1']['id']

                elif i['token0']['symbol'].lower() == token_ticker.lower():
                    if 'id' in i['token0']:
                        pprint.pprint("done getting contract from token")
                        return i['token0']['id']
    return None
    # pprint.pprint(res)


@cached(cache=TTLCache(maxsize=1024, ttl=30))
def get_eth_price_now():
    res = requests.get(url_eth_price_gecko).json()
    if 'ethereum' in res:
        if 'usd' in res['ethereum']:
            return int(res['ethereum']['usd'])
    return 0


@cached(cache=TTLCache(maxsize=1024, ttl=30))
def get_price_now_full(ticker):
    updated_url = url_price_full.replace("$ID", ticker)
    res = requests.get(updated_url).json()[ticker]
    price_usd = res['usd']
    change_percentage = res['usd_24h_change']
    volume_24_usd = res['usd_24h_vol']
    mcap_usd = res['usd_market_cap']
    return price_usd, change_percentage, volume_24_usd, mcap_usd


@cached(cache=TTLCache(maxsize=1024, ttl=600))
def get_price_at(ticker: str, days: int):
    updated_url = url_price_old \
        .replace("$ID", ticker) \
        .replace("$DAYS", str(days))
    res = requests.get(updated_url).json()['prices'][0][1]
    return res


def get_gas_price_raw():
    url = "https://ethgasstation.info/json/ethgasAPI.json"
    return requests.get(url).json()


@dataclass(frozen=True)
class PairedWith:
    ticker: str
    contract: str
    price_usd: float


@dataclass(frozen=True)
class Swap:
    buy: (str, int)
    sell: (str, int)
    id: str
    timestamp: int
    paired_with: PairedWith

    def value_raw_paired_with(self):
        return self.amount_paired_with()

    def is_positif(self):
        return self.buy[0] == self.paired_with.ticker

    def amount_paired_with(self):
        if self.is_positif():
            return self.sell[1]
        else:
            return self.buy[1]

    def to_string(self, custom_emoji=None, with_date=True):
        message = ""
        time_since = time_util.get_minute_diff(self.timestamp)
        date_msg = str(time_since) + " mins ago." if with_date else ""
        if self.is_positif():
            price_usd = pretty_number(self.buy[1] * self.paired_with.price_usd)
            emoji = "🟢" if custom_emoji is None else custom_emoji
            message += emoji + " Buy " + pretty_number(self.sell[1])[0:9] + " " + self.sell[0] + " for " \
                       + pretty_number(self.buy[1])[0:9] + " " + self.buy[0] + " <code>($" + price_usd[0:6] + ")</code> " \
                       + date_msg
        else:
            emoji = "🔴" if custom_emoji is None else custom_emoji
            price_usd = pretty_number(self.sell[1] * self.paired_with.price_usd)
            message += emoji + " Sell " + pretty_number(self.buy[1])[0:9] + " " + self.buy[0] + " for " \
                       + pretty_number(self.sell[1])[0:9] + " " + self.sell[0] + " <code>($" + price_usd[0:6] + ")</code> " \
                       + date_msg
        message += " | " + '<a href="etherscan.io/tx/' + str(self.id) + '">view</a>'
        return message

    def to_string_complex(self):
        if self.is_positif():
            price_usd_raw = self.buy[1] * self.paired_with.price_usd
            price_usd = pretty_number(price_usd_raw)
            # emoji = min(round(self.buy[1]), 30) * "🟢" + "🟢"
            emoji = min((round(price_usd_raw / 300)), 30) * "🟢" + "🟢"
            main_part = "Buy <b>" + pretty_number(self.sell[1])[0:9] + " " + self.sell[0] + "</b> for <b>" \
                        + pretty_number(self.buy[1])[0:9] + ' ' + self.buy[0] + " </b> <code>($" + price_usd[0:6] + ")</code>"
        else:
            price_usd_raw = self.sell[1] * self.paired_with.price_usd
            price_usd = pretty_number(price_usd_raw)
            # emoji = min(round(self.sell[1]), 30) * "🔴" + "🔴"
            emoji = min((round(price_usd_raw / 300)), 30) * "🔴" + "🔴"
            main_part = "Sell <b>" + pretty_number(self.buy[1])[0:9] + " " + self.buy[0] + "</b> for <b>" \
                        + pretty_number(self.sell[1])[0:9] + ' ' + self.sell[0] + " </b> <code>($" + price_usd[0:6] + ")</code>"
        first_row = emoji + '\n'
        end = " | " + '<a href="etherscan.io/tx/' + str(self.id) + '">view</a>'
        return first_row + main_part + end


@dataclass(frozen=True)
class BotSwap:
    swap_buy: Swap
    swap_sell: Swap
    amount_token_pair_stolen: int
    paired_with: PairedWith

    def value_raw_token_paired_with(self):
        return self.amount_token_pair_stolen

    def price_usd(self):
        return self.amount_token_pair_stolen * self.paired_with.price_usd

    def to_string(self):
        price_usd_pretty = pretty_number(self.price_usd())
        emoji = "🤖" * min((round(self.price_usd() * 10) + 1), 30)
        main_part = "Bot stole <b>" + pretty_number(self.amount_token_pair_stolen) + ' ' + self.paired_with.ticker + "</b> <code>($" + price_usd_pretty + ")</code>"
        end = " | " + '<a href="etherscan.io/tx/' + str(self.swap_buy.id) + '">buy tx</a> - ' + '<a href="etherscan.io/tx/' + str(self.swap_sell.id) + '">sell tx</a>'
        return emoji + '\n' + main_part + end

    def to_string_complex(self, eth_price):
        return self.to_string()


@dataclass(frozen=True)
class Mint:
    token_0: (str, int)
    token_1: (str, int)
    id: str
    timestamp: int
    paired_with: PairedWith

    def value_raw_paired_with(self):
        return self.amount_paired_with()

    def price_usd(self):
        return self.amount_paired_with() * self.paired_with.price_usd

    def amount_paired_with(self):
        if self.token_0[0].lower() == self.paired_with.ticker.lower():
            amount_eth = self.token_0[1] * 2
        else:
            amount_eth = self.token_1[1] * 2
        return amount_eth

    def to_string(self, custom_emoji=None):
        emoji = "💚" if custom_emoji is None else custom_emoji
        price_usd = pretty_number(self.price_usd())
        time_since = time_util.get_minute_diff(self.timestamp)
        message = emoji + " Add " + pretty_number(self.token_0[1])[0:6] + ' ' + self.token_0[0] + " and " + \
                  pretty_number(self.token_1[1])[0:6] + ' ' + self.token_1[0] + " in liquidity" \
                  + " <code>($" + price_usd[0:6] + ")</code> " \
                  + str(time_since) + " mins ago."
        message += " | " + '<a href="etherscan.io/tx/' + str(self.id) + '">view</a>'
        return message

    def to_string_complex(self):
        price_usd_raw = self.price_usd()
        price_usd = pretty_number(price_usd_raw)
        emoji = min((round(self.price_usd() / 300)), 30) * "💚" + "💚"
        time_since = time_util.get_minute_diff(self.timestamp)
        first_row = emoji + '\n'
        main_part = "Add " + pretty_number(self.token_0[1])[0:6] + ' ' + self.token_0[0] + " and " + \
                    pretty_number(self.token_1[1])[0:6] + ' ' + self.token_1[0] + " in liquidity" \
                    + " <code>($" + price_usd[0:6] + ")</code> " \
                    + str(time_since) + " mins ago."
        end = " | " + '<a href="etherscan.io/tx/' + str(self.id) + '">view</a>'
        return first_row + main_part + end


@dataclass(frozen=True)
class Burn:
    token_0: (str, int)
    token_1: (str, int)
    id: str
    timestamp: int
    paired_with: PairedWith

    def value_raw_paired_with(self):
        return self.amount_paired_with()

    def price_usd(self):
        return self.amount_paired_with() * self.paired_with.price_usd

    def amount_paired_with(self):
        if self.token_0[0] == self.paired_with.ticker:
            amount_eth = self.token_0[1] * 2
        else:
            amount_eth = self.token_1[1] * 2
        return amount_eth

    def to_string(self, custom_emoji=None):
        emoji = "💔" if custom_emoji is None else custom_emoji
        price_usd = pretty_number(self.price_usd())
        time_since = time_util.get_minute_diff(self.timestamp)
        message = emoji + " Removed " + pretty_number(self.token_0[1])[0:6] + ' ' + self.token_0[0] + " and " \
                  + pretty_number(self.token_1[1])[0:6] + ' ' + self.token_1[0] + " in liquidity" \
                  + " <code>($" + price_usd[0:6] + ")</code> " \
                  + str(time_since) + " mins ago."
        message += " | " + '<a href="etherscan.io/tx/' + str(self.id) + '">view</a>'
        return message

    def to_string_complex(self):
        price_usd_raw = self.price_usd()
        price_usd = pretty_number(price_usd_raw)
        emoji = min((round(self.price_usd() / 300)), 30) * "💔" + "💔"
        time_since = time_util.get_minute_diff(self.timestamp)
        first_row = emoji + '\n'
        main_part = "Removed " + pretty_number(self.token_0[1])[0:6] + ' ' + self.token_0[0] + " and " \
                    + pretty_number(self.token_1[1])[0:6] + ' ' + self.token_1[0] + " in liquidity" \
                    + " <code>($" + price_usd[0:6] + ")</code> " \
                    + str(time_since) + " mins ago."
        end = " | " + '<a href="etherscan.io/tx/' + str(self.id) + '">view</a>'
        return first_row + main_part + end


def get_latest_actions(pair, graphql_client_uni, options=None, amount=30):
    updated_eth_query = query_get_latest.replace("$PAIR", '["' + pair + '"]').replace("$AMOUNT", str(amount))
    res_eth_query = graphql_client_uni.execute(updated_eth_query)
    json_resp_eth = json.loads(res_eth_query)
    return json_resp_eth


def parse_swaps(res, paired_with: PairedWith):
    swaps = res['data']['swaps']
    l_swaps = []
    for swap in swaps:
        amount0In = float(swap['amount0In'])
        amount0Out = float(swap['amount0Out'])
        amount1In = float(swap['amount1In'])
        amount1Out = float(swap['amount1Out'])
        timestamp = int(swap['transaction']['timestamp'])
        id = swap['id'][:-2]
        token0, token1 = parse_pair(swap['pair'])
        if amount0In > 0:
            l_swaps.append(Swap((token0, amount0In), (token1, amount1Out), id, timestamp, paired_with))
        else:
            l_swaps.append(Swap((token1, amount1In), (token0, amount0Out), id, timestamp, paired_with))
    # detect bots:
    # l_swaps = sorted(l_swaps, key=lambda x: x.timestamp, reverse=True)
    # for swap in l_swaps:

    return l_swaps


def parse_mint(res, paired_with: PairedWith):
    mints = res['data']['mints']
    l_mints = []
    for mint in mints:
        amount0 = float(mint['amount0'])
        amount1 = float(mint['amount1'])
        timestamp = int(mint['transaction']['timestamp'])
        id = mint['transaction']['id']
        token0, token1 = parse_pair(mint['pair'])
        l_mints.append(Mint((token0, amount0), (token1, amount1), id, timestamp, paired_with))
    return l_mints


def parse_burns(res, paired_with: PairedWith):
    burns = res['data']['burns']
    l_burns = []
    for burn in burns:
        try:
            amount0 = float(burn['amount0'])
            amount1 = float(burn['amount1'])
            timestamp = int(burn['transaction']['timestamp'])
            id = burn['transaction']['id']
            token0, token1 = parse_pair(burn['pair'])
            l_burns.append(Burn((token0, amount0), (token1, amount1), id, timestamp, paired_with))
        except TypeError:
            pass
    return l_burns


def parse_pair(pair):
    """parse a json pair res queried with last actions"""
    token0 = pair['token0']['symbol']
    token1 = pair['token1']['symbol']
    return token0, token1


def detect_bots(actions):
    swaps = [x for x in actions if type(x) is Swap]
    others = [x for x in actions if type(x) is not Swap]
    yeeted_sells = []
    kept_actions = []
    # We first check the positive actions
    if swaps is not None or swaps is not []:
        for action in swaps:
            if action.is_positif():
                amount_buy_token = action.sell[1]
                similar_sell = next(iter([x for x in swaps if (not x.is_positif() and x.buy[1] == amount_buy_token)]), "")
                if similar_sell != "":
                    pprint.pprint("DETECTED BOT ACTION!: ")
                    pprint.pprint(action.id)
                    pprint.pprint(similar_sell.id)

                    yeeted_sells.append(similar_sell)
                    eth_drained = similar_sell.sell[1] - action.buy[1]
                    bot_action = BotSwap(action, similar_sell, eth_drained, similar_sell.paired_with)
                    kept_actions.append(bot_action)
                else:
                    kept_actions.append(action)
        for action in swaps:  # Yes it's not optimized but n < 10 so who cares
            if not action.is_positif() and action not in yeeted_sells:
                kept_actions.append(action)
    return others + kept_actions


def get_last_actions(pair_contract, token_ticker, paired_with: PairedWith, graphql_client_uni, options=None, amount=50):
    # use this: general end functions convert_to_usd_raw(
    if options is not None:
        if ("whale" in options or "whales" in options or "w" in options) and amount == 50:
            amount = 100
    last_actions = get_latest_actions(pair_contract, graphql_client_uni, options, amount)

    parsed_swaps = parse_swaps(last_actions, paired_with)
    parsed_mints = parse_mint(last_actions, paired_with)
    parsed_burns = parse_burns(last_actions, paired_with)
    all_actions = parsed_burns + parsed_mints + parsed_swaps

    start_message = "Last 5 actions of " + token_ticker.upper() + " with pair " + paired_with.ticker + "/" + token_ticker + " " + str(paired_with.contract)[0:8] + "[...]\n"
    if options is not None:
        if "buy" in options or "buys" in options or "b" in options:
            start_message = start_message.replace("actions", "buys")
            all_actions = [x for x in parsed_swaps if x.is_positif()]
        elif "sell" in options or "sells" in options or "s" in options:
            start_message = start_message.replace("actions", "sells")
            all_actions = [x for x in parsed_swaps if not x.is_positif()]
        elif "liq" in options or "liqs" in options or "liquidity" in options or "l" in options:
            start_message = start_message.replace("actions", "liquidity actions")
            all_actions = parsed_mints + parsed_burns

        if "whale" in options or "whales" in options or "w" in options:
            start_message = start_message + "Showing only actions <b>> 10 Eth:</b>\n"
            to_keep_if_whales = []
            for action in all_actions:
                if action.amount_paired_with() > 10 * get_eth_price_now():
                    to_keep_if_whales.append(action)
            all_actions = to_keep_if_whales

    all_actions_sorted = sorted(all_actions, key=lambda x: x.timestamp, reverse=True)
    return all_actions_sorted, start_message


def get_pair_info_from_pair_contract(token_ticker, pair_contract: str, uni_wrapper, graphqlclient_uni, graphqlclient_eth) -> PairedWith:
    """
    Given a ticker and a pair contract, will return a PairedWith object containing informations about the other ticker
    in the pair
    :param token_ticker:
    :param pair_contract:
    :param uni_wrapper:
    :return: None if not found, else a PairedWith object
    """
    # First from the pair contract we get both contract of the tokens
    t1_contract, t2_contract = web3_util.get_pair_tokens_contracts(uni_wrapper, pair_contract)
    pprint.pprint(t1_contract)
    pprint.pprint(t2_contract)
    # Then we check which one is the token ticker
    t1_info = web3_util.get_token_info(uni_wrapper, t1_contract)
    t2_info = web3_util.get_token_info(uni_wrapper, t2_contract)
    if t1_info['symbol'] != token_ticker.upper():
        symbol = t1_info['symbol']
        price = general_end_functions.convert_to_usd_raw(1, symbol, graphqlclient_uni, graphqlclient_eth)
        return PairedWith(symbol, t1_contract, price)
    elif t2_info['symbol'] != token_ticker.upper():
        symbol = t2_info['symbol']
        price = general_end_functions.convert_to_usd_raw(1, symbol, graphqlclient_uni, graphqlclient_eth)
        return PairedWith(symbol, t1_contract, price)
    else:
        return None


# TODO: stuff will need to be moved from here
def pretty_print_last_actions(token_ticker, pair_contract, graphql_client_uni, graphqlclient_eth, uni_wrapper, options=None):
    paired_with = get_pair_info_from_pair_contract(token_ticker, pair_contract, uni_wrapper, graphql_client_uni, graphqlclient_eth)
    if paired_with is None:
        pprint.pprint("Error fetching pair for token " + token_ticker + " and pair contract " + pair_contract)
        return None
    all_actions_sorted, start_message = get_last_actions(pair_contract, token_ticker, paired_with, graphql_client_uni, options)

    amount = 5
    # check if amount specified in options
    if options is not None:
        for option in options:
            if option.isdigit():
                amount = min([29, int(option)])
                start_message = start_message.replace("Last 5", "Last " + str(amount))

    all_actions_light = all_actions_sorted[0:amount]
    if options is not None:
        if "address" in options or "addr" in options or "a" in options:
            strings = list(map(lambda x: x.to_string(), all_actions_light))
        else:
            strings = list(map(lambda x: x.to_string(), all_actions_light))
    else:
        strings = list(map(lambda x: x.to_string(), all_actions_light))
    string = '\n'.join(strings)
    return start_message + string


def pretty_print_monitor_last_actions(acceptable_ts, token_ticker, pair_contract, graphql_client_uni, graphqlclient_eth, uni_wrapper, options=["whale"], amount=30, blacklist=[]):
    paired_with = get_pair_info_from_pair_contract(token_ticker, pair_contract, uni_wrapper, graphql_client_uni, graphqlclient_eth)
    if paired_with is None:
        pprint.pprint("Error fetching pair for token " + token_ticker + " and pair contract " + pair_contract)
        return None
    all_actions_sorted, start_message = get_last_actions(pair_contract, token_ticker, paired_with, graphql_client_uni, options, amount)
    all_actions_kept = [x for x in all_actions_sorted if x.timestamp > acceptable_ts and x.id not in blacklist]
    if 'print_complex' in options:
        actions_with_bots = detect_bots(all_actions_kept)
        all_actions_kept_sorted = sorted(actions_with_bots, key=lambda x: x.value_raw_paired_with(), reverse=True)
        strings = list(map(lambda x: x.to_string_complex(), all_actions_kept_sorted))
        if len(strings) == 0:
            return None, []
        else:
            ids = [x.id for x in all_actions_kept]
            return '\n\n'.join(strings), ids

    else:
        strings = list(map(lambda x: x.to_string('🐋', with_date=False), all_actions_kept))
    if len(strings) == 0:
        return None
    else:
        return '\n'.join(strings)


def monitor_last_actions_raw(acceptable_ts, token_ticker, pair_contract, graphql_client_uni, graphqlclient_eth, uni_wrapper, options=["whale"], amount=30, blacklist=[]):
    paired_with = get_pair_info_from_pair_contract(token_ticker, pair_contract, uni_wrapper, graphql_client_uni, graphqlclient_eth)
    if paired_with is None:
        pprint.pprint("Error fetching pair for token " + token_ticker + " and pair contract " + pair_contract)
        return None
    all_actions_sorted, start_message = get_last_actions(pair_contract, token_ticker, paired_with, graphql_client_uni, options, amount)
    all_actions_kept = [x for x in all_actions_sorted if x.timestamp > acceptable_ts and x.id not in blacklist]
    if 'print_complex' in options:
        actions_with_bots = detect_bots(all_actions_kept)
        all_actions_kept_sorted = sorted(actions_with_bots, key=lambda x: x.value_raw_paired_with(), reverse=True)
        strings = list(map(lambda x: x.to_string_complex(), all_actions_kept_sorted))
        if len(strings) == 0:
            return None, []
        else:
            ids = [x.id for x in all_actions_kept]
            return '\n\n'.join(strings), ids

    else:
        strings = list(map(lambda x: x.to_string('🐋', with_date=False), all_actions_kept))
    if len(strings) == 0:
        return None
    else:
        return '\n'.join(strings)


@dataclass(frozen=True)
class GasSpent:
    amountTx: int
    eth_spent: float
    total_gas: int
    avg_gas_price: float
    success: (int, int)
    fail: (int, int)
    since: int

    def to_string(self):
        eth_price_now = get_eth_price_now()
        amount_spent_on_gas_raw = keep_significant_number_float(self.eth_spent, 2)
        amount_spent_on_gas_usd = keep_significant_number_float(amount_spent_on_gas_raw * eth_price_now, 2)
        avg_gas_cost = keep_significant_number_float(self.avg_gas_price, 1)
        eth_success = keep_significant_number_float(self.success[1] / 10 ** 18, 3)
        eth_fail = keep_significant_number_float(self.fail[1] / 10 ** 18, 3)
        eth_success_dollar = keep_significant_number_float(eth_success * eth_price_now, 3)
        eth_fail_dollar = keep_significant_number_float(eth_fail * eth_price_now, 3)
        beginning_message = "" if self.since is None else "In the last " + str(self.since) + " days:\n"
        message = "Total number of tx: " + str(self.amountTx) + '\n' \
                  + "Amount spent on gas: Ξ" + str(amount_spent_on_gas_raw) + " = $" + str(
            amount_spent_on_gas_usd) + '\n' \
                  + "Average gas spent per tx = " + str(avg_gas_cost) + '\n' \
                  + "Tx successful = " + str(self.success[0]) + " -> Ξ" + str(eth_success) + " spent in gas ($" + str(
            eth_success_dollar) + ')\n' \
                  + "Tx failed = " + str(self.fail[0]) + " -> Ξ" + str(eth_fail) + " spent in gas ($" + str(
            eth_fail_dollar) + ')'
        return beginning_message + message


def get_gas_spent(address, options=None):
    url = "https://api.etherscan.io/api?module=account&action=txlist&address=$ADDR&startblock=0&endblock=99999999&sort=asc&apikey=$APIKEY"
    url_prepared = url.replace("$APIKEY", etherscan_api_key).replace("$ADDR", address)
    results = requests.get(url_prepared).json()
    txs = results['result']
    total_gas_success = 0
    total_gas_fail = 0
    error_number, success_number = 0, 0
    total_cost_success = 0
    total_cost_fail = 0
    avg_price = 0
    since = None
    ts_min = 0
    if options is not None:
        for option in options:
            if option.isdigit():
                since = int(option)
                ts_min = round(time.time() - 3600 * 24 * since)
    for tx in txs:
        if int(tx['timeStamp']) < ts_min:
            continue
        gas_price_tx = int(tx['gasPrice'])
        gas_used = int(tx['gasUsed'])
        avg_price += gas_price_tx
        if int(tx['isError']) == 1:
            error_number += 1
            total_gas_fail += gas_used
            total_cost_fail += gas_used * gas_price_tx
        else:
            success_number += 1
            total_gas_success += gas_used
            total_cost_success += gas_used * gas_price_tx
    avg_price = round(avg_price / len(txs))
    total_gas = total_gas_success + total_cost_fail
    avg_price_rounded = avg_price / 10 ** 9
    total_cost = ((total_cost_fail + total_cost_success) / 10 ** 18)
    return GasSpent(success_number + error_number, total_cost, total_gas, avg_price_rounded, (success_number, total_cost_success),
                    (error_number, total_cost_fail), since)


def get_balance_wallet_request(wallet):
    url = "https://api.ethplorer.io/getAddressInfo/$WALLET?apiKey=$API_KEY_ETHEXPLORER" \
        .replace('$WALLET', wallet) \
        .replace('$API_KEY_ETHEXPLORER', API_KEY_ETHEXPLORER)
    res = requests.get(url)
    # pprint(res)
    return res.json()


def get_token_info(contract):
    url = "https://api.ethplorer.io/getTokenInfo/$CONTRACT?apiKey=$API_KEY_ETHEXPLORER" \
        .replace('$CONTRACT', contract) \
        .replace('$API_KEY_ETHEXPLORER', API_KEY_ETHEXPLORER)
    res = requests.get(url)
    # pprint(res)
    return res.json()


def main():
    token = "0x9248c485b0b80f76da451f167a8db30f33c70907"
    if util.is_checksumaddr(token):
        pprint.pprint("cool")
    else:
        pprint.pprint("not cool")


if __name__ == '__main__':
    main()
