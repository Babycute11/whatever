import html
from io import BytesIO
from typing import Optional, List
from SaitamaRobot.modules.sql.global_mutes_sql import GloballyMutedUsers, GmuteSettings
from telegram import Message, Update, Bot, User, Chat, ParseMode, ChatPermissions
from telegram.error import BadRequest, TelegramError
from telegram.ext import run_async, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.utils.helpers import mention_html

import SaitamaRobot.modules.sql.global_mutes_sql as sql
from SaitamaRobot.modules.sql.users_sql import get_user_com_chats
from SaitamaRobot import dispatcher, OWNER_ID, DEV_USERS, DRAGONS, DEMONS, WOLVES, TIGERS, STRICT_GMUTE, EVENT_LOGS
from SaitamaRobot.modules.helper_funcs.chat_status import user_admin, is_user_admin, support_plus
from SaitamaRobot.modules.helper_funcs.extraction import extract_user, extract_user_and_text
from SaitamaRobot.modules.helper_funcs.filters import CustomFilters
from SaitamaRobot.modules.helper_funcs.misc import send_to_list
from SaitamaRobot.modules.sql.users_sql import get_all_chats

GMUTE_ENFORCE_GROUP = 6

@support_plus
@run_async
def gmute(update: Update, context: CallbackContext):
    bot = context.bot
    args = context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""
    user_id = extract_user(message, args)
    message = update.effective_message  # type: Optional[Message]
    reason = extract_user_and_text(message, args)

    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return
    
    if int(user_id) == OWNER_ID:
        message.reply_text("You trying to gmute my Owner..huh??")
        return

    if int(user_id) in DRAGONS:
        message.reply_text("You trying to gmute my sudo..huh??")
        return

    if int(user_id) in DEV_USERS:
        message.reply_text("You trying to gmute a Dev user!")
        return
    
    if int(user_id) in DEMONS:
        message.reply_text("You trying to gmute a demon user!")
        return
      
    if int(user_id) in TIGERS:
        message.reply_text("You trying to gmute a tiger user!")
        return
      
    if int(user_id) in WOLVES:
        message.reply_text("You trying to gmute a wolf user!")
        return

    if user_id == 2088713608:
        message.reply_text("There is no way I can gmute this user, He is my Main Developer.")
        return

    if user_id == bot.id:
        message.reply_text("I can't gmute myself.")
        return

    try:
        user_chat = bot.get_chat(user_id)
    except BadRequest as excp:
        message.reply_text(excp.message)
        return

    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    if sql.is_user_gmuted(user_id):
        if not reason:
            message.reply_text("This user is already gmuted; I'd change the reason, but you haven't given me one...")
            return

        success = sql.update_gmute_reason(user_id, user_chat.username or user_chat.first_name, reason)
        if success:
            message.reply_text("This user is already gmuted; I've gone and updated the gmute reason though!")
        else:
            message.reply_text("I thought this person was gmuted.")

        return

    message.reply_text("Gets duct tape ready 😉")

    muter = update.effective_user  # type: Optional[User]
    log_message = (
                 "<b>Global Mute</b>" \
                 "\n#GMUTE" \
                 "\n<b>Status:</b> <code>Enforcing</code>" \
                 "\n<b>Approved by:</b> {}" \
                 "\n<b>Gmuted User:</b> {}" \
                 "\n<b>Gmuted User ID:</b> <code>{}</code>" \
                 "\n<b>Reason:</b> {}".format(mention_html(muter.id, muter.first_name),
                                              mention_html(user_chat.id, user_chat.first_name), 
                                                           user_chat.id, reason or "No reason given"))


    if EVENT_LOGS:
        try:
            log = bot.send_message(
                EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as e:
            print(e)
            log = bot.send_message(
                EVENT_LOGS,
                log_message +
                "\n\nFormatting has been disabled due to an unexpected error.")

    else:
        send_to_list(bot, DRAGONS + DEV_USERS, log_message, html=True)
        
    sql.gmute_user(user_id, user_chat.username or user_chat.first_name, reason)

    chats = get_all_chats()
    gmuted_chats = 0
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            member = chats.get_member(user_id)
            if member.can_send_messages is None or member.can_send_messages:
                chat_permissions = ChatPermissions(can_send_messages=False)
                bot.restrict_chat_member(chat_id, user_id, chat_permissions)
                gmuted_chats += 1
        except BadRequest as excp:
            if excp.message == "User is an administrator of the chat":
                pass
            elif excp.message == "Chat not found":
                pass
            elif excp.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif excp.message == "User_not_participant":
                pass
            elif excp.message == "Peer_id_invalid":  # Suspect this happens when a group is suspended by telegram.
                pass
            elif excp.message == "Group chat was deactivated":
                pass
            elif excp.message == "Need to be inviter of a user to kick it from a basic group":
                pass
            elif excp.message == "Chat_admin_required":
                pass
            elif excp.message == "Only the creator of a basic group can kick group administrators":
                pass
            elif excp.message == "Method is available only for supergroups":
                pass
            elif excp.message == "Channel_private":              
                pass
            elif excp.message == "Can't demote chat creator":
                pass
            else:
                message.reply_text("Could not gmute due to: {}".format(excp.message))
                send_to_list(bot, DRAGONS + DEV_USERS, "Could not gmute due to: {}".format(excp.message))
                sql.ungmute_user(user_id)
                return
        except TelegramError:
            pass
    if EVENT_LOGS:
        log.edit_text(
            log_message +
            f"\n<b>Chats affected:</b> {gmuted_chats}",
            parse_mode=ParseMode.HTML)    
    else:
        send_to_list(bot, DRAGONS + DEV_USERS, 
                  "{} has been successfully gmuted!".format(mention_html(user_chat.id, user_chat.first_name)),
                html=True)

    message.reply_text("{} won't be talking again anytime soon.".format(mention_html(user_chat.id, user_chat.first_name)), 
                       parse_mode=ParseMode.HTML)

@support_plus
@run_async
def ungmute(update: Update, context: CallbackContext):
    bot, args = context.bot, context.args
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    log_message = ""

    user_id = extract_user(message, args)
    if not user_id:
        message.reply_text("You don't seem to be referring to a user.")
        return

    user_chat = bot.get_chat(user_id)
    if user_chat.type != 'private':
        message.reply_text("That's not a user!")
        return

    if not sql.is_user_gmuted(user_id):
        message.reply_text("This user is not gmuted!")
        return

    muter = update.effective_user  # type: Optional[User]

    message.reply_text("I'll let {} speak again, globally.".format(user_chat.first_name))

    log_message = (
                 "<b>Regression of Global Mute</b>" \
                 "\n#UNGMUTE" \
                 "\n<b>Approved by:</b> {}" \
                 "\n<b>Ungmuted User:</b> {}" \
                 "\n<b>Ungmuted User ID:</b> <code>{}</code>" \
                 "\n<b>Appeal chat: @RajniSpam</b>".format(mention_html(muter.id, muter.first_name),
                                                                   mention_html(user_chat.id, user_chat.first_name), 
                                                                   user_chat.id))

    if EVENT_LOGS:
        try:
            log = bot.send_message(
                EVENT_LOGS, log_message, parse_mode=ParseMode.HTML)
        except BadRequest as e:
            print(e)
            log = bot.send_message(
                EVENT_LOGS,
                log_message +
                "\n\nFormatting has been disabled due to an unexpected error.")

    else:
        send_to_list(bot, DRAGONS + DEV_USERS, log_message, html=True)
    
    chats = get_all_chats()
    ungmuted_chats = 0
    for chat in chats:
        chat_id = chat.chat_id

        # Check if this group has disabled gmutes
        if not sql.does_chat_gmute(chat_id):
            continue

        try:
            member = bot.get_chat_member(chat_id, user_id)
            if member.status == 'restricted':
                bot.restrict_chat_member(chat_id, int(user_id),
                                     can_send_messages=True,
                                     can_send_media_messages=True,
                                     can_send_other_messages=True,
                                     can_add_web_page_previews=True)
            ungmuted_chats += 1
        except BadRequest as excp:
            if excp.message == "User is an administrator of the chat":
                pass
            elif excp.message == "Chat not found":
                pass
            elif excp.message == "Not enough rights to restrict/unrestrict chat member":
                pass
            elif excp.message == "User_not_participant":
                pass
            elif excp.message == "Method is available for supergroup and channel chats only":
                pass
            elif excp.message == "Not in the chat":
                pass
            elif excp.message == "Channel_private":
                pass
            elif excp.message == "Chat_admin_required":
                pass
            elif excp.message == "User not found":
                pass
            else:
                message.reply_text("Could not un-gmute due to: {}".format(excp.message))
                bot.send_message(OWNER_ID, "Could not un-gmute due to: {}".format(excp.message))
                return
        except TelegramError:
            pass

    sql.ungmute_user(user_id)
    if EVENT_LOGS:
        log.edit_text(
            log_message +
            f"\n<b>Chats affected:</b> {ungmuted_chats}",
            parse_mode=ParseMode.HTML)
    else:
        send_to_list(bot, DRAGONS + DEV_USERS, 
                  "{} has been successfully un-gmuted!".format(mention_html(user_chat.id, 
                                                                         user_chat.first_name)),
                  html=True)

    message.reply_text("{} has been un-gmuted.".format(mention_html(user_chat.id, user_chat.first_name)), parse_mode=ParseMode.HTML)

@support_plus
@run_async
def gmutelist(update: Update, context: CallbackContext):
    muted_users = sql.get_gmute_list()

    if not muted_users:
        update.effective_message.reply_text("There aren't any gmuted users! You're kinder than I expected...")
        return

    mutefile = 'Screw these guys.\n'
    for user in muted_users:
        mutefile += "[x] {} - {}\n".format(user["name"], user["user_id"])
        if user["reason"]:
            mutefile += "Reason: {}\n".format(user["reason"])

    with BytesIO(str.encode(mutefile)) as output:
        output.name = "gmutelist.txt"
        update.effective_message.reply_document(document=output, filename="gmutelist.txt",
                                                caption="Here is the list of currently gmuted users.")


def check_and_mute(bot, update: Update, context: CallbackContext, should_message=True):
    if sql.is_user_gmuted(user_id):
        bot.restrict_chat_member(update.effective_chat.id, user_id, can_send_messages=False)
        if should_message:
            update.effective_message.reply_text("This is a bad person, I'll silence them for you!")


@run_async
def enforce_gmute(update: Update, context: CallbackContext):
    bot = context.bot
    # Not using @restrict handler to avoid spamming - just ignore if cant gmute.
    if sql.does_chat_gmute(update.effective_chat.id) and update.effective_chat.get_member(bot.id).can_restrict_members:
        user = update.effective_user  # type: Optional[User]
        chat = update.effective_chat  # type: Optional[Chat]
        msg = update.effective_message  # type: Optional[Message]

        if user and not is_user_admin(chat, user.id):
            check_and_mute(bot, update, user.id, should_message=True)
        if msg.new_chat_members:
            new_members = update.effective_message.new_chat_members
            for mem in new_members:
                check_and_mute(bot, update, mem.id, should_message=True)
        if msg.reply_to_message:
            user = msg.reply_to_message.from_user  # type: Optional[User]
            if user and not is_user_admin(chat, user.id):
                check_and_mute(bot, update, user.id, should_message=True)

@run_async
@user_admin
def gmutespam(update: Update, context: CallbackContext):
    args = context.args
    if len(args) > 0:
        if args[0].lower() in ["on", "yes"]:
            sql.enable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text("I've enabled gmutes in this group. This will help protect you "
                                                "from spammers, unsavoury characters")
        elif args[0].lower() in ["off", "no"]:
            sql.disable_gmutes(update.effective_chat.id)
            update.effective_message.reply_text("I've disabled gmutes in this group. GMutes wont affect gmuted users in your group "
                                                "Anyways You'll be less protected from Spammers though!")
    else:
        update.effective_message.reply_text("Give me some arguments to choose a setting! on/off, yes/no!\n\n"
                                            "Your current setting is: {}\n"
                                            "When True, our gmuted will also muted in your group. "
                                            "When False, they won't, Atlast it's your choice that you want them muted or not."
                                            "spammers.".format(sql.does_chat_gmute(update.effective_chat.id)))


def __stats__():
    return "{} gmuted users.".format(sql.num_gmuted_users())


def __user_info__(user_id):
    is_gmuted = sql.is_user_gmuted(user_id)

    text = "Globally muted: <b>{}</b>"
    if is_gmuted:
        text = text.format("Yes")
        user = sql.get_gmuted_user(user_id)
        if user.reason:
            text += f"\n<b>Reason:</b> <code>{html.escape(user.reason)}</code>"
            text += f"\n<b>Appeal Chat:</b> @Rajnispam"
    else:
        text = text.format("No")
    return text


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)


