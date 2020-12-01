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



def get_balance_wallet(wallet: str):
    url = "https://ethplorer.io/service/service.php?data=$WALLET&showTx=all".replace('$WALLET', wallet)
    res = requests.get(url).json()
    tokens_that_were_owned = res['tokens']
    tokens_owned = []
    for token in res['balances']:
        if token['balance'] != 0:
            token_addr = token['contract']
            token_owned_raw = float(token['balance'])
            maybe_token_descr = tokens_that_were_owned.get(token_addr)
            if maybe_token_descr is not None:
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
    tokens_owned_sorted = sorted(tokens_owned, key=lambda x: x.get_amount_usd_token(0.0), reverse=True)
    for token in tokens_owned_sorted:
        print(token.to_string())


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
    get_balance_wallet("0xd08517cd0372cD12B710a554F5025cFD419B43fF")