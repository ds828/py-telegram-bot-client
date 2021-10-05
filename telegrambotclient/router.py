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
                                    UpdateField)
from telegrambotclient.bot import TelegramBot, logger
from telegrambotclient.handler import (
    CallbackQueryHandler, ChannelPostHandler, ChatMemberHandler,
    ChosenInlineResultHandler, CommandHandler, EditedChannelPostHandler,
    EditedMessageHandler, ErrorHandler, ForceReplyHandler, InlineQueryHandler,
    MessageHandler, MyChatMemberHandler, PollAnswerHandler, PollHandler,
    PreCheckoutQueryHandler, ShippingQueryHandler, UpdateHandler,
    _MessageHandler)
from telegrambotclient.utils import pretty_format


class DefaultRoute:
    __slots__ = ("_root_route", "name")

    def __init__(self, name: str, root_route):
        self.name = name
        self._root_route = root_route

    def add_handler(self, handler: UpdateHandler):
        if self.name not in self._root_route:
            self._root_route[self.name] = []
        route = self._root_route[self.name]
        for idx, _handler in enumerate(route):
            if _handler.name == handler.name:
                route[idx] = handler
                return
        route.append(handler)

    def remove_handler(self, handler: UpdateHandler):
        if self.name in self._root_route:
            route = self._root_route[self.name]
            for _handler in route:
                if _handler.name == handler.name:
                    route.remove(_handler)
                    break
            if not route:
                del self._root_route[self.name]

    async def call_handlers(self, bot: TelegramBot, data: TelegramObject):
        for handler in self._root_route.get(self.name, ()):
            if await self.call_handler(handler, bot, data) is bot.stop_call:
                return bot.stop_call
        return bot.next_call

    @staticmethod
    async def call_handler(handler: UpdateHandler, *args, **kwargs):
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
        if self.name not in self._root_route:
            self._root_route[self.name] = {}
        for cmd_word in handler.cmds:
            self._root_route[self.name][cmd_word] = handler
        route = self._root_route.get(UpdateField.MESSAGE.value, {})
        route[self.name] = True
        self._root_route[UpdateField.MESSAGE.value] = route
        route = self._root_route.get(UpdateField.EDITED_MESSAGE.value, {})
        route[self.name] = True
        self._root_route[UpdateField.EDITED_MESSAGE.value] = route

    def remove_handler(self, handler: CommandHandler):
        if self.name in self._root_route:
            route = self._root_route[self.name]
            for cmd_word in handler.cmds:
                if cmd_word in route:
                    del route[cmd_word]
            if not route:
                del self._root_route[self.name]
                if self.name in self._root_route.get(UpdateField.MESSAGE.value,
                                                     {}):
                    del self._root_route[UpdateField.MESSAGE.value][self.name]
                if self.name in self._root_route.get(
                        UpdateField.EDITED_MESSAGE.value, {}):
                    del self._root_route[UpdateField.EDITED_MESSAGE.value][
                        self.name]

    async def call_handlers(self, bot: TelegramBot, message: Message):
        if not message.text or message.text[
                0] != '/' or self.name not in self._root_route:
            return bot.next_call
        # /start@jobs_bot arg1 arg2
        cmd, *args = tuple(message.text.split(maxsplit=1))
        cmd_name, *bot_username = tuple(cmd.split("@"))
        if bot_username and bot_username != bot.user.username:
            return bot.stop_call
        handler = self._root_route.get(self.name, {}).get(cmd_name, None)
        if handler is None:
            return bot.stop_call
        if args:
            return await self.call_handler(handler, bot, message,
                                           *args[0].split(handler.delimiter))
        return await self.call_handler(handler, bot, message)


