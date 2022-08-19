#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging

from telegram import Update
from telegram.ext import PicklePersistence, Updater, CommandHandler, Filters, MessageHandler, ChatMemberHandler

from config import BOT_TOKEN, OWNER_ID
from utils import handlers

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def main(bot_token, owner_id):
    # Start the bot
    my_persistence = PicklePersistence(filename='./data/my_file')
    updater = Updater(token=bot_token, persistence=my_persistence, use_context=True)
    dispatcher = updater.dispatcher
    dispatcher.bot_data['owner_id'] = owner_id
    # on different commands - answer in Telegram
    dispatcher.add_handler(CommandHandler(['start', 'help'], handlers.help_command, run_async=True))
    dispatcher.add_handler(
        MessageHandler(Filters.command & Filters.regex(r'^/set') & Filters.chat_type.groups, handlers.set_command))
    dispatcher.add_handler(
        MessageHandler(Filters.command & Filters.regex(r'^/dz') & Filters.chat_type.groups, handlers.dz_command))
    dispatcher.add_handler(CommandHandler('nc', handlers.nc_command, run_async=True))
    dispatcher.add_handler(MessageHandler(Filters.chat_type.groups & Filters.regex(r'谁去取餐'), handlers.nc_command))
    dispatcher.add_handler(CommandHandler('tj', handlers.tj_command))
    dispatcher.add_handler(CommandHandler('list', handlers.list_command, run_async=True))
    # Handle members joining/leaving chats.
    dispatcher.add_handler(ChatMemberHandler(handlers.greet_chat_members, ChatMemberHandler.CHAT_MEMBER))

    # start the bot using polling
    updater.start_polling(allowed_updates=Update.ALL_TYPES)
    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main(BOT_TOKEN, OWNER_ID)
