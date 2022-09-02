from dotenv import load_dotenv
import os
import tweepy

load_dotenv()
TELEGRAM_BOT_TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
TWITTER_CONSUMER_KEY = os.environ['TWITTER_CONSUMER_KEY']
TWITTER_CONSUMER_SECRET = os.environ['TWITTER_CONSUMER_SECRET']
TWITTER_ACCESS_TOKEN = os.environ['TWITTER_ACCESS_TOKEN']
TWITTER_ACCESS_TOKEN_SECRET = os.environ['TWITTER_ACCESS_TOKEN_SECRET']


def twitter_auth():
    try:
        auth = tweepy.OAuthHandler(TWITTER_CONSUMER_KEY, TWITTER_CONSUMER_SECRET)
    except KeyError as exc:
        var = exc.args[0]
        print(("The required configuration variable {} is missing. "
               "Please review .env").format(var))
        exit(123)

    try:
        auth.set_access_token(TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET)
    except KeyError as exc:
        var = exc.args[0]
        print(("The optional configuration variable {} is missing. "
               "Tweepy will be initialized in 'app-only' mode.").format(var))

    return tweepy.API(auth)
