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
import io

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, Filters, MessageHandler, \
    ConversationHandler, InlineQueryHandler
from telegram.inline.inlinequeryresultarticle import InlineQueryResultArticle
from telegram.inline.inputtextmessagecontent import InputTextMessageContent
from telegram.parsemode import ParseMode
from telegram.utils.helpers import escape_markdown

from telegram.ext.dispatcher import run_async
from telegram.error import ChatMigrated, BadRequest
import libraries.web3_calls as web3_util
from cachetools import cached, TTLCache

import libraries.graphs_util as graphs_util
import libraries.general_end_functions as general_end_functions
import libraries.commands_util as commands_util
import libraries.requests_util as requests_util
import libraries.wolfram_queries as wolfram_queries
import libraries.time_util as time_util
import libraries.util as util
import libraries.scrap_websites_util as scrap_websites_util
import libraries.queries_parser as queries_parser
import libraries.translation_util as translation_util
from libraries.uniswap import Uniswap
from bots.chart_general.bot_charts_values import start_message, message_faq_empty, symbol_gecko, message_faq_additional, \
    emoji_number_dic
from libraries.common_values import *
from web3 import Web3
from libraries.timer_util import RepeatedTimer
from threading import Thread
import libraries.protobuf.filehandler.fileHandler_pb2 as filehandler_pb2
import libraries.protobuf.filehandler.fileHandler_pb2_grpc as filehandler_pb2_grpc
import grpc

# from py_w3c.validators.html.validator import HTMLValidator
from uuid import uuid4

import zerorpc

import wolframalpha

import logging

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

APP_KEY_WOLFRAM = os.environ.get('WOLFRAM_API')

IS_TEST_ENV = False

try:
    wolfram_client = wolframalpha.Client(APP_KEY_WOLFRAM)
except Exception:
    logging.info("Worlfram struggling to connect, trying again")
    wolfram_client = wolframalpha.Client(APP_KEY_WOLFRAM)

announcement_channel_id = -1001478326834

# charts delete
charts_time_refresh = {}

# ZERORPC
zerorpc_client_data_aggregator = zerorpc.Client()
zerorpc_client_data_aggregator.connect("tcp://127.0.0.1:4243")  # TODO: change port to env variable
logging.info(zerorpc_client_data_aggregator.hello("coucou"))

# twitter
APP_KEY = os.environ.get('TWITTER_API_KEY')
APP_SECRET = os.environ.get('TWITTER_API_KEY_SECRET')
ACCESS_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN')
ACCESS_SECRET_TOKEN = os.environ.get('TWITTER_ACCESS_TOKEN_SECRET')
twitter = Twython(APP_KEY, APP_SECRET, ACCESS_TOKEN, ACCESS_SECRET_TOKEN)

# ENV FILES
TELEGRAM_KEY = os.environ.get('CHART_TELEGRAM_KEY')
TELEGRAM_WEBHOOK_PRIVATE_KEY_PATH = os.environ.get('TG_FOMO_WEBHOOK_PRIV_PATH')
TELEGRAM_WEBHOOK_CERT_PATH = os.environ.get('TG_FOMO_WEBHOOK_CERT_PATH')
SERVER_IP = os.environ.get('SERVER_IP')
pair_contract = "0x5a265315520696299fa1ece0701c3a1ba961b888"
decimals = 1000000000000000000  # that's 18
TMP_FOLDER = BASE_PATH + 'tmp/'
supply_file_path = BASE_PATH + 'log_files/chart_bot/supply_log_$TICKER.txt'
supply_chart_path = BASE_PATH + 'log_files/boo_bot/supply_chart_$TICKER.png'
pie_chart_wallet_path = BASE_PATH + 'log_files/boo_bot/pie_chart_wallet.png'

# grpc
GRPC_FILE_HANDLER_CA_PATH = os.environ.get('GRPC_FILE_HANDLER_CA_PATH')
GRPC_FILE_HANDLER_HOST = os.environ.get('GRPC_FILE_HANDLER_HOST')

# web3
infura_url = os.environ.get('INFURA_URL')
w3 = Web3(Web3.HTTPProvider(infura_url))

# web3 uni wrapper
uni_wrapper = Uniswap(web3=w3)

# log_file
charts_path = BASE_PATH + 'log_files/chart_bot/'

default_token = 'ROT'

locale.setlocale(locale.LC_ALL, 'en_US')

graphql_client_uni = GraphQLClient('https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v2')
graphql_client_eth = GraphQLClient('https://api.thegraph.com/subgraphs/name/blocklytics/ethereum-blocks')

rejection_no_default_ticker_message = "No default token found for this chat. Please ask an admin to add one with /set_default_token <TICKER>"

# CONFIG OPTION repeated task
check_big_buys_interval_seconds = 60 * 5

# grpc stuff
if os.environ.get('https_proxy'):
    del os.environ['https_proxy']
if os.environ.get('http_proxy'):
    del os.environ['http_proxy']
with open(GRPC_FILE_HANDLER_CA_PATH, 'rb') as f:
    grpc_file_handler_creds = grpc.ssl_channel_credentials(f.read())
grpc_file_handler_channel = grpc.secure_channel('localhost:8081', grpc_file_handler_creds,
                                                options=(('grpc.ssl_target_name_override', 'foo.test.google.fr'),
                                                         ('grpc.enable_http_proxy', 0),))

# create a stub (client)
grpc_file_handler_client = filehandler_pb2_grpc.FileHandlerAkkaServiceStub(grpc_file_handler_channel)


def get_start_message(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "start")
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=start_message, parse_mode='html', disable_web_page_preview=True)


# button refresh: h:int-d:int-t:token
def get_candlestick(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "chart")
    global charts_time_refresh
    chat_id = update.message.chat_id

    query_received = update.message.text.split(' ')
    channel_token = __get_default_token_channel(chat_id)
    if channel_token is not None:
        default_default_token = channel_token[0]
    else:
        default_default_token = "eth"
    if len(query_received) == 1:
        if channel_token is None:
            context.bot.send_message(chat_id=chat_id, text=rejection_no_default_ticker_message)
            return

    token, start_time, time_period, options = queries_parser.analyze_query_charts(update.message.text,
                                                                                  default_default_token)
    options = None if options == [] else options

    # time_type, k_hours, k_days, tokens = commands_util.check_query(query_received, default_default_token)
    time_type, k_hours, k_days = commands_util.get_time_query(start_time, time_period)
    t_to = int(time.time())
    t_from = t_to - (k_days * 3600 * 24) - (k_hours * 3600)
    trending = util.get_banner_txt(zerorpc_client_data_aggregator)

    maybe_bottom_text = text_if_coin_being_watched(token)

    (message, path, reply_markup_chart) = general_end_functions.send_candlestick_pyplot(token, charts_path, k_days,
                                                                                        k_hours, t_from,
                                                                                        t_to, txt=trending,
                                                                                        options=options,
                                                                                        with_ad=maybe_bottom_text)
    if options is not None:
        if "f" in options or "finance" in options:
            logging.info("finance: not sending vote")
        else:
            util.create_and_send_vote(token, "chart", update.message.from_user.name, zerorpc_client_data_aggregator)
    else:
        util.create_and_send_vote(token, "chart", update.message.from_user.name, zerorpc_client_data_aggregator)
    token_chat_id = str(chat_id) + "_" + token
    charts_time_refresh[token_chat_id] = t_to
    context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'), caption=message, parse_mode="html",
                           reply_markup=reply_markup_chart)
    context.bot.send_photo(chat_id=announcement_channel_id, photo=open(path, 'rb'), caption=message, parse_mode="html")


