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


class DefaultRoute:
    __slots__ = ("_root_route", "_name")

    def __init__(self, name: str, root_route):
        self._name = name
        self._root_route = root_route

    def add_handler(self, handler: UpdateHandler):
        if self._name not in self._root_route:
            self._root_route[self._name] = []
        route = self._root_route[self._name]
        for idx, _handler in enumerate(route):
            if _handler.name == handler.name:
                route[idx] = handler
                return
        route.append(handler)

    def remove_handler(self, handler: UpdateHandler):
        if self._name in self._root_route:
            route = self._root_route[self._name]
            for _handler in route:
                if _handler.name == handler.name:
                    route.remove(_handler)
                    break
            if not route:
                del self._root_route[self._name]

    async def call_handlers(self, bot: TelegramBot,
                            data: TelegramObject) -> bool:
        for handler in self._root_route.get(self._name, ()):
            if await self.call_handler(handler, bot, data) is bot.stop_call:
                return bot.stop_call
        return bot.next_call

    @staticmethod
    async def call_handler(handler: UpdateHandler, *args, **kwargs) -> bool:
        return bool(await handler(*args, **kwargs))


class ErrorRoute(DefaultRoute):
    def __init__(self, root_route):
        super().__init__("error", root_route)

    async def call_handlers(self, bot: TelegramBot, data: TelegramObject,
                            error: Exception) -> bool:
        for handler in self._root_route.get("error", ()):
            if isinstance(error, handler.errors) and await self.call_handler(
                    handler, bot, data, error) is bot.stop_call:
                return bot.stop_call
        return bot.next_call


class CommandRoute(DefaultRoute):
    def __init__(self, root_route):
        super().__init__("cmd", root_route)

    def add_handler(self, handler: CommandHandler):
        if self._name not in self._root_route:
            self._root_route[self._name] = {}
        for cmd_word in handler.cmds:
            self._root_route[self._name][cmd_word] = handler
        route = self._root_route.get(UpdateField.MESSAGE.value, {})
        route[self._name] = True
        self._root_route[UpdateField.MESSAGE.value] = route
        route = self._root_route.get(UpdateField.EDITED_MESSAGE.value, {})
        route[self._name] = True
        self._root_route[UpdateField.EDITED_MESSAGE.value] = route

    def remove_handler(self, handler: CommandHandler):
        if self._name in self._root_route:
            route = self._root_route[self._name]
            for cmd_word in handler.cmds:
                if cmd_word in route:
                    del route[cmd_word]
            if not route:
                del self._root_route[self._name]
                if self._name in self._root_route.get(
                        UpdateField.MESSAGE.value, {}):
                    del self._root_route[UpdateField.MESSAGE.value][self._name]
                if self._name in self._root_route.get(
                        UpdateField.EDITED_MESSAGE.value, {}):
                    del self._root_route[UpdateField.EDITED_MESSAGE.value][
                        self._name]

    async def call_handlers(self, bot: TelegramBot, message: Message) -> bool:
        text = message.text
        if not text or text[0] != '/' or self._name not in self._root_route:
            return bot.next_call
        cmd_and_args = text.split()
        cmd_name_and_bot_username = cmd_and_args[0].split("@")
        if (len(cmd_name_and_bot_username) == 2
                and cmd_name_and_bot_username[1] != bot.user.username):
            return bot.stop_call
        handler = self._root_route.get(self._name,
                                       {}).get(cmd_name_and_bot_username[0],
                                               None)
        if handler is None:
            return bot.next_call
        if len(cmd_and_args) == 1:
            return await self.call_handler(handler, bot, message)
        return await self.call_handler(handler, bot, message,
                                       *cmd_and_args[1:])


class ForceReplyRoute(DefaultRoute):
    def __init__(self, root_route):
        super().__init__("force_reply", root_route)

    def add_handler(self, handler: ForceReplyHandler):
        if self._name not in self._root_route:
            self._root_route[self._name] = {}
        self._root_route[self._name][handler.name] = handler

    def remove_handler(self, handler: ForceReplyHandler):
        if self._name in self._root_route:
            route = self._root_route[self._name]
            if handler.name in route:
                del route[handler.name]
            if not route:
                del self._root_route[self._name]

    async def call_handlers(self, bot: TelegramBot, message: Message) -> bool:
        force_reply_callback_name, force_reply_args = bot.get_force_reply(
            message.chat.id if message.chat else message.from_user.
            id if message.from_user else 0)
        if force_reply_callback_name is None:
            return bot.next_call
        handler = self._root_route.get(self._name,
                                       {}).get(force_reply_callback_name, None)
        if handler is None:
            raise TelegramBotException(
                "{0} is not found as a force reply callback".format(
                    force_reply_callback_name))
        return await self.call_handler(
            handler, bot, message, *
            force_reply_args) if force_reply_args else await self.call_handler(
                handler, bot, message)

    def __contains__(self, force_reply_name: str):
        return force_reply_name in self._root_route.get(self._name, {})


