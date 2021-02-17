import sys
import os
from gevent import monkey

monkey.patch_all()  # REALLY IMPORTANT: ALLOWS ZERORPC AND TG TO WORK TOGETHER

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots')

import eth_event

import time
from web3 import Web3
from pprint import pprint
from cachetools import cached, TTLCache
import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, Filters, MessageHandler, \
    ConversationHandler, InlineQueryHandler
from dataclasses import dataclass
from src.libraries.uniswap import Uniswap
import src.libraries.web3_calls as web3_utils
import src.libraries.util as lib_util

TELEGRAM_KEY = os.environ.get('MONITOR_WALLETS_TELEGRAM_KEY')
DICT_PATH = os.environ.get('WALLET_MONITOR_PATH')
provider_ws_url = os.environ.get('NODE_WS')
web3 = Web3(Web3.WebsocketProvider(provider_ws_url))
uni_wrapper = Uniswap(web3=web3)

weth_raw = "0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2".lower()
weth_checksum = Web3.toChecksumAddress(weth_raw)

last_block_num = web3.eth.getBlock('latest')['number']

uniswap_router_addr = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D".lower()

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

interesting_topic_str = 'd78ad95fa46c994b6551d0da85fc275fe613ce37657fb8d5e3d130840159d822'
interesting_topic = bytes.fromhex(interesting_topic_str)


with open(BASE_PATH + "telegram-bots/src/libraries/uniswap/assets/uniswap-v2/pair.abi", "r") as f:
    abi_pair = json.load(f)


start_message = """Welcome to <b>the FOMO wallet watcher bot</b>, your best fren when it comes to monitor whales / ruggers / andre's wallet.

How does it work?
<b>1/ Add an address to your watch list</b>
You add an address to your watch list with the <b>/monitor_wallet</b> command (for example: /monitor_wallet 0xa14964479ebf9cd336011ad80652b08cd83dfe3a)
(you can also <b>give it a name</b> by adding whatever you want after the address, like /monitor_wallet 0xa14964479ebf9cd336011ad80652b08cd83dfe3a big ape )
<b>2/ That's it!</b>
When the bot detects that the wallet made a new tx, it'll send you a message with the details of it.

You can <b>monitor multiple address</b> by simply calling the /monitor_wallet command multiple times.
Too many messages? You can stop monitoring an address with /remove_wallet.
Want to rename one wallet? Simply delete it and add it again!

<b>Want more kick-ass bots?</b> Check out @TheFomo_Bot
"""


