import locale
import sys
import os
from gevent import monkey
monkey.patch_all()  # REALLY IMPORTANT: ALLOWS ZERORPC AND TG TO WORK TOGETHER

from twython import Twython

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots/src')

from graphqlclient import GraphQLClient
import time
from datetime import datetime
import pprint
import os.path
import re

from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, Filters, MessageHandler
from telegram.error import ChatMigrated
import libraries.web3_calls as web3_util


import libraries.general_end_functions as general_end_functions
import libraries.requests_util as requests_util
import libraries.util as util
import libraries.scrap_websites_util as scrap_websites_util
from libraries.uniswap import Uniswap
from libraries.common_values import *
from web3 import Web3
from threading import Thread
import zerorpc
from dataclasses import dataclass
from cachetools import cached, TTLCache

import logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# charts delete
charts_time_refresh = {}

# ZERORPC
zerorpc_client_data_aggregator = zerorpc.Client()
zerorpc_client_data_aggregator.connect("tcp://127.0.0.1:4243")  # TODO: change port to env variable
pprint.pprint(zerorpc_client_data_aggregator.hello("coucou"))

# twitter
APP_KEY = os.environ.get('TWITTER_API_KEY')
APP_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
twitter = Twython(APP_KEY, APP_SECRET, ACCESS_TOKEN, ACCESS_SECRET_TOKEN)

# ENV FILES
TELEGRAM_KEY = os.environ.get('COIN_TELEGRAM_KEY')
decimals = 1000000000000000000  # that's 18
TMP_FOLDER = BASE_PATH + 'tmp/'
supply_file_path = BASE_PATH + 'log_files/chart_bot/supply_log_$TICKER.txt'
supply_chart_path = BASE_PATH + 'log_files/boo_bot/supply_chart_$TICKER.png'
import random


# web3
infura_url = os.environ.get('INFURA_URL')
pprint.pprint(infura_url)
w3 = Web3(Web3.HTTPProvider(infura_url))

# web3 uni wrapper
uni_wrapper = Uniswap(web3=w3)

# log_file
charts_path = BASE_PATH + 'log_files/coin_bot/'

locale.setlocale(locale.LC_ALL, 'en_US')

graphql_client_uni = GraphQLClient('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2')
graphql_client_eth = GraphQLClient('https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks')


# CONFIG OPTION repeated task
check_buys_interval_second = 60
check_sells_interval_second = 60
check_price_interval_second = 300
print_chart_interval_second = 300
check_gas_interval_second = 900
check_tweets_interval_second = 900
check_biz_interval_second = 1000

already_checked_tx = []
list_channels = {}  # simple kv storage that stores the date of the last action made by the channel

@dataclass(frozen=True)
class Channel:
    channel_id: int
    ticker: str
    contract: str
    pair_contract: str


def _should_send(channel: Channel, diff_time: int=300) -> bool:
    if channel in list_channels:
        now = int(time.time())
        return now - list_channels[channel] < diff_time
    return False


@cached(cache=TTLCache(maxsize=1024, ttl=60))
def get_my_channels(my_name='@coin_chart_bot'):
    results = zerorpc_client_data_aggregator.get_bot_assigned_channels(my_name)
    if results is None or results is []:
        return []
    my_channels = []
    for res in results:
        channel = Channel(channel_id=res[0],
                          ticker=res[1],
                          contract=res[2].lower(),
                          pair_contract=res[3].lower())
        my_channels.append(channel)
    if random.randint(0, 100) > 97:  # TODO: use real logging at one point, that's ridiculous
        pprint.pprint("my channels: ")
        pprint.pprint(my_channels)
    return my_channels


# button refresh: h:int-d:int-t:token
def get_candlestick(context: CallbackContext):

    rand = random.randint(0, 10)

    t_to = int(time.time())
    if rand > 5:
        t_from = t_to - 3600*24
        k_hours, k_days = 0, 1
        options = None
    else:
        t_from = t_to - 3600 * 6
        k_hours, k_days = 6, 0
        options = None

    trending = util.get_banner_txt(zerorpc_client_data_aggregator)

    for channel in get_my_channels():
        if _should_send(channel):
            (message, path, reply_markup_chart) = general_end_functions.send_candlestick_pyplot(channel.ticker, charts_path, k_days,
                                                                                                k_hours, t_from,
                                                                                                t_to, txt=trending, options=options)

            context.bot.send_photo(chat_id=channel.channel_id, photo=open(path, 'rb'), caption=message, parse_mode="html")


