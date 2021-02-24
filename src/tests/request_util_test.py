import requests
from pprint import pprint
from dataclasses import dataclass



# TODO: remove that
import decimal
import locale

# create a new context for this task
ctx = decimal.Context()

# 20 digits should be enough for everyone :D
ctx.prec = 20

def keep_significant_number_float(float_to_keep: float, number: int):
    a = round(float_to_keep, number)
    str_action = "{:.$AMOUNTf}".replace('$AMOUNT', str(number))
    return a  # float(str_action.format(float_to_keep))


def float_to_str(f):
    """
    Convert the given float to a string,
    without resorting to scientific notation
    """
    d1 = ctx.create_decimal(repr(f))
    return format(d1, 'f')

# convert int to nice string: 1234567 => 1 234 567
def number_to_beautiful(nbr):
    return locale.format_string("%d", nbr, grouping=True).replace(",", " ")

def pretty_number(num):
    if round(num) > 10:
        res = number_to_beautiful(round(num))
    elif 0.01 < num < 10.01:
        res = str(keep_significant_number_float(num, 3))  # [0:5]
    else:
        res = str(keep_significant_number_float(num, 6))  # float_to_str(num)[0:10]
    return res


@dataclass(frozen=True)
class TokenOwned:
    name: str
    ticker: str
    address: str
    amount_owned: float
    value_usd: float

    def get_amount_usd_token(self, default=None):
        if self.value_usd is not None:
            return self.value_usd * self.amount_owned
        else:
            return default

    def to_string(self, complex=False):
        top = "*(" + self.ticker[:6] + ") " + self.name[:15] + "*"
        if self.get_amount_usd_token() is not None:
            top += "   -   `$" + pretty_number(self.get_amount_usd_token()) + "`"
        bottom = "`" + pretty_number(self.amount_owned) + "` " + self.ticker[:6]
        if self.value_usd is not None:
            bottom += " - `$" + pretty_number(self.value_usd) + "`"
        return top + '\n' + bottom

    def get_percent(self, total_usd):
        return self.get_amount_usd_token(0.0) / total_usd



def get_balance_wallet(wallet: str):
    url = "https://api.ethplorer.io/getAddressInfo/$WALLET?apiKey=freekey".replace('$WALLET', wallet)
    res = requests.get(url)
    # pprint(res)
    res = res.json()
    # pprint(res)
    eth = res['ETH']
    eth_token = TokenOwned(name='Ether',
                           ticker='ETH',
                           address='',
                           amount_owned=float(eth['balance']),
                           value_usd=float(eth['price']['rate']))
    tokens_that_were_owned = res['tokens']
    tokens_owned = []
    for token in tokens_that_were_owned:
        if token['balance'] != 0:
            token_owned_raw = float(token['balance'])
            maybe_token_descr = token['tokenInfo']
            if maybe_token_descr is not None:
                if 'decimals' not in maybe_token_descr:
                    pass
                elif maybe_token_descr['decimals'] == 0 or 'name' not in maybe_token_descr:
                    pass
                else:
                    pprint(maybe_token_descr)
                    decimals = int(maybe_token_descr['decimals'])
                    amount_owned = token_owned_raw / 10 ** decimals
                    maybe_price_unit_token = maybe_token_descr['price']
                    maybe_price_token_unit_usd = get_price_token(maybe_token_descr)
                    actual_token = TokenOwned(name=maybe_token_descr['name'],
                                              ticker=maybe_token_descr['symbol'],
                                              address=maybe_token_descr['address'],
                                              amount_owned=amount_owned,
                                              value_usd=maybe_price_token_unit_usd)
                    tokens_owned.append(actual_token)
    tokens_owned_sorted = [eth_token] + sorted(tokens_owned, key=lambda x: x.get_amount_usd_token(0.0), reverse=True)
    total_value = 0
    for token in tokens_owned_sorted:
        total_value += token.get_amount_usd_token(0.0)
    values_usd = [(x.ticker, x.get_amount_usd_token(0.0)) for x in tokens_owned_sorted if x.get_percent(total_value) > 0.03]
    values_raw = [x[1] for x in values_usd]
    values_name = [x[0] for x in values_usd]

    # Pie chart, where the slices will be ordered and plotted counter-clockwise:
    missing_amount = total_value - sum(values_raw)
    values_raw += [missing_amount]
    values_name += ['Others']
    import plotly.express as px
    import pandas as pd
    d = {'amount_usd': values_raw, 'label': values_name}
    df = pd.DataFrame(data=d)
    pprint(df)
    fig = px.pie(df, values='amount_usd', names='label',
                 color_discrete_sequence=px.colors.sequential.Agsunset)  # https://plotly.com/python/builtin-colorscales/
    fig.update_traces(texttemplate="%{label}<br>%{percent}<br>%{value:$.2f}")
    fig.update_layout(uniformtext_minsize=16, uniformtext_mode='hide')
    fig.show()


