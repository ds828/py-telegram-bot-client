"""
run: python -m example.select
"""
from telegrambotclient import bot_client
from telegrambotclient.base import (InlineKeyboardButton, MessageField,
                                    ParseMode)
from telegrambotclient.ui import InlineKeyboard, UIHelper

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()
# define yourself emoji
emoji = ("✔️✔️", "")


def select_callback(bot, callback_query, text, value, selected: bool):
    # same fields with send_message
    return {
        "text":
        "<strong>{0}</strong> text={1} value={2}".format(
            "select" if selected else "unselect", text, value),
        "parse_mode":
        ParseMode.HTML
    }


select_name = "my-select"
UIHelper.setup_select(router, select_name, select_callback, emoji=emoji)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message):
    keyboard = InlineKeyboard()
    keyboard.add_buttons(*UIHelper.build_select_buttons(
        select_name,
        ("select1", "select-value1", True),  # selected
        ("select2", None),
        ("select3", ("select-value3", 123)),
        emoji=emoji))
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="Your selections:",
        reply_markup=keyboard.markup(),
    )
    return bot.stop_call


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    options = UIHelper.lookup_select(
        callback_query.message.reply_markup.inline_keyboard,
        select_name,
        emoji=emoji)
    message_text = "\n".join([
        "you select item: text={0}, option={1}".format(text, option)
        for text, option in options
    ])
    bot.send_message(
        chat_id=callback_query.from_user.id,
        text=message_text or "nothing selected",
    )
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(timeout=10)
