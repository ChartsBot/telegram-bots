import time

import os
import sys

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots/src')

import libraries.commands_util as commands_util
import libraries.graphs_util as graphs_util
import libraries.scrap_websites_util as scrap_websites_util
import libraries.requests_util as requests_util
import libraries.util as util
import requests
from libraries.util import float_to_str
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Updater, CommandHandler, CallbackContext
from libraries.images import Ocr
from libraries.common_values import *
import libraries.web3_calls as web3_util
import csv
import datetime
import matplotlib
import matplotlib.dates
import matplotlib.pyplot as plt
from web3 import Web3
from pprint import pprint
from dataclasses import dataclass

API_KEY_ETHEXPLORER = os.environ.get('API_KEY_ETHEXPLORER')

last_time_checked_4chan = 0


def send_candlestick_pyplot(token, charts_path, k_days, k_hours, t_from, t_to, txt: str = None, options=None, with_ad=None):
    print("requesting coin " + token + " from " + str(k_days) + " days and " + str(k_hours) + " hours")

    path = charts_path + token + '.png'
    last_price = graphs_util.print_candlestick(token, t_from, t_to, path, txt, options)

    callback_message = 'refresh_chart_' + "h:" + str(k_hours) + "d:" + str(k_days) + "t:" + token
    callback_message_1_w = 'refresh_chart_' + "h:" + str(0) + "d:" + str(7) + "t:" + token
    callback_message_1_d = 'refresh_chart_' + "h:" + str(0) + "d:" + str(1) + "t:" + token
    callback_message_1_m = 'refresh_chart_' + "h:" + str(0) + "d:" + str(30) + "t:" + token
    callback_message_2_h = 'refresh_chart_' + "h:" + str(2) + "d:" + str(0) + "t:" + token
    refresh_button = InlineKeyboardButton('Refresh ⌛', callback_data=callback_message)
    # delete_button = InlineKeyboardButton('Delete 🗑️', callback_data='delete_message')
    button_list_chart = [[
                            refresh_button
                            # delete_button
                         ],
                         [
                            InlineKeyboardButton('2 hours', callback_data=callback_message_2_h),
                            InlineKeyboardButton('1 day', callback_data=callback_message_1_d),
                            InlineKeyboardButton('1 week', callback_data=callback_message_1_w),
                            InlineKeyboardButton('1 month', callback_data=callback_message_1_m)
                         ]]
    reply_markup_chart = InlineKeyboardMarkup(button_list_chart)
    msg_time = " " + str(k_days) + " day(s) " if k_days > 0 else " last " + str(k_hours) + " hour(s) "
    if with_ad is None:
        ad = util.get_ad()
    else:
        ad = with_ad
    message = "<b>" + token + "</b>" + msg_time + "<code>$" + float_to_str(last_price)[0:10] + "</code>\n" + ad + ""

    return message, path, reply_markup_chart


# sends the current biz threads
def get_biz_no_meme(update: Update, context: CallbackContext, re_4chan):
    chat_id = update.message.chat_id
    threads_ids = scrap_websites_util.get_biz_threads(re_4chan)

    base_url = "boards.4channel.org/biz/thread/"
    message = """Plz go bump the /biz/ threads:
"""
    for thread_id in threads_ids:
        excerpt = thread_id[2] + " | " + thread_id[1]
        message += base_url + str(thread_id[0]) + " -- " + excerpt[0: 100] + "[...] \n"
    if not threads_ids:
        print("sent reminder 4chan /biz/")
        meme_caption = "There hasn't been a Rotten /biz/ thread for a while. Plz go make one."
        context.bot.send_message(chat_id=chat_id, text=meme_caption)
    else:
        context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)


