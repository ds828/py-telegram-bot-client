"""
run in cli: python -m example.radio_group.py
"""
import logging
from simplebot import bot_proxy, SimpleBot
from simplebot.base import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    MessageField,
)
from simplebot.ui import RadioGroup
from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


def radio_toggle_callback(
    bot: SimpleBot, callback_query: CallbackQuery, *option, selected
):
    print(option, selected)


RadioGroup.set_auto_toggle(
    router, name="radio-select", toggle_callback=radio_toggle_callback
)


@router.message_handler(fields=(MessageField.TEXT,))
def on_show_keyboard(bot: SimpleBot, message: Message):
    radio_group = RadioGroup(name="radio-select")
    radio_group.add_options(
        (True, "key1", "value1"),  # selected
        ("key2", "value2", True),
        ("key3", "value3", {"foo": "foo value"}),
    )
    radio_group.add_buttons(InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="Your selections:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=radio_group.layout),
    )


@router.callback_query_handler(static_match="submit")
def on_submit(bot, callback_query):
    radio_group = RadioGroup(
        name="radio-select", layout=callback_query.message.reply_markup.inline_keyboard
    )
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text="you select: {0}".format(
            radio_group.get_selected(),
        ),
    )


example_bot.run_polling(timeout=10)