def get_price_token(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "price")
    chat_id = update.message.chat_id

    query_received = update.message.text.split(' ')
    if len(query_received) == 2:
        ticker = query_received[1]

        if ticker.upper() in symbol_gecko:
            value = symbol_gecko.get(ticker.upper())
            message = general_end_functions.get_price_gecko(value)
            button_list_price = [
                [InlineKeyboardButton('refresh', callback_data='r_p_' + "null" + "_t_" + ticker)]]
            reply_markup_price = InlineKeyboardMarkup(button_list_price)
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html', reply_markup=reply_markup_price,
                                     disable_web_page_preview=True)
        else:
            contract_from_ticker = requests_util.get_token_contract_address(ticker)
            pprint.pprint(contract_from_ticker)
            if contract_from_ticker is None:
                context.bot.send_message(chat_id=chat_id, text='Contract address for ticker ' + ticker + ' not found.')
            else:
                util.create_and_send_vote(ticker, "price", update.message.from_user.name,
                                          zerorpc_client_data_aggregator)
                button_list_price = [
                    [InlineKeyboardButton('refresh', callback_data='r_p_' + contract_from_ticker + "_t_" + ticker)]]
                reply_markup_price = InlineKeyboardMarkup(button_list_price)
                message = general_end_functions.get_price(contract_from_ticker, "", graphql_client_eth,
                                                          graphql_client_uni, ticker.upper(), decimals, uni_wrapper)
                context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html',
                                         reply_markup=reply_markup_price,
                                         disable_web_page_preview=True)
                if not __did_user_vote_too_much(update.message.from_user.name, "price", ticker):
                    context.bot.send_message(chat_id=announcement_channel_id, text=message, parse_mode='html',
                                             disable_web_page_preview=True)
                else:
                    print("user " + update.message.from_user.name + " voted too much")

    elif len(query_received) == 1:  # TODO: merge all those duplicate things
        ticker, addr = __get_default_token_channel(chat_id)
        if ticker is not None:
            if addr is None or addr == "":
                context.bot.send_message(chat_id=chat_id, text='Contract address for ticker ' + ticker + ' not found.')
            else:
                util.create_and_send_vote(ticker, "price", update.message.from_user.name,
                                          zerorpc_client_data_aggregator)
                button_list_price = [
                    [InlineKeyboardButton('refresh', callback_data='r_p_' + addr + "_t_" + ticker)]]
                reply_markup_price = InlineKeyboardMarkup(button_list_price)
                message = general_end_functions.get_price(addr, "", graphql_client_eth,
                                                          graphql_client_uni, ticker.upper(), decimals, uni_wrapper)
                context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html',
                                         reply_markup=reply_markup_price, disable_web_page_preview=True)
                if not __did_user_vote_too_much(update.message.from_user.name, "price", ticker):
                    context.bot.send_message(chat_id=announcement_channel_id, text=message, parse_mode='html',
                                             disable_web_page_preview=True)
        else:
            message = rejection_no_default_ticker_message
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')
    else:
        context.bot.send_message(chat_id=chat_id, text='Please specify the ticker of the desired token.')


def delete_meme(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "delete_meme")
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    can_delete = False
    if update.message.chat.type == 'private':
        can_delete = True
    elif __is_user_admin(context, update):
        can_delete = True
    if can_delete:
        if len(query_received) == 2:
            meme_to_delete = query_received[1]
            file_type = "image" if ".jpg" in meme_to_delete else "video"  # todo: quick hack, fix
            delRequest = filehandler_pb2.FileDeleteRequest(chatId=chat_id,
                                                           fileClassification="meme",
                                                           fileType=file_type,
                                                           name=meme_to_delete)
            response = grpc_file_handler_client.DeleteFile(delRequest)
            context.bot.send_message(chat_id=chat_id, text=response.message)
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text="Please specify which meme you wish to delete (like /delete_meme EminentOldEgret.jpg) or reply /delete_meme to it directly")
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="You don't have the rights to delete a meme. Only admins can do that you silly")


def get_meme(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "get_meme")
    chat_id = update.message.chat_id

    if _is_meme_authorized_on_channel(chat_id):
        fileRequest = filehandler_pb2.FileGetRequest(chatId=chat_id,
                                                     fileClassification="meme",
                                                     fileType="image",
                                                     author="whatever")
        response = grpc_file_handler_client.GetFile(fileRequest)
        pprint.pprint("got nice meme")
        if response.status:
            if response.fileType == "image":
                tmp_meme_path = TMP_FOLDER + 'tmp_meme.png'
                context.bot.send_photo(chat_id=chat_id,
                                       photo=io.BytesIO(response.file),
                                       caption="Dank meme " + response.name
                                       )
            elif response.fileType == "video":
                tmp_meme_path = TMP_FOLDER + 'tmp_meme.mp4'
                context.bot.send_video(chat_id=chat_id,
                                       video=io.BytesIO(response.file),
                                       caption="Dank meme " + response.name
                                       )
            else:
                context.bot.send_message(chat_id=chat_id,
                                         text="file type received: " + response.fileType)
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text="No meme found in this chat")
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="Memes are not activated on this channel. An admin can turn them on with /set_function meme")


def _add_meme_video(message, context: CallbackContext):
    logging.info("adding dank meme - video")

    file_as_bytes, size = general_end_functions.download_video_bytearray(message, context)
    chat_id = message.chat_id
    chat_title = str(message.chat.title)
    file_classification = "meme"
    file_type = "video"
    author = "anon"  # update.message.from_user.name
    time_creation = int(time.time())
    file = filehandler_pb2.FileUploadRequest(chatId=chat_id,
                                             chatTitle=chat_title,
                                             fileClassification=file_classification,
                                             fileType=file_type,
                                             author=author,
                                             timeCreation=time_creation,
                                             file=bytes(file_as_bytes))
    response = grpc_file_handler_client.UploadFile(file)
    return response


def _add_meme_photo(message, context: CallbackContext):
    logging.info("adding dank meme - image")

    file_as_bytes = general_end_functions.download_image_bytearray(message, context)
    chat_id = message.chat_id
    chat_title = str(message.chat.title)
    file_classification = "meme"
    file_type = "image"
    author = "anon"  # update.message.from_user.name
    time_creation = int(time.time())
    logging.info("adding dank meme")
    file = filehandler_pb2.FileUploadRequest(chatId=chat_id,
                                             chatTitle=chat_title,
                                             fileClassification=file_classification,
                                             fileType=file_type,
                                             author=author,
                                             timeCreation=time_creation,
                                             file=bytes(file_as_bytes))
    response = grpc_file_handler_client.UploadFile(file)
    return response


def add_meme_reply(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    # check if quoted message
    if _is_meme_authorized_on_channel(chat_id):
        if update.message.reply_to_message is not None:
            original_message = update.message.reply_to_message
            pprint.pprint(original_message.photo)
            pprint.pprint(original_message.video)
            if original_message.photo:
                response = _add_meme_photo(original_message, context)
                pprint.pprint(response)
                if not response.status:
                    context.bot.send_message(chat_id=chat_id, text="👎 Error uploading meme: " + response.message)
                else:
                    context.bot.send_message(chat_id=chat_id, text="👍 Added meme as " + response.message)
            elif original_message.video:
                response = _add_meme_video(original_message, context)
                pprint.pprint(response)
                if not response.status:
                    context.bot.send_message(chat_id=chat_id, text="👎 Error uploading meme: " + response.message)
                else:
                    context.bot.send_message(chat_id=chat_id, text="👍 Added meme as " + response.message)
            else:
                context.bot.send_message(chat_id=chat_id,
                                         text="Message replied to doesn't seem to contain accepted media (video or photo)")
        else:
            context.bot.send_message(chat_id=chat_id,
                                     text="Message replied to doesn't seem to contain accepted media (video or photo)")
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="Memes are not activated on this channel. An admin can turn them on with /set_function meme")


