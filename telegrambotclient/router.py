from collections import UserDict, UserList
from typing import Callable, Union

from telegrambotclient.base import (CallbackQuery, ChatJoinRequst,
                                    ChatMemberUpdated, ChosenInlineResult,
                                    InlineQuery, Message, MessageField, Poll,
                                    PollAnswer, PreCheckoutQuery,
                                    ShippingQuery, TelegramBotException,
                                    TelegramObject, UpdateField)
from telegrambotclient.bot import TelegramBot, logger
from telegrambotclient.handler import (
    CallbackQueryHandler, ChannelPostHandler, ChatJoinRequestHandler,
    ChatMemberHandler, ChosenInlineResultHandler, CommandHandler,
    EditedChannelPostHandler, EditedMessageHandler, ErrorHandler,
    ForceReplyHandler, InlineQueryHandler, MessageHandler, MyChatMemberHandler,
    PollAnswerHandler, PollHandler, PreCheckoutQueryHandler,
    ShippingQueryHandler, UpdateHandler, _MessageHandler)
from telegrambotclient.utils import parse_callback_data, pretty_format


async def call_handler(handler: UpdateHandler, *args, **kwargs):
    return bool(await handler(*args, **kwargs))


class ListRoute(UserList):
    def add_handler(self, handler: UpdateHandler):
        for idx, _handler in enumerate(self):
            if _handler.callback_name == handler.callback_name:
                self[idx] = handler
                return
        self.data.append(handler)
        return self

    async def call_handlers(self, bot: TelegramBot, data: TelegramObject):
        for handler in self:
            if await call_handler(handler, bot, data) is bot.stop_call:
                return bot.stop_call
        return bot.next_call


class ErrorRoute(ListRoute):
    async def call_handlers(self, bot: TelegramBot, data: TelegramObject,
                            error: Exception) -> bool:
        for handler in self:
            if isinstance(error, handler.errors) and await call_handler(
                    handler, bot, data, error) is bot.stop_call:
                return bot.stop_call
        return bot.next_call


class CommandRoute(UserDict):
    def add_handler(self, handler: CommandHandler):
        for cmd_text in handler.cmds:
            self[cmd_text] = handler
        return self

    async def call_handlers(self, bot: TelegramBot, message: Message):
        entity = message.entities[0]
        bot_command = message.text[entity.offset:entity.length]
        cmd_text, *bot_username = tuple(bot_command.split("@"))
        #for /start@one_bot arg1 arg2 ...
        if bot_username and bot_username != bot.user.username:
            return bot.stop_call
        handler = self.get(cmd_text, None)
        if handler is None:
            return bot.stop_call
        bot_command, *args = tuple(message.text.split())
        return await call_handler(handler, bot, message, *args)


class ForceReplyRoute(UserDict):
    def add_handler(self, handler: ForceReplyHandler):
        self[handler.callback_name] = handler
        return self

    async def call_handlers(self, bot: TelegramBot, message: Message):
        reply_to_message = bot.get_force_reply(
            message.chat.id if message.chat else message.from_user.
            id if message.from_user else 0)
        if not reply_to_message or message.reply_to_message.message_id != reply_to_message[
                "message_id"]:
            return bot.next_call
        handler = self.get(reply_to_message["callback"], None)
        if handler is None:
            raise TelegramBotException(
                "{0} is not found as a force reply callback".format(
                    reply_to_message["callback"]))

        return await call_handler(
            handler, bot, message, *reply_to_message["args"]
        ) if "args" in reply_to_message else await call_handler(
            handler, bot, message)


class MessageRoute(UserList):
    def add_handler(self, handler: _MessageHandler):
        if handler.fields:
            self[0:0] = [(set(handler.fields), handler)]
        else:
            self.append((set(), handler))
        return self

    async def call_handlers(self, bot: TelegramBot, message: Message):
        message_fields_set = set(message.keys())
        for fields_set, handler in self:
            if message_fields_set & fields_set == fields_set and await call_handler(
                    handler, bot, message) is bot.stop_call:
                return bot.stop_call

        return bot.next_call


class CallbackQueryRoute(UserDict):
    def add_handler(self, handler: CallbackQueryHandler):
        self[handler.data] = handler
        return self

    async def call_handlers(self, bot: TelegramBot,
                            callback_query: CallbackQuery):
        handler = self.get(callback_query.data, None)
        if handler and await call_handler(handler, bot,
                                          callback_query) is bot.stop_call:
            return bot.stop_call
        if "|" in callback_query.data:
            button_name, args = parse_callback_data(callback_query.data)
            handler = self.get(button_name, None)
            if handler and await call_handler(handler, bot, callback_query, *
                                              args) is bot.stop_call:
                return bot.stop_call

        return bot.next_call


