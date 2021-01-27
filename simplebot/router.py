from collections import defaultdict
import logging
from typing import Dict, Iterable, Optional, Tuple, Callable, Union

from simplebot.utils import pretty_json
from simplebot.base import (
    CallbackQuery,
    ChosenInlineResult,
    InlineQuery,
    Message,
    MessageField,
    SimpleBotException,
    SimpleObject,
    Update,
    UpdateType,
    ShippingQuery,
    PreCheckoutQuery,
    Poll,
    PollAnswer,
)
from simplebot.bot import SimpleBot
from simplebot.handler import (
    CallbackQueryHandler,
    ChannelPostHandler,
    ChosenInlineResultHandler,
    CommandHandler,
    EditedChannelPostHandler,
    EditedMessageHandler,
    ErrorHandler,
    ForceReplyHandler,
    InlineQueryHandler,
    Interceptor,
    InterceptorType,
    MessageHandler,
    PollAnswerHandler,
    PollHandler,
    PreCheckoutQueryHandler,
    ShippingQueryHandler,
    UpdateHandler,
    _MessageHandler,
)

logger = logging.getLogger("simple-bot")


class SimpleRouter:
    __slots__ = ("_name", "_handlers", "_route_map", "_call_handler_switcher")

    def __init__(
        self,
        name: str,
        handlers: Optional[Iterable[UpdateHandler]] = None,
    ):
        self._name = name
        self._handlers = {}
        self._route_map = {}
        self._call_handler_switcher = {
            UpdateType.MESSAGE: self.__call_message_handler,
            UpdateType.EDITED_MESSAGE: self.__call_edited_message_handler,
            UpdateType.CALLBACK_QUERY: self.__call_callback_query_handler,
            UpdateType.CHANNEL_POST: self.__call_channel_post_handler,
            UpdateType.EDITED_CHANNEL_POST: self.__call_edited_channel_post_handler,
            UpdateType.INLINE_QUERY: self.__call_inline_query_handler,
            UpdateType.CHOSEN_INLINE_RESULT: self.__call_chosen_inline_result_handler,
            UpdateType.SHIPPING_QUERY: self.__call_shipping_query_handler,
            UpdateType.PRE_CHECKOUT_QUERY: self.__call_pre_checkout_query_handler,
            UpdateType.POLL: self.__call_poll_handler,
            UpdateType.POLL_ANSWER: self.__call_poll_answer_handler,
        }
        if handlers:
            for handler in handlers:
                if isinstance(handler, Interceptor):
                    self.register_interceptor(handler)
                    continue
                if isinstance(handler, ErrorHandler):
                    self.register_error_handler(handler)
                    continue
                self.register_handler(handler)

    @property
    def name(self):
        return self._name

    def register_interceptor(self, interceptor: Interceptor):
        self._handlers[interceptor.name] = interceptor
        if interceptor.type not in self._route_map:
            self._route_map[interceptor.type] = {}
        for update_type in interceptor.update_types:
            self._route_map[interceptor.type][update_type] = interceptor.name
            logger.info(
                "bind a %s %s: '%s@%s'",
                interceptor.type,
                interceptor.__class__.__name__,
                interceptor.name,
                self.name,
            )

    def register_error_handler(self, handler: ErrorHandler):
        self._handlers[handler.name] = handler
        if "error" not in self._route_map:
            self._route_map["error"] = {}
        for update_type in handler.update_types:
            if update_type not in self._route_map["error"]:
                self._route_map["error"][update_type] = {}
            for exception in handler.exceptions:
                self._route_map["error"][update_type][exception.__name__] = handler.name
                logger.info(
                    "bind a %s ErrorHandler on %s Update: '%s@%s'",
                    exception.__name__,
                    update_type,
                    handler.name,
                    self.name,
                )

    def __add_and_group(self, update_type: str, handler: _MessageHandler):
        route = self._route_map[update_type]
        if "and" not in route:
            route["and"] = []
        route["and"].append((handler.message_fields, handler.name))

    def __add_or_group(self, update_type: str, handler: _MessageHandler):
        route = self._route_map[update_type]
        if "or" not in route:
            route["or"] = defaultdict(set)
        for field in handler.message_fields:
            route["or"][field].add(handler.name)

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
                    handler.name,
                )
            route["any"] = handler.name
            return
        if isinstance(message_fields, set):
            if len(message_fields) == 1:
                self.__add_or_group(update_type, handler)
            else:
                self.__add_and_group(update_type, handler)
            return
        if isinstance(message_fields, (list, tuple)):
            self.__add_or_group(update_type, handler)

    def __add_edited_message_handler(self, handler: EditedMessageHandler):
        self.__add_message_handler(handler)

    def __add_channel_post_handler(self, handler: ChannelPostHandler):
        self.__add_message_handler(handler)

    def __add_edited_channel_post_handler(self, handler: EditedChannelPostHandler):
        self.__add_message_handler(handler)

    def __add_command_handler(self, handler: CommandHandler):
        if UpdateType.COMMAND.value not in self._route_map:
            self._route_map[UpdateType.COMMAND.value] = {}
        for cmd_word in handler.cmds:
            self._route_map[UpdateType.COMMAND.value][cmd_word] = handler.name

    def __add_force_reply_handler(self, handler: Dict):
        if UpdateType.FORCE_REPLY.value not in self._route_map:
            self._route_map[UpdateType.FORCE_REPLY.value] = set()
        self._route_map[UpdateType.FORCE_REPLY.value].add(handler.name)

    def __add_callback_query_handler(self, handler: CallbackQueryHandler):
        if UpdateType.CALLBACK_QUERY.value not in self._route_map:
            self._route_map[UpdateType.CALLBACK_QUERY.value] = {}
        route = self._route_map[UpdateType.CALLBACK_QUERY.value]
        has_static_match, has_regex_match, has_callable_match = handler.have_matches
        if has_static_match:
            if "static" not in route:
                route["static"] = {}
            route["static"][handler.static_match] = handler.name
        if has_regex_match:
            if "regex" not in route:
                route["regex"] = set()
            route["regex"].add(handler.name)
        if has_callable_match:
            if "callable" not in route:
                route["callable"] = set()
            route["callable"].add(handler.name)
        if not has_static_match and not has_regex_match and not has_callable_match:
            if "any" in route:
                logger.warning(
                    "You are overwritting a callback_query handler: %s on any updatetypes with %s",
                    route["any"],
                    handler.name,
                )
            route["any"] = handler.name

    def register_handler(self, handler: UpdateHandler):
        if not isinstance(handler, UpdateHandler):
            raise SimpleBotException("need a UpdateHandler")
        self._handlers[handler.name] = handler
        for update_type in handler.update_types:
            logger.info(
                "bind a %s Handler: '%s@%s'", update_type, handler.name, self.name
            )
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
            self._route_map[update_type] = handler.name

    def register_force_reply_handler(self, callback: Callable):
        self.register_handler(ForceReplyHandler(callback=callback))

    def register_command_handler(self, callback: Callable, cmds: Iterable[str]):
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
        self.register_handler(EditedMessageHandler(callback=callback, fields=fields))

    def register_channel_post_handler(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        self.register_handler(ChannelPostHandler(callback=callback, fields=fields))

    def register_edited_channel_post_handler(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        self.register_handler(
            EditedChannelPostHandler(callback=callback, fields=fields)
        )

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
        static_match: Optional[str] = None,
        regex_match: Optional[Iterable[str]] = None,
        callable_match: Optional[Callable] = None,
        **kwargs
    ):
        self.register_handler(
            CallbackQueryHandler(
                callback=callback,
                static_match=static_match,
                regex_match=regex_match,
                callable_match=callable_match,
                **kwargs
            )
        )

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
                Interceptor(
                    callback=callback, inter_type=inter_type, update_types=update_types
                )
            )
            return callback

        return decorator

    def error_handler(
        self,
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
        exceptions=(Exception,),
    ):
        def decorator(callback):
            self.register_error_handler(
                ErrorHandler(
                    callback=callback, update_types=update_types, exceptions=exceptions
                )
            )
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
        self, fields: Optional[Iterable[Union[str, MessageField]]] = None
    ):
        def decorator(callback):
            self.register_message_handler(callback, fields)
            return callback

        return decorator

    def edited_message_handler(
        self, fields: Optional[Iterable[Union[str, MessageField]]] = None
    ):
        def decorator(callback):
            self.register_edited_message_handler(callback, fields)
            return callback

        return decorator

    def channel_post_handler(
        self, fields: Optional[Iterable[Union[str, MessageField]]] = None
    ):
        def decorator(callback):
            self.register_channel_post_handler(callback, fields)
            return callback

        return decorator

    def edited_channel_post_handler(
        self, fields: Optional[Iterable[Union[str, MessageField]]] = None
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
        static_match: Optional[str] = None,
        regex_match: Optional[Iterable[str]] = None,
        callable_match: Optional[Callable] = None,
        **kwargs
    ):
        def decorator(callback):
            self.register_callback_query_handler(
                callback, static_match, regex_match, callable_match, **kwargs
            )
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
    # process incoming updates
    #
    ##################################################################################
    async def route(self, bot: SimpleBot, update: Update):
        if update.update_id > bot.last_update_id:
            bot.last_update_id = update.update_id
        update_type, data = self.parse_update_type_and_data(update)
        try:
            if update_type is None:
                raise SimpleBotException("unknown update type")
            await self.__call_before_interceptor(update_type, bot, data)
            await self._call_handler_switcher[update_type](update_type, bot, data)
        except Exception as error:
            await self.__call_error_handler(update_type, bot, data, error)
            raise error
        else:
            await self.__call_after_interceptor(update_type, bot, data)

    async def __call_handler(self, handler_name: str, *args, **kwargs) -> bool:
        return bool(await self._handlers[handler_name](*args, **kwargs))

    async def __call_before_interceptor(
        self, update_type: UpdateType, bot: SimpleBot, data: SimpleObject
    ):
        route = self._route_map.get(InterceptorType.BEFORE.value, None)
        if not route:
            return
        interceptor_name = route.get("any", None)
        if interceptor_name:
            await self.__call_handler(interceptor_name, bot, data)
        interceptor_name = route.get(update_type.value, None)
        if interceptor_name:
            await self.__call_handler(interceptor_name, bot, data)

    async def __call_after_interceptor(
        self, update_type: UpdateType, bot: SimpleBot, data: SimpleObject
    ):
        route = self._route_map.get(InterceptorType.AFTER.value, None)
        if not route:
            return
        interceptor_name = route.get(update_type.value, None)
        if interceptor_name:
            await self.__call_handler(interceptor_name, bot, data)
        interceptor_name = route.get("any", None)
        if interceptor_name:
            await self.__call_handler(interceptor_name, bot, data)

    async def __call_error_handler(
        self, update_type: UpdateType, bot: SimpleBot, data: SimpleObject, error
    ):
        route = self._route_map.get("error", None)
        if not route:
            return
        error_name = type(error).__name__
        _route = route.get("any", None)
        if _route and error_name in _route:
            await self.__call_handler(_route[error_name], bot, data, error)
        _route = route.get(update_type.value, None)
        if _route and error_name in _route:
            await self.__call_handler(_route[error_name], bot, data, error)

    async def __call_command_handler(self, bot: SimpleBot, message: Message) -> bool:
        if UpdateType.COMMAND.value not in self._route_map:
            return False
        if message.text and message.text[0] == "/":
            cmd_and_args = message.text.split()
            cmd_name = cmd_and_args[0].split("@")[0]
            handler_name = self._route_map[UpdateType.COMMAND.value].get(cmd_name, None)
            if handler_name:
                if len(cmd_and_args) == 1:
                    await self.__call_handler(handler_name, bot, message)
                else:
                    await self.__call_handler(
                        handler_name, bot, message, *cmd_and_args[1:]
                    )
                return True
        return False

    async def __call_force_reply_handler(
        self, bot: SimpleBot, message: Message
    ) -> bool:
        force_reply_handler_name, force_reply_args = bot.get_force_reply(
            message.from_user.id
        )
        if force_reply_handler_name:
            if (
                UpdateType.FORCE_REPLY.value not in self._route_map
                or force_reply_handler_name
                not in self._route_map[UpdateType.FORCE_REPLY.value]
            ):
                raise SimpleBotException(
                    "{0} is not a force reply callback".format(force_reply_handler_name)
                )
            if force_reply_args:
                await self.__call_handler(
                    force_reply_handler_name, bot, message, *force_reply_args
                )
            else:
                await self.__call_handler(force_reply_handler_name, bot, message)
            return True
        return False

    async def __call_message_handler(
        self, update_type: UpdateType, bot: SimpleBot, message: Message
    ):
        if await self.__call_command_handler(bot, message):
            return
        if await self.__call_force_reply_handler(bot, message):
            return
        await self.__call_message_like_handler(update_type, bot, message)
        return

    async def __call_edited_message_handler(
        self, update_type: UpdateType, bot: SimpleBot, edited_message: Message
    ):
        await self.__call_message_handler(update_type, bot, edited_message)
        return

    async def __call_message_like_handler(
        self, update_type: UpdateType, bot: SimpleBot, message: Message
    ):
        route = self._route_map.get(update_type.value, None)
        if not route:
            return
        # call the handler on any fields
        handler_name = route.get("any", None)
        if handler_name:
            if not await self.__call_handler(handler_name, bot, message):
                return
        # call 'and' handlers
        and_group = route.get("and", None)
        if and_group:
            message_fields_as_set = set(message.keys())
            for fields, handler_name in and_group:
                if fields <= message_fields_as_set and not await self.__call_handler(
                    handler_name, bot, message
                ):
                    return
        # call 'or' handlers
        or_group = route.get("or", None)
        if or_group:
            for message_field, handler_names in or_group.items():
                if message_field in message:
                    for handler_name in handler_names:
                        if not await self.__call_handler(handler_name, bot, message):
                            return

    async def __call_channel_post_handler(
        self, update_type: UpdateType, bot: SimpleBot, message: Message
    ):
        await self.__call_message_like_handler(update_type, bot, message)

    async def __call_edited_channel_post_handler(
        self, update_type: UpdateType, bot: SimpleBot, message: Message
    ):
        await self.__call_message_like_handler(update_type, bot, message)

    async def __call_callback_query_handler(
        self, update_type: UpdateType, bot: SimpleBot, callback_query: CallbackQuery
    ):
        route = self._route_map.get(update_type.value, None)
        if not route:
            return
        if "any" in route:
            await self.__call_handler(route["all"], bot, callback_query)
            return
        if "static" in route:
            handler_name = route["static"].get(callback_query.data, None)
            if handler_name:
                await self.__call_handler(handler_name, bot, callback_query)
                return
        for handler_name in route.get("regex", ()):
            handler = self._handlers[handler_name]
            result = handler.regex_match(callback_query)
            if result:
                await handler(bot, callback_query, result)
                return
        for handler_name in route.get("callable", ()):
            handler = self._handlers[handler_name]
            result = handler.callable_match(callback_query)
            if result:
                if isinstance(result, bool):
                    await handler(bot, callback_query)
                    return
                if isinstance(result, (list, tuple)):
                    await handler(bot, callback_query, *result)
                    return
                await handler(bot, callback_query, result)

    async def __call_inline_query_handler(
        self, update_type: UpdateType, bot: SimpleBot, inline_query: InlineQuery
    ):
        handler_name = self._route_map.get(update_type.value, None)
        if handler_name:
            await self.__call_handler(handler_name, bot, inline_query)

    async def __call_chosen_inline_result_handler(
        self,
        update_type: UpdateType,
        bot: SimpleBot,
        chosen_inline_result: ChosenInlineResult,
    ):
        await self.__call_inline_query_handler(update_type, bot, chosen_inline_result)

    async def __call_shipping_query_handler(
        self, update_type: UpdateType, bot: SimpleBot, shipping_query: ShippingQuery
    ):
        await self.__call_inline_query_handler(update_type, bot, shipping_query)

    async def __call_pre_checkout_query_handler(
        self,
        update_type: UpdateType,
        bot: SimpleBot,
        pre_checkout_query: PreCheckoutQuery,
    ):
        await self.__call_inline_query_handler(update_type, bot, pre_checkout_query)

    async def __call_poll_handler(
        self, update_type: UpdateType, bot: SimpleBot, poll: Poll
    ):
        await self.__call_inline_query_handler(update_type, bot, poll)

    async def __call_poll_answer_handler(
        self, update_type: UpdateType, bot: SimpleBot, poll_answer: PollAnswer
    ):
        await self.__call_inline_query_handler(update_type, bot, poll_answer)

    def has_force_reply_handler(self, handler_name: str) -> bool:
        return UpdateType.FORCE_REPLY.value in self._route_map and (
            handler_name in self._route_map[UpdateType.FORCE_REPLY.value]
        )

    @property
    def route_map(self):
        return pretty_json(self._route_map)

    @staticmethod
    def parse_update_type_and_data(
        update: Update,
    ) -> Tuple[Optional[UpdateType], Optional[SimpleObject]]:
        for name, value in update.items():
            if name == "update_id":
                continue
            return UpdateType(name), value

        return None, None
