"""
run: python -m example.select_group
"""
from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard, Select

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()
# define yourself emoji
emoji = ("✔️✔️", "")


def select_callback(bot, callback_query, text, option, selected):
    text = "you {0}: text={1} option={2}".format(
        "select" if selected else "unselect", text, option)
    bot.send_message(chat_id=callback_query.from_user.id, text=text)
    # message.text will be changed
    return text


select_name = "my-select"
Select.setup(router, select_name, select_callback, emoji=emoji)


@router.message_handler(fields=MessageField.TEXT)
def on_show_keyboard(bot, message):
    buttons = Select.create(
        select_name,
        ("select1", "select-value1", True),  # selected
        ("select2", "select-value2"),
        ("select3", "select-value3"),
        emoji=emoji)
    keyboard = InlineKeyboard(*buttons)
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
    options = Select.lookup(
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
