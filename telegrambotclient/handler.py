import asyncio
import re
from enum import Enum
from typing import Callable, Iterable, Optional, Tuple, Union

from telegrambotclient.base import CallbackQuery, MessageField, UpdateType


class UpdateHandler:
    __slots__ = ("_update_types", "_callback")

    def __init__(
        self,
        callback: Callable,
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
    ):
        self._callback = callback
        if update_types is None:
            update_types = ("any", )
        self._update_types = tuple(
            map(
                lambda update_type: update_type.value
                if isinstance(update_type, UpdateType) else update_type,
                update_types,
            ))

    @property
    def update_types(self):
        return self._update_types

    def __repr__(self) -> str:
        return "{0}.{1}".format(self._callback.__module__,
                                self._callback.__name__)

    async def __call__(self, *args, **kwargs):
        if asyncio.iscoroutinefunction(self._callback):
            return await self._callback(*args, **kwargs)
        return self._callback(*args, **kwargs)


class ErrorHandler(UpdateHandler):
    __slots__ = ("_errors", )

    def __init__(
        self,
        callback: Callable,
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
        errors: Optional[Iterable[Exception]] = None,
    ):
        super().__init__(callback, update_types)
        self._errors = errors if errors else (Exception, )

    @property
    def error(self):
        return self._errors


class InterceptorType(Enum):
    BEFORE = "before"
    AFTER = "after"


class Interceptor(UpdateHandler):
    __slots__ = ("_inter_type", )

    def __init__(
        self,
        callback: Callable,
        inter_type: Union[str, InterceptorType],
        update_types: Optional[Iterable[Union[str, UpdateType]]] = None,
    ):
        super().__init__(callback, update_types=update_types)
        self._inter_type = (inter_type.value if isinstance(
            inter_type, InterceptorType) else inter_type)

    @property
    def type(self) -> str:
        return self._inter_type


class CommandHandler(UpdateHandler):
    __slots__ = ("_cmds", )

    def __init__(self, callback: Callable, cmds: Iterable):
        super().__init__(callback=callback,
                         update_types=(UpdateType.COMMAND, ))
        self._cmds = cmds

    @property
    def cmds(self) -> Iterable:
        return self._cmds


class ForceReplyHandler(UpdateHandler):
    def __init__(
        self,
        callback: Callable,
    ):
        super().__init__(callback=callback,
                         update_types=(UpdateType.FORCE_REPLY, ))


class _MessageHandler(UpdateHandler):
    __slots__ = ("_message_fields", )

    def __init__(
        self,
        callback: Callable,
        update_type: Union[str, UpdateType],
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        super().__init__(callback=callback, update_types=(update_type, ))
        if isinstance(fields, MessageField):
            self._message_fields = fields.fields
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
            callback=callback,
            update_type=UpdateType.MESSAGE,
            fields=fields,
        )


class EditedMessageHandler(_MessageHandler):
    def __init__(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        super().__init__(
            callback=callback,
            update_type=UpdateType.EDITED_MESSAGE,
            fields=fields,
        )


class ChannelPostHandler(_MessageHandler):
    def __init__(
        self,
        callback: Callable,
        fields: Optional[Iterable[Union[str, MessageField]]] = None,
    ):
        super().__init__(
            callback=callback,
            update_type=UpdateType.CHANNEL_POST,
            fields=fields,
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
    __slots__ = (
        "_callback_data",
        "_callback_data_name",
        "_callback_data_patterns",
        "_callback_data_parse",
        "_kwargs",
    )

    def __init__(self,
                 callback: Callable,
                 callback_data: Optional[str] = None,
                 callback_data_name: Optional[str] = None,
                 callback_data_regex: Optional[Iterable[str]] = None,
                 callback_data_parse: Optional[Callable] = None,
                 **kwargs):
        super().__init__(callback=callback,
                         update_types=(UpdateType.CALLBACK_QUERY, ))
        self._callback_data = callback_data
        self._callback_data_name = callback_data_name
        self._callback_data_patterns = tuple(
            re.compile(regex)
            for regex in callback_data_regex) if callback_data_regex else ()
        self._callback_data_parse = callback_data_parse
        self._kwargs = kwargs

    @property
    def have_matchers(self) -> Tuple[bool, bool, bool, bool]:
        return (
            bool(self._callback_data),
            bool(self._callback_data_name),
            bool(self._callback_data_patterns),
            bool(self._callback_data_parse),
        )

    @property
    def any_callback_data(self):
        one, two, three, four = self.have_matchers
        return not one and not two and not three and not four

    @property
    def callback_data(self):
        return self._callback_data

    @property
    def callback_data_name(self):
        return self._callback_data_name

    def callback_data_match(self, callback_query: CallbackQuery):
        for pattern in self._callback_data_patterns:
            result = pattern.match(callback_query.data)
            if result:
                return result
        return None

    def callback_data_parse(self, callback_query: CallbackQuery):
        if self._callback_data_parse:
            return self._callback_data_parse(callback_query.data,
                                             **self._kwargs)
        return False


class InlineQueryHandler(UpdateHandler):
    def __init__(
        self,
        callback: Callable,
    ):
        super().__init__(callback=callback,
                         update_types=(UpdateType.INLINE_QUERY, ))


class ChosenInlineResultHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback,
                         update_types=(UpdateType.CHOSEN_INLINE_RESULT, ))


class ShippingQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_types=(UpdateType.SHIPPING_QUERY, ))


class PreCheckoutQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback,
                         update_types=(UpdateType.PRE_CHECKOUT_QUERY, ))


class PollHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_types=(UpdateType.POLL, ))


class PollAnswerHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_types=(UpdateType.POLL_ANSWER, ))