def handle_new_video(update: Update, context: CallbackContext):
    try:
        caption = update['message']['caption']
        if caption == "/add_meme":
            chat_id = update.message.chat_id

            try:
                response = _add_meme_video(update.message, context)
                pprint.pprint(response)
                if response.status == False:
                    context.bot.send_message(chat_id=chat_id, text="👎 Error uploading meme: " + response.message)
                else:
                    context.bot.send_message(chat_id=chat_id, text="👍 Added meme as " + response.message)
            except IndexError:
                error_msg = "Adding image failed: no image provided. Make sure to send it as a file and not an image."
                context.bot.send_message(chat_id=chat_id, text=error_msg)
        else:
            pass
    except KeyError:
        pass


def handle_new_image(update: Update, context: CallbackContext):
    try:
        caption = update['message']['caption']
        if caption == "/add_meme":
            chat_id = update.message.chat_id
            if _is_meme_authorized_on_channel(chat_id):
                try:
                    response = _add_meme_photo(update.message, context)
                    pprint.pprint(response)
                    if response.status == False:
                        context.bot.send_message(chat_id=chat_id, text="👎 Error uploading meme: " + response.message)
                    else:
                        context.bot.send_message(chat_id=chat_id, text="👍 Added meme as " + response.message)
                except IndexError:
                    error_msg = "Adding image failed: no image provided. Make sure to send it as a file and not an image."
                    context.bot.send_message(chat_id=chat_id, text=error_msg)
                else:
                    context.bot.send_message(chat_id=chat_id,
                                             text="Memes are not activated on this channel. An admin can turn them on with /set_function meme")
        else:
            pass
    except KeyError:
        pass


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


def refresh_price(update: Update, context: CallbackContext):
    __log_channel(update.callback_query.message.chat, "refresh_price")
    print("refreshing price")
    query = update.callback_query.data
    contract_from_ticker = query.split('r_p_')[1].split('_t')[0]
    token_name = query.split('_t_')[1]
    if token_name.upper() in symbol_gecko:
        value = symbol_gecko.get(token_name.upper())
        message = general_end_functions.get_price_gecko(value)
        button_list_price = [
            [InlineKeyboardButton('refresh', callback_data='r_p_' + "null" + "_t_" + token_name)]]
        reply_markup_price = InlineKeyboardMarkup(button_list_price)
    else:
        message = general_end_functions.get_price(contract_from_ticker, "", graphql_client_eth,
                                                  graphql_client_uni,
                                                  token_name.upper(), decimals, uni_wrapper)
        button_list_price = [[InlineKeyboardButton('refresh', callback_data='refresh_price_' + contract_from_ticker)]]
        reply_markup_price = InlineKeyboardMarkup(button_list_price)
    if update.callback_query.message.text != message:
        update.callback_query.edit_message_text(text=message, parse_mode='html', reply_markup=reply_markup_price,
                                                disable_web_page_preview=True)


def delete_message(update: Update, context: CallbackContext):
    print("deleting chart")
    chat_id = update.callback_query.message.chat_id
    message_id = update.callback_query.message.message_id
    context.bot.delete_message(chat_id=chat_id, message_id=message_id)


def _stop_if_refreshing_too_early(context, chat_id, token_chat_id, t_to) -> bool:
    global charts_time_refresh
    members_count = context.bot.get_chat_members_count(chat_id)
    logging.info("members count: " + str(members_count))
    if members_count >= 100:
        if token_chat_id not in charts_time_refresh:
            charts_time_refresh[token_chat_id] = t_to
            return False
        else:
            last_time = charts_time_refresh[token_chat_id]
            if t_to - last_time < 30:
                logging.debug("requesting chart refresh too early")
                return False
            else:
                charts_time_refresh[token_chat_id] = t_to
                return True
    else:
        return False


def refresh_chart(update: Update, context: CallbackContext):
    __log_channel(update.callback_query.message.chat, "refresh_chart")
    print("refreshing chart")
    query = update.callback_query.data
    chat_id = update.callback_query.message.chat_id

    k_hours = int(re.search(r'\d+', query.split('h:')[1]).group())
    k_days = int(re.search(r'\d+', query.split('d:')[1]).group())
    token = re.search(r'([A-Za-z0-9-]+)', query.split('t:')[1]).group()[:-1]
    options = query.split('o:')[1].split("//")
    token_chat_id = str(chat_id) + "_" + token

    t_to = int(time.time())
    if not _stop_if_refreshing_too_early(context, chat_id, token_chat_id, t_to):
        t_from = t_to - (k_days * 3600 * 24) - (k_hours * 3600)

        message_id = update.callback_query.message.message_id
        trending = util.get_banner_txt(zerorpc_client_data_aggregator)
        maybe_bottom_text = text_if_coin_being_watched(token)
        (message, path, reply_markup_chart) = general_end_functions.send_candlestick_pyplot(token, charts_path, k_days,
                                                                                            k_hours, t_from, t_to,
                                                                                            txt=trending,
                                                                                            options=options,
                                                                                            with_ad=maybe_bottom_text)
        context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'), caption=message, parse_mode="html",
                               reply_markup=reply_markup_chart)
        context.bot.delete_message(chat_id=chat_id, message_id=message_id)


# sends the current biz threads
def get_biz(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "biz")
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    base_url = "boards.4channel.org/biz/thread/"
    message = """Plz go bump the /biz/ threads:
"""
    if len(query_received) == 2:
        word = query_received[-1]
        word_regex_friendly = word.replace('$', '\\$')
        threads_ids = scrap_websites_util.get_biz_threads(re.compile(word_regex_friendly))
        for thread_id in threads_ids:
            excerpt = (thread_id[2] + " | " + thread_id[1])
            parsed_excerpt = util.cleanhtml(excerpt)
            message += base_url + str(thread_id[0]) + " -- " + parsed_excerpt[0: 100] + "[...] \n"
        if not threads_ids:
            no_thread_message = "No current /biz/ thread containing the word $WORD. You can make one at https://boards.4channel.org/biz/.".replace(
                "$WORD", word)
            context.bot.send_message(chat_id=chat_id, text=no_thread_message, disable_web_page_preview=True)
        else:
            context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)
            context.bot.send_message(chat_id=announcement_channel_id, text=message, disable_web_page_preview=True)
    elif len(query_received) == 1:  # TODO: merge all that
        word, addr = __get_default_token_channel(chat_id)
        if word is None or word.lower() == "null":
            context.bot.send_message(chat_id=chat_id,
                                     text='No default ticker set up for this channel. An admin can add one with the /set_default_token command. In the meantime, you can use /biz by doing /biz KEYWORD')
        else:
            word_regex_friendly = word.replace('$', '\\$')
            threads_ids = scrap_websites_util.get_biz_threads(re.compile(word_regex_friendly))
            for thread_id in threads_ids:
                excerpt = thread_id[2] + " | " + thread_id[1]
                message += base_url + str(thread_id[0]) + " -- " + excerpt[0: 100] + "[...] \n"
            if not threads_ids:
                no_thread_message = "No current /biz/ thread containing the word $WORD. You can make one at https://boards.4channel.org/biz/.".replace(
                    "$WORD", word)
                context.bot.send_message(chat_id=chat_id, text=no_thread_message, disable_web_page_preview=True)
            else:
                context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)
                context.bot.send_message(chat_id=announcement_channel_id, text=message, disable_web_page_preview=True)


    else:
        context.bot.send_message(chat_id=chat_id,
                                 text='Please use the format /biz WORD')