class MessageRoute(DefaultRoute):
    def __init__(self, name: str, root_route):
        super().__init__(name, root_route)

    def add_handler(self, handler: _MessageHandler):
        if self._name not in self._root_route:
            self._root_route[self._name] = {}
        route = self._root_route[self._name]
        message_fields = handler.message_fields
        if message_fields is None:
            DefaultRoute("all", route).add_handler(handler)
        elif isinstance(message_fields, str):
            if "|" not in route:
                route["|"] = defaultdict(list)
            DefaultRoute(message_fields, route["|"]).add_handler(handler)
        elif isinstance(message_fields, tuple):
            if "|" not in route:
                route["|"] = defaultdict(list)
            for field in handler.message_fields or ():
                DefaultRoute(field, route["|"]).add_handler(handler)
        elif isinstance(message_fields, set):
            DefaultRoute("&", route).add_handler(handler)

    def remove_handler(self, handler: _MessageHandler):
        if self._name in self._root_route:
            route = self._root_route[self._name]
            message_fields = handler.message_fields
            if message_fields is None:
                DefaultRoute("all", route).remove_handler(handler)
            elif isinstance(message_fields, str) and "|" in route:
                DefaultRoute(message_fields,
                             route["|"]).remove_handler(handler)
            elif isinstance(message_fields, tuple) and "|" in route:
                for field in handler.message_fields or ():
                    DefaultRoute(field, route["|"]).remove_handler(handler)
            elif isinstance(message_fields, set):
                DefaultRoute("&", route).remove_handler(handler)
            if not route:
                del self._root_route[self._name]

    async def call_handlers(self, bot: TelegramBot, message: Message) -> bool:
        if self._name in self._root_route:
            route = self._root_route[self._name]
            # call 'and' handlers
            handlers = route.get("&", None)
            if handlers:
                message_fields_set = set(message.keys())
                for handler in handlers:
                    if handler.fields <= message_fields_set:
                        if await self.call_handler(handler, bot,
                                                   message) is bot.stop_call:
                            return bot.stop_call
            # call 'or' handlers
            handler_dict = route.get("|", None)
            if handler_dict:
                for message_field in handler_dict.keys():
                    if message_field in message:
                        for handler in handler_dict[message_field]:
                            if await self.call_handler(
                                    handler, bot, message) is bot.stop_call:
                                return bot.stop_call
            # call 'all' handlers
            handlers = route.get("all", None)
            if handlers:
                for handler in handlers:
                    if await self.call_handler(handler, bot,
                                               message) is bot.stop_call:
                        return bot.stop_call
        return bot.next_call


