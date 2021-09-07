from collections import defaultdict
from typing import Callable, List, Tuple, Union

try:
    import ujson as json
except ImportError:
    import json

from telegrambotclient.base import (CallbackQuery, ChatMemberUpdated,
                                    ChosenInlineResult, InlineQuery, Message,
                                    MessageField, Poll, PollAnswer,
                                    PreCheckoutQuery, ShippingQuery,
                                    TelegramBotException, TelegramObject,
                                    Update, UpdateField, logger)
from telegrambotclient.bot import TelegramBot
from telegrambotclient.handler import (
    CallbackQueryHandler, ChannelPostHandler, ChatMemberHandler,
    ChosenInlineResultHandler, CommandHandler, EditedChannelPostHandler,
    EditedMessageHandler, ErrorHandler, ForceReplyHandler, InlineQueryHandler,
    MessageHandler, MyChatMemberHandler, PollAnswerHandler, PollHandler,
    PreCheckoutQueryHandler, ShippingQueryHandler, UpdateHandler,
    _MessageHandler)
from telegrambotclient.utils import pretty_format


class ListRoute:
    __slots__ = ("_route", )

    def __init__(self, name: str, root_route):
        if name not in root_route:
            root_route[name] = []
        self._route = root_route[name]

    def add_handler(self, handler: UpdateHandler):
        self.add_handler_to_list(self._route, handler)

    async def call_handlers(self, bot: TelegramBot,
                            data: TelegramObject) -> bool:
        for handler in self._route:
            if await self.call_handler(handler, bot, data) is bot.stop_call:
                return bot.stop_call
        return bot.next_call

    @staticmethod
    async def call_handler(handler: UpdateHandler, *args, **kwargs) -> bool:
        return bool(await handler(*args, **kwargs))

    @staticmethod
    def add_handler_to_list(route, handler):
        for idx, _handler in enumerate(route):
            if _handler.name == handler.name:
                route[idx] = handler
                return route
        route.append(handler)


class ErrorRoute(ListRoute):
    def __init__(self, root_route):
        super().__init__("error", root_route)

    async def call_handlers(self, bot: TelegramBot, data: TelegramObject,
                            error: Exception) -> bool:
        for handler in self._route:
            if await self.call_handler(handler, bot, data,
                                       error) is bot.stop_call:
                return bot.stop_call
        return bot.next_call


class DictRoute(ListRoute):
    def __init__(self, name: str, root_route):
        if name not in root_route:
            root_route[name] = {}
        self._route = root_route[name]


class CommandRoute(DictRoute):
    def __init__(self, root_route):
        super().__init__("command", root_route)

    def add_handler(self, handler: CommandHandler):
        for cmd_word in handler.cmds:
            self._route[cmd_word] = handler

    async def call_handlers(self, bot: TelegramBot, message: Message) -> bool:
        text = message.text
        if not text or text[0] != '/' or not self._route:
            return bot.next_call
        cmd_and_args = text.split()
        cmd_name_and_bot_username = cmd_and_args[0].split("@")
        if (len(cmd_name_and_bot_username) == 2
                and cmd_name_and_bot_username[1] != bot.user.username):
            return bot.stop_call
        handler = self._route.get(cmd_name_and_bot_username[0], None)
        if handler is None:
            return bot.next_call
        if len(cmd_and_args) == 1:
            return await self.call_handler(handler, bot, message)
        return await self.call_handler(handler, bot, message,
                                       *cmd_and_args[1:])


class ForceReplyRoute(DictRoute):
    def __init__(self, root_route):
        super().__init__("force_reply", root_route)

    def add_handler(self, handler: ForceReplyHandler):
        self._route[handler.name] = handler

    async def call_handlers(self, bot: TelegramBot, message: Message) -> bool:
        force_reply_callback_name, force_reply_args = bot.get_force_reply(
            message.chat.id if message.chat else message.from_user.
            id if message.from_user else 0)
        if force_reply_callback_name is None:
            return bot.next_call
        handler = self._route.get(force_reply_callback_name, None)
        if handler is None:
            raise TelegramBotException(
                "{0} is not a force reply callback".format(
                    force_reply_callback_name))
        return await self.call_handler(
            handler, bot, message, *
            force_reply_args) if force_reply_args else await self.call_handler(
                handler, bot, message)

    def __contains__(self, force_reply_name: str):
        return force_reply_name in self._route


