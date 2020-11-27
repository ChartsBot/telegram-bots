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
print_chart_interval_second = 180
check_gas_interval_second = 600
check_tweets_interval_second = 1000
check_biz_interval_second = 1000


@dataclass(frozen=True)
class Channel:
    channel_id: int
    ticker: str
    contract: str
    pair_contract: str


coin_token_channel = Channel(channel_id=-1001269515340,
                             ticker='COIN',
                             contract="0xE61fDAF474Fac07063f2234Fb9e60C1163Cfa850".lower(),
                             pair_contract="0xff62e62e8b3cf80050464b86194e52c3ead43bb6".lower())

epan_token_channel = Channel(channel_id=-1001294607485,
                             ticker='EPAN',
                             contract="0x72630B1e3B42874bf335020Ba0249e3E9e47Bafc".lower(),
                             pair_contract="0xeb4770eea58fefab132663b852a8b7a35a843c71".lower())

cp3r_token_channel = Channel(channel_id=-1001356862307,
                             ticker='CP3R',
                             contract="0x7Ef1081Ecc8b5B5B130656a41d4cE4f89dBBCC8c".lower(),
                             pair_contract="0xbc6b3dc17e86c8cacf0f384f2e19468c36154a22".lower())

sav3_token_channel = Channel(channel_id=-1001188590509,
                             ticker='SAV3',
                             contract="0x6e10aacb89a28d6fa0fe68790777fec7e7f01890".lower(),
                             pair_contract="0xc2b7888a8d7b62e2a518bbc79fbbd6b75da524b6".lower())

kp3r_token_channel = Channel(channel_id=-1001205642974,
                             ticker='KP3R',
                             contract="0x1ceb5cb57c4d4e2b2433641b95dd330a33185a44".lower(),
                             pair_contract="0x87febfb3ac5791034fd5ef1a615e9d9627c2665d".lower())

channel_list = [coin_token_channel, epan_token_channel, cp3r_token_channel, sav3_token_channel, kp3r_token_channel]

# button refresh: h:int-d:int-t:token
def get_candlestick(context: CallbackContext):

    rand = random.randint(0, 10)

    t_to = int(time.time())
    if rand > 5:
        t_from = t_to - 3600*24
        k_hours, k_days = 0, 1
        options = None
    else:
        t_from = t_to - 3600
        k_hours, k_days = 1, 0
        options = None

    trending = util.get_banner_txt(zerorpc_client_data_aggregator)

    for channel in channel_list:

        (message, path, reply_markup_chart) = general_end_functions.send_candlestick_pyplot(channel.ticker, charts_path, k_days,
                                                                                            k_hours, t_from,
                                                                                            t_to, txt=trending, options=options)

        context.bot.send_photo(chat_id=channel.channel_id, photo=open(path, 'rb'), caption=message, parse_mode="html")


def get_price_token(context: CallbackContext):
    for channel in channel_list:

        message = general_end_functions.get_price(channel.contract, channel.pair_contract, graphql_client_eth,
                                                  graphql_client_uni, channel.ticker.upper(), decimals, uni_wrapper)
        context.bot.send_message(chat_id=channel.channel_id, text=message, parse_mode='html', disable_web_page_preview=True)


# sends the current biz threads
def get_biz(context: CallbackContext):
    for channel in channel_list:
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
            meme_caption = "No current /biz/ thread containing the word $WORD. You can make one at https://boards.4channel.org/biz/.".replace(
                "$WORD", word)
            context.bot.send_message(chat_id=channel.channel_id, text=meme_caption, disable_web_page_preview=True)
        else:
            context.bot.send_message(chat_id=channel.channel_id, text=message, disable_web_page_preview=True)


def get_twitter(context: CallbackContext):
    for channel in channel_list:
        tweets_of_the_last_minutes = int(check_tweets_interval_second / 60) * 2
        res = scrap_websites_util.get_last_tweets(twitter, channel.ticker, tweets_of_the_last_minutes)
        context.bot.send_message(chat_id=channel.channel_id, text=res, parse_mode='html', disable_web_page_preview=True)


def get_gas_average(context: CallbackContext):
    asap, fast, average, low = general_end_functions.get_gas_price()
    message = "<b>Gas price:</b><code>" + \
              "\nASAP: " + str(asap) + \
              " --- Fast: " + str(fast) + \
              "\nAvg : " + str(average) + \
              " --- Slow: " + str(low) + "</code>"
    for channel in channel_list:
        context.bot.send_message(chat_id=channel.channel_id, text=message, disable_web_page_preview=True, parse_mode='html')


def get_trending(context: CallbackContext):
    for channel in channel_list:

        res = zerorpc_client_data_aggregator.view_trending()
        context.bot.send_message(chat_id=channel.channel_id, text=res)


def get_actions(context: CallbackContext):
    for channel in channel_list:

        print("checking monitors")
        now = round(time.time())
        last_min = now - 80

        options = ["print_complex"]

        latest_actions_pretty = requests_util.pretty_print_monitor_last_actions(last_min, channel.pair_contract.lower(),
                                                                                graphql_client_uni, options, amount=100)
        if latest_actions_pretty is not None:
            links = '<a href="etherscan.io/token/' + channel.contract + '">Etherscan</a> | <a href="https://app.uniswap.org/#/swap?inputCurrency=' + channel.contract + '">Uniswap</a>'

            message = "🚀Actions of the last minute: \n\n" + latest_actions_pretty + '\n' + links

            try:
                context.bot.send_message(chat_id=channel.channel_id, text=message, disable_web_page_preview=True, parse_mode='html')
            except ChatMigrated as err:
                print("CHANNEL ID CHANGED: ", err)
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
    j.run_repeating(get_price_token, interval=check_price_interval_second, first=6)
    j.run_repeating(get_candlestick, interval=print_chart_interval_second, first=60)
    j.run_repeating(get_gas_average, interval=check_gas_interval_second, first=200)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

commands = """
chart - <TICKER> Display charts of the TICKER.
twitter - <TICKER> Get latests twitter containing $<TICKER>. 
price - <TICKER> get price of the <TICKER> token.
biz - <WORD> get 4chan/biz threads containing <WORD>.
gas - Get gas price.
faq - Print the FAQ.
convert - <AMOUNT> <TICKER> option(<TICKER>) convert amount of ticker to usd (and to the second ticker if specified). 
balance - <WALLET> <TICKER> check how much an address has of a specific coin.
timeto - time until date passed as argument.
last_actions - <TICKER> get the last trades / liq events of the coin.
trending - See which coins are trending in dextrends.
translate - <LANGUAGE_TO> <TEXT> Translate a text into the desired language.
"""
