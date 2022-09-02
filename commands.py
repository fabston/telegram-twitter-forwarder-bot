import telegram
import tweepy

from models import Subscription
from util import with_touched_chat, escape_markdown, markdown_twitter_usernames

allowed_ids = [441985603, 311991287]

table_id = 1


def cmd_ping(bot, update):
    bot.reply(update, 'Pong!')


@with_touched_chat
def cmd_start(bot, update, chat=None):
    bot.reply(
        update,
        "Sorry anon, but you prob have no perms to use me 😕")


@with_touched_chat
def cmd_help(bot, update, chat=None):
    bot.reply(update, """
- /sub - subscribes to updates from users
- /unsub - unsubscribes from users
- /list  - lists current subscriptions
- /export - sends you a /sub command that contains all current subscriptions
- /all - shows you the latest tweets from all subscriptions
- /wipe - remove all the data about you and your subscriptions
- /help - view help text
""".format(), disable_web_page_preview=True, parse_mode=telegram.ParseMode.MARKDOWN)


@with_touched_chat
def cmd_sub(bot, update, args, chat=None):
    if update.message.chat_id in allowed_ids:
        if len(args) < 1:
            bot.reply(update, "Use /sub username1 username2 username3 ...")
            return
        tw_usernames = args
        not_found = []
        already_subscribed = []
        successfully_subscribed = []

        for tw_username in tw_usernames:
            tw_user = bot.get_tw_user(tw_username)

            if tw_user is None:
                not_found.append(tw_username)
                continue

            if Subscription.select().where(
                    Subscription.tw_user == tw_user,
                    Subscription.tg_chat == table_id).count() == 1:
                already_subscribed.append(tw_user.full_name)
                continue

            Subscription.create(tg_chat=table_id, tw_user=tw_user)
            successfully_subscribed.append(tw_user.full_name)

        reply = ""

        if len(not_found) != 0:
            reply += "❌ I didn't find username{} {}\n\n".format(
                "" if len(not_found) == 1 else "s",
                ", ".join(not_found)
            )

        if len(already_subscribed) != 0:
            reply += "ℹ️ You're already subscribed to `{}`\n\n".format(
                ", ".join(already_subscribed)
            )

        if len(successfully_subscribed) != 0:
            reply += "✅ I've added your subscription to: `{}`".format(
                ", ".join(successfully_subscribed)
            )
        for user in allowed_ids:
            bot.sendMessage(user, reply, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        pass


@with_touched_chat
def cmd_unsub(bot, update, args, chat=None):
    if update.message.chat_id in allowed_ids:
        if len(args) < 1:
            bot.reply(update, "`Use /unsub username1 username2 username3 ...`", parse_mode=telegram.ParseMode.MARKDOWN)
            return
        tw_usernames = args
        not_found = []
        successfully_unsubscribed = []

        for tw_username in tw_usernames:
            tw_user = bot.get_tw_user(tw_username)

            if tw_user is None or Subscription.select().where(
                    Subscription.tw_user == tw_user,
                    Subscription.tg_chat == table_id).count() == 0:
                not_found.append(tw_username)
                continue

            Subscription.delete().where(
                Subscription.tw_user == tw_user,
                Subscription.tg_chat == table_id).execute()

            successfully_unsubscribed.append(tw_user.full_name)

        reply = ""

        if len(not_found) != 0:
            reply += "ℹ️ I didn't find any subscription to `{}`\n\n".format(
                ", ".join(not_found)
            )

        if len(successfully_unsubscribed) != 0:
            reply += "🗑 You are no longer subscribed to `{}`".format(
                ", ".join(successfully_unsubscribed)
            )
        for user in allowed_ids:
            bot.sendMessage(user, reply, parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        pass


@with_touched_chat
def cmd_list(bot, update, chat=None):
    if update.message.chat_id in allowed_ids:
        subscriptions = list(Subscription.select().where(
            Subscription.tg_chat == table_id))

        if len(subscriptions) == 0:
            return bot.reply(update, 'You have no subscriptions yet! Add one with /sub username')

        subs = ['']
        for sub in subscriptions:
            subs.append(f"`{sub.tw_user.full_name}`")

        subject = "This group is" if chat.is_group else "You are"

        bot.reply(
            update,
            subject + " subscribed to the following Twitter users:\n" +
            "\n • ".join(subs) + "\n\nYou can remove any of them using /unsub username"
            , parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        pass


@with_touched_chat
def cmd_export(bot, update, chat=None):
    if update.message.chat_id in allowed_ids:
        subscriptions = list(Subscription.select().where(
            Subscription.tg_chat == table_id))

        if len(subscriptions) == 0:
            return bot.reply(update, 'You have no subscriptions yet! Add one with /sub username')

        subs = ['']
        for sub in subscriptions:
            subs.append(sub.tw_user.screen_name)

        subject = "Use this to subscribe to all subscribed Twitter users in another chat:\n\n"

        bot.reply(
            update,
            subject + "/sub " + " ".join(subs))
    else:
        pass


@with_touched_chat
def cmd_wipe(bot, update, chat=None):
    if update.message.chat_id == 441985603:
        subscriptions = list(Subscription.select().where(
            Subscription.tg_chat == table_id))

        subs = "You had no subscriptions."
        if subscriptions:
            subs = ''.join([
                "For the record, you were subscribed to these users: ",
                ', '.join((s.tw_user.screen_name for s in subscriptions)),
                '.'])

        bot.reply(update, "Okay, I'm forgetting about this chat. " + subs +
                  " Come back to me anytime you want. Goodbye!")
        chat.delete_instance(recursive=True)
    else:
        pass


@with_touched_chat
def cmd_all(bot, update, chat=None):
    if update.message.chat_id in allowed_ids:
        subscriptions = list(Subscription.select().where(
            Subscription.tg_chat == table_id))

        if len(subscriptions) == 0:
            return bot.reply(update, 'You have no subscriptions, so no tweets to show!')

        text = ""

        for sub in subscriptions:
            if sub.last_tweet is None:
                text += "\n{screen_name}: <no tweets yet>".format(
                    screen_name=escape_markdown(sub.tw_user.screen_name),
                )
            else:
                text += ("\n{screen_name}:\n{text} "
                         "[link](https://twitter.com/{screen_name}/status/{tw_id})").format(
                    text=markdown_twitter_usernames(escape_markdown(sub.last_tweet.text)),
                    tw_id=sub.last_tweet.tw_id,
                    screen_name=escape_markdown(sub.tw_user.screen_name),
                )

        bot.reply(update, text,
                  disable_web_page_preview=True,
                  parse_mode=telegram.ParseMode.MARKDOWN)
    else:
        pass


@with_touched_chat
def cmd_export_friends(bot, update, chat):
    if update.message.chat_id in allowed_ids:
        if not chat.is_authorized:
            if not chat.twitter_request_token:
                bot.reply(update, "You have not authorized yet. Use /auth to do it")
            else:
                bot.reply(update, "You have not verified your authorization yet. Use /verify code to do it")
            return
        bot_auth = bot.tw.auth
        api = chat.tw_api(bot_auth.consumer_key, bot_auth.consumer_secret)
        screen_names = [f.screen_name for f in tweepy.Cursor(api.friends).items()]
        bot.reply(update, "Use this to subscribe to all your Twitter friends:")
        bot.reply(update, "/sub {}".format(" ".join(screen_names)))
    else:
        pass
