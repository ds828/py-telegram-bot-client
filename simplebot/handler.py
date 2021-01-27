import re
import asyncio
from typing import Iterable, Optional, Callable, Tuple, Union
from enum import Enum
from simplebot.base import CallbackQuery, MessageField, UpdateType


class UpdateHandler:
    __slots__ = ("_update_types", "_callback")

    def __init__(
        self,
        callback: Callable,
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
    ):
        if update_types is None:
            update_types = ("any",)
        self._update_types = tuple(
            map(
                lambda update_type: update_type.value
                if isinstance(update_type, UpdateType)
                else update_type,
                update_types,
            )
        )
        self._callback = callback

    @property
    def update_types(self):
        return self._update_types

    @property
    def name(self):
        return "{0}.{1}".format(self._callback.__module__, self._callback.__name__)

    def __str__(self) -> str:
        return "{0}@{1}".format(self.update_types, self.name)

    async def __call__(self, *args, **kwargs):
        if asyncio.iscoroutinefunction(self._callback):
            return await self._callback(*args, **kwargs)
        return self._callback(*args, **kwargs)


class ErrorHandler(UpdateHandler):
    __slots__ = ("_exceptions",)

    def __init__(
        self,
        callback: Callable,
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
        exceptions: Optional[Iterable[Exception]] = None,
    ):
        super().__init__(callback, update_types)
        self._exceptions = exceptions if exceptions else (Exception,)

    @property
    def exceptions(self):
        return self._exceptions

    async def __call__(self, bot, data, exception, *args, **kwargs):
        if isinstance(exception, self._exceptions):
            return await super().__call__(bot, data, exception, *args, **kwargs)
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
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
    ):
        super().__init__(callback, update_types=update_types)
        self._inter_type = (
            inter_type.value if isinstance(inter_type, InterceptorType) else inter_type
        )

    @property
    def type(self) -> str:
        return self._inter_type


class CommandHandler(UpdateHandler):
    __slots__ = ("_cmds",)

    def __init__(self, callback: Callable, cmds: Iterable):
        super().__init__(callback=callback, update_types=(UpdateType.COMMAND,))
        self._cmds = cmds

    @property
    def cmds(self) -> Iterable:
        return self._cmds


class ForceReplyHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback=callback, update_types=(UpdateType.FORCE_REPLY,))


class _MessageHandler(UpdateHandler):
    __slots__ = ("_message_fields",)

    def __init__(
        self,
        callback: Callable,
        update_type: Union[str, UpdateType],
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        super().__init__(callback=callback, update_types=(update_type,))
        if fields:
            self._message_fields = type(fields)(
                map(
                    lambda field: field.value
                    if isinstance(field, MessageField)
                    else field,
                    fields,
                )
            )
        else:
            self._message_fields = fields

    @property
    def message_fields(self) -> Iterable:
        return self._message_fields


class MessageHandler(_MessageHandler):
    def __init__(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        super().__init__(
            callback=callback, update_type=UpdateType.MESSAGE, fields=fields
        )


class EditedMessageHandler(_MessageHandler):
    def __init__(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        super().__init__(
            callback=callback, update_type=UpdateType.EDITED_MESSAGE, fields=fields
        )


class ChannelPostHandler(_MessageHandler):
    def __init__(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        super().__init__(
            callback=callback, update_type=UpdateType.CHANNEL_POST, fields=fields
        )


class EditedChannelPostHandler(_MessageHandler):
    def __init__(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        super().__init__(
            callback=callback,
            update_type=UpdateType.EDITED_CHANNEL_POST,
            fields=fields,
        )


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
        super().__init__(callback=callback, update_types=(UpdateType.CALLBACK_QUERY,))
        self._static_match = static_match
        self._regex_patterns = None
        if regex_match:
            self._regex_patterns = tuple(
                [re.compile(regex_str) for regex_str in regex_match]
            )
        self._callable_match = callable_match
        self._kwargs = kwargs

    @property
    def static_match(self):
        return self._static_match

    @property
    def have_matches(self) -> Tuple[bool, bool, bool]:
        return (
            bool(self._static_match),
            bool(self._regex_patterns),
            bool(self._callable_match),
        )

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


class InlineQueryHandler(UpdateHandler):
    def __init__(
        self,
        callback: Callable,
    ):
        super().__init__(callback=callback, update_types=(UpdateType.INLINE_QUERY,))


class ChosenInlineResultHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_types=(UpdateType.CHOSEN_INLINE_RESULT,))


class ShippingQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_types=(UpdateType.SHIPPING_QUERY,))


class PreCheckoutQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_types=(UpdateType.PRE_CHECKOUT_QUERY,))


class PollHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_types=(UpdateType.POLL,))


class PollAnswerHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_types=(UpdateType.POLL_ANSWER,))
