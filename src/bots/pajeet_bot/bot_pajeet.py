import sys
import os


from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, CallbackQueryHandler, Filters, MessageHandler, \
    ConversationHandler, InlineQueryHandler
from telegram.inline.inlinequeryresultarticle import InlineQueryResultArticle
from telegram.inline.inputtextmessagecontent import InputTextMessageContent
from telegram.parsemode import ParseMode
from telegram.utils.helpers import escape_markdown

from telegram.ext.dispatcher import run_async
from telegram.error import ChatMigrated, BadRequest
from uuid import uuid4
import random

import logging

BASE_PATH = os.environ.get('BASE_PATH')
sys.path.insert(1, BASE_PATH + '/telegram-bots/src')

TELEGRAM_KEY = os.environ.get('PAJEET_TELEGRAM_KEY')

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')



def inline_query(update: Update, context: CallbackContext) -> None:
    query = update.inline_query.query
    message_start = "I am "
    if query != "":
        message_start = query + " is "

    n = random.randint(0, 100)
    message = message_start + str(n) + "% pajeet!"
    results = [
        InlineQueryResultArticle(
            id=uuid4(),
            title="How pajeet are you?",
            description="Send you current pajeet level to the chat",
            input_message_content=InputTextMessageContent(
                message, parse_mode=ParseMode.HTML, disable_web_page_preview=True
            ),
            thumb_url='https://blog.umamiparis.com/wp-content/uploads/2020/01/shutterstock_197567537-2.jpg'
        )
    ]
    update.inline_query.answer(results, cache_time=60)


def main():
    updater = Updater(TELEGRAM_KEY, use_context=True, workers=1)
    dp = updater.dispatcher
    dp.add_handler(InlineQueryHandler(inline_query))


    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
