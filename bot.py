import logging

import telegram
import tweepy
import re
from pytz import timezone, utc
from telegram import Bot
from telegram.error import TelegramError

from models import TelegramChat, TwitterUser
from util import escape_markdown, prepare_tweet_text


class TwitterForwarderBot(Bot):

    def __init__(self, token, tweepy_api_object, update_offset=0):
        super().__init__(token=token)
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("Initializing")
        self.update_offset = update_offset
        self.tw = tweepy_api_object

    def reply(self, update, text, *args, **kwargs):
        self.sendMessage(chat_id=update.message.chat.id, text=text, *args, **kwargs)

    def send_tweet(self, chat, tweet):
        try:
            # Check if chars/words exist in tweet
            filters = (
                '$', '#', '%', 'short', 'long', 'buy', 'sell', 'profit', 'profits', 'loss', 'losses', 'bull', 'bear',
                'bullish', 'bearish', 'btc', 'target', 'targets', 'price', 'bottom', 'top', 'entry', 'exit', 'time',
                'timeframe', 'support', 'resistance', 's/r', 'r/r', 'dollar', 'rejection', 'line', 'level', 'levels',
                'pump', 'pumped', 'dump', 'dumped', 'capitulation', 'analysis', 'study', 'forecast', 'test', 'testing',
                'tested', 'backtest', 'supply', 'demand', 'distribution', 'zone', 'zones', 'area', 'areas', 'candle',
                'candles', 'signal', 'signals', 'uptrend', 'downtrend', 'reversal', 'reversals', 'alt', 'season',
                'floor',
                'free', 'hedge', 'pair', 'open interest', 'funding')

            words = re.sub('(@|\/)\w*\d\w*', '', tweet.text)

            self.logger.debug("Sending tweet {} to chat {}...".format(
                tweet.tw_id, chat.chat_id
            ))

            '''
            Use a soft-hyphen to put an invisible link to the first
            image in the tweet, which will then be displayed as preview
            '''
            photo_url = ''
            if tweet.photo_url:
                photo_url = '[\xad](%s)' % tweet.photo_url

            created_dt = utc.localize(tweet.created_at)
            if chat.timezone_name is not None:
                tz = timezone(chat.timezone_name)
                created_dt = created_dt.astimezone(tz)
            created_at = created_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
            text = f"{photo_url}*{escape_markdown(tweet.name)}* " \
                   f"([@{tweet.screen_name}](https://twitter.com/{tweet.screen_name})):\n\n" \
                   f"{prepare_tweet_text(tweet.text)}{tweet.replied_text}\n\n" \
                   f"[View tweet](https://twitter.com/{tweet.screen_name}/status/{tweet.tw_id})"

            if any(x in words.lower() for x in filters) and tweet.text[:1] != '@' and tweet.text[:2] != 'RT':
                self.sendMessage(chat_id=-1001662252448, disable_web_page_preview=not photo_url, text=text,
                                 parse_mode=telegram.ParseMode.MARKDOWN)
            else:
                self.sendMessage(chat_id=-1001199638566, disable_web_page_preview=not photo_url, text=text,
                                 parse_mode=telegram.ParseMode.MARKDOWN)

        except TelegramError as e:
            self.logger.info("Couldn't send tweet {} to chat {}: {}".format(
                tweet.tw_id, chat.chat_id, e.message
            ))

            delet_this = None

            if e.message == 'Bad Request: group chat was migrated to a supergroup chat':
                delet_this = True

            if e.message == "Unauthorized":
                delet_this = True

            if delet_this:
                self.logger.info("Marking chat for deletion")
                chat.delete_soon = True
                chat.save()

    def get_chat(self, tg_chat):
        db_chat, _created = TelegramChat.get_or_create(
            chat_id=tg_chat.id,
            tg_type=tg_chat.type,
        )
        return db_chat

    def get_tw_user(self, tw_username):
        try:
            tw_user = self.tw.get_user(tw_username)
        except tweepy.error.TweepError as err:
            self.logger.error(err)
            return None

        db_user, _created = TwitterUser.get_or_create(
            screen_name=tw_user.screen_name,
            defaults={
                'name': tw_user.name,
            },
        )

        if not _created:
            if db_user.name != tw_user.name:
                db_user.name = tw_user.name
                db_user.save()

        return db_user
