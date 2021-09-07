import asyncio
import re
from typing import Callable, Set, Tuple, Union

from telegrambotclient.base import CallbackQuery, MessageField, UpdateField


class UpdateHandler:
    __slots__ = ("_callback", "_update_field")

    def __init__(self, callback: Callable, update_field: Union[UpdateField,
                                                               str]):
        self._callback = callback
        self._update_field = update_field.value if isinstance(
            update_field, UpdateField) else update_field

    @property
    def name(self):
        return "{0}.{1}".format(self._callback.__module__,
                                self._callback.__name__)

    @property
    def update_field(self) -> str:
        return self._update_field

    def __repr__(self) -> str:
        return self.name

    async def __call__(self, *args, **kwargs):
        return await self._callback(
            *args, **kwargs) if asyncio.iscoroutinefunction(
                self._callback) else self._callback(*args, **kwargs)


class ErrorHandler(UpdateHandler):
    __slots__ = ("_errors", )

    def __init__(self, callback: Callable, errors: Tuple = None):
        super().__init__(callback=callback, update_field="error")
        self._errors = errors or (Exception, )

    @property
    def errors(self) -> Tuple:
        return self._errors


class CommandHandler(UpdateHandler):
    __slots__ = ("_cmds", )

    def __init__(self, callback: Callable, cmds: Tuple[str]):
        super().__init__(callback=callback, update_field="command")
        self._cmds = cmds

    @property
    def cmds(self) -> Tuple:
        return self._cmds


class ForceReplyHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback=callback, update_field="force_reply")


class _MessageHandler(UpdateHandler):
    __slots__ = ("_message_fields", )

    def __init__(self,
                 callback: Callable,
                 update_field: Union[UpdateField, str] = UpdateField.MESSAGE,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback, update_field=update_field)
        if isinstance(fields, MessageField):
            self._message_fields = fields.fields
        else:
            self._message_fields = fields

    @property
    def message_fields(self) -> Union[str, Set, Tuple, None]:
        return self._message_fields


class MessageHandler(_MessageHandler):
    def __init__(self,
                 callback: Callable,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.MESSAGE,
                         fields=fields)


class EditedMessageHandler(_MessageHandler):
    def __init__(self,
                 callback: Callable,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.EDITED_MESSAGE,
                         fields=fields)


class ChannelPostHandler(_MessageHandler):
    def __init__(self,
                 callback: Callable,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.CHANNEL_POST,
                         fields=fields)


class EditedChannelPostHandler(_MessageHandler):
    def __init__(self,
                 callback: Callable,
                 fields: Union[MessageField, str] = None):
        super().__init__(callback=callback,
                         update_field=UpdateField.EDITED_CHANNEL_POST,
                         fields=fields)


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
                         update_field=UpdateField.CALLBACK_QUERY)
        self._callback_data = callback_data
        self._callback_data_name = callback_data_name
        self._callback_data_patterns = tuple(
            re.compile(regex) for regex in callback_data_regex) if isinstance(
                callback_data_regex, tuple) else ()
        self._callback_data_parse = callback_data_parse
        self._kwargs = kwargs

    @property
    def have_matchers(self) -> Tuple[bool, bool, bool, bool]:
        return (bool(self._callback_data), bool(self._callback_data_name),
                bool(self._callback_data_patterns),
                bool(self._callback_data_parse))

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
    def __init__(self, callback: Callable):
        super().__init__(callback=callback,
                         update_field=UpdateField.INLINE_QUERY)


class ChosenInlineResultHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback,
                         update_field=UpdateField.CHOSEN_INLINE_RESULT)


class ShippingQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.SHIPPING_QUERY)


class PreCheckoutQueryHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.PRE_CHECKOUT_QUERY)


class PollHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.POLL)


class PollAnswerHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.POLL_ANSWER)


class MyChatMemberHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.MY_CHAT_MEMBER)


class ChatMemberHandler(UpdateHandler):
    def __init__(self, callback: Callable):
        super().__init__(callback, update_field=UpdateField.CHAT_MEMBER)


HandlerMapping = {
    UpdateField.MESSAGE: MessageHandler,
    UpdateField.EDITED_MESSAGE: EditedMessageHandler,
    UpdateField.CHANNEL_POST: ChannelPostHandler,
    UpdateField.EDITED_CHANNEL_POST: EditedChannelPostHandler,
    UpdateField.INLINE_QUERY: InlineQueryHandler,
    UpdateField.CHOSEN_INLINE_RESULT: ChosenInlineResultHandler,
    UpdateField.CALLBACK_QUERY: CallbackQueryHandler,
    UpdateField.SHIPPING_QUERY: ShippingQueryHandler,
    UpdateField.PRE_CHECKOUT_QUERY: PreCheckoutQueryHandler,
    UpdateField.POLL: PollHandler,
    UpdateField.POLL_ANSWER: PollAnswerHandler,
    UpdateField.MY_CHAT_MEMBER: MyChatMemberHandler,
    UpdateField.CHAT_MEMBER: ChatMemberHandler
}
