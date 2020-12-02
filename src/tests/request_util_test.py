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
        top = "<b>(" + self.ticker[:6] + ") " + self.name[:15] + "</b>"
        if self.get_amount_usd_token() is not None:
            top += "   -   <code>$" + pretty_number(self.get_amount_usd_token()) + "</code>"
        bottom = "<code>" + pretty_number(self.amount_owned) + "</code> " + self.ticker[:6]
        if self.value_usd is not None:
            bottom += " - <code>$" + pretty_number(self.value_usd) + "</code>"
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
                if maybe_token_descr['decimals'] == 0 or 'name' not in maybe_token_descr:
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


if __name__ == '__main__':
    get_balance_wallet("0x56B082C827b61dD481A06240e604a13eD4738Ec4")
    # url = "https://api.ethplorer.io/getTokenInfo/0xd08517cd0372cD12B710a554F5025cFD419B43fF"
    # res = requests.get(url).json()
    # pprint(res)