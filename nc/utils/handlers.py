#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import random
from typing import List, Optional, Tuple

from cachetools import cached, TTLCache
from telegram import Update, Bot, ChatMemberUpdated, ChatMember, ParseMode, BotCommand, User
from telegram.ext import CallbackContext

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


def help_command(update: Update, context: CallbackContext):
    """Send a message when the command /help is issued."""
    manual_message = """
    /set - 设置地址，如：/set 北京市北京xxxx路66号
/set1 - 设置地址1，使用 /dz1 来查看对应的地址（以此类推 /set2 /set3）
/dz - 查看 /set 命令设置的地址
/nc - 在群聊中随机选取一个人去取餐
/list - 列出所有已经记录的群成员
    """
    update.effective_message.reply_text(manual_message)
    if not context.bot.get_my_commands():
        bot_cmd_list = manual_message.split('\n')
        bot_cmds = []
        for bot_cmd_line in bot_cmd_list:
            if not bot_cmd_line.strip():
                continue
            bot_cmd_ = bot_cmd_line.strip()[1:].split(' - ')
            bot_cmd = BotCommand(bot_cmd_[0], bot_cmd_[1])
            bot_cmds.append(bot_cmd)
        context.bot.set_my_commands(bot_cmds)


def set_command(update: Update, context: CallbackContext):
    """Send a message when the message starts with /set is issued."""
    # 判断是否为管理员
    if update.effective_user.id not in get_admin_ids(context.bot, update.effective_chat.id):
        update.effective_message.reply_text('只有管理员才能使用此命令！')
        return
    text = update.effective_message.text
    if text:
        cmd = text.split()[0]
        if cmd == '/set':
            dz_num = 0
        else:
            tmp = cmd[4:]
            try:
                dz_num = int(tmp)
            except ValueError:
                update.effective_message.reply_text(
                    '命令格式错误，请使用 /set 命令 或 /set1 /set2 /set3 ...数字可无限大但必须为整数')
                return

        context.chat_data.setdefault('dz', dict())
        context.chat_data['dz'][dz_num] = text[len(cmd):]
        dz_str = '' if dz_num == 0 else str(dz_num)
        set_message = '地址设置成功！' + '\n' + '/dz' + dz_str + '：' + context.chat_data['dz'][dz_num]
        update.effective_message.reply_text(set_message)


def dz_command(update: Update, context: CallbackContext):
    """Send a message when the command /dz* is issued."""
    if update.effective_message.text == '/dz':
        dz_num = 0
    else:
        text = update.effective_message.text
        cmd = text.split()[0]
        tmp = cmd[3:]
        try:
            dz_num = int(tmp)
        except ValueError:
            update.effective_message.reply_text(
                '命令格式错误，请使用 /dz 命令 或 /dz1 /dz2 /dz3 ...数字可无限大但必须为整数')
            return
    context.chat_data.setdefault('dz', dict())
    if dz_num in context.chat_data['dz']:
        update.effective_message.reply_text(context.chat_data['dz'][dz_num])
    else:
        update.effective_message.reply_text('没有设置地址！')


def nc_command(update: Update, context: CallbackContext):
    """Send a message when the command /nc is issued."""
    member_list = get_member_ids(context)
    for _ in range(10):
        chosen_one_id = member_list[random.randint(0, len(member_list) - 1)]
        chosen_one = update.effective_chat.get_member(chosen_one_id)
        # 判断是否为群员
        if chosen_one.status in [
            ChatMember.MEMBER,
            ChatMember.CREATOR,
            ChatMember.ADMINISTRATOR,
        ] or (chosen_one.status == ChatMember.RESTRICTED and chosen_one.is_member):
            break
        else:
            context.chat_data['members'].remove(chosen_one_id)
    else:
        update.effective_message.reply_text('没有可用的人去取餐！')
        return

    chosen_member = chosen_one.user.mention_html()
    update.effective_message.reply_text(chosen_member + ' 去取餐！使用 /dz 查看地址！', parse_mode=ParseMode.HTML)


def tj_command(update: Update, context: CallbackContext):
    """Send a message when the command /tj is issued."""
    context.chat_data.setdefault('members', set())
    user = []
    if add_member(context, update.effective_message.from_user):
        user.append(update.effective_message.from_user.mention_html())
    if update.effective_message.reply_to_message:
        if add_member(context, update.effective_message.reply_to_message.from_user):
            user.append(update.effective_message.reply_to_message.from_user.mention_html())
    update.effective_message.reply_text(f'{" ".join(user)} 添加成功！', parse_mode=ParseMode.HTML)


def list_command(update: Update, context: CallbackContext):
    """Send a message when the command /list is issued."""
    member_list = get_member_ids(context)
    if not member_list:
        update.effective_message.reply_text('没有已经记录的群成员！')
        return
    member_list = [update.effective_chat.get_member(member_id).user.mention_html() for member_id in member_list]
    update.effective_message.reply_text('已经记录的群成员：' + '\n' + '\n'.join(member_list), parse_mode=ParseMode.HTML)


@cached(cache=TTLCache(maxsize=2048, ttl=60))
def get_admin_ids(bot: Bot, chat_id: int) -> List:
    """Returns a list of admin IDs for a given chat. Results are cached for 1 minute."""
    return [admin.user.id for admin in bot.get_chat_administrators(chat_id)]


def get_member_ids(context: CallbackContext) -> List:
    return list(context.chat_data.setdefault('members', set()))


def extract_status_change(
        chat_member_update: ChatMemberUpdated,
) -> Optional[Tuple[bool, bool]]:
    """Takes a ChatMemberUpdated instance and extracts whether the 'old_chat_member' was a member
    of the chat and whether the 'new_chat_member' is a member of the chat. Returns None, if
    the status didn't change.
    """
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.CREATOR,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.CREATOR,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


def greet_chat_members(update: Update, context: CallbackContext) -> None:
    """Greets new users in chats and announces when someone leaves"""
    result = extract_status_change(update.chat_member)
    if result is None:
        return

    was_member, is_member = result
    # cause_name = update.chat_member.from_user.mention_html()
    member_name = update.chat_member.new_chat_member.user.mention_html()
    # 记录群聊中的所有成员ID
    context.chat_data.setdefault('members', set())
    if not was_member and is_member:
        update.effective_chat.send_message(
            f"{member_name} 进群。欢迎！",
            parse_mode=ParseMode.HTML,
        )
        # 记录新加入群员ID
        add_member(context, update.chat_member.new_chat_member.user)
    elif was_member and not is_member:
        update.effective_chat.send_message(
            f"{member_name} 退出群聊。",
            parse_mode=ParseMode.HTML,
        )
        # 移除群员ID
        context.chat_data['members'].remove(update.chat_member.new_chat_member.user.id)


def add_member(context: CallbackContext, user: User) -> bool:
    """Adds a new member to the chat's member list."""
    context.chat_data.setdefault('members', set())
    if user.is_bot:
        return False
    context.chat_data['members'].add(user.id)
    return True
