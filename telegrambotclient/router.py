import logging
from collections import defaultdict
from typing import Callable, List, Tuple, Union

try:
    import ujson as json
except ImportError:
    import json

from telegrambotclient.base import (CallbackQuery, ChosenInlineResult,
                                    InlineQuery, Message, MessageField, Poll,
                                    PollAnswer, PreCheckoutQuery,
                                    ShippingQuery, TelegramBotException,
                                    Update, UpdateType)
from telegrambotclient.bot import TelegramBot
from telegrambotclient.handler import (
    CallbackQueryHandler, ChannelPostHandler, ChosenInlineResultHandler,
    CommandHandler, EditedChannelPostHandler, EditedMessageHandler,
    ErrorHandler, ForceReplyHandler, InlineQueryHandler, MessageHandler,
    PollAnswerHandler, PollHandler, PreCheckoutQueryHandler,
    ShippingQueryHandler, UpdateHandler, _MessageHandler)
from telegrambotclient.utils import pretty_format

logger = logging.getLogger("telegram-bot-client")


class TelegramRouter:
    __slots__ = ("_name", "_route_map", "_handler_callers")
    next_call = True
    stop_call = False
    update_type_values = UpdateType.__members__.values()

    def __init__(self, name: str):
        self._name = name
        self._route_map = {}
        self._handler_callers = {
            UpdateType.MESSAGE: self.call_message_handler,
            UpdateType.EDITED_MESSAGE: self.call_edited_message_handler,
            UpdateType.CALLBACK_QUERY: self.call_callback_query_handler,
            UpdateType.CHANNEL_POST: self.call_channel_post_handler,
            UpdateType.EDITED_CHANNEL_POST:
            self.call_edited_channel_post_handler,
            UpdateType.INLINE_QUERY: self.call_inline_query_handler,
            UpdateType.CHOSEN_INLINE_RESULT:
            self.call_chosen_inline_result_handler,
            UpdateType.SHIPPING_QUERY: self.call_shipping_query_handler,
            UpdateType.PRE_CHECKOUT_QUERY:
            self.call_pre_checkout_query_handler,
            UpdateType.POLL: self.call_poll_handler,
            UpdateType.POLL_ANSWER: self.call_poll_answer_handler,
        }

    @property
    def name(self):
        return self._name

    def register_handlers(self, handlers):
        for handler in handlers:
            self.register_handler(handler)

    def register_error_handler(self, handler: ErrorHandler):
        if "error" not in self._route_map:
            self._route_map["error"] = []
        self._route_map["error"].append(handler)
        logger.info("bind a error handler for %s on %s@%s",
                    ",".join([error.__name__ for error in handler.errors]),
                    handler, self.name)

    def register_handler(self, handler: UpdateHandler):
        assert isinstance(handler, UpdateHandler), True
        update_type = handler.update_type
        logger.info("bind a %s handler: '%s@%s'", update_type, handler,
                    self.name)
        if isinstance(handler, CommandHandler):
            self.__add_command_handler(handler)
            return
        if isinstance(handler, ForceReplyHandler):
            self.__add_force_reply_handler(handler)
            return
        if isinstance(handler, MessageHandler):
            self.__add_message_handler(handler)
            return
        if isinstance(handler, EditedMessageHandler):
            self.__add_edited_message_handler(handler)
            return
        if isinstance(handler, CallbackQueryHandler):
            self.__add_callback_query_handler(handler)
            return
        if isinstance(handler, ChannelPostHandler):
            self.__add_channel_post_handler(handler)
            return
        if isinstance(handler, EditedChannelPostHandler):
            self.__add_edited_channel_post_handler(handler)
            return
        # for others update handlers
        self._route_map[update_type] = handler

    def register_force_reply_handler(self, callback: Callable):
        self.register_handler(ForceReplyHandler(callback=callback))

    def register_command_handler(self, callback: Callable, cmds: Tuple[str]):
        self.register_handler(CommandHandler(callback=callback, cmds=cmds))

    def register_message_handler(
        self,
        callback: Callable,
        fields: Union[str, MessageField] = MessageField.TEXT,
    ):
        self.register_handler(MessageHandler(callback=callback, fields=fields))

    def register_edited_message_handler(
        self,
        callback: Callable,
        fields: Union[str, MessageField] = MessageField.TEXT,
    ):
        self.register_handler(
            EditedMessageHandler(callback=callback, fields=fields))

    def register_channel_post_handler(
        self,
        callback: Callable,
        fields: Union[str, MessageField] = MessageField.TEXT,
    ):
        self.register_handler(
            ChannelPostHandler(callback=callback, fields=fields))

    def register_edited_channel_post_handler(
            self,
            callback: Callable,
            fields: Union[str, MessageField] = MessageField.TEXT):
        self.register_handler(
            EditedChannelPostHandler(callback=callback, fields=fields))

    def register_inline_query_handler(
        self,
        callback: Callable,
    ):
        self.register_handler(InlineQueryHandler(callback=callback))

    def register_chosen_inline_result_handler(
        self,
        callback: Callable,
    ):
        self.register_handler(ChosenInlineResultHandler(callback=callback))

    def register_callback_query_handler(self,
                                        callback: Callable,
                                        callback_data: str = None,
                                        callback_data_name: str = None,
                                        callback_data_regex: Tuple[str] = None,
                                        callback_data_parse: Callable = None,
                                        **kwargs):
        self.register_handler(
            CallbackQueryHandler(callback=callback,
                                 callback_data=callback_data,
                                 callback_data_name=callback_data_name,
                                 callback_data_regex=callback_data_regex,
                                 callback_data_parse=callback_data_parse,
                                 **kwargs))

    def register_shipping_query_handler(self, callback: Callable):
        self.register_handler(ShippingQueryHandler(callback=callback))

    def register_pre_checkout_query_handler(self, callback: Callable):
        self.register_handler(PreCheckoutQueryHandler(callback=callback))

    def register_poll_handler(self, callback: Callable):
        self.register_handler(PollHandler(callback=callback))

    def register_poll_answer_handler(self, callback: Callable):
        self.register_handler(PollAnswerHandler(callback=callback))

    ###################################################################################
    #
    # register handlers with decorators
    #
    ##################################################################################
    def error_handler(
        self,
        errors: Union[List, Tuple] = None,
    ):
        def decorator(callback):
            self.register_error_handler(
                ErrorHandler(callback=callback,
                             errors=tuple(errors) if errors else None))
            return callback

        return decorator

    def force_reply_handler(self):
        def decorator(callback):
            self.register_force_reply_handler(callback)
            return callback

        return decorator

    def command_handler(self, cmds: Tuple[str]):
        def decorator(callback):
            self.register_command_handler(callback, cmds)
            return callback

        return decorator

    def message_handler(
        self,
        fields: Union[str, MessageField] = MessageField.TEXT,
    ):
        def decorator(callback):
            self.register_message_handler(callback, fields)
            return callback

        return decorator

    def edited_message_handler(
        self,
        fields: Union[str, MessageField] = MessageField.TEXT,
    ):
        def decorator(callback):
            self.register_edited_message_handler(callback, fields)
            return callback

        return decorator

    def channel_post_handler(
        self,
        fields: Union[str, MessageField] = MessageField.TEXT,
    ):
        def decorator(callback):
            self.register_channel_post_handler(callback, fields)
            return callback

        return decorator

    def edited_channel_post_handler(
        self,
        fields: Union[str, MessageField] = MessageField.TEXT,
    ):
        def decorator(callback):
            self.register_edited_channel_post_handler(callback, fields)
            return callback

        return decorator

    def inline_query_handler(self):
        def decorator(callback):
            self.register_inline_query_handler(callback)
            return callback

        return decorator

    def chosen_inline_result_handler(self):
        def decorator(callback):
            self.register_chosen_inline_result_handler(callback)
            return callback

        return decorator

    def callback_query_handler(self,
                               callback_data: str = None,
                               callback_data_name: str = None,
                               callback_data_regex: Tuple[str] = None,
                               callback_data_parse: Callable = None,
                               **kwargs):
        def decorator(callback):
            self.register_callback_query_handler(callback, callback_data,
                                                 callback_data_name,
                                                 callback_data_regex,
                                                 callback_data_parse, **kwargs)
            return callback

        return decorator

    def shipping_query_handler(self):
        def decorator(callback):
            self.register_shipping_query_handler(callback)
            return callback

        return decorator

    def pre_checkout_query_handler(self):
        def decorator(callback):
            self.register_pre_checkout_query_handler(callback)
            return callback

        return decorator

    def poll_handler(self):
        def decorator(callback):
            self.register_poll_handler(callback)
            return callback

        return decorator

    def poll_answer_handler(self):
        def decorator(callback):
            self.register_poll_answer_handler(callback)
            return callback

        return decorator

    def __add_command_handler(self, handler: CommandHandler):
        if UpdateType.MESSAGE.value not in self._route_map:
            self._route_map[UpdateType.MESSAGE.value] = {}
        if "cmd" not in self._route_map[UpdateType.MESSAGE.value]:
            self._route_map[UpdateType.MESSAGE.value]["cmd"] = {}
        for cmd_word in handler.cmds:
            self._route_map[
                UpdateType.MESSAGE.value]["cmd"][cmd_word] = handler

    def __add_force_reply_handler(self, handler: ForceReplyHandler):
        if UpdateType.FORCE_REPLY.value not in self._route_map:
            self._route_map[UpdateType.FORCE_REPLY.value] = {}
        self._route_map[UpdateType.FORCE_REPLY.value][str(handler)] = handler

    def __add_message_handler(self, handler: _MessageHandler):
        update_type = handler.update_type
        if update_type not in self._route_map:
            self._route_map[update_type] = {}
        route = self._route_map[update_type]
        message_fields = handler.message_fields
        if isinstance(message_fields,
                      (str, tuple)) and len(message_fields) == 1:
            if "|" not in route:
                route["|"] = defaultdict(list)
            for field in handler.message_fields:
                route["|"][field].append(handler)
        elif isinstance(message_fields, set):
            if "&" not in route:
                route["&"] = []
            route["&"].append((handler.message_fields, handler))

    def __add_edited_message_handler(self, handler: EditedMessageHandler):
        self.__add_message_handler(handler)

    def __add_channel_post_handler(self, handler: ChannelPostHandler):
        self.__add_message_handler(handler)

    def __add_edited_channel_post_handler(self,
                                          handler: EditedChannelPostHandler):
        self.__add_message_handler(handler)

    def __add_callback_query_handler(self, handler: CallbackQueryHandler):
        if UpdateType.CALLBACK_QUERY.value not in self._route_map:
            self._route_map[UpdateType.CALLBACK_QUERY.value] = {}
        route = self._route_map[UpdateType.CALLBACK_QUERY.value]
        has_callback_data, has_callback_data_name, has_callback_data_regex, has_callback_data_parse = handler.have_matchers
        if has_callback_data:
            if "data" not in route:
                route["data"] = {}
            route["data"][handler.callback_data] = handler
        if has_callback_data_name:
            if "name" not in route:
                route["name"] = {}
            route["name"][handler.callback_data_name] = handler
        if has_callback_data_regex:
            if "regex" not in route:
                route["regex"] = []
            route["regex"].append(handler)
        if has_callback_data_parse:
            if "parse" not in route:
                route["parse"] = []
            route["parse"].append(handler)

    ###################################################################################
    #
    # handler callers
    #
    ##################################################################################
    @classmethod
    def parse_update_type_and_data(cls, update: Update) -> Tuple:
        for name, value in update.items():
            if name in cls.update_type_values:
                return name, value
        raise TelegramBotException("unknown update type")

    @classmethod
    async def call_handler(cls, handler: UpdateHandler, *args,
                           **kwargs) -> bool:
        return bool(await handler(*args, **kwargs))

    async def route(self, bot: TelegramBot, update: Update):
        if update.update_id and update.update_id > bot.last_update_id:
            bot.last_update_id = update.update_id
        update_type, data = self.parse_update_type_and_data(update)
        route = self._route_map.get(update_type, None)
        if not route:
            return
        try:
            await self._handler_callers[update_type](route, bot, data)
        except Exception as error:
            for handler in self._route_map.get("error", ()):
                if isinstance(error, handler.errors):
                    await self.call_handler(handler, bot, data, error)
            raise error

    async def call_command_handler(self, bot: TelegramBot,
                                   message: Message) -> bool:
        text = message.text
        if not text or text[0] != '/' or "cmd" not in self._route_map.get(
                UpdateType.MESSAGE.value, {}):
            return self.next_call
        cmd_and_args = text.split()
        cmd_name_and_bot_username = cmd_and_args[0].split("@")
        if (len(cmd_name_and_bot_username) == 2
                and cmd_name_and_bot_username[1] != bot.user.username):
            return self.stop_call
        handler = self._route_map[UpdateType.MESSAGE.value]["cmd"].get(
            cmd_name_and_bot_username[0], None)
        if handler is None:
            return self.next_call
        if len(cmd_and_args) == 1:
            return await self.call_handler(handler, bot, message)
        return await self.call_handler(handler, bot, message,
                                       *cmd_and_args[1:])

    async def call_force_reply_handler(self, bot: TelegramBot,
                                       message: Message) -> bool:
        if not message.chat:
            raise TelegramBotException("message.chat is None")
        force_reply_callback_name, force_reply_args = bot.get_force_reply(
            message.chat.id)
        if force_reply_callback_name is None:
            return self.next_call
        handler = self.get_force_reply_handler(force_reply_callback_name)
        if handler is None:
            raise TelegramBotException(
                "{0} is not a force reply callback".format(
                    force_reply_callback_name))
        return await self.call_handler(
            handler, bot, message, *
            force_reply_args) if force_reply_args else await self.call_handler(
                handler, bot, message)

    async def __call_message_like_handler(self, route, bot: TelegramBot,
                                          message: Message) -> bool:
        # call 'and' handlers
        and_handlers = route.get("&", None)
        if and_handlers:
            message_fields_set = set(message.keys())
            for fields, handler in and_handlers:
                if fields <= message_fields_set:
                    if await self.call_handler(handler, bot,
                                               message) is self.stop_call:
                        return self.stop_call
        # call 'or' handlers
        or_dict = route.get("|", None)
        if or_dict:
            for message_field, handlers in or_dict.items():
                if message_field in message:
                    for handler in handlers:
                        if await self.call_handler(handler, bot,
                                                   message) is self.stop_call:
                            return self.stop_call
        return bot.next_call

    async def call_message_handler(self, route, bot: TelegramBot,
                                   message: Message) -> bool:
        if await self.call_command_handler(bot, message) is self.stop_call:
            return bot.stop_call
        if await self.call_force_reply_handler(bot, message) is self.stop_call:
            return bot.stop_call
        return await self.__call_message_like_handler(route, bot, message)

    async def call_edited_message_handler(self, route, bot: TelegramBot,
                                          edited_message: Message) -> bool:
        if await self.call_command_handler(bot,
                                           edited_message) is self.stop_call:
            return bot.stop_call
        # for edited messages, their fields should be text ONLY for force_reply
        if edited_message.text and await self.call_force_reply_handler(
                bot, edited_message) is self.stop_call:
            return self.stop_call
        return await self.__call_message_like_handler(route, bot,
                                                      edited_message)

    async def call_channel_post_handler(self, route, bot: TelegramBot,
                                        message: Message) -> bool:
        return await self.__call_message_like_handler(route, bot, message)

    async def call_edited_channel_post_handler(self, route, bot: TelegramBot,
                                               message: Message) -> bool:
        return await self.__call_message_like_handler(route, bot, message)

    async def call_callback_query_handler(
            self, route, bot: TelegramBot,
            callback_query: CallbackQuery) -> bool:
        if callback_query.data is None:
            raise TelegramBotException("callback_query.data is None")
        # for callback_data
        handler = route.get("data", {}).get(callback_query.data, None)
        if handler and await self.call_handler(
                handler, bot, callback_query) is self.stop_call:
            return self.stop_call
        #for callback_data_name
        start_and_args = callback_query.data.split("|")
        handler = route.get("name", {}).get(start_and_args[0], None)
        if handler and await self.call_handler(
                handler, bot, callback_query,
                *json.loads(start_and_args[1]) if len(start_and_args) == 2 else
            ()) is self.stop_call:
            return bot.stop_call
        # for callback_data_regex
        for handler in route.get("regex", ()):
            result = handler.callback_data_match(callback_query)
            if result and await handler(bot, callback_query,
                                        result) is self.stop_call:
                return bot.stop_call
        # for callback_data_parse
        for handler in route.get("parse", ()):
            result = handler.callback_data_parse(callback_query)
            if result:
                if isinstance(result, bool) and await self.call_handler(
                        handler, bot, callback_query) is self.stop_call:
                    return self.stop_call
                if isinstance(result,
                              (list, tuple, set)) and await self.call_handler(
                                  handler, bot, callback_query, *
                                  result) is self.stop_call:
                    return self.stop_call
                if await self.call_handler(handler, bot, callback_query,
                                           result) is self.stop_call:
                    return self.stop_call
        return bot.next_call

    async def call_inline_query_handler(self, route, bot: TelegramBot,
                                        inline_query: InlineQuery) -> bool:
        return await self.call_handler(route, bot, inline_query)

    async def call_chosen_inline_result_handler(
            self, handler, bot: TelegramBot,
            chosen_inline_result: ChosenInlineResult) -> bool:
        return await self.call_handler(handler, bot, chosen_inline_result)

    async def call_shipping_query_handler(
            self, handler, bot: TelegramBot,
            shipping_query: ShippingQuery) -> bool:
        return await self.call_handler(handler, bot, shipping_query)

    async def call_pre_checkout_query_handler(
            self, handler, bot: TelegramBot,
            pre_checkout_query: PreCheckoutQuery) -> bool:
        return await self.call_handler(handler, bot, pre_checkout_query)

    async def call_poll_handler(self, handler, bot: TelegramBot,
                                poll: Poll) -> bool:
        return await self.call_handler(handler, bot, poll)

    async def call_poll_answer_handler(self, handler, bot: TelegramBot,
                                       poll_answer: PollAnswer) -> bool:
        return await self.call_handler(handler, bot, poll_answer)

    def get_force_reply_handler(self,
                                callback_name: str) -> Union[Callable, None]:
        return self._route_map.get(UpdateType.FORCE_REPLY.value,
                                   {}).get(callback_name, None)

    def has_force_reply_callback(self, callback_name: str) -> bool:
        return self.get_force_reply_handler(callback_name) is not None

    def __repr__(self):
        return "\r\n{0}".format(pretty_format(self._route_map))
