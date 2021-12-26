"""
run: python -m example.radio
"""
from telegrambotclient import bot_client
from telegrambotclient.base import InlineKeyboardButton, MessageField
from telegrambotclient.ui import InlineKeyboard
from telegrambotclient.utils import build_callback_data, parse_callback_data

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()
emoji = ("🔘", "⚪")

select_options = {
    1: ("select-text-1", True),  # selected
    2: ("select-text-2", False),
    3: ("select-text-3", False),
}


@router.message_handler(MessageField.TEXT)
def on_show_keyboard(bot, message):
    keyboard = InlineKeyboard()
    keyboard.add_buttons(*[
        InlineKeyboardButton(
            text="{0}{1}".format(emoji[0] if selected else emoji[1], text),
            callback_data=build_callback_data("select", value, selected))
        for value, (text, selected) in select_options.items()
    ])
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="Your selections:",
        reply_markup=keyboard.markup(),
    )
    return bot.stop_call


@router.callback_query_handler(callback_data="select")
def on_select(bot, callback_query, value, selected):
    if selected:
        bot.answer_callback_query(callback_query_id=callback_query.id)
    else:
        keyboard = InlineKeyboard(
            *callback_query.message.reply_markup.inline_keyboard)
        for button, (value_, (text, _)) in zip(keyboard.get_buttons("select"),
                                               select_options.items()):
            keyboard.replace(
                button.callback_data,
                InlineKeyboardButton(text="{0}{1}".format(emoji[1], text),
                                     callback_data=build_callback_data(
                                         "select", value_, False)))
        new_button = InlineKeyboardButton(
            text="{0}{1}".format(emoji[0], select_options[value][0]),
            callback_data=build_callback_data("select", value, True))
        if keyboard.replace(build_callback_data("select", value, False),
                            new_button):

            bot.edit_message_text(chat_id=callback_query.from_user.id,
                                  message_id=callback_query.message.message_id,
                                  text=callback_query.message.text,
                                  reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(
        *callback_query.message.reply_markup.inline_keyboard)
    for button in keyboard.get_buttons("select"):
        callback_data_name, (value, selected) = parse_callback_data(
            button.callback_data)
        if selected:
            # filter selected options
            message_text = "text={0}, callback_data_name={1} value={2} status={3}".format(
                button.text[len(emoji[0]):], callback_data_name, value,
                selected)
            bot.send_message(
                chat_id=callback_query.from_user.id,
                text=message_text,
            )
            break
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