def get_price_token(maybe_token):
    maybe_price_unit_token = maybe_token['price']
    if maybe_price_unit_token is not False:
        if maybe_price_unit_token['currency'] == "USD":
            price_token_unit_usd = float(maybe_price_unit_token['rate'])
            return price_token_unit_usd
    return None


def get_amount_usd_token(value, amount):
    if value is not None:
        return value * amount
    else:
        return None



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
        eth_price_now = 550# get_eth_price_now()
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

import time

def get_gas_spent_test(address, options=None):
    url = "https://api.etherscan.io/api?module=account&action=txlist&address=$ADDR&startblock=0&endblock=99999999&sort=asc&apikey=$APIKEY"
    url_prepared = url.replace("$APIKEY", 'DX6N2XZ3A45NY4VFAKHIKRAR7KXVYYUN91').replace("$ADDR", address)
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
                ts_min = round(time.time() - 3600 * since)
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


url_graphex_backend = "https://chartex.pro/api/history?symbol=$EXCHANGE%3A$SYMBOL&resolution=$RESOLUTION&from=$TFROM&to=$TTO"

jwt='''token=9e2c54ee-d1d5-4605-91fc-25ffabfae31e; chartex_connection_string=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhZGRyZXNzIjoiMHhkMDg1MTdjZDAzNzJjRDEyQjcxMGE1NTRGNTAyNWNGRDQxOUI0M2ZGIiwiYmFsYW5jZSI6IjEwMTE3LjcyIiwidGllciI6ImV4cGVydCIsImlhdCI6MTYwNjI0MTI3NH0.P13JNbjNA--Mwd2SK0GRGU777rCmZMmBJvWEVlUCv4E'''


def create_url_request_graphex(symbol, resolution, t_from, t_to, exchange):
    return url_graphex_backend \
        .replace('$EXCHANGE', exchange) \
        .replace("$SYMBOL", symbol) \
        .replace("$RESOLUTION", str(resolution)) \
        .replace("$TFROM", str(t_from)) \
        .replace("$TTO", str(t_to))


def get_graphex_data(token, resolution, t_from, t_to, with_exchange=True, exchange='UNISWAP'):

    symbol = token
    url = create_url_request_graphex(symbol, resolution, t_from, t_to, exchange)
    name = 'cookie'
    header = {name: jwt}
    resp = requests.get(url, headers=header)
    return resp


def get_chartex_symbol(symbol):
    url = 'https://chartex.pro/api/symbols?symbol=WYNAUT'
    name = 'cookie'
    header = {name: jwt}
    resp = requests.get(url, headers=header)
    return resp


if __name__ == '__main__':
    token = 'BSC_PANCAKESWAP:wynaut'
    res = get_chartex_symbol(token)
    jres = res.json()
    pprint(jres)
    ticker = jres['ticker']
    print(ticker)

    t_to = int(time.time())
    t_from = int(time.time()) - 3600 * 24 * 3
    exchange = 'BSC_PANCAKESWAP'
    res = get_graphex_data("wynaut", 5, t_from, t_to, exchange)
    pprint(res.text)
    pprint(res.status_code)
    res2 = res.json()
    pprint(res2)

    # res = get_gas_spent_test("0x56B082C827b61dD481A06240e604a13eD4738Ec4", ["5"])
    # res = get_balance_wallet("0x56B082C827b61dD481A06240e604a13eD4738Ec4")
    # pprint(res.to_string())
    # url = "https://api.ethplorer.io/getTokenInfo/0xd08517cd0372cD12B710a554F5025cFD419B43fF"
    # res = requests.get(url).json()
    # pprint(res)