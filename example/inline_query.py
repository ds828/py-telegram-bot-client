"""
run: python -m example.inline_query
enable inline mode:
send the /setinline command to @BotFather and /setinlinefeedback to enable chosen_inline_result
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import (InlineKeyboardButton, InlineQuery,
                                    InlineQueryResultArticle,
                                    InputTextMessageContent)
from telegrambotclient.ui import InlineKeyboard

BOT_TOKEN = "<BOT_TOKEN>"

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)
router = bot_client.router()


@router.inline_query_handler()
def on_query(bot, inline_query: InlineQuery):
    keyboard = InlineKeyboard([
        InlineKeyboardButton(text="show this article", callback_data="show"),
    ])
    results = (InlineQueryResultArticle(
        id="article",
        title=inline_query.query or "article title",
        input_message_content=InputTextMessageContent(
            message_text="article content"),
        thumb_url=
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1200px-Telegram_logo.svg.png",
        reply_markup=keyboard.markup()), )
    bot.answer_inline_query(inline_query_id=inline_query.id, results=results)


@router.chosen_inline_result_handler()
def on_chosen_inline_result(bot, chosen_inline_result):
    bot.send_message(
        chat_id=chosen_inline_result.from_user.id,
        text="you select: {0}".format(chosen_inline_result.result_id),
    )


@router.callback_query_handler(callback_data="show")
def on_show(bot, callback_query):
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="article content",
    )


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
