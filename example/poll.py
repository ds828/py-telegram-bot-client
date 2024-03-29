"""
run: python -m example.poll.py
"""
from telegrambotclient import bot_client
from telegrambotclient.base import Poll, PollType

BOT_TOKEN = "<BOT_TOKEN>"

router = bot_client.router()


@router.command_handler("/vote")
def on_show_vote_poll(bot, message):
    bot.send_poll(
        chat_id=message.chat.id,
        question="regular vote",
        options=("option 1", "option 2", "option 3"),
    )
    return bot.stop_call


@router.poll_handler()
def on_poll_state(bot, poll: Poll):
    print("receive a vote on {0}".format(poll.options))
    return bot.stop_call


@router.command_handler("/quiz")
def on_show_quiz_poll(bot, message):
    bot.send_poll(
        chat_id=message.chat.id,
        question="quiz",
        options=("answer 1", "answer 2", "answer 3"),
        is_anonymous=False,
        type=PollType.QUIZ,
        correct_option_id=2,
    )
    return bot.stop_call


@router.poll_answer_handler()
def on_poll_answer(bot, poll_answer):
    bot.send_message(chat_id=poll_answer.user.id,
                     text="you select: {0}".format(poll_answer.option_ids))
    print(poll_answer)
    return bot.stop_call


async def on_update(bot, update):
    await router.dispatch(bot, update)


bot = bot_client.create_bot(token=BOT_TOKEN)
bot.delete_webhook(drop_pending_updates=True)
bot.run_polling(on_update, timeout=10)
