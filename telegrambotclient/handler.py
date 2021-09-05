import asyncio
import re
from typing import Callable, Set, Tuple, Union

from telegrambotclient.base import CallbackQuery, MessageField, UpdateType


class UpdateHandler:
    __slots__ = ("_update_type", "_callback")

    def __init__(
        self,
        callback: Callable,
        update_type: Union[UpdateType, str],
    ):
        self._callback = callback
        self._update_type = update_type.value if isinstance(
            update_type, UpdateType) else update_type

    @property
    def update_type(self) -> str:
        return self._update_type

    def __repr__(self) -> str:
        return "{0}.{1}".format(self._callback.__module__,
                                self._callback.__name__)

    async def __call__(self, *args, **kwargs):
        if asyncio.iscoroutinefunction(self._callback):
            return await self._callback(*args, **kwargs)
        return self._callback(*args, **kwargs)


class ErrorHandler:
    __slots__ = (
        "_callback",
        "_errors",
    )

    def __init__(
        self,
        callback: Callable,
        errors: Tuple = None,
    ):
        self._callback = callback
        self._errors = errors or (Exception, )

    def __repr__(self) -> str:
        return "{0}.{1}".format(self._callback.__module__,
                                self._callback.__name__)

    async def __call__(self, *args, **kwargs):
        if asyncio.iscoroutinefunction(self._callback):
            return await self._callback(*args, **kwargs)
        return self._callback(*args, **kwargs)

    @property
    def errors(self) -> Tuple:
        return self._errors


class CommandHandler(UpdateHandler):
    __slots__ = ("_cmds", )

    def __init__(self, callback: Callable, cmds: Tuple[str]):
        super().__init__(callback=callback, update_type=UpdateType.COMMAND)
        self._cmds = cmds

    @property
    def cmds(self) -> Tuple:
        return self._cmds


class ForceReplyHandler(UpdateHandler):
    def __init__(
        self,
        callback: Callable,
    ):
        super().__init__(callback=callback, update_type=UpdateType.FORCE_REPLY)


class _MessageHandler(UpdateHandler):
    __slots__ = ("_message_fields", )

    def __init__(
        self,
        callback: Callable,
        update_type: Union[UpdateType, str] = UpdateType.MESSAGE,
        fields: Union[MessageField, str] = MessageField.TEXT,
    ):
        super().__init__(callback=callback, update_type=update_type)
        if isinstance(fields, MessageField):
            self._message_fields = fields.fields
        else:
            self._message_fields = fields

    @property
    def message_fields(self) -> Union[str, Set, Tuple]:
        return self._message_fields


class MessageHandler(_MessageHandler):
    def __init__(
        self,
        callback: Callable,
        fields: Union[MessageField, str] = MessageField.TEXT,
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
        fields: Union[MessageField, str] = MessageField.TEXT,
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
        fields: Union[MessageField, str] = MessageField.TEXT,
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
        fields: Union[MessageField, str] = MessageField.TEXT,
    ):
        super().__init__(
            callback=callback,
            update_type=UpdateType.EDITED_CHANNEL_POST,
            fields=fields,
        )


class CallbackQueryHandler(UpdateHandler):
    __slots__ = ("_callback_data", "_callback_data_name",
                 "_callback_data_patterns", "_callback_data_parse", "_kwargs")

    def __init__(self,
                 callback: Callable,
                 callback_data: str = None,
                 callback_data_name: str = None,
                 callback_data_regex: Tuple[str] = None,
                 callback_data_parse: Callable = None,
                 **kwargs):
        super().__init__(callback=callback,
                         update_type=UpdateType.CALLBACK_QUERY)
        self._callback_data = callback_data
        self._callback_data_name = callback_data_name
        self._callback_data_patterns = tuple(
            re.compile(regex) for regex in callback_data_regex) if isinstance(
                callback_data_regex, tuple) else ()
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
    def callback_data(self):
        return self._callback_data

    @property
    def callback_data_name(self):
        return self._callback_data_name

    def callback_data_match(self, callback_query: CallbackQuery):
        for pattern in self._callback_data_patterns:
            if callback_query.data:
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
                         update_type=UpdateType.INLINE_QUERY)


class ChosenInlineResultHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_type=UpdateType.CHOSEN_INLINE_RESULT)


class ShippingQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_type=UpdateType.SHIPPING_QUERY)


class PreCheckoutQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_type=UpdateType.PRE_CHECKOUT_QUERY)


class PollHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_type=UpdateType.POLL)


class PollAnswerHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_type=UpdateType.POLL_ANSWER)
