import locale
import sys
import os
from gevent import monkey
monkey.patch_all()  # REALLY IMPORTANT: ALLOWS ZERORPC AND TG TO WORK TOGETHER

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots/src')

from twython import Twython
from graphqlclient import GraphQLClient
import time
from datetime import datetime
import pprint
import os.path
import re
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, MessageHandler, Filters
import telegram.error
import libraries.graphs_util as graphs_util
import libraries.general_end_functions as general_end_functions
import libraries.commands_util as commands_util
import libraries.scrap_websites_util as scrap_websites_util
import libraries.git_util as git_util
import libraries.requests_util as requests_util
import libraries.util as util
from bots.boo_bank.bot_boo_values import links, how_to_swap
from libraries.timer_util import RepeatedTimer
from libraries.uniswap import Uniswap
from libraries.common_values import *
import libraries.time_util as time_util
import libraries.web3_calls as web3_util
from web3 import Web3
import zerorpc
import html

# ZERORPC
zerorpc_client_data_aggregator = zerorpc.Client()
zerorpc_client_data_aggregator.connect("tcp://127.0.0.1:4243")
pprint.pprint(zerorpc_client_data_aggregator.hello("coucou"))

button_list_price = [[InlineKeyboardButton('refresh', callback_data='refresh_price')]]
reply_markup_price = InlineKeyboardMarkup(button_list_price)

APP_KEY = os.environ.get('TWITTER_API_KEY')
APP_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')

twitter = Twython(APP_KEY, APP_SECRET, ACCESS_TOKEN, ACCESS_SECRET_TOKEN)

# time
last_time_checked_4chan = 0
last_time_checked_twitter = 0

# log_file
charts_path = BASE_PATH + 'log_files/chart_bot/'

locale.setlocale(locale.LC_ALL, 'en_US')

# web3
infura_url = os.environ.get('INFURA_URL')
pprint.pprint(infura_url)
w3 = Web3(Web3.HTTPProvider(infura_url))
uni_wrapper = Uniswap(web3=w3)

graphql_client_uni = GraphQLClient('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2')
graphql_client_eth = GraphQLClient('https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks')

re_4chan = re.compile(r'\$BOOB|BOOB')
TELEGRAM_KEY = os.environ.get('BOO_TELEGRAM_KEY')
MEME_GIT_REPO = os.environ.get('BOO_MEME_GIT_REPO')
MEME_PWD = os.environ.get('BOO_MEME_GIT_REPO_DELETE_PWD')
TMP_FOLDER = BASE_PATH + 'tmp/'
boob_contract = "0xa9c44135b3a87e0688c41cf8c27939a22dd437c9"
name = "Boo Bank"
ticker = 'BOOB'
ecto_contract = "0x921c87490ccbef90a3b0fc1951bd9064f7220af6"
ecto_name = "Ectoplasma"
ecto_ticker = 'ECTO'
pair_contract = "0x6e31ef0b62a8abe30d80d35476ca78897dffa769"
bbra_name = "BBRA"
bbra_ticker = 'BBRA'
bbra_contract = "0x70460c3bb9abcc0aa51f922c00d37816d6ede4d7"

decimals = 1000000000000000000  # that's 18
git_url = "https://api.github.com/repos/boobank/boo-memes/contents/memesFolder"

# add meme
git_handler = git_util.MemeHandler(MEME_GIT_REPO, git_url)

supply_file_path = BASE_PATH + 'log_files/boo_bot/supply_log.txt'
supply_chart_path = BASE_PATH + 'log_files/boo_bot/supply_chart.png'


