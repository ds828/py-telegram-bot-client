"""
run in terminal: python -m example.callback_query
To enable inline mode, send the /setinline command to @BotFather
and /setinlinefeedback to enable chosen_inline_result
"""
from telegrambotclient import TelegramBot, bot_client
from telegrambotclient.base import (CallbackQuery, ChosenInlineResult,
                                    InlineKeyboardButton, InlineQuery,
                                    InlineQueryResultPhoto)
from telegrambotclient.ui import InlineKeyboard
from telegrambotclient.utils import build_callback_data

from example.settings import BOT_TOKEN

router = bot_client.router()
example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.inline_query_handler()
def on_query(bot: TelegramBot, inline_query: InlineQuery):
    keyboard = InlineKeyboard()
    keyboard.add_buttons(
        InlineKeyboardButton(text="show url",
                             callback_data=build_callback_data(
                                 "show-url", "photo-1")))
    query = inline_query.query
    results = (InlineQueryResultPhoto(
        id="photo-1",
        photo_url=
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1200px-Telegram_logo.svg.png",
        thumb_url=
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1200px-Telegram_logo.svg.png",
        title="results",
        description="based on your query: {0}".format(query),
        caption="telegram photo",
        reply_markup=keyboard.markup(),
    ), )
    bot.answer_inline_query(inline_query_id=inline_query.id, results=results)


@router.chosen_inline_result_handler()
def on_chosen_inline_result(bot: TelegramBot,
                            chosen_inline_result: ChosenInlineResult):
    bot.send_message(
        chat_id=chosen_inline_result.from_user.id,
        text="you select: {0}".format(chosen_inline_result.result_id),
    )


@router.callback_query_handler(callback_data_name="show-url")
def on_show_url(bot: TelegramBot, callback_query: CallbackQuery,
                query_result_id: str):
    print(query_result_id)
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text=
        "https://upload.wikimedia.org/wikipedia/commons/thumb/8/82/Telegram_logo.svg/1200px-Telegram_logo.svg.png",
    )


example_bot.run_polling(timeout=10)