class CallbackQueryRoute(DefaultRoute):
    def __init__(self, root_route):
        super().__init__(UpdateField.CALLBACK_QUERY.value, root_route)

    def add_handler(self, handler: CallbackQueryHandler):
        if self._name not in self._root_route:
            self._root_route[self._name] = {}
        route = self._root_route[self._name]
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
            DefaultRoute("regex", route).add_handler(handler)
        if has_callback_data_parse:
            DefaultRoute("parse", route).add_handler(handler)

    def remove_handler(self, handler: CallbackQueryHandler):
        if self._name in self._root_route:
            route = self._root_route[self._name]
            has_callback_data, has_callback_data_name, has_callback_data_regex, has_callback_data_parse = handler.have_matchers
            if has_callback_data and "data" in route and handler.callback_data in route[
                    "data"]:
                del route["data"][handler.callback_data]
            if has_callback_data_name and "name" in route and handler.callback_data_name in route[
                    "name"]:
                del route["name"][handler.callback_data_name]
            if has_callback_data_regex:
                DefaultRoute("regex", route).remove_handler(handler)
            if has_callback_data_parse:
                DefaultRoute("parse", route).remove_handler(handler)
            if not route:
                del self._root_route[self._name]

    async def call_handlers(self, bot: TelegramBot,
                            callback_query: CallbackQuery) -> bool:
        if callback_query.data is None:
            raise TelegramBotException("callback_query.data is None")
        if self._name in self._root_route:
            route = self._root_route[self._name]
            # for callback_data
            handler = route.get("data", {}).get(callback_query.data, None)
            if handler and await self.call_handler(
                    handler, bot, callback_query) is bot.stop_call:
                return bot.stop_call
            #for callback_data_name
            callback_name_data = callback_query.data.split("|")
            if len(callback_name_data) == 2:
                callback_name, callback_data = tuple(callback_name_data)
                handler = route.get("name", {}).get(callback_name, None)
                if handler and await self.call_handler(
                        handler, bot, callback_query, *
                        json.loads(callback_data)) is bot.stop_call:
                    return bot.stop_call
            # for callback_data_regex
            for handler in route.get("regex", ()):
                result = handler.callback_data_match(callback_query)
                if result and await self.call_handler(
                        handler, bot, callback_query, result) is bot.stop_call:
                    return bot.stop_call
            # for callback_data_parse
            for handler in route.get("parse", ()):
                result = handler.callback_data_parse(callback_query)
                if result and await self.call_handler(
                        handler, bot, callback_query, result) is bot.stop_call:
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
        return DefaultRoute(update_field, self._route_map).add_handler(handler)

    def remove_handler(self, handler: UpdateHandler):
        assert isinstance(handler, UpdateHandler), True
        update_field = handler.update_field
        logger.info("unbind a %s handler: '%s@%s'", update_field, handler.name,
                    self.name)
        if isinstance(handler, CommandHandler):
            return CommandRoute(self._route_map).remove_handler(handler)
        if isinstance(handler, ForceReplyHandler):
            return ForceReplyRoute(self._route_map).remove_handler(handler)
        if isinstance(handler, MessageHandler):
            return MessageRoute(UpdateField.MESSAGE.value,
                                self._route_map).remove_handler(handler)
        if isinstance(handler, EditedMessageHandler):
            return MessageRoute(UpdateField.EDITED_MESSAGE.value,
                                self._route_map).remove_handler(handler)
        if isinstance(handler, CallbackQueryHandler):
            return CallbackQueryRoute(self._route_map).remove_handler(handler)
        if isinstance(handler, ChannelPostHandler):
            return MessageRoute(UpdateField.CHANNEL_POST.value,
                                self._route_map).remove_handler(handler)
        if isinstance(handler, EditedChannelPostHandler):
            return MessageRoute(UpdateField.EDITED_CHANNEL_POST.value,
                                self._route_map).add_handler(handler)
        if isinstance(handler, ErrorHandler):
            return ErrorRoute(self._route_map).remove_handler(handler)
        # for others update handlers
        return DefaultRoute(update_field,
                            self._route_map).remove_handler(handler)

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
            if name in cls.update_field_values and value:
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
        if message.text and await CommandRoute(self._route_map).call_handlers(
                bot, message) is self.stop_call:
            return self.stop_call
        if await ForceReplyRoute(self._route_map).call_handlers(
                bot, message) is self.stop_call:
            return self.stop_call

        return await MessageRoute(UpdateField.MESSAGE.value,
                                  self._route_map).call_handlers(bot, message)

    async def call_edited_message_handlers(self, bot: TelegramBot,
                                           edited_message: Message) -> bool:
        if edited_message.text:
            if await CommandRoute(self._route_map).call_handlers(
                    bot, edited_message) is self.stop_call:
                return self.stop_call
            # for a edited message, the fields should be text ONLY for force_reply
            if await ForceReplyRoute(self._route_map).call_handlers(
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
        return await DefaultRoute(UpdateField.INLINE_QUERY.value,
                                  self._route_map).call_handlers(
                                      bot, inline_query)

    async def call_chosen_inline_result_handlers(
            self, bot: TelegramBot,
            chosen_inline_result: ChosenInlineResult) -> bool:
        return await DefaultRoute(UpdateField.CHOSEN_INLINE_RESULT.value,
                                  self._route_map).call_handlers(
                                      bot, chosen_inline_result)

    async def call_shipping_query_handlers(
            self, bot: TelegramBot, shipping_query: ShippingQuery) -> bool:
        return await DefaultRoute(UpdateField.SHIPPING_QUERY.value,
                                  self._route_map).call_handlers(
                                      bot, shipping_query)

    async def call_pre_checkout_query_handlers(
            self, bot: TelegramBot,
            pre_checkout_query: PreCheckoutQuery) -> bool:
        return await DefaultRoute(UpdateField.PRE_CHECKOUT_QUERY.value,
                                  self._route_map).call_handlers(
                                      bot, pre_checkout_query)

    async def call_poll_handlers(self, bot: TelegramBot, poll: Poll) -> bool:
        return await DefaultRoute(UpdateField.POLL.value,
                                  self._route_map).call_handlers(bot, poll)

    async def call_poll_answer_handlers(self, bot: TelegramBot,
                                        poll_answer: PollAnswer) -> bool:
        return await DefaultRoute(UpdateField.POLL_ANSWER.value,
                                  self._route_map).call_handlers(
                                      bot, poll_answer)

    async def call_my_chat_member_handlers(
            self, bot: TelegramBot,
            my_chat_member_updated: ChatMemberUpdated) -> bool:
        return await DefaultRoute(UpdateField.MY_CHAT_MEMBER,
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