def get_price_token(context: CallbackContext):
    for channel in get_my_channels():
        if _should_send(channel):

            message = general_end_functions.get_price(channel.contract, channel.pair_contract, graphql_client_eth,
                                                      graphql_client_uni, channel.ticker.upper(), decimals, uni_wrapper)
            context.bot.send_message(chat_id=channel.channel_id, text=message, parse_mode='html', disable_web_page_preview=True)


# sends the current biz threads
def get_biz(context: CallbackContext):
    for channel in get_my_channels():
        if _should_send(channel):
            base_url = "boards.4channel.org/biz/thread/"

            word = '$' + channel.ticker
            word_regex_friendly = word.replace('$', '\\$')
            message = """Current /biz threads containing the word $WORD:
        """.replace("WORD", channel.ticker)
            threads_ids = scrap_websites_util.get_biz_threads(re.compile(word_regex_friendly))
            for thread_id in threads_ids:
                excerpt = thread_id[2] + " | " + thread_id[1]
                message += base_url + str(thread_id[0]) + " -- " + excerpt[0: 100] + "[...] \n"
            if not threads_ids:
                meme_caption = "No current /biz/ thread containing the word $WORD. You can make one at boards.4chan.org/biz/.".replace(
                    "$WORD", word)
                context.bot.send_message(chat_id=channel.channel_id, text=meme_caption, disable_web_page_preview=True)
            else:
                context.bot.send_message(chat_id=channel.channel_id, text=message, disable_web_page_preview=True)


def get_twitter(context: CallbackContext):
    for channel in get_my_channels():
        tweets_of_the_last_minutes = int(check_tweets_interval_second / 60) * 2
        res = scrap_websites_util.get_last_tweets(twitter, channel.ticker, tweets_of_the_last_minutes)
        if "unable to find" not in res:
            context.bot.send_message(chat_id=channel.channel_id, text=res, parse_mode='html', disable_web_page_preview=True)


def get_gas_average(context: CallbackContext):
    asap, fast, average, low = general_end_functions.get_gas_price()
    message = "<b>Gas price:</b><code>" + \
              "\nASAP: " + str(asap) + \
              " --- Fast: " + str(fast) + \
              "\nAvg : " + str(average) + \
              " --- Slow: " + str(low) + "</code>"
    for channel in get_my_channels():
        context.bot.send_message(chat_id=channel.channel_id, text=message, disable_web_page_preview=True, parse_mode='html')


def get_trending(context: CallbackContext):
    for channel in get_my_channels():

        res = zerorpc_client_data_aggregator.view_trending()
        context.bot.send_message(chat_id=channel.channel_id, text=res)


def get_actions(context: CallbackContext):
    global already_checked_tx

    for channel in get_my_channels():
        try:
            pprint.pprint(channel)
            now = round(time.time())
            last_min = now - 200

            options = ["print_complex"]

            latest_actions_pretty, ids = requests_util.pretty_print_monitor_last_actions(last_min, channel.pair_contract.lower(),
                                                                                    graphql_client_uni, options, amount=100, blacklist=already_checked_tx)
            already_checked_tx += ids
            if latest_actions_pretty is not None:

                now = int(time.time())
                list_channels[channel] = now

                links = '<a href="etherscan.io/token/' + channel.contract + '">Etherscan</a> | <a href="https://app.uniswap.org/#/swap?inputCurrency=' + channel.contract + '">Buy on uniswap</a>'

                message = "🚀Actions of the last minute: \n\n" + latest_actions_pretty + '\n\n' + links

                try:
                    context.bot.send_message(chat_id=channel.channel_id, text=message, disable_web_page_preview=True, parse_mode='html')
                except ChatMigrated as err:
                    print("CHANNEL ID CHANGED: ", err)
                    pass
        except KeyError:
            pass


def main():
    updater = Updater(TELEGRAM_KEY, use_context=True, workers=8)
    dp = updater.dispatcher

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update, context):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    j = updater.job_queue
    j.run_repeating(get_actions, interval=check_buys_interval_second, first=6)
    # j.run_repeating(callback_minute_check_buys, interval=check_sells_interval_second, first=15)
    j.run_repeating(get_biz, interval=check_biz_interval_second, first=round(check_biz_interval_second / 2))
    j.run_repeating(get_twitter, interval=check_tweets_interval_second, first=200)
    j.run_repeating(get_price_token, interval=check_price_interval_second, first=200)
    j.run_repeating(get_candlestick, interval=print_chart_interval_second, first=60)
    j.run_repeating(get_gas_average, interval=check_gas_interval_second, first=200)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