def get_twitter(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "twitter")
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    if len(query_received) == 2:
        ticker = query_received[-1]
        res = scrap_websites_util.get_last_tweets(twitter, ticker)
        context.bot.send_message(chat_id=chat_id, text=res, parse_mode='html', disable_web_page_preview=True)
        context.bot.send_message(chat_id=announcement_channel_id, text=res, parse_mode='html',
                                 disable_web_page_preview=True)
    elif len(query_received) == 1:
        ticker, addr = __get_default_token_channel(chat_id)
        if ticker is None or ticker.lower() == "null":
            context.bot.send_message(chat_id=chat_id,
                                     text='No default ticker set up for this channel. An admin can add one with the /set_default_token command. In the meantime, you can use /twitter by doing /twitter TOKEN')
        else:
            res = scrap_websites_util.get_last_tweets(twitter, ticker)
            context.bot.send_message(chat_id=chat_id, text=res, parse_mode='html', disable_web_page_preview=True)
            context.bot.send_message(chat_id=announcement_channel_id, text=res, parse_mode='html',
                                     disable_web_page_preview=True)
    else:
        context.bot.send_message(chat_id=chat_id, text="Please use the format /twitter TOKEN_TICKER.",
                                 parse_mode='html', disable_web_page_preview=True)


def do_convert(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "convert")
    query_received = update.message.text.split(' ')
    chat_id = update.message.chat_id
    message = general_end_functions.convert_to_something(query_received, graphql_client_uni, graphql_client_eth)
    context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True, parse_mode='html')


def balance_token_in_wallet(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "balance")
    query_received = update.message.text.split(' ')
    chat_id = update.message.chat_id
    if len(query_received) == 3:
        wallet = query_received[1]
        ticker = query_received[2]
        amount, amount_usd = general_end_functions.get_balance_token_wallet(w3, wallet, ticker, graphql_client_uni,
                                                                            graphql_client_eth)
        message = "wallet " + str(wallet)[0:3] + '[...]' + " contains <b>" + str(
            util.pretty_number(amount)) + " " + ticker + " = " + str(amount_usd) + " usd</b>."
        context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')
        # res = con
    elif len(query_received) == 2 and query_received[1] == "jackpot":
        wallet = "0x9284b7fb2c842666dae4e87ddb49106b72820d26"
        ticker = "LUCKY"
        amount, amount_usd = general_end_functions.get_balance_token_wallet(w3, wallet, ticker, graphql_client_uni,
                                                                            graphql_client_eth)
        message = "<b>🍀 Lucky Daily Jackpot Balance</b>," + str(amount) + " " + ticker + " = <b>" + str(
            amount_usd) + " usd</b>."
        context.bot.send_message(chat_id=chat_id, text=message, parse_mode="html")
    elif len(query_received) == 2:
        wallet = query_received[1]
        channel_token = __get_default_token_channel(chat_id)
        if channel_token is not None:
            ticker = channel_token[0]
            amount, amount_usd = general_end_functions.get_balance_token_wallet(w3, wallet, ticker, graphql_client_uni,
                                                                                graphql_client_eth)
            message = "wallet " + str(wallet)[0:3] + '[...]' + " contains <b>" + str(
                util.pretty_number(amount)) + " " + ticker + " = " + str(amount_usd) + " usd</b>."
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html')
    else:
        context.bot.send_message(chat_id=chat_id, text="Wrong arguments. Please use /balance WALLET TOKEN")


def get_gas_average(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "gas")
    chat_id = update.message.chat_id
    asap, fast, average, low, price_one_tx_asap_eth, price_one_tx_asap_usd = general_end_functions.get_gas_price(True)
    message = "<b>Gas price:</b><code>" + \
              "\nASAP: " + str(asap) + \
              "\nFast: " + str(fast) + \
              "\nAvg : " + str(average) + \
              "\nSlow: " + str(low) + \
              "\nASAP tx: Ξ" + str(price_one_tx_asap_eth)[0:8] + " | $" + str(price_one_tx_asap_usd)[0:4] + "</code>"
    context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True, parse_mode='html')
    context.bot.send_message(chat_id=announcement_channel_id, text=message, disable_web_page_preview=True,
                             parse_mode='html')


def get_time_to(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "timeto")
    chat_id = update.message.chat_id
    query_received = update.message.text[7:]
    if query_received == "jackpot" or query_received == " jackpot":
        query_received = "7 pm CST"
    elif query_received.lower() == "christmas" or query_received.lower() == " christmas":
        logging.info("requesting timeto christmas")
        query_received = "25 december"

    higher, time_to = time_util.get_time_diff(query_received)
    word = ' is ' if higher else ' was '
    message = str(query_received) + word + str(time_to) + " from now."
    context.bot.send_message(chat_id=chat_id, text=message, disable_web_page_preview=True)


# TODO: fix stuff with default token not being fully used
def get_latest_actions(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "last_actions")
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    if len(query_received) == 1:
        default_token = __get_default_token_channel(chat_id)
        if default_token is not None:
            latest_actions_pretty = general_end_functions.get_last_actions_token_in_eth_pair(default_token[0],
                                                                                             uni_wrapper,
                                                                                             graphql_client_uni,
                                                                                             graphql_client_eth)
            util.create_and_send_vote(default_token[0], "actions", update.message.from_user.name,
                                      zerorpc_client_data_aggregator)
            context.bot.send_message(chat_id=chat_id, text=latest_actions_pretty, disable_web_page_preview=True,
                                     parse_mode='html')
            context.bot.send_message(chat_id=announcement_channel_id, text=latest_actions_pretty,
                                     disable_web_page_preview=True, parse_mode='html')
        else:
            context.bot.send_message(chat_id=chat_id, text=rejection_no_default_ticker_message)
    else:
        default_token = __get_default_token_channel(chat_id)
        if default_token is not None:
            ticker, addr = default_token[0], default_token[1]
        else:
            ticker, addr = None, None
        token, options = queries_parser.analyze_query_last_actions(update.message.text, ticker)
        if token is not None:

            latest_actions_pretty = general_end_functions.get_last_actions_token_in_eth_pair(token, uni_wrapper,
                                                                                             graphql_client_uni,
                                                                                             graphql_client_eth,
                                                                                             None, options)

            util.create_and_send_vote(token, "actions", update.message.from_user.name, zerorpc_client_data_aggregator)
            context.bot.send_message(chat_id=chat_id, text=latest_actions_pretty, disable_web_page_preview=True,
                                     parse_mode='html')
            context.bot.send_message(chat_id=announcement_channel_id, text=latest_actions_pretty,
                                     disable_web_page_preview=True, parse_mode='html')
        else:
            context.bot.send_message(chat_id=chat_id, text=rejection_no_default_ticker_message)


def get_trending(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "trending")
    chat_id = update.message.chat_id
    res = zerorpc_client_data_aggregator.view_trending()
    context.bot.send_message(chat_id=chat_id, text=res)
    context.bot.send_message(chat_id=announcement_channel_id, text=res)


