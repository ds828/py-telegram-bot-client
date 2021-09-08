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
from telegrambotclient.ui import InlineKeyboard, Select, UIHelper
from telegrambotclient.utils import pretty_print

BOT_TOKEN = "<BOT_TOKEN>"

logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)

router = bot_client.router()


@router.command_handler(cmds=("/start", ))
def on_start(bot, message, *payload):
    logger.debug(payload)
    # use payload to load goods from the order and automatic place a same order
    bot.send_message(chat_id=message.chat.id, text="show a new same invoice")
    return bot.stop_call


UIHelper.setup_select(router, "menu")


@router.command_handler(cmds=("/menu", ))
def on_show_menu(bot, message):
    buttons = UIHelper.build_select_buttons(
        "menu",
        ("4 cup cakes $9.98", ("4 cup cake", 998)),
        ("4 egg ta $4.99", ("4 egg ta", 499)),
        ("6 inch cake $49.98", ("6 inch cake", 4998)),
    )
    keyboard = InlineKeyboard(*buttons)
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="your menu is below",
        reply_markup=keyboard.markup(),
    )
    return bot.stop_call


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    options = Select.lookup(
        callback_query.message.reply_markup.inline_keyboard, "menu")
    if options:
        bot.edit_message_reply_markup(
            chat_id=callback_query.from_user.id,
            message_id=callback_query.message.message_id,
            reply_markup=None,
        )
        bot.send_invoice(
            chat_id=callback_query.from_user.id,
            title="order from yummy cake",
            description="\n ".join([option[0] for option in options]),
            payload="your-order-id",
            # https://core.telegram.org/bots/payments#getting-a-token
            provider_token="<PAYMENT-TOKEN-BOTFATHER-GIVE-YOUR>",
            start_parameter="random-str-mapping-to-order-id",
            currency="AUD",
            prices=tuple(
                LabeledPrice(label=option[1][0], amount=option[1][1])
                for option in options),
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


@router.message_handler(fields=MessageField.SUCCESSFUL_PAYMENT)
def on_successful_payment(bot, message):
    # Once your bot receives this message, it should proceed with delivering the goods or services purchased by the user.
    pretty_print(message.successful_payment)
    return bot.stop_call


bot = bot_client.create_bot(token=BOT_TOKEN, router=router)
bot.delete_webhook(drop_pending_updates=True)
cmd_start = BotCommand(command="/start", description="start to buy same goods")
cmd_menu = BotCommand(command="/menu", description="show menu")
bot.set_my_commands(commands=(cmd_start, cmd_menu))
bot.run_polling(timeout=10)
