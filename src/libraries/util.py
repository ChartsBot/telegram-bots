import locale
import os
import random
import decimal
import hashlib
from binascii import hexlify
import re
import html
from web3 import Web3
from py_w3c.validators.html.validator import HTMLValidator

BASE_PATH = os.environ.get('BASE_PATH')

from datetime import datetime

supply_file_path = BASE_PATH + 'log_files/chart_bot/supply_log_$TICKER.txt'
cleanr = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')


def get_ad():
    if random.randint(0, 100) > 65:
        ads_file_path = BASE_PATH + "ads/chart_ads.txt"
        with open(ads_file_path) as f:
            content = f.readlines()
        # you may also want to remove whitespace characters like `\n` at the end of each line
        content = [x.strip() for x in content]
        return random.choice(content)
    else:
        return ""


def build_menu(buttons, n_cols, header_buttons=None, footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu


# create a new context for this task
ctx = decimal.Context()

# 20 digits should be enough for everyone :D
ctx.prec = 20


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


def create_href_str(url, message):
    return "<a href=\"" + url + "\">" + message + "</a>"


def get_random_string(length):
    # put your letters in the following string
    sample_letters = 'abcdefghi'
    result_str = ''.join((random.choice(sample_letters) for i in range(length)))
    return result_str


def create_and_send_vote(ticker, method, username, zerorpc_client):
    now_ts = round(datetime.now().timestamp())
    id_vote = random.randint(0, 1000000000000)
    hashed_username = get_hashed_uname(username)
    vote = (id_vote, hashed_username, now_ts, ticker.upper(), method)
    zerorpc_client.add_vote(vote)


def get_hashed_uname(username):
    hex_username = hexlify(username.encode())
    return hashlib.sha512(hex_username + hex_username).hexdigest()


def keep_significant_number_float(float_to_keep: float, number: int):
    a = round(float_to_keep, number)
    str_action = "{:.$AMOUNTf}".replace('$AMOUNT', str(number))
    return a  # float(str_action.format(float_to_keep))


def get_banner_txt(rpc_client):
    # if random.randrange(10) > 7:
    #     return get_ad()
    # else:
    return rpc_client.view_trending_simple()


def write_supply_cap(supply_cap: int, token_name: str):
    path = supply_file_path.replace("$TICKER", token_name.upper())
    with open(path, "a") as supply_file:
        time_now = datetime.now()
        date_time_str = time_now.strftime("%m/%d/%Y,%H:%M:%S")
        message_to_write = date_time_str + " " + str(supply_cap) + "\n"
        supply_file.write(message_to_write)


def cleanhtml(raw_html):
    cleantext = re.sub(cleanr, '', raw_html)
    return html.unescape(cleantext)


def to_checksumaddr(addr):
    return Web3.toChecksumAddress(addr)

def is_checksumaddr(addr):
    try:
        Web3.toChecksumAddress(addr)
        return True
    except Exception:
        return False


def get_change(current, previous):
    if current == previous:
        return 0
    try:
        return (abs(current - previous) / previous) * 100.0
    except ZeroDivisionError:
        return 0
