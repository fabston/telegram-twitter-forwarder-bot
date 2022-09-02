import logging

from telegram.ext import CommandHandler
from telegram.ext import Updater

from bot import TwitterForwarderBot
from commands import *
from job import FetchAndSendTweetsJob

from dotenv import load_dotenv
import os

from auth import twitter_auth

load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']

if __name__ == '__main__':
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.WARNING)

    logging.getLogger(TwitterForwarderBot.__name__).setLevel(logging.DEBUG)
    logging.getLogger(FetchAndSendTweetsJob.__name__).setLevel(logging.DEBUG)

    # initialize telegram API
    token = TELEGRAM_BOT_TOKEN
    updater = Updater(bot=TwitterForwarderBot(token, twitter_auth()))
    dispatcher = updater.dispatcher

    # set commands
    dispatcher.add_handler(CommandHandler('start', cmd_start))
    dispatcher.add_handler(CommandHandler('help', cmd_help))
    dispatcher.add_handler(CommandHandler('ping', cmd_ping))
    dispatcher.add_handler(CommandHandler('sub', cmd_sub, pass_args=True))
    dispatcher.add_handler(CommandHandler('unsub', cmd_unsub, pass_args=True))
    dispatcher.add_handler(CommandHandler('list', cmd_list))
    dispatcher.add_handler(CommandHandler('export', cmd_export))
    dispatcher.add_handler(CommandHandler('all', cmd_all))
    dispatcher.add_handler(CommandHandler('wipe', cmd_wipe))
    dispatcher.add_handler(CommandHandler('export_friends', cmd_export_friends))

    # put job
    queue = updater.job_queue
    queue.put(FetchAndSendTweetsJob(), next_t=0)

    # poll
    updater.start_polling()