class MessageRoute(DictRoute):
    def __init__(self, name: str, root_route):
        super().__init__(name, root_route)

    def add_handler(self, handler: _MessageHandler):
        message_fields = handler.message_fields
        if message_fields is None:
            if "all" not in self._route:
                self._route["all"] = []
            self.add_handler_to_list(self._route["all"], handler)
        elif isinstance(message_fields, str):
            if "|" not in self._route:
                self._route["|"] = defaultdict(list)
            self.add_handler_to_list(self._route["|"][message_fields], handler)
        elif isinstance(message_fields, tuple):
            if "|" not in self._route:
                self._route["|"] = defaultdict(list)
            for field in handler.message_fields or ():
                self.add_handler_to_list(self._route["|"][field], handler)
        elif isinstance(message_fields, set):
            if "&" not in self._route:
                self._route["&"] = []
            self.add_handler_to_list(self._route["&"], handler)

    async def call_handlers(self, bot: TelegramBot, message: Message) -> bool:
        # call 'and' handlers
        handlers = self._route.get("&", None)
        if handlers:
            message_fields_set = set(message.keys())
            for handler in handlers:
                if handler.fields <= message_fields_set:
                    if await self.call_handler(handler, bot,
                                               message) is bot.stop_call:
                        return bot.stop_call
        # call 'or' handlers
        handler_dict = self._route.get("|", None)
        if handler_dict:
            for message_field in handler_dict.keys():
                if message_field in message:
                    for handler in handler_dict[message_field]:
                        if await self.call_handler(handler, bot,
                                                   message) is bot.stop_call:
                            return bot.stop_call
        # call 'all' handlers
        handlers = self._route.get("all", None)
        if handlers:
            for handler in handlers:
                if await self.call_handler(handler, bot,
                                           message) is bot.stop_call:
                    return bot.stop_call
        return bot.next_call


class CallbackQueryRoute(DictRoute):
    def __init__(self, root_route):
        super().__init__(UpdateField.CALLBACK_QUERY.value, root_route)

    def add_handler(self, handler: CallbackQueryHandler):
        has_callback_data, has_callback_data_name, has_callback_data_regex, has_callback_data_parse = handler.have_matchers
        if has_callback_data:
            if "data" not in self._route:
                self._route["data"] = {}
            self._route["data"][handler.callback_data] = handler
        if has_callback_data_name:
            if "name" not in self._route:
                self._route["name"] = {}
            self._route["name"][handler.callback_data_name] = handler
        if has_callback_data_regex:
            if "regex" not in self._route:
                self._route["regex"] = []
            self.add_handler_to_list(self._route["regex"], handler)
        if has_callback_data_parse:
            if "parse" not in self._route:
                self._route["parse"] = []
            self.add_handler_to_list(self._route["parse"], handler)

    async def call_handlers(self, bot: TelegramBot,
                            callback_query: CallbackQuery) -> bool:
        if callback_query.data is None:
            raise TelegramBotException("callback_query.data is None")
        # for callback_data
        handler = self._route.get("data", {}).get(callback_query.data, None)
        if handler and await self.call_handler(
                handler, bot, callback_query) is bot.stop_call:
            return bot.stop_call
        #for callback_data_name
        callback_name_data = callback_query.data.split("|")
        if len(callback_name_data) == 2:
            callback_name, callback_data = tuple(callback_name_data)
            handler = self._route.get("name", {}).get(callback_name, None)
            if handler and await self.call_handler(
                    handler, bot, callback_query, *
                    json.loads(callback_data)) is bot.stop_call:
                return bot.stop_call
        # for callback_data_regex
        for handler in self._route.get("regex", ()):
            result = handler.callback_data_match(callback_query)
            if result and await handler(bot, callback_query,
                                        result) is bot.stop_call:
                return bot.stop_call
        # for callback_data_parse
        for handler in self._route.get("parse", ()):
            result = handler.callback_data_parse(callback_query)
            if result and await self.call_handler(handler, bot, callback_query,
                                                  result) is bot.stop_call:
                return bot.stop_call
        return bot.next_call


