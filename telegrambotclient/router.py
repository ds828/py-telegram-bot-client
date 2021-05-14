import logging
from collections import defaultdict
from typing import Callable, Dict, Iterable, Optional, Tuple, Union

try:
    import ujson as json
except ImportError:
    import json

from telegrambotclient.base import (CallbackQuery, ChosenInlineResult,
                                    InlineQuery, Message, MessageField, Poll,
                                    PollAnswer, PreCheckoutQuery,
                                    ShippingQuery, TelegramBotException,
                                    TelegramObject, Update, UpdateType)
from telegrambotclient.bot import TelegramBot
from telegrambotclient.handler import (
    CallbackQueryHandler, ChannelPostHandler, ChosenInlineResultHandler,
    CommandHandler, EditedChannelPostHandler, EditedMessageHandler,
    ErrorHandler, ForceReplyHandler, InlineQueryHandler, Interceptor,
    InterceptorType, MessageHandler, PollAnswerHandler, PollHandler,
    PreCheckoutQueryHandler, ShippingQueryHandler, UpdateHandler,
    _MessageHandler)
from telegrambotclient.utils import pretty_format

logger = logging.getLogger("telegram-bot-client")


class TelegramRouter:
    __slots__ = ("_name", "_route_map", "_handler_callers")
    next_call = True
    stop_call = False
    update_type_values = UpdateType.__members__.values()
    before_interceptor_value = InterceptorType.BEFORE.value
    after_interceptor_value = InterceptorType.AFTER.value

    def __init__(
        self,
        name: str,
        handlers: Optional[Iterable[UpdateHandler]] = None,
    ):
        self._name = name
        self._route_map = {}
        self._handler_callers = {
            UpdateType.MESSAGE: self.__call_message_handler,
            UpdateType.EDITED_MESSAGE: self.__call_edited_message_handler,
            UpdateType.CALLBACK_QUERY: self.__call_callback_query_handler,
            UpdateType.CHANNEL_POST: self.__call_channel_post_handler,
            UpdateType.EDITED_CHANNEL_POST:
            self.__call_edited_channel_post_handler,
            UpdateType.INLINE_QUERY: self.__call_inline_query_handler,
            UpdateType.CHOSEN_INLINE_RESULT:
            self.__call_chosen_inline_result_handler,
            UpdateType.SHIPPING_QUERY: self.__call_shipping_query_handler,
            UpdateType.PRE_CHECKOUT_QUERY:
            self.__call_pre_checkout_query_handler,
            UpdateType.POLL: self.__call_poll_handler,
            UpdateType.POLL_ANSWER: self.__call_poll_answer_handler,
        }
        self.register_handlers(handlers or ())

    @property
    def name(self):
        return self._name

    def register_handlers(self, handlers):
        for handler in handlers:
            if isinstance(handler, Interceptor):
                self.register_interceptor(handler)
                continue
            if isinstance(handler, ErrorHandler):
                self.register_error_handler(handler)
                continue
            self.register_handler(handler)

    def register_interceptor(self, interceptor: Interceptor):
        if interceptor.type not in self._route_map:
            self._route_map[interceptor.type] = {}
        for update_type in interceptor.update_types:
            self._route_map[interceptor.type][update_type] = interceptor
            logger.info(
                "bind a %s %s: '%s@%s'",
                interceptor.type,
                interceptor.__class__.__name__,
                interceptor,
                self.name,
            )

    def register_error_handler(self, handler: ErrorHandler):
        if "error" not in self._route_map:
            self._route_map["error"] = defaultdict(list)
        for update_type in handler.update_types:
            self._route_map["error"][update_type].append(handler)
            logger.info(
                "bind a ErrorHandler on %s Update: %s@%s",
                update_type,
                handler,
                self.name,
            )

    def __add_and_group(self, update_type: str, handler: _MessageHandler):
        route = self._route_map[update_type]
        if "and" not in route:
            route["and"] = []
        route["and"].append((handler.message_fields, handler))

    def __add_or_group(self, update_type: str, handler: _MessageHandler):
        route = self._route_map[update_type]
        if "or" not in route:
            route["or"] = defaultdict(list)
        for field in handler.message_fields:
            route["or"][field].append(handler)

    def __add_message_handler(self, handler: MessageHandler):
        update_type = handler.update_types[0]
        if update_type not in self._route_map:
            self._route_map[update_type] = {}
        route = self._route_map[update_type]
        message_fields = handler.message_fields
        if message_fields is None:
            if "any" in route:
                logger.warning(
                    "You are overwritting a message handler: %s on any updatetypes with %s",
                    route["any"],
                    handler,
                )
            route["any"] = handler
            return
        if len(message_fields) == 1:
            self.__add_or_group(update_type, handler)
            return
        if isinstance(message_fields, set):
            self.__add_and_group(update_type, handler)
        else:
            self.__add_or_group(update_type, handler)

    def __add_edited_message_handler(self, handler: EditedMessageHandler):
        self.__add_message_handler(handler)

    def __add_channel_post_handler(self, handler: ChannelPostHandler):
        self.__add_message_handler(handler)

    def __add_edited_channel_post_handler(self,
                                          handler: EditedChannelPostHandler):
        self.__add_message_handler(handler)

    def __add_command_handler(self, handler: CommandHandler):
        if UpdateType.COMMAND.value not in self._route_map:
            self._route_map[UpdateType.COMMAND.value] = {}
        for cmd_word in handler.cmds:
            self._route_map[UpdateType.COMMAND.value][cmd_word] = handler

    def __add_force_reply_handler(self, handler: Dict):
        if UpdateType.FORCE_REPLY.value not in self._route_map:
            self._route_map[UpdateType.FORCE_REPLY.value] = {}
        self._route_map[UpdateType.FORCE_REPLY.value][str(handler)] = handler

    def __add_callback_query_handler(self, handler: CallbackQueryHandler):
        if UpdateType.CALLBACK_QUERY.value not in self._route_map:
            self._route_map[UpdateType.CALLBACK_QUERY.value] = {}
        route = self._route_map[UpdateType.CALLBACK_QUERY.value]
        has_callback_data, has_callback_data_name, has_callback_data_regex, has_callback_data_parse = handler.have_matchers
        if has_callback_data:
            if "callback_data" not in route:
                route["callback_data"] = {}
            route["callback_data"][handler.callback_data] = handler
        if has_callback_data_name:
            if "callback_data_name" not in route:
                route["callback_data_name"] = {}
            route["callback_data_name"][handler.callback_data_name] = handler
        if has_callback_data_regex:
            if "callback_data_regex" not in route:
                route["callback_data_regex"] = []
            route["callback_data_regex"].append(handler)
        if has_callback_data_parse:
            if "callback_data_parse" not in route:
                route["callback_data_parse"] = []
            route["callback_data_parse"].append(handler)
        if handler.any_callback_data:
            if "any_callback_data" in route:
                logger.warning(
                    "You are overwritting a callback_query handler: %s on any callback data with %s",
                    route["any_callback_data"],
                    handler,
                )
            route["any_callback_data"] = handler

    def register_handler(self, handler: UpdateHandler):
        if not isinstance(handler, UpdateHandler):
            raise TelegramBotException("need a UpdateHandler")
        for update_type in handler.update_types:
            logger.info("bind a %s Handler: '%s@%s'", update_type, handler,
                        self.name)
            if update_type == UpdateType.COMMAND.value:
                self.__add_command_handler(handler)
                continue
            if update_type == UpdateType.FORCE_REPLY.value:
                self.__add_force_reply_handler(handler)
                continue
            if update_type == UpdateType.MESSAGE.value:
                self.__add_message_handler(handler)
                continue
            if update_type == UpdateType.EDITED_MESSAGE.value:
                self.__add_edited_message_handler(handler)
                continue
            if update_type == UpdateType.CALLBACK_QUERY.value:
                self.__add_callback_query_handler(handler)
                continue
            if update_type == UpdateType.CHANNEL_POST.value:
                self.__add_channel_post_handler(handler)
                continue
            if update_type == UpdateType.EDITED_CHANNEL_POST.value:
                self.__add_edited_channel_post_handler(handler)
                continue
            # for others update handlers
            self._route_map[update_type] = handler

    def register_force_reply_handler(self, callback: Callable):
        self.register_handler(ForceReplyHandler(callback=callback))

    def register_command_handler(self, callback: Callable,
                                 cmds: Iterable[str]):
        self.register_handler(CommandHandler(callback=callback, cmds=cmds))

    def register_message_handler(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        self.register_handler(MessageHandler(callback=callback, fields=fields))

    def register_edited_message_handler(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        self.register_handler(
            EditedMessageHandler(callback=callback, fields=fields))

    def register_channel_post_handler(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        self.register_handler(
            ChannelPostHandler(callback=callback, fields=fields))

    def register_edited_channel_post_handler(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
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

    def register_callback_query_handler(
            self,
            callback: Callable,
            callback_data: Optional[str] = None,
            callback_data_name: Optional[str] = None,
            callback_data_regex: Optional[Iterable[str]] = None,
            callback_data_parse: Optional[Callable] = None,
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
    def interceptor(
        self,
        inter_type: InterceptorType,
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
    ):
        def decorator(callback):
            self.register_interceptor(
                Interceptor(callback=callback,
                            inter_type=inter_type,
                            update_types=update_types))
            return callback

        return decorator

    def error_handler(
        self,
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
        errors: Optional[Iterable[Exception]] = None,
    ):
        def decorator(callback):
            self.register_error_handler(
                ErrorHandler(callback=callback,
                             update_types=update_types,
                             errors=errors))
            return callback

        return decorator

    def force_reply_handler(self):
        def decorator(callback):
            self.register_force_reply_handler(callback)
            return callback

        return decorator

    def command_handler(self, cmds: Iterable[str]):
        def decorator(callback):
            self.register_command_handler(callback, cmds)
            return callback

        return decorator

    def message_handler(
        self,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        def decorator(callback):
            self.register_message_handler(callback, fields)
            return callback

        return decorator

    def edited_message_handler(
        self,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        def decorator(callback):
            self.register_edited_message_handler(callback, fields)
            return callback

        return decorator

    def channel_post_handler(
        self,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        def decorator(callback):
            self.register_channel_post_handler(callback, fields)
            return callback

        return decorator

    def edited_channel_post_handler(
        self,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
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

    def callback_query_handler(
            self,
            callback_data: Optional[str] = None,
            callback_data_name: Optional[str] = None,
            callback_data_regex: Optional[Iterable[str]] = None,
            callback_data_parse: Optional[Callable] = None,
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

    ###################################################################################
    #
    # call handlers
    #
    ##################################################################################
    async def route(self, bot: TelegramBot, update: Update):
        if update.update_id > bot.last_update_id:
            bot.last_update_id = update.update_id
        update_type, data = self.parse_update_type_and_data(update)
        try:
            if update_type is None:
                raise TelegramBotException("unknown update type")
            await self.__call_before_interceptor(update_type, bot, data)
            await self._handler_callers[update_type](update_type, bot, data)
        except Exception as error:
            await self.__call_error_handler(update_type, bot, data, error)
            raise error
        finally:
            await self.__call_after_interceptor(update_type, bot, data)

    @classmethod
    async def __call_handler(cls, handler: UpdateHandler, *args,
                             **kwargs) -> bool:
        return cls.next_call if await handler(*args, **
                                              kwargs) else cls.stop_call

    async def __call_before_interceptor(self, update_type: UpdateType,
                                        bot: TelegramBot,
                                        data: TelegramObject):
        route = self._route_map.get(self.before_interceptor_value, None)
        if not route:
            return
        interceptor = route.get("any", None)
        if interceptor:
            await self.__call_handler(interceptor, bot, data)
        interceptor = route.get(update_type.value, None)
        if interceptor:
            await self.__call_handler(interceptor, bot, data)

    async def __call_after_interceptor(self, update_type: UpdateType,
                                       bot: TelegramBot, data: TelegramObject):
        route = self._route_map.get(self.after_interceptor_value, None)
        if not route:
            return
        interceptor = route.get(update_type.value, None)
        if interceptor:
            await self.__call_handler(interceptor, bot, data)
        interceptor = route.get("any", None)
        if interceptor:
            await self.__call_handler(interceptor, bot, data)

    async def __call_error_handler(self, update_type: UpdateType,
                                   bot: TelegramBot, data: TelegramObject,
                                   error):
        route = self._route_map.get("error", None)
        if not route:
            return
        handlers = route.get("any", None)
        if handlers:
            for handler in handlers:
                if isinstance(error, handler.error):
                    await self.__call_handler(handler, bot, data, error)
        handlers = route.get(update_type.value, None)
        if handlers:
            for handler in handlers:
                if isinstance(error, handler.error):
                    await self.__call_handler(handler, bot, data, error)

    async def __call_command_handler(self, bot: TelegramBot,
                                     message: Message) -> bool:
        command_type = UpdateType.COMMAND.value
        text = message.text
        if text is None or text[
                0] != '/' or command_type not in self._route_map:
            return self.next_call
        cmd_and_args = text.split()
        cmd_name_and_bot_username = cmd_and_args[0].split("@")
        if (len(cmd_name_and_bot_username) == 2
                and cmd_name_and_bot_username[1] != bot.username):
            return self.stop_call
        handler = self._route_map[command_type].get(
            cmd_name_and_bot_username[0], None)
        if handler is None:
            return self.next_call
        if len(cmd_and_args) == 1:
            return await self.__call_handler(handler, bot, message)
        return await self.__call_handler(handler, bot, message,
                                         *cmd_and_args[1:])

    async def __call_force_reply_handler(self, bot: TelegramBot,
                                         message: Message) -> bool:
        force_reply_callback_name, force_reply_args = bot.get_force_reply(
            message.chat.id)
        if force_reply_callback_name is None:
            return self.next_call
        handler = self.get_force_reply_handler(force_reply_callback_name)
        if handler is None:
            raise TelegramBotException(
                "{0} is not a force reply callback".format(
                    force_reply_callback_name))
        if force_reply_args:
            return await self.__call_handler(handler, bot, message,
                                             *force_reply_args)
        return await self.__call_handler(handler, bot, message)

    async def __call_message_like_handler(self, update_type: UpdateType,
                                          bot: TelegramBot, message: Message):
        route = self._route_map.get(update_type.value, None)
        if not route:
            return self.next_call
        # call 'and' handlers
        and_group = route.get("and", None)
        if and_group:
            message_fields_as_set = set(message.keys())
            for fields, handler in and_group:
                if fields <= message_fields_as_set:
                    if (await self.__call_handler(handler, bot, message) is
                            self.stop_call):
                        return self.stop_call
        # call 'or' handlers
        or_group = route.get("or", None)
        if or_group:
            for message_field, handlers in or_group.items():
                if message_field in message:
                    for handler in handlers:
                        if (await self.__call_handler(handler, bot, message) is
                                self.stop_call):
                            return self.stop_call
        # call the handler on any fields
        handler = route.get("any", None)
        if handler:
            return await self.__call_handler(handler, bot, message)

    async def __call_message_handler(self, update_type: UpdateType,
                                     bot: TelegramBot, message: Message):
        if await self.__call_command_handler(bot, message) is self.next_call:
            if await self.__call_force_reply_handler(
                    bot, message) is self.next_call:
                await self.__call_message_like_handler(update_type, bot,
                                                       message)

    async def __call_edited_message_handler(self, update_type: UpdateType,
                                            bot: TelegramBot,
                                            edited_message: Message):
        if await self.__call_command_handler(bot,
                                             edited_message) is self.next_call:
            # for edited messages, their fields should be text ONLY for force_reply
            if edited_message.text and await self.__call_force_reply_handler(
                    bot, edited_message) is self.stop_call:
                return
            await self.__call_message_like_handler(update_type, bot,
                                                   edited_message)

    async def __call_channel_post_handler(self, update_type: UpdateType,
                                          bot: TelegramBot, message: Message):
        await self.__call_message_like_handler(update_type, bot, message)

    async def __call_edited_channel_post_handler(self, update_type: UpdateType,
                                                 bot: TelegramBot,
                                                 message: Message):
        await self.__call_message_like_handler(update_type, bot, message)

    async def __call_callback_query_handler(self, update_type: UpdateType,
                                            bot: TelegramBot,
                                            callback_query: CallbackQuery):
        routes = self._route_map.get(update_type.value, None)
        if not routes:
            return
        if ("any_callback_data" in routes and
                await self.__call_handler(routes["any_callback_data"], bot,
                                          callback_query) is self.stop_call):
            return
        if "callback_data" in routes:
            handler = routes["callback_data"].get(callback_query.data, None)
            if (handler and await self.__call_handler(
                    handler, bot, callback_query) is self.stop_call):
                return
        if "callback_data_name" in routes:
            start_and_args = callback_query.data.split("|")
            handler = routes["callback_data_name"].get(start_and_args[0], None)
            if (handler and await self.__call_handler(
                    handler, bot, callback_query,
                    *json.loads(start_and_args[1])
                    if len(start_and_args) == 2 else None) is self.stop_call):
                return
        for handler in routes.get("callback_data_regex", ()):
            result = handler.callback_data_match(callback_query)
            if result and await handler(bot, callback_query,
                                        result) is self.stop_call:
                return
        for handler in routes.get("callback_data_parse", ()):
            result = handler.callback_data_parse(callback_query)
            if result:
                if (isinstance(result, bool) and await self.__call_handler(
                        handler, bot, callback_query) is self.stop_call):
                    return
                if (isinstance(result, (list, tuple, set)) and
                        await self.__call_handler(handler, bot, callback_query,
                                                  *result) is self.stop_call):
                    return
                if (await self.__call_handler(handler, bot, callback_query,
                                              result) is self.stop_call):
                    return

    async def __call_inline_query_handler(self, update_type: UpdateType,
                                          bot: TelegramBot,
                                          inline_query: InlineQuery):
        handler = self._route_map.get(update_type.value, None)
        if handler:
            await self.__call_handler(handler, bot, inline_query)

    async def __call_chosen_inline_result_handler(
        self,
        update_type: UpdateType,
        bot: TelegramBot,
        chosen_inline_result: ChosenInlineResult,
    ):
        await self.__call_inline_query_handler(update_type, bot,
                                               chosen_inline_result)

    async def __call_shipping_query_handler(self, update_type: UpdateType,
                                            bot: TelegramBot,
                                            shipping_query: ShippingQuery):
        await self.__call_inline_query_handler(update_type, bot,
                                               shipping_query)

    async def __call_pre_checkout_query_handler(
        self,
        update_type: UpdateType,
        bot: TelegramBot,
        pre_checkout_query: PreCheckoutQuery,
    ):
        await self.__call_inline_query_handler(update_type, bot,
                                               pre_checkout_query)

    async def __call_poll_handler(self, update_type: UpdateType,
                                  bot: TelegramBot, poll: Poll):
        await self.__call_inline_query_handler(update_type, bot, poll)

    async def __call_poll_answer_handler(self, update_type: UpdateType,
                                         bot: TelegramBot,
                                         poll_answer: PollAnswer):
        await self.__call_inline_query_handler(update_type, bot, poll_answer)

    def get_force_reply_handler(self,
                                callback_name: str) -> Optional[Callable]:
        force_reply_type_value = UpdateType.FORCE_REPLY.value
        if force_reply_type_value in self._route_map:
            return self._route_map[force_reply_type_value].get(
                callback_name, None)
        return None

    def has_force_reply_callback(self, callback_name: str) -> bool:
        return self.get_force_reply_handler(callback_name) is not None

    def has_callback_query_handler(self, callback: Callable) -> bool:
        if "callback_query" in self._route_map:
            callback_name = "{0}.{1}".format(callback.__module__,
                                             callback.__name__)
            callback_query_handlers = self._route_map["callback_query"]
            for handler in callback_query_handlers.get("callback_data",
                                                       {}).values():
                if str(handler) == callback_name:
                    return True
            for handler in callback_query_handlers.get("callback_data_name",
                                                       {}).values():
                if str(handler) == callback_name:
                    return True
            for handler in callback_query_handlers.get("callback_data_regex",
                                                       ()):
                if str(handler) == callback_name:
                    return True
            for handler in callback_query_handlers.get("callback_data_parse",
                                                       ()):
                if str(handler) == callback_name:
                    return True
        return False

    def __repr__(self):
        return "\r\n{0}".format(pretty_format(self._route_map))

    @classmethod
    def parse_update_type_and_data(
        cls,
        update: Update,
    ) -> Tuple[Optional[UpdateType], Optional[TelegramObject]]:
        for name, value in update.items():
            if name in cls.update_type_values:
                return UpdateType(name), value
        return None, None