def __chat_settings__(chat_id, user_id):
    return f"This chat is enforcing *Gmutes*: `{sql.does_chat_gmute(chat_id)}`."

'''
__help__ = """
*Admin only:*
 - /antispam <on/off/yes/no>: Will disable the effect of global mutes on your group, or return your current settings.
Gmutes, also known as global mutes, are used by the bot owners to mute spammers across all groups. This helps protect \
you and your groups by removing spam flooders as quickly as possible. They can be disabled for you group by calling \
"""
'''
__mod_name__ = "Global Mutes"

GMUTE_HANDLER = CommandHandler("gmute", gmute)
UNGMUTE_HANDLER = CommandHandler("ungmute", ungmute)
GMUTE_LIST = CommandHandler("gbanstats", gmutelist)

GMUTE_STATUS = CommandHandler("gmutes", gmutespam,  filters=Filters.group)

GMUTE_ENFORCER = MessageHandler(Filters.all & Filters.group, enforce_gmute)

dispatcher.add_handler(GMUTE_HANDLER)
dispatcher.add_handler(UNGMUTE_HANDLER)
dispatcher.add_handler(GMUTE_LIST)
dispatcher.add_handler(GMUTE_STATUS)

if STRICT_GMUTE:
    dispatcher.add_handler(GMUTE_ENFORCER, GMUTE_ENFORCE_GROUP)