# TODO: rewrite it so that it's no longer a slow piece of crap
def get_price(contract, pair_contract, graphclient_eth, graphclient_uni, name, decimals, uni_wrapper):
    print("getting price for contract: " + str(contract))
    t0 = time.time()
    (derivedETH_7d, token_price_7d_usd, derivedETH_1d, token_price_1d_usd, derivedETH_now,
     token_price_now_usd) = requests_util.get_price_raw(graphclient_eth, graphclient_uni, contract)
    print("getting price for contract took " + str(round(time.time() - t0)))

    supply_cap_token = requests_util.get_supply_cap_raw(contract, decimals)
    util.write_supply_cap(round(supply_cap_token), name)
    supply_cat_pretty = str(util.number_to_beautiful(round(supply_cap_token)))
    market_cap = util.number_to_beautiful(int(float(supply_cap_token) * token_price_now_usd))

    if pair_contract == "" or pair_contract is None:
        pair = web3_util.does_pair_token_eth_exist(contract, uni_wrapper)
        print("pair found = " + str(pair))
        if pair is not None:
            vol_24h = requests_util.get_volume_24h(graphclient_uni, pair.lower())
        else:
            vol_24h = 0
    else:
        pair = pair_contract
        vol_24h = requests_util.get_volume_24h(graphclient_uni, pair.lower())

    if token_price_7d_usd is not None and token_price_7d_usd != 0.0:
        var_7d = - int(((token_price_7d_usd - token_price_now_usd) / token_price_7d_usd) * 100) if token_price_7d_usd > token_price_now_usd else int(((token_price_now_usd - token_price_7d_usd) / token_price_7d_usd) * 100)
        var_7d_str = "+" + str(var_7d) + "%" if var_7d > 0 else str(var_7d) + "%"
        var_7d_msg = "\n7D :  " + var_7d_str
    else:
        var_7d_msg = ""
    if token_price_1d_usd is not None and token_price_1d_usd != 0.0:
        var_1d = - int(((token_price_1d_usd - token_price_now_usd) / token_price_1d_usd) * 100) if token_price_1d_usd > token_price_now_usd else int(((token_price_now_usd - token_price_1d_usd) / token_price_1d_usd) * 100)
        var_1d_str = "+" + str(var_1d) + "%" if var_1d > 0 else str(var_1d) + "%"
        var_1d_msg = "\n24H:  " + var_1d_str
    else:
        var_1d_msg = ""

    print("vol 24: " + str(vol_24h))

    vol_24_pretty = util.number_to_beautiful(vol_24h)

    msg_vol_24 = "\nVol 24H = $" + vol_24_pretty if vol_24_pretty != "0" else ""

    holders = requests_util.get_number_holder_token(contract)
    holders_str = "\nHolders = " + str(holders) if holders != -1 else ""
    links = '<a href="etherscan.io/token/' + contract + '">Etherscan</a>|<a href="https://app.uniswap.org/#/swap?inputCurrency=' + contract + '">Uni</a>'
    ad = util.get_ad()
    message = "<b>" + name + '</b><code>' \
              + "\nETH: Ξ" + float_to_str(derivedETH_now)[0:10] \
              + "\nUSD: $" + float_to_str(token_price_now_usd)[0:10] \
              + var_1d_msg \
              + var_7d_msg \
              + "\n" \
              + msg_vol_24 \
              + "\nS.  Cap = " + supply_cat_pretty \
              + "\nM.  Cap = $" + market_cap \
              + holders_str + "</code>"\
              + "\n" + links \
              + "\n" + ad
    return message


def get_price_gecko(name):
    price_usd_now, change_percentage, volume_24_usd, mcap_usd = requests_util.get_price_now_full(name)
    price_usd_7_d = requests_util.get_price_at(name, 7)
    ad = util.get_ad()

    var_7d = - int(((price_usd_7_d - price_usd_now) / price_usd_7_d) * 100) if price_usd_7_d > price_usd_now else int(((price_usd_now - price_usd_7_d) / price_usd_7_d) * 100)
    var_7d_str = "+" + str(var_7d) + "%" if var_7d > 0 else str(var_7d) + "%"
    message = "<b>" + name + '</b><code>' \
              + "\nUSD: $" + util.pretty_number(price_usd_now) \
              + "\n24H:  " + str(change_percentage)[0:5] + "%"  \
              + "\n7D :  " + var_7d_str \
              + "\n" \
              + "\nVol 24H = $" + util.number_to_beautiful(volume_24_usd) \
              + "\nM.  Cap = $" + util.number_to_beautiful(mcap_usd) + '</code>' \
              + "\n" + ad
    return message


