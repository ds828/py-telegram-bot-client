"""
run: python -m example.force_reply
"""
import logging

from telegrambotclient import bot_client
from telegrambotclient.base import ForceReply, MessageField

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.message_handler(MessageField.TEXT)
def on_force_reply(bot, message):
    reply_to_message = bot.send_message(chat_id=message.chat.id,
                                        text="reply some text",
                                        reply_markup=ForceReply())
    bot.join_force_reply(message.chat.id, reply_to_message, on_reply_callback,
                         123, "value")
    return bot.stop_call


@router.force_reply_handler()
def on_reply_callback(bot, message, value_1, value_2):
    if not message.text:
        reply_to_message = bot.send_message(chat_id=message.chat.id,
                                            text="reply some text",
                                            reply_markup=ForceReply())
        # waiting for reply again with same callback and args
        bot.update_force_reply(message.chat.id, reply_to_message)
        return bot.stop_call
    bot.reply_message(
        message,
        text="You reply: '{0}' and args: {1}, {2}".format(
            message.text, value_1, value_2),
    )
    # remove this force reply callback if it is done
    bot.remove_force_reply(message.chat.id)
    return bot.stop_call


logger = logging.getLogger("telegram-bot-client")
logger.setLevel(logging.DEBUG)
logger.debug(router)


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