def get_start_message(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    context.bot.send_message(chat_id=chat_id, text=start_message, parse_mode='html', disable_web_page_preview=True)


@dataclass(frozen=True)
class TokenInfo:
    addr: str
    name: str
    symbol: str
    decimals: int


@dataclass(frozen=True)
class Swap:
    buy: (TokenInfo, int)
    sell: (TokenInfo, int)
    sender: str
    to: str

    def buy_no_decimal(self):
        return self.buy[1] / 10 ** self.buy[0].decimals

    def sell_no_decimal(self):
        return self.sell[1] / 10 ** self.sell[0].decimals

    def buy_name(self, with_html_tags=False):
        symbol = self.buy[0].symbol
        if with_html_tags:
            return '<b>' + symbol + '</b>'
        else:
            return symbol

    def sell_name(self, with_html_tags=False):
        symbol = self.sell[0].symbol
        if with_html_tags:
            return '<b>' + symbol + '</b>'
        else:
            return symbol

    def to_string(self, with_html_tags=False, with_sender=False):
        message = "Bought " + lib_util.pretty_number(self.buy_no_decimal()) + ' ' + self.buy_name(with_html_tags) + ' for ' \
                  + lib_util.pretty_number(self.sell_no_decimal()) + ' ' + self.sell_name(with_html_tags)
        return message


def monitor_wallet(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query = update.message.text.split(' ')
    if len(query) < 2:
        context.bot.send_message(chat_id=chat_id, text="Error: wrong number of arguments. Please use the format /monitor_wallet ADDRESS")
    else:
        try:
            Web3.toChecksumAddress(query[1].lower())
        except Exception:
            context.bot.send_message(chat_id=chat_id, text="Error adding this wallet, please make sure that your're sending a correct eth address")
            return
        if len(query) > 2:
            custom_wallet_name = ' '.join(query[2:])
        else:
            custom_wallet_name = 'wallet'
        (res, res_message) = add_watch_user(str(chat_id), query[1], custom_wallet_name)
        if res:
            context.bot.send_message(chat_id=chat_id, text="Added this wallet to your list of watched wallets.")
        else:
            context.bot.send_message(chat_id=chat_id, text="Error adding this wallet: " +  res_message)



def remove_wallet(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query = update.message.text.split(' ')
    if len(query) != 2:
        context.bot.send_message(chat_id=chat_id, text="Error: wrong number of arguments. Please use the format /remove_wallet ADDRESS")
    else:
        try:
            Web3.toChecksumAddress(query[1].lower())
        except Exception:
            context.bot.send_message(chat_id=chat_id, text="Error removing this wallet, please make sure that your're sending a correct eth address")
            return
        remove_wallet_from_user(str(chat_id), query[1])
        context.bot.send_message(chat_id=chat_id, text="Removed this wallet to your list of watched wallets.")


def view_wallets(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    query = update.message.text.split(' ')
    if len(query) != 1:
        context.bot.send_message(chat_id=chat_id, text="Error: wrong number of arguments. Please use the format /view_wallets")
    else:
        list_wallets = get_list_watch_user(str(chat_id))
        pprint(list_wallets)
        if not list_wallets:
            context.bot.send_message(chat_id=chat_id, text="Not watching any wallet now")
        else:
            message = "You are currently monitoring the following wallets:\n"
            for wallet in list_wallets:
                message += json.dumps(wallet) + '\n'
            context.bot.send_message(chat_id=chat_id, text=message)


def get_list_watch_user(user):
    l_dict = get_list_watch_all()
    l_wallets_watch = []
    for key in l_dict.keys():
        pprint(key)
        if user in l_dict[key]:

            l_wallets_watch.append(key)
    return l_wallets_watch


@cached(cache=TTLCache(maxsize=1024, ttl=10))
def get_list_watch_user_cached(user):
    l_dict = get_list_watch_all()
    l_wallets_watch = []
    for key in l_dict.keys():
        if user in l_dict[key]:
            l_wallets_watch.append(key)
    return l_wallets_watch


def add_watch_user(user, address, custom_wallet_name) -> (bool, str):
    l_dict = get_list_watch_all()
    address = address.lower()
    user_dict = {user.lower(): {'name': custom_wallet_name}}
    if address in l_dict:
        old_value = l_dict[address]
        if user in old_value:
            logging.warning("User " + user.lower() + " tries to monitor the add " + address + " even though he already watches it")
            return False, "Address already registered by the user"
        else:
            old_value.append(user_dict)
            l_dict.update({address: old_value})
            update_list_wallet_watch(l_dict)
            return True, ""
    else:
        l_dict.update({address: [user_dict]})
        update_list_wallet_watch(l_dict)
        return True, ""


@cached(cache=TTLCache(maxsize=1024, ttl=10))
def get_list_watch_all(path=DICT_PATH):
    a_file = open(path, "r")
    output = json.loads(a_file.read())
    return output


def remove_wallet_from_user(user, address):
    l_dict = get_list_watch_all()
    address = address.lower()
    user = user.lower()
    if address in l_dict:
        old_value = l_dict[address]

        if user in old_value:
            old_value.remove(user)
            l_dict.update({address: old_value})
            update_list_wallet_watch(l_dict)
            return True, ""
        else:
            logging.warning("Can't remove addr " + address + " from user " + user + " cause can't find the user in the list of user that watch this addr")
            return False, "not in user list of watched addresses"
    else:
        logging.warning("Can't remove addr " + address + " from user " + user + " cause can't find the addr in the first place")
        return False, "not in user list of watched addresses"


def update_list_wallet_watch(dict_to_write, path=DICT_PATH):
    a_file = open(path, "w")
    json.dump(dict_to_write, a_file)
    a_file.close()


def parse_swap(log):
    addr_pair = log['address']
    [(t0_balance, t0_address), (t1_balance, t1_address), amount_lp] = web3_utils.get_lp_value(uni_wrapper, addr_pair)
    t0_info = web3_utils.get_token_info(uni_wrapper, t0_address)
    t0_info = TokenInfo(addr=t0_address, name=t0_info['name'], symbol=t0_info['symbol'], decimals=t0_info['decimals'])
    t1_info = web3_utils.get_token_info(uni_wrapper, t1_address)
    t1_info = TokenInfo(addr=t1_address, name=t1_info['name'], symbol=t1_info['symbol'], decimals=t1_info['decimals'])
    topic_map = eth_event.get_topic_map(abi_pair)
    swap = eth_event.decode_logs([log], topic_map)
    # pprint(swap)
    (amount0In, amount1Out, amount1In, amount0Out, to, sender) = (None, None, None, None, None, None)
    for value in swap[0]['data']:
        # pprint(value)
        if value['name'] == 'sender':
            sender = value['value']
        elif value['name'] == 'to':
            to = value['value']
        elif value['name'] == 'amount0In':
            amount0In = int(value['value'])
        elif value['name'] == 'amount0Out':
            amount0Out = int(value['value'])
        elif value['name'] == 'amount1In':
            amount1In = int(value['value'])
        elif value['name'] == 'amount1Out':
            amount1Out = int(value['value'])
    if None in [amount0In, amount1Out, amount1In, amount0Out, to, sender]:
        return None
    if amount0In > 0:
        return Swap((t1_info, amount1Out), (t0_info, amount0In), sender=to, to=sender)
    else:
        return Swap((t0_info, amount0Out), (t1_info, amount1In), sender=sender, to=to)

def get_swaps_of_tx_receipt(tx_receipt):
    tx_logs = tx_receipt['logs']
    swaps = []
    for log in tx_logs:
        if interesting_topic in log['topics']:
            swap = parse_swap(log)
            swaps.append(swap)
    return swaps


def concatenate_swaps(swaps, tx_from) -> Swap:
    if isinstance(swaps, Swap):
        return swaps
    else:
        swap_0 = swaps[0]
        swap_last = swaps[-1]
        sender = tx_from
        to = swap_last.to
        buy = swap_last.buy
        sell = swap_0.sell
        return Swap(buy=buy, sell=sell, to=to, sender=sender)


def parse_uniswap_tx(tx_receipt, tx_from):
    swaps = get_swaps_of_tx_receipt(tx_receipt)
    concatenanted_swap = concatenate_swaps(swaps, tx_from)
    return concatenanted_swap


def callback_get_block(context: CallbackContext):
    global last_block_num
    block = web3.eth.getBlock('latest')
    latest_block = int(block['number'])

    if last_block_num < latest_block:
        for block_num in range(last_block_num + 1, latest_block + 1):
            logging.info("analysing new block: " + str(block_num))
            block = web3.eth.getBlock(block_num)
            txs = block['transactions']
            for tx in txs:
                try:
                    res = web3.eth.getTransaction(tx)
                    if res is not None:
                        tx_hash = res['hash'].hex()
                        tx_from = res['from'].lower()
                        # pprint(tx_from)
                        tx_to = res['to'].lower()
                        watch_list = get_list_watch_all()
                        if tx_from in watch_list and watch_list[tx_from]:
                            message_second = ""
                            if tx_to == uniswap_router_addr:
                                tx_receipt = web3.eth.getTransactionReceipt(tx)
                                swap = parse_uniswap_tx(tx_receipt, tx_from)
                                message_second = "\n" + swap.to_string(True)
                                message_second += ' ( <a href="app.uniswap.org/#/swap?inputCurrency=' + swap.buy[0].addr + '&?outputCurrency=' + swap.sell[0].addr + \
                                           '">swap on uniswap</a> )'
                            for tg_account in watch_list[tx_from]:
                                watched_add_name = watch_list[tx_from][tg_account]['name']
                                message = 'Looks like one of your watched address <b>' + watched_add_name + '</b>(' + tx_from + ') just made a tx (<a href="etherscan.com/tx/' + tx_hash + '">etherscan</a> | <a href="https://app.zerion.io/' + tx_from + '/history">zerion</a>)'
                                if message_second != "":
                                    message = message + message_second
                                context.bot.send_message(chat_id=int(tg_account), text=message, parse_mode='html', disable_web_page_preview=True)
                                logging.info("Sent a message to " + tg_account)
                except Exception as e:
                    pass

            last_block_num = int(block['number'])
            logging.info("done analysing block")


def main():
    updater = Updater(TELEGRAM_KEY, use_context=True, workers=2)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler('start', get_start_message))
    dp.add_handler(CommandHandler('monitor_wallet', monitor_wallet))
    dp.add_handler(CommandHandler('view_wallets', view_wallets))
    dp.add_handler(CommandHandler('remove_wallet', remove_wallet))
    j = updater.job_queue
    j.run_repeating(callback_get_block, interval=15, first=5)
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()

commands = """
monitor_wallet - Start monitor a wallet.
view_wallets - View the list of wallets that you monitor.
remove_wallet - Remove one wallet from your watch list.
"""

