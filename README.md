# Telegram Bot API Client

A telegram bot API client is written in python3.5+ and currently compatible with Telegram Bot API v5.2 and later.
The reason for writing this bot utility is that I wish to run multi telegram bots which could have same or different business logic **(route policy)** in one process . I reckon it is lightweight, fast, full implement and only **urllib3** dependent.

# Update 5.2.5

Optimize: add a context manager on session implement

# Update 5.2.4.1

Fix bug... correct TelegramBotAPIException

# Update 5.2.4

Optimize: make define your local API host easy, and your API host can use 'http://'

# Update 5.2.3

Optimize: make all bots call same one TelegramBotAPI instance

# Update 5.2.2

Add a confirm in ui

# Quick to go

This is a simple echo bot.


	from telegrambotclient import bot_client
	from telegrambotclient.base import MessageField, ParseMode

	# define a unnamed router
	router = bot_client.router()
	# define a bot with the router
	my_bot = bot_client.create_bot(token=<BOT_TOKEN>, router=router)
	# delete webhook if did or not
	my_bot.delete_webhook(drop_pending_updates=True)

	# decorate a handler callback on incoming message updates that have a text field
	@router.message_handler(fields=MessageField.TEXT)
	def on_echo_text(bot, message):
	    # receive and reply
	    sent_message = bot.send_message(
		        chat_id=message.chat.id,
		        text="I receive: <strong>{0}</strong>".format(message.text),
		        parse_mode=ParseMode.HTML,
		    )
	    # pin the sent message
	    bot.pin_chat_message(chat_id=message.chat.id, message_id=sent_message.message_id)

	# run polling to fetch updates in every 10s
	my_bot.run_polling(timeout=10)


## Call telegram bot APIs

