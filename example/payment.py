"""
go to payment provider to sign up
use @BotFather to connect the payment provider
detail on https://core.telegram.org/bots/payments
run in terminal: python -m example.payment
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import (BotCommand, InlineKeyboardButton,
                                    LabeledPrice, MessageField, ShippingOption)
from telegrambotclient.ui import InlineKeyboard
from telegrambotclient.utils import (build_callback_data, parse_callback_data,
                                     pretty_print)

BOT_TOKEN = "<BOT_TOKEN>"

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()
emoji = ("✔️" "")

menu = {
    1: ("4 cup cakes $9.98", 988),
    2: ("4 egg ta $4.99", 499),
    3: ("6 inch cake $49.98", 499)
}


@router.command_handler("/start")
def on_start(bot, message, *payload):
    logger.debug(payload)
    # use payload to load goods from the order and automatic place a same order
    bot.send_message(chat_id=message.chat.id, text="show a new same invoice")
    return bot.stop_call


@router.command_handler("/menu")
def on_show_menu(bot, message, *args):
    keyboard = InlineKeyboard()
    keyboard.add_buttons(*[
        InlineKeyboardButton(text=text,
                             callback_data=build_callback_data(
                                 "select-item", item_id, False))
        for item_id, (text, _) in menu.items()
    ])
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="your menu",
        reply_markup=keyboard.markup(),
    )
    return bot.stop_call


@router.callback_query_handler(callback_data="select-item")
def on_select_item(bot, callback_query, item_id, selected):
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)
    new_button = InlineKeyboardButton(
        text="{0}{1}".format(emoji[1] if selected else emoji[0],
                             menu[item_id][0]),
        callback_data=build_callback_data("select-item", item_id,
                                          not selected))
    if keyboard.replace(build_callback_data("select-item", item_id, selected),
                        new_button):
        bot.edit_message_text(chat_id=callback_query.from_user.id,
                              message_id=callback_query.message.message_id,
                              text=callback_query.message.text,
                              reply_markup=keyboard.markup())
    return bot.stop_call


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(
        callback_query.message.reply_markup.inline_keyboard)
    selected_items = []
    btn_group = keyboard.group("select-item")
    for button in btn_group:
        # selected button
        if button.text.startswith(emoji[0]) and button.callback_data:
            # title, price
            selected_items.append(
                (button.text[len(emoji[0]):],
                 menu[parse_callback_data(button.callback_data)[1][0]][1]))

    if selected_items:
        bot.edit_message_reply_markup(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=None,
        )

        bot.send_invoice(
            chat_id=callback_query.from_user.id,
            title="order detail",
            description="\n".join([text for text, _ in selected_items]),
            payload="your-order-id",
            # https://core.telegram.org/bots/payments#getting-a-token
            provider_token="<PAYMENT-TOKEN>",
            start_parameter="random-str-mapping-to-order-id",
            currency="AUD",
            prices=tuple(
                LabeledPrice(label=text, amount=price)
                for text, price in selected_items),
            need_name=True,
            need_phone_number=True,
            need_shipping_address=True,
            is_flexible=True,
        )

    return bot.stop_call


@router.shipping_query_handler()
def on_shipping_query(bot, shipping_query):
    # check delivery address is possible and caculate delivery fee
    logger.debug(shipping_query.shipping_address)
    bot.answer_shipping_query(
        shipping_query_id=shipping_query.id,
        ok=True,
        shipping_options=(
            ShippingOption(id="1",
                           title="delivery",
                           prices=(LabeledPrice(label="delivery fee",
                                                amount=998), )),
            ShippingOption(id="2",
                           title="pick up",
                           prices=(LabeledPrice(label="pick up", amount=0), )),
        ),
    )

    return bot.stop_call


@router.pre_checkout_query_handler()
def on_pre_checkout_query(bot, pre_checkout_query):
    # do somthing to prepare the order, such as check goods are available
    # Your bot must reply using answerPrecheckoutQuery within 10 seconds after receiving this update or the transaction is canceled.
    bot.answer_pre_checkout_query(pre_checkout_query_id=pre_checkout_query.id,
                                  ok=True)

    return bot.stop_call


@router.message_handler(MessageField.SUCCESSFUL_PAYMENT)
def on_successful_payment(bot, message):
    # Once your bot receives this message, it should proceed with delivering the goods or services purchased by the user.
    pretty_print(message.successful_payment)
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
cmd_start = BotCommand(command="/start", description="start to buy same goods")
cmd_menu = BotCommand(command="/menu", description="show menu")
bot.set_my_commands(commands=(cmd_start, cmd_menu))
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