def get_gas_spent(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "gas_spent")
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    if len(query_received) >= 2:
        addr, options = queries_parser.analyze_query_gas_spent(update.message.text)
        res = general_end_functions.get_gas_spent(addr, options)
        context.bot.send_message(chat_id=chat_id, text=res)
    else:
        context.bot.send_message(chat_id=chat_id,
                                 text="Please use the format /gas_spent address (ex: /gas_spent 0xBE0eB53F46cd790Cd13851d5EFf43D12404d33E8)")


# ADMIN STUFF
def set_faq(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "set_faq")
    chat_id = update.message.chat_id
    query_received = update.message.text[8:]
    if __is_user_admin(context, update):
        if query_received != "":
            faq = query_received
            res = zerorpc_client_data_aggregator.set_faq(chat_id, faq)
            message_info = res + '\n' + message_faq_additional
            context.bot.send_message(chat_id=chat_id, text=message_info, parse_mode='html',
                                     disable_web_page_preview=True)
        else:
            context.bot.send_message(chat_id=chat_id, text="Please use the format /set_faq FAQ")
    else:
        context.bot.send_message(chat_id=chat_id, text="Only an admin can do that you silly.")


def get_the_faq(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "faq")
    chat_id = update.message.chat_id
    res = __get_faq_channel(chat_id)
    if res == "null" or res is None:
        res = message_faq_empty
    try:
        context.bot.send_message(chat_id=chat_id, text=res, parse_mode='html', disable_web_page_preview=True)
    except BadRequest:
        header = "Looks like some html tags are not properly set. Here's the raw faq: \n"
        context.bot.send_message(chat_id=chat_id, text=header + res, disable_web_page_preview=True)


def __get_faq_channel(channel_id: int):
    res = zerorpc_client_data_aggregator.get_faq(channel_id)
    return res


def set_default_token(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "set_default_token")
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    if __is_user_admin(context, update):
        if len(query_received) == 2:
            ticker = query_received[1].upper()
            token_addr = requests_util.get_token_contract_address(ticker)
            logging.info("setting default channel " + str(chat_id) + " with address " + str(token_addr))
            res = zerorpc_client_data_aggregator.set_default_token(chat_id, ticker, token_addr)
            context.bot.send_message(chat_id=chat_id, text=res)
        elif len(query_received) == 3:
            ticker = query_received[1].upper()
            token_addr = query_received[2].lower()
            logging.info("setting default channel " + str(chat_id) + " with address " + str(token_addr))
            res = zerorpc_client_data_aggregator.set_default_token(chat_id, ticker, token_addr)
            context.bot.send_message(chat_id=chat_id, text=res)

        else:
            context.bot.send_message(chat_id=chat_id, text="Please use the format /set_default_token TICKER (address)")
    else:
        context.bot.send_message(chat_id=chat_id, text="Only an admin can do that you silly.")


def get_default_token(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "default_token")
    chat_id = update.message.chat_id
    ticker, addr = __get_default_token_channel(chat_id)
    context.bot.send_message(chat_id=chat_id, text="ticker: " + str(ticker) + " - addr: " + str(addr))


def __get_default_token_channel(channel_id: int):
    res = zerorpc_client_data_aggregator.get_default_token(channel_id)
    if res is not None:
        logging.debug("Default token channel " + str(channel_id) + " is " + str(res[0]) + " - " + str(res[1]))
    else:
        logging.debug("Default token channel " + str(channel_id) + " is None")
    return res


def set_function(update: Update, context: CallbackContext):
    channel_type = update.message.chat.type
    __log_channel(update.message.chat, "set_function")
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    if __is_user_admin(context, update) or channel_type == "private":
        if len(query_received) == 2:
            arg = query_received[1]
            if arg.lower() == "meme":
                res = not _is_meme_authorized_on_channel(chat_id)
                pprint.pprint(res)
                _update_meme_status_on_channel(chat_id, res)
                if res:
                    context.bot.send_message(chat_id=chat_id,
                                             text="Memes are now activated. You can now:\nAdd some with /add_meme\nView one random with /get_meme\nRemove one with /delete_meme (only for admins).")
                else:
                    context.bot.send_message(chat_id=chat_id,
                                             text="Memes are now de-activated. You can always go back with /set_function meme (only for admins)")
        else:
            context.bot.send_message(chat_id=chat_id, text="Wrongly formatted query")
    else:
        context.bot.send_message(chat_id=chat_id, text="This function is only available to admins or in private chat")


def set_monitor(update: Update, context: CallbackContext):
    channel_type = update.message.chat.type
    __log_channel(update.message.chat, "set_monitor")
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    if __is_user_admin(context, update) or channel_type == "private":
        if len(query_received) == 2:
            ticker = query_received[1].upper()
            token_addr = requests_util.get_token_contract_address(ticker)
            message = "setting watcher for token actions (buys > 10eth) with address " + str(
                token_addr) + ". If it is not the correct address, please define it explicitly with /set_default_token TICKER ADDRESS"
            res = zerorpc_client_data_aggregator.add_monitor(chat_id, token_addr, "buy")
            context.bot.send_message(chat_id=chat_id, text=message)
        elif len(query_received) == 3:
            ticker = query_received[1].upper()
            token_addr = query_received[2].lower()
            message = "setting watcher for token actions (buys > 10eth) with address " + str(
                token_addr) + ". If it is not the correct address, please define it explicitly with /set_default_token TICKER ADDRESS"
            res = zerorpc_client_data_aggregator.add_monitor(chat_id, token_addr, "buy")
            context.bot.send_message(chat_id=chat_id, text=message)
    else:
        context.bot.send_message(chat_id=chat_id, text="Only admins can do that you silly")


def __is_user_admin(context, update):
    user = context.bot.get_chat_member(update.effective_chat.id, update.message.from_user.id)
    status = user.status
    username = user.user.username
    return status == 'administrator' or status == 'creator' or username == 'rotted_ben'


def get_chart_supply(update: Update, context: CallbackContext):
    __log_channel(update.message.chat, "chart_supply")
    chat_id = update.message.chat_id

    query_received = update.message.text.split(' ')
    default_ticker_channel = __get_default_token_channel(chat_id)
    ok = True
    if len(query_received) == 1 and (default_ticker_channel is None or default_ticker_channel == "null"):
        ok = False
    if default_ticker_channel is None or default_ticker_channel == "":
        default_ticker_channel = ""
    else:
        default_ticker_channel = default_ticker_channel[0]
    if ok:

        time_type, k_hours, k_days, tokens = commands_util.check_query(query_received, default_ticker_channel)

        if isinstance(tokens, list):
            tokens = tokens[0]

        ticker_supply_file_path = supply_file_path.replace("$TICKER", tokens.upper())
        ticker_supply_chart_path = supply_chart_path.replace("$TICKER", tokens.upper())

        current_token_nbr = general_end_functions.send_supply_single_pyplot(ticker_supply_file_path,
                                                                            k_days,
                                                                            k_hours,
                                                                            tokens,
                                                                            ticker_supply_chart_path)

        current_token_str = util.number_to_beautiful(current_token_nbr)

        msg_time = " " + str(k_days) + " day(s) " if k_days > 0 else " last " + str(k_hours) + " hour(s) "

        caption = "Supply of the last " + msg_time + ".\nCurrent supply: \n<b>" + tokens + ":</b> <pre>" + current_token_str + "</pre>"

        context.bot.send_photo(chat_id=chat_id,
                               photo=open(ticker_supply_chart_path, 'rb'),
                               caption=caption,
                               parse_mode="html")