telegrambotclient has same parameter signatures with official Telegram Bot APIs. Please see [official Telegram Bot API document](https://core.telegram.org/bots/api) when calling telegram bot APIs.

### Quick to reply

For those sendXXX APIs, such as sendMessage, sendDocument, sendLocation etc. **telegram bot api client** also provides a shortcut to reply XXX which are named reply_XXX

	sent_message = bot.reply_message(
	        message,
	        text="I receive: <strong>{0}</strong>".format(message.text),
	        parse_mode=ParseMode.HTML,
	    )
## Multi bots through webhook

In my case, I use [fastapi](https://fastapi.tiangolo.com/) and [uvicron](https://www.uvicorn.org/) to provide a HTTP interface to receive updates from the official Telegram Bot Server. For development and testing, [ngrok](https://ngrok.com/) give a HTTPs URL on my localhost server with a real-time HTTP traffic tunnel.


	# run in terminal and get a https tunnel on port 8000 in Austrlia
	ngrok http 8000 --region=au

source code:

  	from fastapi import FastAPI, Request, status
	from telegrambotclient import bot_client
  	from telegrambotclient.base import MessageField, ParseMode
    	# from ngrok's https url, replace it with yours
  	WEBHOOK_URL = "https://5f9d0f13b9fb.au.ngrok.io/bot/{0}"

    	# define a default routers
  	router = bot_client.router()
	# two bots have same router
	bot1 = bot_client.create_bot(token=<BOT1_TOKEN>, router=router)
	bot2 = bot_client.create_bot(token=<BOT2_TOKEN>, router=router)
	# conveninet function to set or change the webhook url
	bot1.setup_webhook(WEBHOOK_URL.format(<BOT1_TOKEN>))
	bot2.setup_webhook(WEBHOOK_URL.format(<BOT2_TOKEN>))

	@router.message_handler(fields=MessageField.TEXT)
	def on_echo_text(bot, message):
	    bot.reply_message(message, text="I receive: <strong>{0}</strong>".format(message.text), parse_mode=ParseMode.HTML)

	app = FastAPI()

	# waiting for incoming updates and dispatch them
	@app.post("/bot/{bot_token}", status_code=status.HTTP_200_OK)
	async def process_telegram_update(bot_token: str, request: Request):
	    await bot_client.dispatch(bot_token, await request.json())
	    return ""

## Multi bots and routers play around

	from fastapi import FastAPI, Request, status
	from telegrambotclient import bot_client
	from telegrambotclient.base import Message, MessageField, ParseMode
	# from ngrok's https url, replace it with yours
	WEBHOOK_URL = "https://5f9d0f13b9fb.au.ngrok.io/bot/{0}"

	router1 = bot_client.router("router1")
	router2 = bot_client.router("router2")
	bot1 = bot_client.create_bot(token=<BOT1_TOKEN>, router=router1)
	bot2 = bot_client.create_bot(token=<BOT2_TOKEN>, router=router2)
	# conveninet function to set or change the webhook url
	bot1.setup_webhook(WEBHOOK_URL.format(<BOT1_TOKEN>))
	bot2.setup_webhook(WEBHOOK_URL.format(<BOT2_TOKEN>))

	# bind a handler on router1
	@router1.message_handler(fields=MessageField.TEXT)
	def on_router1_echo(bot, message):
	    bot.reply_message(
	        message,
	        text="I receive: <strong>{0}</strong> from router1".format(message.text),
	        parse_mode=ParseMode.HTML,
	    )

	# bind a handler on router2
	@router2.message_handler(fields=MessageField.TEXT)
	def on_router2_echo(bot, message):
	    bot.reply_message(
	        message,
	        text="I receive: <strong>{0}</strong> from router2".format(message.text),
	        parse_mode=ParseMode.HTML,
	    )

	app = FastAPI()

	# waiting for incoming updates and dispatch them
	@app.post("/bot/{bot_token}", status_code=status.HTTP_200_OK)
	async def process_telegram_update(bot_token: str, request: Request):
	    await bot_client.dispatch(bot_token, await request.json())
	    return ""

##  Register handlers



### decorator
	@router.message_handler(fields=MessageField.TEXT)
	def on_message(bot, message):
		pass

### function
good way to register one callback on multi routers

	def on_message(bot, message):
	    pass

	router1.register_message_handler(callback=on_message, fields=MessageField.TEXT)
	router2.register_message_handler(callback=on_message, fields=MessageField.TEXT)

### route for multi message fields
	@router.message_handler(fields=MessageField.TEXT | MessageField.LOCATION)
	def on_any_message_fields(bot, message: Message):
	    # call when a message include 'text' OR 'location' fields
	    pass

	@router.message_handler(fields=MessageField.ANIMATION & MessageField.DOCUMENT)
	def on_animation(bot, message: Message):
	    # call when a message include 'animation' AND 'document' fields
	    pass


### All-in
	from telegrambotclient import bot_client
	from telegrambotclient.base import (
	    BotCommand,
	    Message,
	    MessageType,
	)
	from telegrambotclient.handler import CommandHandler, MessageHandler

	def on_mycmd(bot, message: Message):
	    bot.reply_message(message, text=message.text)

	def on_message(bot, message: Message):
	    bot.reply_message(message, text=message.text)

	handlers = (
	    CommandHandler(callback=on_mycmd, cmds=("/mycmd1", "/mycmd2")),
	    MessageHandler(callback=on_message, fields=(MessageField.TEXT,)),
	)
	# way1: define a named router for creating a bot
	# router1 = bot_client.router(name="router1", handlers=handlers)
	# example_bot = bot_client.create_bot(token=BOT_TOKEN, router=router1)

	# way2: quick to work, define a router is not necessary if just one router is needed
	example_bot = bot_client.create_bot(token=BOT_TOKEN, handlers=handlers)
	example_bot.delete_webhook(drop_pending_updates=True)
	cmd1 = BotCommand(command="/mycmd1", description="cmd1")
	cmd2 = BotCommand(command="/mycmd2", description="cmd2")
	example_bot.set_my_commands(commands=(cmd1, cmd2))
	example_bot.run_polling(timeout=10)

## [Please try examples for more detail](https://github.com/songdi/py-telegram-bot-client/tree/main/example)
