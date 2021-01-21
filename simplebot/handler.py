import re
import asyncio
from typing import Iterable, Optional, Callable, Tuple, Union
from enum import Enum
from simplebot.base import CallbackQuery, InlineQuery, UpdateType, MessageType


class UpdateHandler:
    __slots__ = ("_update_type", "_callback")

    def __init__(self, callback: Callable, update_type: Union[str, UpdateType] = UpdateType.ALL):
        self._update_type = update_type.value if isinstance(update_type, Enum) else update_type
        self._callback = callback

    @property
    def update_type(self):
        return self._update_type

    @property
    def name(self):
        return "{0}.{1}".format(self._callback.__module__, self._callback.__name__)

    def __str__(self) -> str:
        return "{0}@{1}".format(self.update_type, self.name)

    async def __call__(self, *args, **kwargs):
        if asyncio.iscoroutinefunction(self._callback):
            return await self._callback(*args, **kwargs)
        return self._callback(*args, **kwargs)


class ErrorHandler(UpdateHandler):
    __slots__ = ("_error_type",)

    def __init__(
        self,
        callback: Callable,
        update_type: Union[str, UpdateType] = UpdateType.ALL,
        error_type=Exception,
    ):
        super(ErrorHandler, self).__init__(callback, update_type)
        self._error_type = error_type

    async def __call__(self, bot, data, error, *args, **kwargs):
        if isinstance(error, self._error_type):
            return await super().__call__(bot, data, error, *args, **kwargs)
        return None


class InterceptorType(Enum):
    BEFORE = "before"
    AFTER = "after"


class Interceptor(UpdateHandler):
    __slots__ = ("_inter_type",)

    def __init__(
        self,
        callback: Callable,
        inter_type: Union[str, InterceptorType],
        update_type: Union[str, UpdateType] = UpdateType.ALL,
    ):
        super(Interceptor, self).__init__(callback, update_type=update_type)
        self._inter_type = inter_type.value if isinstance(inter_type, Enum) else inter_type

    @property
    def type(self) -> str:
        return self._inter_type


class CommandHandler(UpdateHandler):
    __slots__ = ("_cmds",)

    def __init__(self, callback: Callable, cmds: Iterable):
        super(CommandHandler, self).__init__(callback=callback, update_type=UpdateType.COMMAND)
        self._cmds = cmds

    @property
    def cmds(self) -> Iterable:
        return self._cmds


class ForceReplyHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super(ForceReplyHandler, self).__init__(
            callback=callback, update_type=UpdateType.FORCE_REPLY
        )


class _MessageHandler(UpdateHandler):
    __slots__ = ("_message_type",)

    def __init__(
        self,
        callback: Callable,
        update_type: Union[str, UpdateType],
        message_type: Union[str, MessageType],
    ):
        super(_MessageHandler, self).__init__(callback=callback, update_type=update_type)
        self._message_type = message_type.value if isinstance(message_type, Enum) else message_type

    @property
    def message_type(self) -> MessageType:
        return self._message_type


class MessageHandler(_MessageHandler):
    def __init__(self, callback: Callable, message_type: MessageType = MessageType.ALL):
        super(MessageHandler, self).__init__(
            callback=callback, update_type=UpdateType.MESSAGE, message_type=message_type
        )


class EditedMessageHandler(_MessageHandler):
    def __init__(self, callback: Callable, message_type: MessageType = MessageType.ALL):
        super(EditedMessageHandler, self).__init__(
            callback=callback, update_type=UpdateType.EDITED_MESSAGE, message_type=message_type
        )


class ChannelPostHandler(_MessageHandler):
    def __init__(self, callback: Callable, message_type: MessageType = MessageType.ALL):
        super(ChannelPostHandler, self).__init__(
            callback=callback, update_type=UpdateType.CHANNEL_POST, message_type=message_type
        )


class EditedChannelPostHandler(_MessageHandler):
    def __init__(self, callback: Callable, message_type: MessageType = MessageType.ALL):
        super(EditedChannelPostHandler, self).__init__(
            callback=callback, update_type=UpdateType.EDITED_CHANNEL_POST, message_type=message_type
        )


class InlineQueryHandler(UpdateHandler):
    __slots__ = ("_regex_patterns", "_callable_match", "_kwargs")

    def __init__(
        self,
        callback: Callable,
        regex_match: Optional[Iterable[str]] = None,
        callable_match: Optional[Callable] = None,
        **kwargs
    ):
        super(InlineQueryHandler, self).__init__(
            callback=callback, update_type=UpdateType.INLINE_QUERY
        )
        self._regex_patterns = None
        if regex_match:
            self._regex_patterns = tuple([re.compile(regex_str) for regex_str in regex_match])
        self._callable_match = callable_match
        self._kwargs = kwargs

    @property
    def have_matches(self) -> Tuple[bool, bool]:
        return bool(self._regex_patterns), bool(self._callable_match)

    def regex_match(self, inline_query: InlineQuery):
        if not self._regex_patterns:
            return None
        for pattern in self._regex_patterns:
            result = pattern.match(inline_query.query)
            if result:
                return result
        return None

    def callable_match(self, inline_query: InlineQuery):
        if self._callable_match:
            return self._callable_match(inline_query, **self._kwargs)
        return False


ChosenInlineResultHandler = InlineQueryHandler


class CallbackQueryHandler(UpdateHandler):
    __slots__ = ("_static_match", "_regex_patterns", "_callable_match", "_kwargs")

    def __init__(
        self,
        callback: Callable,
        static_match: Optional[str] = None,
        regex_match: Optional[Iterable[str]] = None,
        callable_match: Optional[Callable] = None,
        **kwargs
    ):
        super(CallbackQueryHandler, self).__init__(
            callback=callback, update_type=UpdateType.CALLBACK_QUERY
        )
        self._static_match = static_match
        self._regex_patterns = None
        if regex_match:
            self._regex_patterns = tuple([re.compile(regex_str) for regex_str in regex_match])
        self._callable_match = callable_match
        self._kwargs = kwargs

    @property
    def static_match(self):
        return self._static_match

    @property
    def have_matches(self) -> Tuple[bool, bool, bool]:
        return bool(self._static_match), bool(self._regex_patterns), bool(self._callable_match)

    def regex_match(self, callback_query: CallbackQuery):
        if not self._regex_patterns:
            return None
        for pattern in self._regex_patterns:
            result = pattern.match(callback_query.data)
            if result:
                return result
        return None

    def callable_match(self, callback_query: CallbackQuery):
        if self._callable_match:
            return self._callable_match(callback_query.data, **self._kwargs)
        return False


class ShippingQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super(ShippingQueryHandler, self).__init__(callback, update_type=UpdateType.SHIPPING_QUERY)


class PreCheckoutQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super(PreCheckoutQueryHandler, self).__init__(
            callback, update_type=UpdateType.PRE_CHECKOUT_QUERY
        )


class PollHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super(PollHandler, self).__init__(callback, update_type=UpdateType.POLL)


class PollAnswerHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super(PollAnswerHandler, self).__init__(callback, update_type=UpdateType.POLL_ANSWER)