def _is_meme_authorized_on_channel(channel_id: int) -> bool:
    return zerorpc_client_data_aggregator.get_meme_channel_value(channel_id)


def _update_meme_status_on_channel(channel_id: int, status: bool):
    return zerorpc_client_data_aggregator.update_meme_channel_value(channel_id, status)


@cached(cache=TTLCache(maxsize=1024, ttl=120))
def _is_coin_being_watched(ticker: str):
    return zerorpc_client_data_aggregator.is_coin_being_watched(ticker.upper())


def text_if_coin_being_watched(ticker: str, small=False):
    if _is_coin_being_watched(ticker):
        print(ticker + " is being watched")
        if small:
            return "➡ @TheFomoBot_" + ticker.upper() + "_actions ⬅"
        else:
            return "Live $" + ticker.upper() + " actions ➡ @TheFomoBot_" + ticker.upper() + "_actions ⬅"
    else:
        return None


def __log_channel(chat, method):
    now = datetime.now().strftime('%Y-%m-%d, %H')
    # today = datetime.today().strftime('%Y-%m-%d')
    chat_id = chat.id
    channel_type = chat.type
    chat_name = chat.title
    print("chat_id = " + str(chat_id) + " - type = " + str(channel_type) + " - chat_name =  " + str(
        chat_name) + " - method " + method)
    zerorpc_client_data_aggregator.log_action(chat_id, channel_type, str(chat_name), now,
                                              method)  # casting chat name to str in case it's None


def __did_user_vote_too_much(username, method, token):
    hashed_uname = util.get_hashed_uname(username)
    return zerorpc_client_data_aggregator.did_user_vote_too_much(hashed_uname, method, token.upper())


def callback_minute(context: CallbackContext):
    if IS_TEST_ENV:
        return
    channels_to_check = zerorpc_client_data_aggregator.get_all_monitors()
    print("checking monitors")
    now = round(time.time())
    last_min = now - (60 * 5) - 20

    new_list = dict()
    if channels_to_check is not None:
        for c in channels_to_check:
            if c[1].lower() in new_list:
                new_list[c[1].lower()] = new_list.get(c[1].lower()) + [c[0]]
            else:
                new_list[c[1].lower()] = [c[0]]

    for coin in new_list:
        # pprint.pprint(channel_mon)
        # channel = channel_mon[0]
        # coin = channel_mon[1]
        # monitor_type = channel_mon[2]
        options = ["buy", "whale"]
        pair = web3_util.does_pair_token_eth_exist(coin, uni_wrapper)
        latest_actions_pretty = requests_util.pretty_print_monitor_last_actions(last_min, coin, pair.lower(),
                                                                                graphql_client_uni, graphql_client_eth,
                                                                                uni_wrapper, options)
        if latest_actions_pretty is not None:
            maybe_bottom_text = text_if_coin_being_watched(coin)
            if maybe_bottom_text is not None and maybe_bottom_text != "":
                follow_up_message = "\n" + maybe_bottom_text
            else:
                follow_up_message = ""
            print("follow up message: " + follow_up_message)
            message = latest_actions_pretty + follow_up_message
            for channel in new_list[coin]:
                logging.info("sent latest actions to channel: " + str(channel))
                try:
                    context.bot.send_message(chat_id=channel, text=message, disable_web_page_preview=True,
                                             parse_mode='html')
                except ChatMigrated as err:
                    print("CHANNEL ID CHANGED: ", err)
                    pass