class TelegramRouter:
    __slots__ = ("_name", "_route_map", "_handler_callers")
    next_call = True
    stop_call = False
    update_field_values = UpdateField.__members__.values()

    def __init__(self, name: str):
        self._name = name
        self._route_map = {}
        self._handler_callers = {
            UpdateField.MESSAGE: self.call_message_handlers,
            UpdateField.EDITED_MESSAGE: self.call_edited_message_handlers,
            UpdateField.CALLBACK_QUERY: self.call_callback_query_handlers,
            UpdateField.CHANNEL_POST: self.call_channel_post_handlers,
            UpdateField.EDITED_CHANNEL_POST:
            self.call_edited_channel_post_handlers,
            UpdateField.INLINE_QUERY: self.call_inline_query_handlers,
            UpdateField.CHOSEN_INLINE_RESULT:
            self.call_chosen_inline_result_handlers,
            UpdateField.SHIPPING_QUERY: self.call_shipping_query_handlers,
            UpdateField.PRE_CHECKOUT_QUERY:
            self.call_pre_checkout_query_handlers,
            UpdateField.POLL: self.call_poll_handlers,
            UpdateField.POLL_ANSWER: self.call_poll_answer_handlers,
            UpdateField.MY_CHAT_MEMBER: self.call_my_chat_member_handlers,
            UpdateField.CHAT_MEMBER: self.call_chat_member_handlers
        }

    @property
    def name(self):
        return self._name

    def register_handlers(self, handlers):
        for handler in handlers:
            self.register_handler(handler)

    def register_handler(self, handler: UpdateHandler):
        assert isinstance(handler, UpdateHandler), True
        update_field = handler.update_field
        logger.info("bind a %s handler: '%s@%s'", update_field, handler.name,
                    self.name)
        if isinstance(handler, CommandHandler):
            return CommandRoute(self._route_map).add_handler(handler)
        if isinstance(handler, ForceReplyHandler):
            return ForceReplyRoute(self._route_map).add_handler(handler)
        if isinstance(handler, MessageHandler):
            return MessageRoute(UpdateField.MESSAGE.value,
                                self._route_map).add_handler(handler)
        if isinstance(handler, EditedMessageHandler):
            return MessageRoute(UpdateField.EDITED_MESSAGE.value,
                                self._route_map).add_handler(handler)
        if isinstance(handler, CallbackQueryHandler):
            return CallbackQueryRoute(self._route_map).add_handler(handler)
        if isinstance(handler, ChannelPostHandler):
            return MessageRoute(UpdateField.CHANNEL_POST.value,
                                self._route_map).add_handler(handler)
        if isinstance(handler, EditedChannelPostHandler):
            return MessageRoute(UpdateField.EDITED_CHANNEL_POST.value,
                                self._route_map).add_handler(handler)
        if isinstance(handler, ErrorHandler):
            return ErrorRoute(self._route_map).add_handler(handler)
        # for others update handlers
        return ListRoute(update_field, self._route_map).add_handler(handler)

    def register_error_handler(self, callback: Callable, errors: Union[List,
                                                                       Tuple]):
        self.register_handler(
            ErrorHandler(callback=callback,
                         errors=tuple(errors) if errors else None))

    def register_command_handler(self, callback: Callable, cmds: Tuple[str]):
        self.register_handler(CommandHandler(callback=callback, cmds=cmds))

    def register_force_reply_handler(self, callback: Callable):
        self.register_handler(ForceReplyHandler(callback=callback))

    def register_message_handler(self,
                                 callback: Callable,
                                 fields: Union[str, MessageField] = None):
        self.register_handler(MessageHandler(callback=callback, fields=fields))

    def register_edited_message_handler(self,
                                        callback: Callable,
                                        fields: Union[str,
                                                      MessageField] = None):
        self.register_handler(
            EditedMessageHandler(callback=callback, fields=fields))

    def register_channel_post_handler(self,
                                      callback: Callable,
                                      fields: Union[str, MessageField] = None):
        self.register_handler(
            ChannelPostHandler(callback=callback, fields=fields))

    def register_edited_channel_post_handler(self,
                                             callback: Callable,
                                             fields: Union[
                                                 str, MessageField] = None):
        self.register_handler(
            EditedChannelPostHandler(callback=callback, fields=fields))

    def register_inline_query_handler(self, callback: Callable):
        self.register_handler(InlineQueryHandler(callback=callback))

    def register_chosen_inline_result_handler(self, callback: Callable):
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

    def register_my_chat_member_handler(self, callback: Callable):
        self.register_handler(MyChatMemberHandler(callback=callback))

    def register_chat_member_handler(self, callback: Callable):
        self.register_handler(ChatMemberHandler(callback=callback))

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
            self.register_error_handler(callback, errors)
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

    def message_handler(self, fields: Union[str, MessageField] = None):
        def decorator(callback):
            self.register_message_handler(callback, fields)
            return callback

        return decorator

    def edited_message_handler(self, fields: Union[str, MessageField] = None):
        def decorator(callback):
            self.register_edited_message_handler(callback, fields)
            return callback

        return decorator

    def channel_post_handler(self, fields: Union[str, MessageField] = None):
        def decorator(callback):
            self.register_channel_post_handler(callback, fields)
            return callback

        return decorator

    def edited_channel_post_handler(self,
                                    fields: Union[str, MessageField] = None):
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

    def my_chat_member_handler(self):
        def decorator(callback):
            self.register_my_chat_member_handler(callback)
            return callback

        return decorator

    def chat_member_handler(self):
        def decorator(callback):
            self.register_chat_member_handler(callback)
            return callback

        return decorator

    ###################################################################################
    #
    # handler callers
    #
    ##################################################################################
    @classmethod
    def parse_update_field_and_data(cls, update: Update) -> Tuple:
        for name, value in update.items():
            if name in cls.update_field_values:
                return name, value
        raise TelegramBotException("unknown update field:\r\n{0}".format(
            pretty_format(update)))

    async def route(self, bot: TelegramBot, update: Update):
        if update.update_id and update.update_id > bot.last_update_id:
            bot.last_update_id = update.update_id
        update_field, data = self.parse_update_field_and_data(update)
        route = self._route_map.get(update_field, None)
        if route:
            try:
                await self._handler_callers[update_field](bot, data)
            except Exception as error:
                await ErrorRoute(self._route_map
                                 ).call_handlers(bot, data, error)
                raise error

    async def call_message_handlers(self, bot: TelegramBot,
                                    message: Message) -> bool:
        if await CommandRoute(self._route_map).call_handlers(
                bot, message) is self.stop_call:
            return self.stop_call
        if await ForceReplyRoute(self._route_map).call_handlers(
                bot, message) is self.stop_call:
            return self.stop_call

        return await MessageRoute(UpdateField.MESSAGE.value,
                                  self._route_map).call_handlers(bot, message)

    async def call_edited_message_handlers(self, bot: TelegramBot,
                                           edited_message: Message) -> bool:
        if await CommandRoute(self._route_map).call_handlers(
                bot, edited_message) is self.stop_call:
            return self.stop_call
        # for a edited message, the fields should be text ONLY for force_reply
        if edited_message.text and await ForceReplyRoute(
                self._route_map).call_handlers(
                    bot, edited_message) is self.stop_call:
            return self.stop_call
        return await MessageRoute(UpdateField.EDITED_MESSAGE.value,
                                  self._route_map).call_handlers(
                                      bot, edited_message)

    async def call_channel_post_handlers(self, bot: TelegramBot,
                                         message: Message) -> bool:
        return await MessageRoute(UpdateField.CHANNEL_POST.value,
                                  self._route_map).call_handlers(bot, message)

    async def call_edited_channel_post_handlers(self, bot: TelegramBot,
                                                message: Message) -> bool:
        return await MessageRoute(UpdateField.EDITED_CHANNEL_POST.value,
                                  self._route_map).call_handlers(bot, message)

    async def call_callback_query_handlers(
            self, bot: TelegramBot, callback_query: CallbackQuery) -> bool:
        return await CallbackQueryRoute(self._route_map
                                        ).call_handlers(bot, callback_query)

    async def call_inline_query_handlers(self, bot: TelegramBot,
                                         inline_query: InlineQuery) -> bool:
        return await ListRoute(UpdateField.INLINE_QUERY.value,
                               self._route_map).call_handlers(
                                   bot, inline_query)

    async def call_chosen_inline_result_handlers(
            self, bot: TelegramBot,
            chosen_inline_result: ChosenInlineResult) -> bool:
        return await ListRoute(UpdateField.CHOSEN_INLINE_RESULT.value,
                               self._route_map).call_handlers(
                                   bot, chosen_inline_result)

    async def call_shipping_query_handlers(
            self, bot: TelegramBot, shipping_query: ShippingQuery) -> bool:
        return await ListRoute(UpdateField.SHIPPING_QUERY.value,
                               self._route_map).call_handlers(
                                   bot, shipping_query)

    async def call_pre_checkout_query_handlers(
            self, bot: TelegramBot,
            pre_checkout_query: PreCheckoutQuery) -> bool:
        return await ListRoute(UpdateField.PRE_CHECKOUT_QUERY.value,
                               self._route_map).call_handlers(
                                   bot, pre_checkout_query)

    async def call_poll_handlers(self, bot: TelegramBot, poll: Poll) -> bool:
        return await ListRoute(UpdateField.POLL.value,
                               self._route_map).call_handlers(bot, poll)

    async def call_poll_answer_handlers(self, bot: TelegramBot,
                                        poll_answer: PollAnswer) -> bool:
        return await ListRoute(UpdateField.POLL_ANSWER.value,
                               self._route_map).call_handlers(
                                   bot, poll_answer)

    async def call_my_chat_member_handlers(
            self, bot: TelegramBot,
            my_chat_member_updated: ChatMemberUpdated) -> bool:
        return await ListRoute(UpdateField.MY_CHAT_MEMBER,
                               self._route_map).call_handlers(
                                   bot, my_chat_member_updated)

    async def call_chat_member_handlers(
            self, bot: TelegramBot,
            chat_member_updated: ChatMemberUpdated) -> bool:
        return await self.call_my_chat_member_handlers(bot,
                                                       chat_member_updated)

    def has_force_reply_callback(self, force_reply_name: str) -> bool:
        return force_reply_name in ForceReplyRoute(self._route_map)

    def __repr__(self):
        return pretty_format(self._route_map)