def get_help(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    message = """<b>How to use the bot:</b>
<b>/price:</b> display the price of the token as well as relevant metrics
<b>/chart:</b> display a candlestick chart of the last 24 hours.
To show the last 14 days: use /chart 14 d
To show the last 7 hours: use /chart 7 h
A problem? Suggestion? Want this bot for your token? -> contact @ rotted_ben"""
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')


def download_image(update: Update, context: CallbackContext, path):
    image = context.bot.getFile(update.message.photo[-1])
    file_id = str(image.file_id)
    print("file_id: " + file_id)
    img_path = path + file_id + ".png"
    image.download(img_path)
    return img_path


def ocr_image(update: Update, context: CallbackContext, tmp_path):
    img_path = download_image(update, context, tmp_path)
    ocr = Ocr(img_path)
    text_in_ocr = ocr.start_ocr().replace('\n', ' ')
    print("recognized text = " + text_in_ocr)
    return text_in_ocr


def strp_date(raw_date):
    return datetime.datetime.strptime(raw_date, '%m/%d/%Y,%H:%M:%S')


def print_chart_supply_single_token(dates_raw, supply, name, chart_path):
    dates = matplotlib.dates.date2num(dates_raw)
    cb91_green = '#47DBCD'
    plt.style.use('dark_background')

    matplotlib.rcParams.update({'font.size': 22})
    f = plt.figure(figsize=(16, 9))

    ax = f.add_subplot(111)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plot1 = ax.plot_date(dates, supply, 'r', label=name)

    ax.set_ylabel(name)

    plots = plot1
    labs = [l.get_label() for l in plots]
    ax.legend(plots, labs, bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
              ncol=2, mode="expand", borderaxespad=0.)

    plt.gcf().autofmt_xdate()
    plt.savefig(chart_path, bbox_inches='tight', dpi=300)
    plt.close(f)


def send_supply_single_pyplot(supply_file_path, k_days, k_hours, name, chart_path):

    list_time_supply = []

    with open(supply_file_path, newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=' ', quotechar='|')
        for row in reader:
            list_time_supply.append((row[0], row[1]))

    now = datetime.datetime.utcnow()

    filtered_values = [x for x in list_time_supply if
                       now - strp_date(x[0]) < datetime.timedelta(days=k_days, hours=k_hours)]

    dates_pure = keep_dates(filtered_values)
    supply = [int(round(float(value[1]))) for value in filtered_values]

    print_chart_supply_single_token(dates_pure, supply, name, chart_path)
    current_supply_str = supply[-1]
    return current_supply_str


def print_chart_supply_two_tokens(dates_raw, supply_t1, name_t1, supply_t2, name_t2, chart_path):
    dates = matplotlib.dates.date2num(dates_raw)
    cb91_green = '#47DBCD'
    plt.style.use('dark_background')

    matplotlib.rcParams.update({'font.size': 22})
    f = plt.figure(figsize=(16, 9))

    ax = f.add_subplot(111)
    ax.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plot1 = ax.plot_date(dates, supply_t1, 'r', label=name_t1)

    ax2 = ax.twinx()
    ax2.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda x, p: format(int(x), ',')))
    plot2 = ax2.plot_date(dates, supply_t2, cb91_green, label=name_t2)

    ax.set_ylabel(name_t1)
    ax2.set_ylabel(name_t2)

    plots = plot1 + plot2
    labs = [l.get_label() for l in plots]
    ax.legend(plots, labs, bbox_to_anchor=(0., 1.02, 1., .102), loc='lower left',
              ncol=2, mode="expand", borderaxespad=0.)

    plt.gcf().autofmt_xdate()
    plt.savefig(chart_path, bbox_inches='tight', dpi=300)
    plt.close(f)


def send_supply_two_pyplot(supply_file_path, k_days, k_hours, name_t1, name_t2, chart_path):

    list_time_supply = []

    with open(supply_file_path, newline='') as csv_file:
        reader = csv.reader(csv_file, delimiter=' ', quotechar='|')
        for row in reader:
            list_time_supply.append((row[0], row[1], row[2]))

    now = datetime.datetime.utcnow()

    filtered_values = [x for x in list_time_supply if
                       now - strp_date(x[0]) < datetime.timedelta(days=k_days, hours=k_hours)]

    dates_pure = keep_dates(filtered_values)
    supply_t1 = [int(round(float(value[1]))) for value in filtered_values]
    supply_t2 = [int(round(float(value[2]))) for value in filtered_values]

    print_chart_supply_two_tokens(dates_pure, supply_t1, name_t1, supply_t2, name_t2, chart_path)
    current_t1_str = supply_t1[-1]
    current_t2_str = supply_t2[-1]
    return current_t1_str, current_t2_str


# util for get_chart_pyplot
def keep_dates(values_list):
    dates_str = []
    for values in values_list:
        dates_str.append(values[0])

    dates_datetime = []
    for date_str in dates_str:
        date_datetime = datetime.datetime.strptime(date_str, '%m/%d/%Y,%H:%M:%S')
        dates_datetime.append(date_datetime)
    return dates_datetime


def convert_to_usd_raw(amount, currency_ticker, graphqlclient_uni, graphqlclient_eth):
    if currency_ticker.lower() == 'eth':
        eth_price = requests_util.get_eth_price_now()
        return amount * eth_price
    elif currency_ticker.lower() == "lambo":
        return float(lambo_price_usd) * amount
    else:
        contract_from_ticker = requests_util.get_token_contract_address(currency_ticker)
        (derivedETH_now, token_price_now_usd) = requests_util.get_price_raw_now(graphqlclient_eth, graphqlclient_uni, contract_from_ticker)
        total = amount * token_price_now_usd
        return total