def translate_text(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    # check if quoted message
    if update.message.reply_to_message is not None:
        original_message = update.message.reply_to_message.text
        if len(query_received) == 1:
            language_to = "en"
        else:
            language_to = query_received[1]
        logging.info("translating " + original_message + " to " + language_to)
        translation = translation_util.pretty_translate(original_message, language_to)
        context.bot.send_message(chat_id=chat_id, text=translation, parse_mode='html', disable_web_page_preview=True)
    else:
        if len(query_received) <= 2:
            message = "To use this endpoint, either quote a message that you wish to translate, or do /translate LANGUAGE TEXT"
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html', disable_web_page_preview=True)
        else:
            language_to = query_received[1]
            original_message = ' '.join(query_received[2:])
            logging.info("translating " + original_message + " to " + language_to)
            translation = translation_util.pretty_translate(original_message, language_to)
            context.bot.send_message(chat_id=chat_id, text=translation, parse_mode='html',
                                     disable_web_page_preview=True)


def ask_wolfram(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    if len(query_received) == 1:
        context.bot.send_message(chat_id=chat_id, text="To use this method, please use /ask YOUR QUESTION")
    else:
        query = ' '.join(query_received[1:])
        res = wolfram_queries.ask_wolfram_raw(query, wolfram_client)
        context.bot.send_message(chat_id=chat_id, text=res[:4055], parse_mode='html', disable_web_page_preview=True)


def get_price_direct(update: Update, context: CallbackContext):
    command_list = ["p", "start", "charts", "chart", "c", "price", "twitter", "t", "biz", "b", "convert", "gas", "g",
                    "balance", "timeto", "last_actions", "l", "trending", "gas_spent", "tr", "translate", "ask",
                    "set_default_token", "get_default_token", "set_faq", "faq", "chart_supply", "set_monitor",
                    "restart", "ban"]
    chat_id = update.message.chat_id
    ticker = update.message.text.split(' ')[0][1:]
    if ticker not in command_list:  # should not be needed but keeping it just in case
        __log_channel(update.message.chat, "price_direct")
        if ticker.upper() in symbol_gecko:
            value = symbol_gecko.get(ticker.upper())
            message = general_end_functions.get_price_gecko(value)
            button_list_price = [
                [InlineKeyboardButton('refresh', callback_data='r_p_' + "null" + "_t_" + ticker)]]
            reply_markup_price = InlineKeyboardMarkup(button_list_price)
            context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html', reply_markup=reply_markup_price,
                                     disable_web_page_preview=True)
        else:
            contract_from_ticker = requests_util.get_token_contract_address(ticker)
            if contract_from_ticker is not None:
                util.create_and_send_vote(ticker, "price", update.message.from_user.name,
                                          zerorpc_client_data_aggregator)
                button_list_price = [
                    [InlineKeyboardButton('refresh', callback_data='r_p_' + contract_from_ticker + "_t_" + ticker)]]
                reply_markup_price = InlineKeyboardMarkup(button_list_price)
                message = general_end_functions.get_price(contract_from_ticker, "", graphql_client_eth,
                                                          graphql_client_uni, ticker.upper(), decimals, uni_wrapper)
                context.bot.send_message(chat_id=chat_id, text=message, parse_mode='html',
                                         reply_markup=reply_markup_price, disable_web_page_preview=True)
                if not __did_user_vote_too_much(update.message.from_user.name, "price", ticker):
                    context.bot.send_message(chat_id=announcement_channel_id, text=message, parse_mode='html',
                                             disable_web_page_preview=True)


def add_channel(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    if len(query_received) != 6:
        context.bot.send_message(chat_id=chat_id, text="wrong number of args")
    else:
        channel_id = query_received[1]
        ticker = query_received[2]
        contract = query_received[3]
        pair_contract = query_received[4]
        bot_assigned = query_received[5]
        zerorpc_client_data_aggregator.assign_bot_to(channel_id, ticker, contract, pair_contract, bot_assigned)
        context.bot.send_message(chat_id=chat_id, text="added channel")


def analyze_wallet(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query_received = update.message.text.split(' ')
    logging.info("Analyzing wallet ")
    if len(query_received) < 2:
        context.bot.send_message(chat_id=chat_id,
                                 text="To use this command, please use the syntax /analyze_wallet wallet (option: -simple), eg: /analyze_wallet 0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B")
    else:
        wallet = query_received[1]
        if not Web3.isAddress(wallet.lower()):
            context.bot.send_message(chat_id=chat_id,
                                     text="Provided wallet " + wallet + " is not a valid Ethereum address.")
        else:
            if '-simple' in query_received:
                res = general_end_functions.get_balance_wallet(wallet.lower(), pie_chart_wallet_path, True)
            else:
                res = general_end_functions.get_balance_wallet(wallet.lower(), pie_chart_wallet_path, False)
            context.bot.send_message(chat_id=chat_id, text=res[:4093], parse_mode='MarkdownV2',
                                     disable_web_page_preview=True)
            context.bot.send_photo(chat_id=chat_id, photo=open(pie_chart_wallet_path, 'rb'))


def error_callback(update, context):
    pprint.pprint(context.error)


# Stages
FIRST, SECOND = range(2)
# Callback data
ONE, TWO = range(2)
TRENDING = 'TRENDING'
GAS = 'SHOW_GAS_PRICE'

TRENDING_TXT = "🔥 Trending"
GAS_TXT = "⛽ Gas"

HOME_KEYBOARD = [
    [
        InlineKeyboardButton("🔥 Trending", callback_data=TRENDING),
        InlineKeyboardButton("⛽ Gas", callback_data=GAS),
    ]
]

REPLY_HOME_KEYBOARD = [
    [
        TRENDING_TXT,
        GAS_TXT
    ]
]


def send_chart_trending(update: Update, context: CallbackContext) -> None:
    """Prompt same text & keyboard as `start` does but not as new message"""
    # Get CallbackQuery from Update
    logging.info("Sending chart in private")
    query = update.callback_query
    chat_id = query.message.chat_id
    text_query = query.data[4:]
    pprint.pprint(text_query)
    token = text_query
    time_type, k_hours, k_days = 'd', 0, 3
    t_to = int(time.time())
    t_from = t_to - (k_days * 3600 * 24) - (k_hours * 3600)
    trending = util.get_banner_txt(zerorpc_client_data_aggregator)

    maybe_bottom_text = text_if_coin_being_watched(token)

    (message, path, reply_markup_chart) = general_end_functions.send_candlestick_pyplot(token, charts_path, k_days,
                                                                                        k_hours, t_from,
                                                                                        t_to, txt=trending,
                                                                                        options=["rsi"],
                                                                                        with_ad=maybe_bottom_text)

    util.create_and_send_vote(token, "chart", update.callback_query.message.from_user.name,
                              zerorpc_client_data_aggregator)
    token_chat_id = str(chat_id) + "_" + token
    charts_time_refresh[token_chat_id] = t_to
    context.bot.send_photo(chat_id=chat_id, photo=open(path, 'rb'), caption=message, parse_mode="html",
                           reply_markup=reply_markup_chart)
    query.answer()
    # Instead of sending a new message, edit the message that
    # originated the CallbackQuery. This gives the feeling of an
    # interactive menu.
    return FIRST


def _get_button_name(position, list):
    if position == 0:
        return "🥇 " + list[position]
    elif position == 1:
        return "🥈 " + list[position]
    elif position == 2:
        return "🥉 " + list[position]
    else:
        return emoji_number_dic.get(position + 1) + " " + list[position]


def view_trending(update: Update, context: CallbackContext):
    """Show new choice of buttons"""
    logging.info("Viewing trending charts")
    chat_id = update.message.chat_id
    res = zerorpc_client_data_aggregator.view_trending_raw()
    pprint.pprint(res)
    kb = [[], [], [], []]
    for i in range(0, len(res)):
        kb[i // 3].append(InlineKeyboardButton(_get_button_name(i, res), callback_data="TRD:" + res[i]))
    reply_markup = InlineKeyboardMarkup(kb)
    context.bot.send_message(text="Here's what's trending", chat_id=chat_id, reply_markup=reply_markup)
    # query.edit_message_text(
    #     text="Here a the trending tokens:", reply_markup=reply_markup
    # )
    return FIRST


def view_gas(update: Update, context: CallbackContext):
    """Show new choice of buttons"""
    logging.info("Viewing gas price")
    chat_id = update.message.chat_id
    asap, fast, average, low, price_one_tx_asap_eth, price_one_tx_asap_usd = general_end_functions.get_gas_price(True)
    message = "<b>Gas price:</b><code>" + \
              "\nASAP: " + str(asap) + \
              "\nFast: " + str(fast) + \
              "\nAvg : " + str(average) + \
              "\nSlow: " + str(low) + \
              "\nASAP tx: Ξ" + str(price_one_tx_asap_eth)[0:8] + " | $" + str(price_one_tx_asap_usd)[0:4] + "</code>"
    context.bot.send_message(text=message, chat_id=chat_id, parse_mode="html")
    return FIRST


def start_menu_private_conv(update: Update, context: CallbackContext) -> None:
    """Send message on `/start`."""
    # Get user that sent /start and log his name
    user = update.message.from_user
    logging.info("User %s started the conversation.", user.name)
    # Build InlineKeyboard where each button has a displayed text
    # and a string as callback_data
    # The keyboard is a list of button rows, where each row is in turn
    # a list (hence `[[...]]`).
    reply_markup = ReplyKeyboardMarkup(REPLY_HOME_KEYBOARD, resize_keyboard=True)
    # Send message with text and appended InlineKeyboard
    members_count = context.bot.get_chat_members_count(update.message.chat_id)
    if members_count > 2:
        get_start_message(update, context)
        return ConversationHandler.END
    else:
        update.message.reply_text("Choose your path", reply_markup=reply_markup)
        # Tell ConversationHandler that we're in state `FIRST` now
        return FIRST


def inlinequery(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    pprint.pprint(query)
    ticker = query.lower()

    if len(ticker) > 2:
        if ticker.upper() in symbol_gecko:
            value = symbol_gecko.get(ticker.upper())
            message = general_end_functions.get_price_gecko(value)
        else:
            contract_from_ticker = requests_util.get_token_contract_address(ticker)
            pprint.pprint(contract_from_ticker)
            if contract_from_ticker is None:
                message = "Ticker not found"
            else:
                message = general_end_functions.get_price(contract_from_ticker, "", graphql_client_eth,
                                                          graphql_client_uni, ticker.upper(), decimals, uni_wrapper)
        results = [
            InlineQueryResultArticle(
                id=uuid4(),
                title=ticker.upper(),
                input_message_content=InputTextMessageContent(
                    message, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                )
            )
        ]
        update.inline_query.answer(results, cache_time=60)
    else:
        res = [["btc", "Bitcoin", "https://lebitcoin.fr/logos/BC_Logo_.png"],
               ["eth", "Ethereum", "https://www.bitladon.fr/img/currency/ETH_groot.png"],
               ["link", "Chainlink", "https://firebounty.com/image/939-chainlink"],
               ["dot", "Polkadot",
                "https://assets.coingecko.com/coins/images/12171/small/aJGBjJFU_400x400.jpg?1597804776"]]
        results = []
        for i in range(0, len(res)):
            ticker = res[i][0]
            if ticker.upper() in symbol_gecko:
                value = symbol_gecko.get(ticker.upper())
                message = general_end_functions.get_price_gecko(value)
            else:
                contract_from_ticker = requests_util.get_token_contract_address(ticker)
                pprint.pprint(contract_from_ticker)
                if contract_from_ticker is None:
                    message = "Ticker not found"
                else:
                    message = general_end_functions.get_price(contract_from_ticker, "", graphql_client_eth,
                                                              graphql_client_uni, ticker.upper(), decimals, uni_wrapper)
            results.append(InlineQueryResultArticle(
                id=uuid4(),
                title=res[i][1],
                input_message_content=InputTextMessageContent(
                    message, parse_mode=ParseMode.HTML, disable_web_page_preview=True
                ),
                thumb_url=res[i][2]
            ))
        update.inline_query.answer(results, cache_time=60)


def main():
    global TELEGRAM_KEY
    global IS_TEST_ENV
    webhook_port = 8443
    webhook_url = 'https://' + SERVER_IP + ':' + str(webhook_port) + '/' + TELEGRAM_KEY
    if len(sys.argv) == 2:
        TELEGRAM_KEY = sys.argv[1]
        webhook_port = 88
        webhook_url = 'https://' + SERVER_IP + ':' + str(webhook_port) + '/' + TELEGRAM_KEY
        IS_TEST_ENV = True
    logging.info("webhook url is: " + webhook_url + " on port: " + str(webhook_port))
    pprint.pprint(TELEGRAM_WEBHOOK_PRIVATE_KEY_PATH)
    pprint.pprint(TELEGRAM_WEBHOOK_CERT_PATH)
    updater = Updater(TELEGRAM_KEY, use_context=True, workers=16)
    updater.start_webhook(listen='0.0.0.0',
                          port=webhook_port,
                          url_path=TELEGRAM_KEY,
                          key=TELEGRAM_WEBHOOK_PRIVATE_KEY_PATH,
                          cert=TELEGRAM_WEBHOOK_CERT_PATH,
                          webhook_url=webhook_url)
    dp = updater.dispatcher

    def stop_and_restart():
        """Gracefully stop the Updater and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update, context):
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start_menu_private_conv),
                      MessageHandler(Filters.text([TRENDING_TXT]), view_trending, run_async=True),
                      MessageHandler(Filters.text([GAS_TXT]), view_gas, run_async=True),
                      ],
        states={
            FIRST: [
                # CommandHandler(TRENDING_TXT, view_trending),
                # CommandHandler(GAS_TXT, view_gas),
                CallbackQueryHandler(refresh_chart, pattern='refresh_chart(.*)'),
                CallbackQueryHandler(refresh_price, pattern='r_p_(.*)'),
                CallbackQueryHandler(delete_message, pattern='delete_message'),
                MessageHandler(Filters.text(TRENDING_TXT), view_trending, run_async=True),
                MessageHandler(Filters.text(GAS_TXT), view_gas, run_async=True),
                CallbackQueryHandler(send_chart_trending, pattern='TRD:(.*)'),
            ]
        },
        fallbacks=[CommandHandler('start', get_start_message)],
        allow_reentry=True
    )

    dp.add_handler(conv_handler)

    # dp.add_error_handler(error_callback)
    dp.add_handler(CommandHandler('start', get_start_message))
    dp.add_handler(CommandHandler(['charts', 'chart', 'c'], get_candlestick, run_async=True))
    dp.add_handler(CommandHandler(['price', 'p'], get_price_token, run_async=True))
    dp.add_handler(CommandHandler(['twitter', 't'], get_twitter, run_async=True))
    dp.add_handler(CommandHandler(['biz', 'b'], get_biz, run_async=True))
    dp.add_handler(CommandHandler('convert', do_convert, run_async=True))
    dp.add_handler(CommandHandler(['gas', 'g'], get_gas_average, run_async=True))
    dp.add_handler(CommandHandler('balance', balance_token_in_wallet, run_async=True))
    dp.add_handler(CommandHandler('timeto', get_time_to))
    dp.add_handler(CommandHandler(['last_actions', 'l'], get_latest_actions, run_async=True))
    dp.add_handler(CommandHandler('trending', get_trending, run_async=True))
    dp.add_handler(CommandHandler('gas_spent', get_gas_spent, run_async=True))
    dp.add_handler(CommandHandler(['tr', 'translate'], translate_text, run_async=True))
    dp.add_handler(CommandHandler(['ask'], ask_wolfram, run_async=True))
    dp.add_handler(CommandHandler(['analyze_wallet'], analyze_wallet, run_async=True))
    # dank memes
    dp.add_handler(CommandHandler(['get_meme'], get_meme, run_async=True))
    dp.add_handler(CommandHandler(['add_meme'], add_meme_reply, run_async=True))
    dp.add_handler(CommandHandler(['delete_meme'], delete_meme, run_async=True))
    # customoization stuff
    dp.add_handler(CommandHandler('set_default_token', set_default_token))
    dp.add_handler(CommandHandler('get_default_token', get_default_token))
    dp.add_handler(CommandHandler('set_faq', set_faq))
    dp.add_handler(CommandHandler('faq', get_the_faq, run_async=True))
    dp.add_handler(CommandHandler('chart_supply', get_chart_supply, run_async=True))
    dp.add_handler(CommandHandler('set_monitor', set_monitor, run_async=False))
    dp.add_handler(CommandHandler('set_function', set_function, run_async=False))
    # dp.add_handler(CommandHandler('stop_monitor', stop_monitor, run_async=False))
    # callbacks queries
    dp.add_handler(CallbackQueryHandler(refresh_chart, pattern='refresh_chart(.*)', run_async=True))
    dp.add_handler(CallbackQueryHandler(refresh_price, pattern='r_p_(.*)', run_async=True))
    dp.add_handler(CallbackQueryHandler(delete_message, pattern='delete_message', run_async=True))

    dp.add_handler(MessageHandler(Filters.photo, handle_new_image, run_async=True))
    dp.add_handler(MessageHandler(Filters.video, handle_new_video, run_async=True))
    # admin stuff
    dp.add_handler(CommandHandler('restart', restart, filters=Filters.user(username='@rotted_ben')))
    dp.add_handler(CommandHandler('add_channel', add_channel, filters=Filters.user(username='@rotted_ben')))

    # inline query
    dp.add_handler(InlineQueryHandler(inlinequery))

    dp.add_handler(MessageHandler(Filters.command, get_price_direct, run_async=True))

    j = updater.job_queue
    if not IS_TEST_ENV:
        j.run_repeating(callback_minute, interval=check_big_buys_interval_seconds, first=15)

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
gas_spent - (/gas_spent WALLET (optional: number of days)) Shows how much gas a wallet has spent on a transaction
faq - Print the FAQ.
convert - <AMOUNT> <TICKER> option(<TICKER>) convert amount of ticker to usd (and to the second ticker if specified). 
balance - <WALLET> <TICKER> check how much an address has of a specific coin.
timeto - time until date passed as argument.
last_actions - <TICKER> get the last trades / liq events of the coin.
trending - See which coins are trending in dextrends.
analyze_wallet - Provides analytics about a wallet (eg /analyze_wallet 0xbA1504000B5aC6cE413A1626d4833857Dd7311a0)
translate - <LANGUAGE_TO> <TEXT> Translate a text into the desired language.
add_meme - Add a meme
get_meme - Get a random meme
set_function - Admin functionalities (like /set_function meme)
"""