class TelegramRouter:
    __slots__ = ("name", "route_map", "_handler_callers")
    NEXT_CALL = True
    STOP_CALL = False
    UPDATE_FIELD_VALUES = UpdateField.__members__.values()

    def __init__(self, name):
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
        logger.info("bind a %s handler: '%s@%s'", update_field,
                    handler.callback_name, self.name)
        route_data = self.route_map.get(update_field, {})
        if isinstance(handler, CallbackQueryHandler):
            self.route_map[update_field] = CallbackQueryRoute(
                route_data).add_handler(handler)
            return self

        if isinstance(handler, (MessageHandler, EditedMessageHandler,
                                ChannelPostHandler, EditedChannelPostHandler)):
            self.route_map[update_field] = MessageRoute(
                route_data).add_handler(handler)
            return self

        if isinstance(handler, CommandHandler):
            self.route_map[update_field] = CommandRoute(
                route_data).add_handler(handler)
            return self

        if isinstance(handler, ForceReplyHandler):
            self.route_map[update_field] = ForceReplyRoute(
                route_data).add_handler(handler)
            return self

        route_data = self.route_map[update_field] = self.route_map.get(
            handler.update_field, [])

        if isinstance(handler, ErrorHandler):
            self.route_map[update_field] = ErrorRoute(route_data).add_handler(
                handler)
            return self

        # for others update handlers, using listroute
        self.route_map[update_field] = ListRoute(route_data).add_handler(
            handler)
        return self

    def register_error_handler(self, callback: Callable, *errors):
        return self.register_handler(ErrorHandler(callback, *errors))

    def register_command_handler(self, callback: Callable, *cmds):
        return self.register_handler(CommandHandler(callback, *cmds))

    def register_force_reply_handler(self, callback: Callable):
        return self.register_handler(ForceReplyHandler(callback=callback))

    def register_message_handler(self,
                                 callback: Callable,
                                 fields: Union[str, MessageField] = None):
        return self.register_handler(
            MessageHandler(callback=callback, fields=fields))

    def register_edited_message_handler(self,
                                        callback: Callable,
                                        fields: Union[str,
                                                      MessageField] = None):
        return self.register_handler(
            EditedMessageHandler(callback=callback, fields=fields))

    def register_channel_post_handler(self,
                                      callback: Callable,
                                      fields: Union[str, MessageField] = None):
        return self.register_handler(
            ChannelPostHandler(callback=callback, fields=fields))

    def register_edited_channel_post_handler(self,
                                             callback: Callable,
                                             fields: Union[
                                                 str, MessageField] = None):
        return self.register_handler(
            EditedChannelPostHandler(callback=callback, fields=fields))

    def register_inline_query_handler(self, callback: Callable):
        return self.register_handler(InlineQueryHandler(callback=callback))

    def register_chosen_inline_result_handler(self, callback: Callable):
        return self.register_handler(
            ChosenInlineResultHandler(callback=callback))

    def register_callback_query_handler(self,
                                        callback: Callable,
                                        callback_data: str = None,
                                        game_short_name: str = None):
        return self.register_handler(
            CallbackQueryHandler(callback=callback,
                                 callback_data=callback_data,
                                 game_short_name=game_short_name))

    def register_shipping_query_handler(self, callback: Callable):
        return self.register_handler(ShippingQueryHandler(callback=callback))

    def register_pre_checkout_query_handler(self, callback: Callable):
        return self.register_handler(
            PreCheckoutQueryHandler(callback=callback))

    def register_poll_handler(self, callback: Callable):
        return self.register_handler(PollHandler(callback=callback))

    def register_poll_answer_handler(self, callback: Callable):
        return self.register_handler(PollAnswerHandler(callback=callback))

    def register_my_chat_member_handler(self, callback: Callable):
        return self.register_handler(MyChatMemberHandler(callback=callback))

    def register_chat_member_handler(self, callback: Callable):
        return self.register_handler(ChatMemberHandler(callback=callback))

    def register_chat_join_request_handler(self, callback: Callable):
        return self.register_handler(ChatJoinRequestHandler(callback=callback))

    ###################################################################################
    #
    # register handlers with decorators
    #
    ##################################################################################
    def error_handler(
        self,
        *errors,
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

    def command_handler(self, *cmds):
        def decorator(callback):
            self.register_command_handler(callback, *cmds)
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
                               game_short_name: str = None):
        def decorator(callback):
            self.register_callback_query_handler(callback, callback_data,
                                                 game_short_name)
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

    def chat_join_request_handler(self):
        def decorator(callback):
            self.register_chat_join_request_handler(callback)
            return callback

        return decorator

    ##################################################################################
    #
    # handler callers
    #
    ##################################################################################
    @classmethod
    def parse_update_field_and_data(cls, update: TelegramObject):
        for name, value in update.items():
            if name in cls.UPDATE_FIELD_VALUES and value:
                return name, TelegramObject(**value)
        raise TelegramBotException("unknown update field: {0}".format(
            pretty_format(update)))

    async def dispatch(self, bot: TelegramBot, update: TelegramObject):
        logger.debug(
            "\n----------------------------- update ----------------------------------\n%s",
            pretty_format(update))
        update_field, data = self.parse_update_field_and_data(update)
        route = self.route_map.get(update_field, None)
        if route:
            try:
                await self._handler_callers[update_field](bot, data)
            except Exception as error:
                await ErrorRoute(self.route_map.get("error", [])
                                 ).call_handlers(bot, data, error)
                raise error

    async def call_message_handlers(self, bot: TelegramBot, message: Message):
        if message.entities and message.entities[
                0].type == "bot_command" and await CommandRoute(
                    self.route_map.get("command", {})).call_handlers(
                        bot, message) is self.STOP_CALL:
            return self.STOP_CALL

        if "reply_to_message" in message and await ForceReplyRoute(
                self.route_map.get("force_reply", {})).call_handlers(
                    bot, message) is self.STOP_CALL:
            return self.STOP_CALL
        route = self.route_map.get(UpdateField.MESSAGE.value, {})
        return await MessageRoute(route).call_handlers(bot, message)

    async def call_edited_message_handlers(self, bot: TelegramBot,
                                           edited_message: Message):
        if edited_message.entities and edited_message.entities[
                0].type == "bot_command" and await CommandRoute(
                    self.route_map.get("command", {})).call_handlers(
                        bot, edited_message) is self.STOP_CALL:
            return self.STOP_CALL

        if "reply_to_message" in edited_message and await ForceReplyRoute(
                self.route_map.get("force_reply", {})).call_handlers(
                    bot, edited_message) is self.STOP_CALL:
            return self.STOP_CALL

        route = self.route_map.get(UpdateField.EDITED_MESSAGE.value, {})
        return await MessageRoute(route).call_handlers(bot, edited_message)

    async def call_channel_post_handlers(self, bot: TelegramBot,
                                         message: Message):
        return await MessageRoute(
            self.route_map.get(UpdateField.CHANNEL_POST.value,
                               {})).call_handlers(bot, message)

    async def call_edited_channel_post_handlers(self, bot: TelegramBot,
                                                message: Message):
        return await MessageRoute(
            self.route_map.get(UpdateField.EDITED_CHANNEL_POST.value,
                               {})).call_handlers(bot, message)

    async def call_callback_query_handlers(self, bot: TelegramBot,
                                           callback_query: CallbackQuery):
        return await CallbackQueryRoute(
            self.route_map.get(UpdateField.CALLBACK_QUERY.value,
                               {})).call_handlers(bot, callback_query)

    async def call_inline_query_handlers(self, bot: TelegramBot,
                                         inline_query: InlineQuery):
        return await ListRoute(
            self.route_map.get(UpdateField.INLINE_QUERY.value,
                               ())).call_handlers(bot, inline_query)

    async def call_chosen_inline_result_handlers(
            self, bot: TelegramBot, chosen_inline_result: ChosenInlineResult):
        return await ListRoute(
            self.route_map.get(UpdateField.CHOSEN_INLINE_RESULT.value,
                               ())).call_handlers(bot, chosen_inline_result)

    async def call_shipping_query_handlers(self, bot: TelegramBot,
                                           shipping_query: ShippingQuery):
        return await ListRoute(
            self.route_map.get(UpdateField.SHIPPING_QUERY.value,
                               ())).call_handlers(bot, shipping_query)

    async def call_pre_checkout_query_handlers(
            self, bot: TelegramBot, pre_checkout_query: PreCheckoutQuery):
        return await ListRoute(
            self.route_map.get(UpdateField.PRE_CHECKOUT_QUERY.value,
                               ())).call_handlers(bot, pre_checkout_query)

    async def call_poll_handlers(self, bot: TelegramBot, poll: Poll):
        return await ListRoute(self.route_map.get(UpdateField.POLL.value, ())
                               ).call_handlers(bot, poll)

    async def call_poll_answer_handlers(self, bot: TelegramBot,
                                        poll_answer: PollAnswer):
        return await ListRoute(
            self.route_map.get(UpdateField.POLL_ANSWER.value,
                               ())).call_handlers(bot, poll_answer)

    async def call_my_chat_member_handlers(
            self, bot: TelegramBot, my_chat_member_updated: ChatMemberUpdated):
        return await ListRoute(
            self.route_map.get(UpdateField.MY_CHAT_MEMBER.value,
                               ())).call_handlers(bot, my_chat_member_updated)

    async def call_chat_member_handlers(
            self, bot: TelegramBot, chat_member_updated: ChatMemberUpdated):
        return await self.call_my_chat_member_handlers(bot,
                                                       chat_member_updated)

    async def call_chat_join_reqeust_handlers(
            self, bot: TelegramBot, chat_join_request: ChatJoinRequst):
        return await ListRoute(
            self.route_map.get(UpdateField.CHAT_JOIN_REQUEST.value,
                               ())).call_handlers(bot, chat_join_request)

    def has_force_reply_callback(self, force_reply_name: str):
        return force_reply_name in ForceReplyRoute(
            self.route_map.get("force_reply", {}))

    def __repr__(self):
        return pretty_format(self.route_map)
