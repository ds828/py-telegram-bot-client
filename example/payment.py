"""
go to payment provider to sign up
use @BotFather to connect the payment provider
detail on https://core.telegram.org/bots/payments
run in terminal: python -m example.payment.py
"""
import logging

from simplebot import SimpleBot, bot_proxy
from simplebot.base import (BotCommand, InlineKeyboardButton, LabeledPrice,
                            Message, MessageField, PreCheckoutQuery,
                            ShippingOption, ShippingQuery)
from simplebot.ui import InlineKeyboard
from simplebot.utils import pretty_print

from example.settings import BOT_TOKEN

logger = logging.getLogger("simple-bot")
logger.setLevel(logging.DEBUG)

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)

cmd_start = BotCommand(command="/start", description="start to buy same goods")
cmd_menu = BotCommand(command="/menu", description="show menu")
example_bot.set_my_commands(commands=(cmd_start, cmd_menu))


@router.command_handler(cmds=("/start", ))
def on_start(bot: SimpleBot, message: Message, *payload):
    print(payload)
    # use payload to load goods in the order and automatic place a same order
    bot.send_message(chat_id=message.chat.id, text="show a new same invoice")


InlineKeyboard.auto_select(router, "menu")


@router.command_handler(cmds=("/menu", ))
def on_show_menu(bot: SimpleBot, message: Message):
    keyboard = InlineKeyboard()
    keyboard.add_select_group(
        "menu",
        ("4 cup cakes $9.98", ("4 cup cake", 998)),
        ("4 egg ta $4.99", ("4 egg ta", 499)),
        ("6 inch cake $49.98", ("6 inch cake", 4998)),
    )
    keyboard.add_buttons(
        InlineKeyboardButton(text="submit", callback_data="submit"))
    bot.send_message(
        chat_id=message.chat.id,
        text="your menu is below",
        reply_markup=keyboard.markup(),
    )


@router.callback_query_handler(callback_data="submit")
def on_submit(bot, callback_query):
    keyboard = InlineKeyboard(
        keyboard=callback_query.message.reply_markup.inline_keyboard)
    bot.edit_message_reply_markup(
        chat_id=callback_query.from_user.id,
        message_id=callback_query.message.message_id,
        reply_markup=None,
    )
    selected_options = keyboard.get_select_value("menu")
    bot.send_invoice(
        chat_id=callback_query.from_user.id,
        title="order from yummy cake",
        description="\n ".join([option[0] for option in selected_options]),
        payload="your-order-id",
        # https://core.telegram.org/bots/payments#getting-a-token
        provider_token="<PAYMENT-TOKEN-BOTFATHER-GIVE-YOUR>",
        start_parameter="random-str-mapping-to-order-id",
        currency="AUD",
        prices=[
            LabeledPrice(label=option[0], amount=option[1])
            for option in selected_options
        ],
        need_name=True,
        need_phone_number=True,
        need_shipping_address=True,
        is_flexible=True,
    )


@router.shipping_query_handler()
def on_shipping_query(bot: SimpleBot, shipping_query: ShippingQuery):
    # check delivery address is possible and caculate delivery fee
    print(shipping_query.shipping_address)
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


@router.pre_checkout_query_handler()
def on_pre_checkout_query(bot: SimpleBot,
                          pre_checkout_query: PreCheckoutQuery):
    # do somthing to prepare the order, such as check goods are available
    # Your bot must reply using answerPrecheckoutQuery within 10 seconds after receiving this update or the transaction is canceled.
    bot.answer_pre_checkout_query(pre_checkout_query_id=pre_checkout_query.id,
                                  ok=True)


@router.message_handler(fields=MessageField.SUCCESSFUL_PAYMENT)
def on_successful_payment(bot: SimpleBot, message: Message):
    # Once your bot receives this message, it should proceed with delivering the goods or services purchased by the user.
    pretty_print(message.successful_payment)


example_bot.run_polling(timeout=10)