class ForceReplyRoute(DefaultRoute):
    def __init__(self, root_route):
        super().__init__("force_reply", root_route)

    def add_handler(self, handler: ForceReplyHandler):
        if self.name not in self._root_route:
            self._root_route[self.name] = {}
        self._root_route[self.name][handler.name] = handler

    def remove_handler(self, handler: ForceReplyHandler):
        if self.name in self._root_route:
            route = self._root_route[self.name]
            if handler.name in route:
                del route[handler.name]
            if not route:
                del self._root_route[self.name]

    async def call_handlers(self, bot: TelegramBot, message: Message):
        force_reply_callback_name, force_reply_args = bot.get_force_reply(
            message.chat.id if message.chat else message.from_user.
            id if message.from_user else 0)
        if force_reply_callback_name is None:
            return bot.next_call
        handler = self._root_route.get(self.name,
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
        return force_reply_name in self._root_route.get(self.name, {})


class MessageRoute(DefaultRoute):
    def __init__(self, name: str, root_route):
        super().__init__(name, root_route)

    def add_handler(self, handler: _MessageHandler):
        if self.name not in self._root_route:
            self._root_route[self.name] = {}
        route = self._root_route[self.name]
        message_fields = handler.fields
        if not message_fields:
            DefaultRoute("all", route).add_handler(handler)
        elif isinstance(message_fields, str):
            if "|" not in route:
                route["|"] = defaultdict(list)
            DefaultRoute(message_fields, route["|"]).add_handler(handler)
        elif isinstance(message_fields, tuple):
            if "|" not in route:
                route["|"] = defaultdict(list)
            for field in message_fields:
                DefaultRoute(field, route["|"]).add_handler(handler)
        elif isinstance(message_fields, set):
            DefaultRoute("&", route).add_handler(handler)

    def remove_handler(self, handler: _MessageHandler):
        if self.name in self._root_route:
            route = self._root_route[self.name]
            message_fields = handler.fields
            if not message_fields:
                DefaultRoute("all", route).remove_handler(handler)
            elif isinstance(message_fields, str) and "|" in route:
                DefaultRoute(message_fields,
                             route["|"]).remove_handler(handler)
            elif isinstance(message_fields, tuple) and "|" in route:
                for field in message_fields:
                    DefaultRoute(field, route["|"]).remove_handler(handler)
            elif isinstance(message_fields, set):
                DefaultRoute("&", route).remove_handler(handler)
            if not route:
                del self._root_route[self.name]

    async def call_handlers(self, bot: TelegramBot, message: Message):
        if self.name in self._root_route:
            route = self._root_route[self.name]
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
        if self.name not in self._root_route:
            self._root_route[self.name] = {}
        route = self._root_route[self.name]
        if handler.callback_data:
            if "data" not in route:
                route["data"] = {}
            route["data"][handler.callback_data] = handler
        if handler.callback_data_name:
            if "name" not in route:
                route["name"] = {}
            route["name"][handler.callback_data_name] = handler
        if handler.callback_data_patterns:
            DefaultRoute("regex", route).add_handler(handler)
        if handler.callback_data_parser:
            DefaultRoute("parse", route).add_handler(handler)
        if handler.game_short_name:
            if "game" not in route:
                route["name"] = {}
            route["game"][handler.game_short_name] = handler

    def remove_handler(self, handler: CallbackQueryHandler):
        if self.name in self._root_route:
            route = self._root_route[self.name]
            if handler.callback_data and "data" in route and handler.callback_data in route[
                    "data"]:
                del route["data"][handler.callback_data]
            if handler.callback_data_name and "name" in route and handler.callback_data_name in route[
                    "name"]:
                del route["name"][handler.callback_data_name]
            if handler.callback_data_patterns:
                DefaultRoute("regex", route).remove_handler(handler)
            if handler.callback_data_parser:
                DefaultRoute("parse", route).remove_handler(handler)
            if handler.game_short_name and "game" in route and handler.game_short_name in route[
                    "game"]:
                del route["game"][handler.callback_data_name]
            if not route:
                del self._root_route[self.name]

    async def call_handlers(self, bot: TelegramBot,
                            callback_query: CallbackQuery):
        if self.name in self._root_route:
            route = self._root_route[self.name]
            if callback_query.data:
                # for callback_data
                handler = route.get("data", {}).get(callback_query.data, None)
                if handler and await self.call_handler(
                        handler, bot, callback_query) is bot.stop_call:
                    return bot.stop_call
                #for callback_data_name
                if "|" in callback_query.data:
                    callback_name, callback_data = tuple(
                        callback_query.data.split("|", maxsplit=1))
                    if callback_data:
                        handler = route.get("name",
                                            {}).get(callback_name, None)
                        if handler and await self.call_handler(
                                handler, bot, callback_query,
                                *json.loads(callback_data)) is bot.stop_call:
                            return bot.stop_call
                # for callback_data_regex
                for handler in route.get("regex", ()):
                    result = handler.match_callback_data(callback_query)
                    if result and await self.call_handler(
                            handler, bot, callback_query,
                            result) is bot.stop_call:
                        return bot.stop_call
                # for callback_data_parse
                for handler in route.get("parse", ()):
                    result = handler.parse_callback_data(callback_query)
                    if result and await self.call_handler(
                            handler, bot, callback_query,
                            result) is bot.stop_call:
                        return bot.stop_call
            elif callback_query.game_short_name:
                handler = route.get("game",
                                    {}).get(callback_query.game_short_name,
                                            None)
                if handler and await self.call_handler(
                        handler, bot, callback_query) is bot.stop_call:
                    return bot.stop_call

        return bot.next_call


class TelegramRouter:
    __slots__ = ("name", "route_map", "_handler_callers")
    NEXT_CALL = True
    STOP_CALL = False
    UPDATE_FIELD_VALUES = UpdateField.__members__.values()

    def __init__(self, name: str):
        self.name = name
        self.route_map = {}
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

    def register_handlers(self, handlers):
        for handler in handlers:
            self.register_handler(handler)

    def register_handler(self, handler: UpdateHandler):
        assert isinstance(handler, UpdateHandler), True
        update_field = handler.update_field
        logger.info("bind a %s handler: '%s@%s'", update_field, handler.name,
                    self.name)
        if isinstance(handler, CommandHandler):
            return CommandRoute(self.route_map).add_handler(handler)
        if isinstance(handler, ForceReplyHandler):
            return ForceReplyRoute(self.route_map).add_handler(handler)
        if isinstance(handler, MessageHandler):
            return MessageRoute(UpdateField.MESSAGE.value,
                                self.route_map).add_handler(handler)
        if isinstance(handler, EditedMessageHandler):
            return MessageRoute(UpdateField.EDITED_MESSAGE.value,
                                self.route_map).add_handler(handler)
        if isinstance(handler, CallbackQueryHandler):
            return CallbackQueryRoute(self.route_map).add_handler(handler)
        if isinstance(handler, ChannelPostHandler):
            return MessageRoute(UpdateField.CHANNEL_POST.value,
                                self.route_map).add_handler(handler)
        if isinstance(handler, EditedChannelPostHandler):
            return MessageRoute(UpdateField.EDITED_CHANNEL_POST.value,
                                self.route_map).add_handler(handler)
        if isinstance(handler, ErrorHandler):
            return ErrorRoute(self.route_map).add_handler(handler)
        # for others update handlers
        return DefaultRoute(update_field, self.route_map).add_handler(handler)

    def remove_handler(self, handler: UpdateHandler):
        assert isinstance(handler, UpdateHandler), True
        update_field = handler.update_field
        logger.info("unbind a %s handler: '%s@%s'", update_field, handler.name,
                    self.name)
        if isinstance(handler, CommandHandler):
            return CommandRoute(self.route_map).remove_handler(handler)
        if isinstance(handler, ForceReplyHandler):
            return ForceReplyRoute(self.route_map).remove_handler(handler)
        if isinstance(handler, MessageHandler):
            return MessageRoute(UpdateField.MESSAGE.value,
                                self.route_map).remove_handler(handler)
        if isinstance(handler, EditedMessageHandler):
            return MessageRoute(UpdateField.EDITED_MESSAGE.value,
                                self.route_map).remove_handler(handler)
        if isinstance(handler, CallbackQueryHandler):
            return CallbackQueryRoute(self.route_map).remove_handler(handler)
        if isinstance(handler, ChannelPostHandler):
            return MessageRoute(UpdateField.CHANNEL_POST.value,
                                self.route_map).remove_handler(handler)
        if isinstance(handler, EditedChannelPostHandler):
            return MessageRoute(UpdateField.EDITED_CHANNEL_POST.value,
                                self.route_map).add_handler(handler)
        if isinstance(handler, ErrorHandler):
            return ErrorRoute(self.route_map).remove_handler(handler)
        # for others update handlers
        return DefaultRoute(update_field,
                            self.route_map).remove_handler(handler)

    def register_error_handler(self, callback: Callable, errors):
        self.register_handler(
            ErrorHandler(callback=callback,
                         errors=tuple(errors) if errors else None))

    def register_command_handler(self,
                                 callback: Callable,
                                 cmds,
                                 delimiter=" "):
        self.register_handler(
            CommandHandler(callback=callback, cmds=cmds, delimiter=delimiter))

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
                                        game_short_name: str = None,
                                        **kwargs):
        self.register_handler(
            CallbackQueryHandler(callback=callback,
                                 callback_data=callback_data,
                                 callback_data_name=callback_data_name,
                                 callback_data_regex=callback_data_regex,
                                 callback_data_parse=callback_data_parse,
                                 game_short_name=game_short_name,
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
                               game_short_name: str = None,
                               **kwargs):
        def decorator(callback):
            self.register_callback_query_handler(callback, callback_data,
                                                 callback_data_name,
                                                 callback_data_regex,
                                                 callback_data_parse,
                                                 game_short_name, **kwargs)
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
    def parse_update_field_and_data(cls, update):
        for name, value in update.items():
            if name in cls.UPDATE_FIELD_VALUES and value:
                return name, TelegramObject(**value)
        raise TelegramBotException("unknown update field: {0}".format(
            pretty_format(update)))

    async def route(self, bot: TelegramBot, update):
        if update["update_id"] and update["update_id"] > bot.last_update_id:
            bot.last_update_id = update["update_id"]
        update_field, data = self.parse_update_field_and_data(update)
        route = self.route_map.get(update_field, None)
        if route:
            try:
                await self._handler_callers[update_field](bot, data)
            except Exception as error:
                await ErrorRoute(self.route_map
                                 ).call_handlers(bot, data, error)
                raise error

    async def call_message_handlers(self, bot: TelegramBot, message: Message):
        if message.text and await CommandRoute(self.route_map).call_handlers(
                bot, message) is self.STOP_CALL:
            return self.STOP_CALL
        if await ForceReplyRoute(self.route_map).call_handlers(
                bot, message) is self.STOP_CALL:
            return self.STOP_CALL

        return await MessageRoute(UpdateField.MESSAGE.value,
                                  self.route_map).call_handlers(bot, message)

    async def call_edited_message_handlers(self, bot: TelegramBot,
                                           edited_message: Message):
        if edited_message.text:
            if await CommandRoute(self.route_map).call_handlers(
                    bot, edited_message) is self.STOP_CALL:
                return self.STOP_CALL
            # for a edited message, the fields should be text ONLY for force_reply
            if await ForceReplyRoute(self.route_map).call_handlers(
                    bot, edited_message) is self.STOP_CALL:
                return self.STOP_CALL
        return await MessageRoute(UpdateField.EDITED_MESSAGE.value,
                                  self.route_map).call_handlers(
                                      bot, edited_message)

    async def call_channel_post_handlers(self, bot: TelegramBot,
                                         message: Message):
        return await MessageRoute(UpdateField.CHANNEL_POST.value,
                                  self.route_map).call_handlers(bot, message)

    async def call_edited_channel_post_handlers(self, bot: TelegramBot,
                                                message: Message):
        return await MessageRoute(UpdateField.EDITED_CHANNEL_POST.value,
                                  self.route_map).call_handlers(bot, message)

    async def call_callback_query_handlers(self, bot: TelegramBot,
                                           callback_query: CallbackQuery):
        return await CallbackQueryRoute(self.route_map
                                        ).call_handlers(bot, callback_query)

    async def call_inline_query_handlers(self, bot: TelegramBot,
                                         inline_query: InlineQuery):
        return await DefaultRoute(UpdateField.INLINE_QUERY.value,
                                  self.route_map).call_handlers(
                                      bot, inline_query)

    async def call_chosen_inline_result_handlers(
            self, bot: TelegramBot, chosen_inline_result: ChosenInlineResult):
        return await DefaultRoute(UpdateField.CHOSEN_INLINE_RESULT.value,
                                  self.route_map).call_handlers(
                                      bot, chosen_inline_result)

    async def call_shipping_query_handlers(self, bot: TelegramBot,
                                           shipping_query: ShippingQuery):
        return await DefaultRoute(UpdateField.SHIPPING_QUERY.value,
                                  self.route_map).call_handlers(
                                      bot, shipping_query)

    async def call_pre_checkout_query_handlers(
            self, bot: TelegramBot, pre_checkout_query: PreCheckoutQuery):
        return await DefaultRoute(UpdateField.PRE_CHECKOUT_QUERY.value,
                                  self.route_map).call_handlers(
                                      bot, pre_checkout_query)

    async def call_poll_handlers(self, bot: TelegramBot, poll: Poll):
        return await DefaultRoute(UpdateField.POLL.value,
                                  self.route_map).call_handlers(bot, poll)

    async def call_poll_answer_handlers(self, bot: TelegramBot,
                                        poll_answer: PollAnswer):
        return await DefaultRoute(UpdateField.POLL_ANSWER.value,
                                  self.route_map).call_handlers(
                                      bot, poll_answer)

    async def call_my_chat_member_handlers(
            self, bot: TelegramBot, my_chat_member_updated: ChatMemberUpdated):
        return await DefaultRoute(UpdateField.MY_CHAT_MEMBER,
                                  self.route_map).call_handlers(
                                      bot, my_chat_member_updated)

    async def call_chat_member_handlers(
            self, bot: TelegramBot, chat_member_updated: ChatMemberUpdated):
        return await self.call_my_chat_member_handlers(bot,
                                                       chat_member_updated)

    def has_force_reply_callback(self, force_reply_name: str):
        return force_reply_name in ForceReplyRoute(self.route_map)

    def __repr__(self):
        return pretty_format(self.route_map)
