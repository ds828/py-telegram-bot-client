"""
run in terminal: python -m example.callback_query.py
To enable inline mode, send the /setinline command to @BotFather
"""
from simplebot.ui import Keyboard
from simplebot import bot_proxy, SimpleBot
from simplebot.base import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultPhoto,
)
from simplebot.utils import build_callback_data, parse_callback_data
from example.settings import BOT_TOKEN


router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.inline_query_handler()
def on_query(bot: SimpleBot, inline_query: InlineQuery):
    keyboard = Keyboard()
    keyboard.add_buttons(
        InlineKeyboardButton(
            text="show url", callback_data=build_callback_data("show-url", "photo-1")
        )
    )
    query = inline_query.query
    results = (
        InlineQueryResultPhoto(
            id="photo-1",
            photo_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1200px-Telegram_logo.svg.png",
            thumb_url="https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1200px-Telegram_logo.svg.png",
            title="results",
            description="based on your query: {0}".format(query),
            caption="telegram photo",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard.layout),
        ),
    )
    bot.answer_inline_query(inline_query_id=inline_query.id, results=results)


@router.callback_query_handler(callable_match=parse_callback_data, name="show-url")
def on_show_url(bot: SimpleBot, callback_query: CallbackQuery, query_result_id: str):
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1200px-Telegram_logo.svg.png",
    )


example_bot.run_polling(timeout=10)