def convert_to_usd(amount, currency_ticker, graphqlclient_uni, graphqlclient_eth):
    total = convert_to_usd_raw(amount, currency_ticker, graphqlclient_uni, graphqlclient_eth)
    return util.number_to_beautiful(round(total)) if round(total) > 10 else float_to_str(total)


def convert_to_something(query_received, graphql_client_uni, graphql_client_eth):
    if len(query_received) == 3:
        ticker_req = query_received[2]
        amount = float(query_received[1])
        res = convert_to_usd(amount, ticker_req, graphql_client_uni, graphql_client_eth)
        message = str(amount) + " " + ticker_req + " = " + res + " USD"
        return message
    elif len(query_received) == 4:
        ticker_req = query_received[2]
        amount = float(query_received[1])
        ticker_to = query_received[3]
        res_req = convert_to_usd_raw(1, ticker_req, graphql_client_uni, graphql_client_eth)

        res_ticker_to = convert_to_usd_raw(1, ticker_to, graphql_client_uni, graphql_client_eth)
        res = amount * (res_req / res_ticker_to)
        res_req_usd_str = util.number_to_beautiful(round(res_req * amount)) if round(res_req * amount) > 10 else util.float_to_str(res_req * amount)
        res_str = util.number_to_beautiful(round(res)) if round(res) > 10 else util.float_to_str(res)[0:10]
        message = str(amount) + " " + ticker_req + " = " + res_req_usd_str + " USD or " + res_str + " " + ticker_to
        return message
    else:
        return "Wrong format. Please use /convert AMOUNT CURRENCY (optional: CURRENCY_TO)"


def get_balance_token_wallet(w3, wallet, ticker, graphqlclient_uni, graphqlclient_eth):
    print(str(wallet))
    print(str(ticker))
    contract_from_ticker = requests_util.get_token_contract_address(ticker)
    amount = web3_util.get_balance_token_wallet_raw(w3, wallet, contract_from_ticker)
    amount_usd = convert_to_usd(amount, ticker, graphqlclient_uni, graphqlclient_eth)  # TODO: add contract_from_ticker in convert_to_usd to avoid double call
    return amount, amount_usd


def get_gas_price():
    gas_price_raw = requests_util.get_gas_price_raw()
    asap = int(gas_price_raw['fastest'] / 10)
    fast = int(gas_price_raw['fast'] / 10)
    average = int(gas_price_raw['average'] / 10)
    low = int(gas_price_raw['safeLow'] / 10)
    return asap, fast, average, low


def get_last_actions_token_in_eth_pair(token_ticker, uni_wrapper, graphql_client_uni, contract: str = None, options=None):
    print("options: ")
    pprint(options)
    token_contract = contract if contract is not None else requests_util.get_token_contract_address(token_ticker)
    pair = web3_util.does_pair_token_eth_exist(token_contract, uni_wrapper)
    print("pair: " + str(pair))
    if pair is None:
        return None
    else:
        strings = requests_util.pretty_print_last_actions(pair.lower(), graphql_client_uni, options)
        return strings


def get_gas_spent(address):
    if not Web3.isAddress(address.lower()):
        return "Address " + str(address.lower()) + " not valid."
    else:
        gas_spent = requests_util.get_gas_spent(address)
        return gas_spent.to_string()


# Todo: put that somewhere else
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
            top += "   -   <code>$" + util.pretty_number(self.get_amount_usd_token()) + "</code>"
        bottom = "<code>" + util.pretty_number(self.amount_owned) + "</code> " + self.ticker[:6]
        if self.value_usd is not None:
            bottom += " - <code>$" + util.pretty_number(self.value_usd) + "</code>"
        return top + '\n' + bottom


def get_balance_wallet(wallet: str, simple=False):
    url = "https://api.ethplorer.io/getAddressInfo/$WALLET?apiKey=$API_KEY_ETHEXPLORER"\
        .replace('$WALLET', wallet)\
        .replace('$API_KEY_ETHEXPLORER', API_KEY_ETHEXPLORER)
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
    total_value = eth_token.get_amount_usd_token(0.0)
    for token in tokens_owned:
        total_value += token.get_amount_usd_token(0.0)
    message = "<b>Total value of wallet: </b><code>" + util.pretty_number(total_value) + "</code>"
    if simple:
        tokens_owned_sorted = [x for x in tokens_owned if x.get_amount_usd_token(0.0) > 0.01]
        tokens_owned_sorted = [eth_token] + sorted(tokens_owned_sorted, key=lambda x: x.get_amount_usd_token(0.0), reverse=True)
        message_top = "Overview of wallet " + wallet[0:10] + "...:\n"
    else:
        message_top = "Full view of wallet " + wallet[0:10] + "...:\n"
    for token in tokens_owned_sorted:
        message += token.to_string() + "\n"
    return message_top + message


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
    print("coucou")