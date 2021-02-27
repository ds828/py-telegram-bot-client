"""
run in terminal: python -m example.force_reply.py
"""
from simplebot import bot_proxy, SimpleBot
from simplebot.base import Message, ForceReply, MessageField

from example.settings import BOT_TOKEN

router = bot_proxy.router()
example_bot = bot_proxy.create_bot(token=BOT_TOKEN, router=router)
example_bot.delete_webhook(drop_pending_updates=True)


@router.message_handler(fields=(MessageField.TEXT,))
def on_force_reply(bot: SimpleBot, message: Message):
    bot.send_message(
        chat_id=message.chat.id, text="reply something", reply_markup=ForceReply()
    )
    bot.join_force_reply(message.from_user.id, on_callback_reply, 123, "value")


@router.force_reply_handler()
def on_callback_reply(
    bot: SimpleBot, message: Message, force_reply_arg_1, force_reply_arg_2
):
    bot.reply_message(
        message,
        text="you reply: '{0}' and args: {1}, {2}".format(
            message.text, force_reply_arg_1, force_reply_arg_2
        ),
    )
    # after processing, remove this force reply callback
    bot.force_reply_done(message.from_user.id)


example_bot.run_polling(timeout=10)