# button refresh: h:int-d:int-t:token
def get_candlestick(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    if update.message.chat.title == "BBRA":
        context.bot.send_message(chat_id=chat_id, text="We created a price discussion channel\n you can make the boobanker bot stuff in there @BBRAprice")
        return

    query_received = update.message.text.split(' ')
    default_ticker = ticker
    if "BBRA" in update.message.chat.title:
        default_ticker = "BBRA"

    time_type, k_hours, k_days, tokens = commands_util.check_query(query_received, default_ticker)
    t_to = int(time.time())
    t_from = t_to - (k_days * 3600 * 24) - (k_hours * 3600)
    banner_txt = util.get_banner_txt(zerorpc_client_data_aggregator)

    if isinstance(tokens, list):
        for token in tokens:
            (message, path, reply_markup_chart) = general_end_functions.send_candlestick_pyplot(token, charts_path, k_days, k_hours, t_from, t_to, banner_txt)
            util.create_and_send_vote(token, "chart", update.message.from_user.name, zerorpc_client_data_aggregator)
            context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'), caption=message, parse_mode="html", reply_markup=reply_markup_chart)
    else:
        (message, path, reply_markup_chart) = general_end_functions.send_candlestick_pyplot(tokens, charts_path, k_days, k_hours, t_from, t_to, banner_txt)
        util.create_and_send_vote(tokens, "chart", update.message.from_user.name, zerorpc_client_data_aggregator)
        context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'), caption=message, parse_mode="html", reply_markup=reply_markup_chart)


def get_price_token(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if update.message.chat.title == "BBRA":
        context.bot.send_message(chat_id=chat_id, text="We created a price discussion channel\n you can make the boobanker bot stuff in there @BBRAprice")
    else:
        message = general_end_functions.get_price(boob_contract, pair_contract, graphql_client_eth, graphql_client_uni, name, decimals, uni_wrapper)
        util.create_and_send_vote(ticker, "price", update.message.from_user.name, zerorpc_client_data_aggregator)
        context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html', disable_web_page_preview=True)


def get_price_ecto(update: Update, context: CallbackContext):
    message = general_end_functions.get_price(ecto_contract, pair_contract, graphql_client_eth, graphql_client_uni, ecto_name, decimals, uni_wrapper)
    chat_id = update.message.chat_id
    if update.message.chat.title == "BBRA":
        context.bot.send_message(chat_id=chat_id, text="We created a price discussion channel\n you can make the boobanker bot stuff in there @BBRAprice")
        return
    util.create_and_send_vote("ECTO", "price", update.message.from_user.name, zerorpc_client_data_aggregator)
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html', disable_web_page_preview=True)


def get_price_bbra(update: Update, context: CallbackContext):
    message = general_end_functions.get_price(bbra_contract, pair_contract, graphql_client_eth, graphql_client_uni, bbra_name, decimals, uni_wrapper)
    chat_id = update.message.chat_id
    if update.message.chat.title == "BBRA":
        context.bot.send_message(chat_id=chat_id, text="We created a price discussion channel\n you can make the boobanker bot stuff in there @BBRAprice")
        return
    util.create_and_send_vote("BBRA", "price", update.message.from_user.name, zerorpc_client_data_aggregator)
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html', disable_web_page_preview=True)



def refresh_chart(update: Update, context: CallbackContext):
    print("refreshing chart")
    query = update.callback_query.data

    k_hours = int(re.search(r'\d+', query.split('h:')[1]).group())
    k_days = int(re.search(r'\d+', query.split('d:')[1]).group())
    token = query.split('t:')[1]

    banner_txt = util.get_banner_txt(zerorpc_client_data_aggregator)

    t_to = int(time.time())
    t_from = t_to - (k_days * 3600 * 24) - (k_hours * 3600)

    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id

    (message, path, reply_markup_chart) = general_end_functions.send_candlestick_pyplot(token, charts_path, k_days, k_hours, t_from, t_to, banner_txt)
    try:
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)
        context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'), caption=message, parse_mode="html", reply_markup=reply_markup_chart)
    except telegram.error.BadRequest:
        print("couldn't find message to deleted but catched the error")
        pass


def refresh_price(update: Update, context: CallbackContext):
    print("refreshing price")
    message = general_end_functions.get_price(boob_contract, pair_contract, graphql_client_eth, graphql_client_uni,
                                              name, decimals)
    update.callback_query.edit_message_text(text=message, parse_mode='html', reply_markup=reply_markup_price, disable_web_page_preview=True)


def get_help(update: Update, context: CallbackContext):
    general_end_functions.get_help(update, context)


def get_twitter(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    actual_ticker = ticker
    if len(query_received) == 2:
        actual_ticker = query_received[1]
    res = scrap_websites_util.get_last_tweets(twitter, actual_ticker)
    context.bot.send_message(chat_id=chat_id, text=res, parse_mode='html', disable_web_page_preview=True)


def delete_chart_message(update: Update, context: CallbackContext):
    print("deleting chart")
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def handle_new_image(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    try:
        caption = update['message']['caption']
        if caption == "/add_meme" and chat_id == -1001187740219:
            if git_handler.add_meme(update, context):
                context.bot.send_message(chat_id=chat_id, text="Got it boss!")
            else:
                error_msg = "Adding image failed: no image provided or incorrect format."
                context.bot.send_message(chat_id=chat_id, text=error_msg)
        else:
            __send_message_if_ocr(update, context)
    except KeyError:
        __send_message_if_ocr(update, context)


def __send_message_if_ocr(update, context):
    message_id = update.message.message_id
    chat_id = update.message.chat_id
    try:
        text_in_ocr = general_end_functions.ocr_image(update, context, TMP_FOLDER)
        if ('transaction cannot succeed' and 'one of the tokens' in text_in_ocr) or (
                'transaction will not succeed' and 'price movement or' in text_in_ocr):
            context.bot.send_message(chat_id=chat_id, text=test_error_token, reply_to_message_id=message_id)
    except IndexError:
        pass


def send_meme_to_chat(update: Update, context: CallbackContext):
    url = git_handler.get_url_meme()
    chat_id = update.message.chat_id
    context.bot.send_photo(chat_id=chat_id, photo=url)


# sends the current biz threads
def get_biz(update: Update, context: CallbackContext):
    global last_time_checked_4chan
    chat_id = update.message.chat_id
    new_time = round(time.time())
    if new_time - last_time_checked_4chan > 60:
        last_time_checked_4chan = new_time
        threads_ids = scrap_websites_util.get_biz_threads(re_4chan)

        base_url = "boards.4channel.org/biz/thread/"
        message = """Plz go bump the /biz/ threads:
"""
        for thread_id in threads_ids:
            excerpt = (thread_id[2] + " | " + thread_id[1]).replace("<br>", "")
            parsed_excerpt = html.unescape(excerpt)
            message += base_url + str(thread_id[0]) + " -- " + parsed_excerpt[0: 100] + "[...] \n"
        if not threads_ids:
            meme_url = git_handler.get_url_meme()
            meme_caption = "There hasn't been a BoobBank /biz/ thread for a while. Here's a meme, go make one https://boards.4channel.org/biz/."
            context.bot.send_photo(chat_id=chat_id, photo=meme_url, caption=meme_caption)
        else:
            context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text='Only checking 4chan/twitter/charts once per minute. Don\'t spam.')


# sends the main links
def get_links(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=links, disable_web_page_preview=True, parse_mode='html')


def send_music(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    filename = random.sample(os.listdir(BASE_PATH + 'audio/boo/'), 1)[0]
    context.bot.send_audio(chat_id=chat_id,
                           audio=open(BASE_PATH + 'audio/boo/' + filename, 'rb'),
                           parse_mode='html')


def send_ballad(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    caption = "🎸🤘🎼 <i>Give it to me boobies</i>🎼🤘🎸"
    context.bot.send_audio(chat_id=chat_id,
                           audio=open(BASE_PATH + 'audio/boo/bbra_anthem.mp3', 'rb'),
                           caption=caption,
                           parse_mode='html')


def send_anthem(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    caption = "🎸🤘🎼 <i>I want my stacked boobiiiiieeesssss</i>🎼🤘🎸"
    context.bot.send_audio(chat_id=chat_id,
                           audio=open(BASE_PATH + 'audio/boo/boo_anthem.mp3', 'rb'),
                           caption=caption,
                           parse_mode='html')


def send_flyer(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    path = BASE_PATH + 'images/boo/flyer.jpg'
    context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'))


def send_flyer_bbra(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    path = BASE_PATH + 'images/boo/flyer_bbra.jpg'
    context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'))


def log_current_supply():
    number_boob = requests_util.get_supply_cap_raw(boob_contract, decimals)
    number_ecto = requests_util.get_supply_cap_raw(ecto_contract, decimals)
    with open(supply_file_path, "a") as supply_file:
        time_now = datetime.now()
        date_time_str = time_now.strftime("%m/%d/%Y,%H:%M:%S")
        message_to_write = date_time_str + " " + str(number_boob) + " " + str(number_ecto) + "\n"
        supply_file.write(message_to_write)


def get_chart_supply(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id

    query_received = update.message.text.split(' ')

    if update.message.chat.title == "BBRA":
        context.bot.send_message(chat_id=chat_id, text="We created a price discussion channel\n you can make the boobanker bot price stuff in there @BBRAprice")
        return

    if "bbra" in query_received or "BBRA" in query_received or "BBRA" in update.message.chat.title:
        supply_file_path_general = BASE_PATH + 'log_files/chart_bot/supply_log_$TICKER.txt'
        ticker_supply_file_path = supply_file_path_general.replace("$TICKER", "BBRA")
        if "BBRA" in update.message.chat.title:
            time_type, k_hours, k_days, tokens = commands_util.check_query(query_received, ticker)
        else:
            time_type, k_hours, k_days, tokens = commands_util.check_query(query_received[1:], ticker)
        current_token_nbr = general_end_functions.send_supply_single_pyplot(ticker_supply_file_path,
                                                                            k_days,
                                                                            k_hours,
                                                                            "BBRA",
                                                                            supply_chart_path)

        current_token_str = util.number_to_beautiful(current_token_nbr)

        msg_time = " " + str(k_days) + " day(s) " if k_days > 0 else " last " + str(k_hours) + " hour(s) "

        caption = "Supply of the last " + msg_time + ".\nCurrent supply: \n<b>" + "BBRA" + ":</b> <pre>" + current_token_str + "</pre>"

        context.bot.send_photo(chat_id=chat_id,
                               photo=open(supply_chart_path, 'rb'),
                               caption=caption,
                               parse_mode="html")
    else:
        time_type, k_hours, k_days, tokens = commands_util.check_query(query_received, ticker)

        current_boob_nbr, current_ecto_nbr = general_end_functions.send_supply_two_pyplot(supply_file_path,
                                                                                          k_days,
                                                                                          k_hours,
                                                                                          "BOOB",
                                                                                          "ECTO",
                                                                                          supply_chart_path)

        current_boob_str = util.number_to_beautiful(current_boob_nbr)
        current_ecto_str = util.number_to_beautiful(current_ecto_nbr)

        msg_time = " " + str(k_days) + " day(s) " if k_days > 0 else " last " + str(k_hours) + " hour(s) "

        caption = "Supply of the last " + msg_time + ".\nCurrent supply: \n<b>BOOB:</b> <pre>" + current_boob_str + \
                  "</pre> \n<b>ECTO:</b> <pre>" + current_ecto_str + "</pre>"

        context.bot.send_photo(chat_id=chat_id,
                               photo=open(supply_chart_path, 'rb'),
                               caption=caption,
                               parse_mode="html")


def amount_bbra_locked(update: Update, context: CallbackContext):

    chat_id = update.message.chat_id

    wallet = "0x0000000000000000000000000000000000000000"
    contract_pair_eth_bbra = "0xf76b7146093b7b43c543d2e354a2d9c67d8e206f"
    amount_locked_lp_raw = web3_util.get_balance_token_wallet_raw(w3, wallet, contract_pair_eth_bbra)
    value_lp = web3_util.get_lp_value(uni_wrapper, contract_pair_eth_bbra)
    bbra_amount = value_lp[0][0] / 10 ** 18
    eth_amount = value_lp[1][0] / 10 ** 18
    lp_total = value_lp[2]
    locked_eth = (eth_amount / lp_total) * amount_locked_lp_raw
    locked_bbra = (bbra_amount / lp_total) * amount_locked_lp_raw

    message = "There are <b>" + '{:.2f}'.format(amount_locked_lp_raw) + " BBRA-ETH LP tokens</b> locked forever = "
    message += "<b>" + '{:.2f}'.format(locked_eth) + " ETH </b> and <b>" + '{:.2f}'.format(locked_bbra) + " BBRA</b>. "
    message += '<a href="https://etherscan.io/token/0xf76b7146093b7b43c543d2e354a2d9c67d8e206f?a=0x0000000000000000000000000000000000000000">proof</a>'
    context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html', disable_web_page_preview=True)
    # res = con



def send_how_to_swap(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=how_to_swap, disable_web_page_preview=True, parse_mode='html')


def do_convert(update: Update, context: CallbackContext):
    query_received = update.message.text.split(' ')
    chat_id = update.message.chat_id
    message = general_end_functions.convert_to_something(query_received, graphql_client_uni, graphql_client_eth)
    context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True, parse_mode='html')


def delete_meme(update: Update, context: CallbackContext):
    git_handler.delete_meme(update, context, MEME_PWD)


def get_latest_actions(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    if update.message.chat.title == "BBRA":
        context.bot.send_message(chat_id=chat_id, text="We created a price discussion channel\n you can make the boobanker bot stuff in there @BBRAprice")
        return
    query_received = update.message.text.split(' ')
    if len(query_received) == 1:
        token_ticker = "BOOB"
        latest_actions_pretty = general_end_functions.get_last_actions_token_in_eth_pair(token_ticker, uni_wrapper, graphql_client_uni)
        context.bot.send_message(chat_id=chat_id, text=latest_actions_pretty, disable_web_page_preview=True, parse_mode='html')
    elif len(query_received) == 2:
        token_ticker = query_received[1]
        latest_actions_pretty = general_end_functions.get_last_actions_token_in_eth_pair(token_ticker, uni_wrapper, graphql_client_uni)
        context.bot.send_message(chat_id=chat_id, text=latest_actions_pretty, disable_web_page_preview=True, parse_mode='html')
    else:
        context.bot.send_message(chat_id=chat_id, text="Please use the format /last_actions TOKEN_TICKER")


def get_trending(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    res = zerorpc_client_data_aggregator.view_trending()
    context.bot.send_message(chat_id=chat_id, text=res)


def get_time_to(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query_received = update.message.text[7:]
    pprint.pprint(query_received)

    higher, time_to = time_util.get_time_diff(query_received)
    pprint.pprint(time_to)
    word = ' is ' if higher else ' was '
    message = str(query_received) + word + str(time_to) + " from now."
    context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)


def get_citadel(update: Update, context: CallbackContext):
    message = 'If you have 100 $BOOB in your wallet you can enter the elitist Titty Citadel to get the latest news first: <a href="https://telegram.me/collablandbot?start=recsaxjYhsEbaBC4T_-tpc">CLICK HERE TO JOIN THE CITADEL</a>'
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True, parse_mode='html')


def main():
    updater = Updater(TELEGRAM_KEY, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler(['chart', 'c'], get_candlestick))
    dp.add_handler(CommandHandler('price', get_price_token))
    dp.add_handler(CommandHandler('boob', get_price_token))
    dp.add_handler(CommandHandler('bbra', get_price_bbra))
    dp.add_handler(CommandHandler('locked_bbras', amount_bbra_locked))
    dp.add_handler(CommandHandler('timeto', get_time_to))
    dp.add_handler(CommandHandler('ecto', get_price_ecto))
    dp.add_handler(CallbackQueryHandler(refresh_chart, pattern='refresh_chart(.*)'))
    dp.add_handler(CallbackQueryHandler(refresh_price, pattern='refresh_price'))
    dp.add_handler(CallbackQueryHandler(delete_chart_message, pattern='delete_message'))
    dp.add_handler(CommandHandler('help', get_help))
    dp.add_handler(CommandHandler('twitter', get_twitter))
    dp.add_handler(MessageHandler(Filters.photo, handle_new_image))
    dp.add_handler(CommandHandler('give_meme', send_meme_to_chat))
    dp.add_handler(CommandHandler('meme', send_meme_to_chat))
    dp.add_handler(CommandHandler('biz', get_biz))
    dp.add_handler(CommandHandler('links', get_links))
    dp.add_handler(CommandHandler('anthem', send_anthem))
    dp.add_handler(CommandHandler('music', send_music))
    dp.add_handler(CommandHandler('ballad', send_ballad))
    dp.add_handler(CommandHandler('flyer_bbra', send_flyer_bbra))
    dp.add_handler(CommandHandler('flyer', send_flyer))
    dp.add_handler(CommandHandler('chart_supply', get_chart_supply))
    dp.add_handler(CommandHandler('how_to_swap', send_how_to_swap))
    dp.add_handler(CommandHandler('convert', do_convert))
    dp.add_handler(CommandHandler('delete_meme_secret', delete_meme))
    dp.add_handler(CommandHandler('last_actions', get_latest_actions))
    dp.add_handler(CommandHandler('trending', get_trending))
    dp.add_handler(CommandHandler('citadel', get_citadel))
    RepeatedTimer(120, log_current_supply)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

commands = """
help - How to use the bot.
chart - Display a chart of the price.
boob - Get the current price of $BOOB.
bbra - Get the current price of $BBRA
ecto - Get the current price of $ECTO.
locked_bbras - See how much liquidity is locked forever
ballad - BBRA music.
flyer_bbra - Explain bbra.
chart_supply - Display a chart of the supply (BOOB and ECTO).
twitter - Get the last tweets concerning $BOOB.
add_meme - Add a meme to the meme folder.
give_meme - Returns a random meme from the meme folder.
anthem - Send the Boo Bank Org. national anthem.
music - Send a random music from the jukebox.
flyer - Show the flyer.
biz - Display current 4chan threads.
how_to_swap - Guide on how to swap ecto
convert - convert AMOUNT MONEY
trending - See which coins are trending in dextrends
citadel - Infos about the tiddy citadel
"""
