# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
"""
Userbot module to help you manage a group
"""

from asyncio import sleep
from os import remove

from telethon.errors import (
    BadRequestError,
    ChatAdminRequiredError,
    ImageProcessFailedError,
    PhotoCropSizeSmallError,
    UserAdminInvalidError,
)
from telethon.errors.rpcerrorlist import (
    BadRequestError,
    MessageTooLongError,
    UserAdminInvalidError,
    UserIdInvalidError,
)
from telethon.tl.functions.channels import (
    EditAdminRequest,
    EditBannedRequest,
    EditPhotoRequest,
)
from telethon.tl.functions.messages import UpdatePinnedMessageRequest
from telethon.tl.types import (
    ChannelParticipantAdmin,
    ChannelParticipantCreator,
    ChannelParticipantsAdmins,
    ChannelParticipantsBots,
    ChatAdminRights,
    ChatBannedRights,
    MessageEntityMentionName,
    MessageMediaPhoto,
)

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, bot
from userbot.events import register

# =================== CONSTANT ===================
PP_TOO_SMOL = "`La imagen es demasiado pequeña`"
PP_ERROR = "`Fallo al procesar la imagen`"
NO_ADMIN = "`No soy administrador!`"
NO_PERM = "`No tengo suficientes permisos!`"
NO_SQL = "`Ejecutando en modo Non-SQL!`"

CHAT_PP_CHANGED = "`Imagen del chat cambiada`"
CHAT_PP_ERROR = (
    "`Algún problema con la actualización de la foto.,`"
    "`tal vez porque no soy administrador,`"
    "`o no tengo suficientes permisos.`"
)
INVALID_MEDIA = "`Extensión inválida`"

BANNED_RIGHTS = ChatBannedRights(
    until_date=None,
    view_messages=True,
    send_messages=True,
    send_media=True,
    send_stickers=True,
    send_gifs=True,
    send_games=True,
    send_inline=True,
    embed_links=True,
)

UNBAN_RIGHTS = ChatBannedRights(
    until_date=None,
    send_messages=None,
    send_media=None,
    send_stickers=None,
    send_gifs=None,
    send_games=None,
    send_inline=None,
    embed_links=None,
)

MUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=True)

UNMUTE_RIGHTS = ChatBannedRights(until_date=None, send_messages=False)
# ================================================


@register(outgoing=True, pattern="^.setgpic$")
async def set_group_photo(gpic):
    """ El comando .setgpic, cambia la imagen de un grupo """
    await gpic.edit("`Procesando...`")
    await sleep(1)
    if not gpic.is_group:
        await gpic.edit("`No creo que esto sea un grupo.`")
        return
    replymsg = await gpic.get_reply_message()
    chat = await gpic.get_chat()
    admin = chat.admin_rights
    creator = chat.creator
    photo = None

    if not admin and not creator:
        await gpic.edit(NO_ADMIN)
        return

    if replymsg and replymsg.media:
        if isinstance(replymsg.media, MessageMediaPhoto):
            photo = await gpic.client.download_media(message=replymsg.photo)
        elif "image" in replymsg.media.document.mime_type.split("/"):
            photo = await gpic.client.download_file(replymsg.media.document)
        else:
            await gpic.edit(INVALID_MEDIA)

    if photo:
        try:
            await gpic.client(
                EditPhotoRequest(gpic.chat_id, await gpic.client.upload_file(photo))
            )
            await gpic.edit(CHAT_PP_CHANGED)

        except PhotoCropSizeSmallError:
            await gpic.edit(PP_TOO_SMOL)
        except ImageProcessFailedError:
            await gpic.edit(PP_ERROR)


@register(outgoing=True, pattern="^.promote(?: |$)(.*)")
async def promote(promt):
    """ El comando .promote, promueve a la persona respondida / etiquetada """
    # Get targeted chat
    chat = await promt.get_chat()
    # Grab admin status or creator in a chat
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, also return
    if not admin and not creator:
        await promt.edit(NO_ADMIN)
        return

    new_rights = ChatAdminRights(
        add_admins=False,
        invite_users=True,
        change_info=False,
        ban_users=True,
        delete_messages=True,
        pin_messages=True,
    )

    await promt.edit("`Promoviendo...`")
    user, rank = await get_user_from_event(promt)
    if not rank:
        rank = "Administrator"  # Just in case.
    if user:
        pass
    else:
        return

    # Try to promote if current user is admin or creator
    try:
        await promt.client(EditAdminRequest(promt.chat_id, user.id, new_rights, rank))
        await promt.edit("`Promovido con éxito!`")

    # If Telethon spit BadRequestError, assume
    # we don't have Promote permission
    except BadRequestError:
        await promt.edit(NO_PERM)
        return

    # Announce to the logging group if we have promoted successfully
    if BOTLOG:
        await promt.client.send_message(
            BOTLOG_CHATID,
            "#PROMOVIDO\n"
            f"USUARIO: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {promt.chat.title}(`{promt.chat_id}`)",
        )


@register(outgoing=True, pattern="^.demote(?: |$)(.*)")
async def demote(dmod):
    """ El comando .demote, degrada a la persona respondida / etiquetada """
    # Admin right check
    chat = await dmod.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    if not admin and not creator:
        await dmod.edit(NO_ADMIN)
        return

    # If passing, declare that we're going to demote
    await dmod.edit("`Degradando...`")
    rank = "admeme"  # dummy rank, lol.
    user = await get_user_from_event(dmod)
    user = user[0]
    if user:
        pass
    else:
        return

    # New rights after demotion
    newrights = ChatAdminRights(
        add_admins=None,
        invite_users=None,
        change_info=None,
        ban_users=None,
        delete_messages=None,
        pin_messages=None,
    )
    # Edit Admin Permission
    try:
        await dmod.client(EditAdminRequest(dmod.chat_id, user.id, newrights, rank))

    # If we catch BadRequestError from Telethon
    # Assume we don't have permission to demote
    except BadRequestError:
        await dmod.edit(NO_PERM)
        return
    await dmod.edit("`Demoted Successfully!`")

    # Announce to the logging group if we have demoted successfully
    if BOTLOG:
        await dmod.client.send_message(
            BOTLOG_CHATID,
            "#DEGRADADO\n"
            f"USUARIO: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {dmod.chat.title}(`{dmod.chat_id}`)",
        )


@register(outgoing=True, pattern="^.ban(?: |$)(.*)")
async def ban(bon):
    """ El comando .ban, prohíbe a la persona respondida / etiquetada """
    # Here laying the sanity check
    chat = await bon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        await bon.edit(NO_ADMIN)
        return

    user, reason = await get_user_from_event(bon)
    if user:
        pass
    else:
        return

    # Announce that we're going to whack the pest
    await bon.edit("`Baneado!😎`")

    try:
        await bon.client(EditBannedRequest(bon.chat_id, user.id, BANNED_RIGHTS))
    except BadRequestError:
        await bon.edit(NO_PERM)
        return
    # Helps ban group join spammers more easily
    try:
        reply = await bon.get_reply_message()
        if reply:
            await reply.delete()
    except BadRequestError:
        await bon.edit("`I dont have message nuking rights! But still he was banned!`")
        return
    # Delete message and then tell that the command
    # is done gracefully
    # Shout out the ID, so that fedadmins can fban later
    if reason:
        await bon.edit(
            f"{user.first_name} was banned !!\
        \nID: `{str(user.id)}`\
        \nReason: {reason}"
        )
    else:
        await bon.edit(
            f"{user.first_name} was banned !!\
        \nID: `{str(user.id)}`"
        )
    # Announce to the logging group if we have banned the person
    # successfully!
    if BOTLOG:
        await bon.client.send_message(
            BOTLOG_CHATID,
            "#BAN\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {bon.chat.title}(`{bon.chat_id}`)",
        )


@register(outgoing=True, pattern="^.unban(?: |$)(.*)")
async def nothanos(unbon):
    """ El comando .unban, anula la prohibición de la persona respondida / etiquetada """
    # Here laying the sanity check
    chat = await unbon.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        await unbon.edit(NO_ADMIN)
        return

    # If everything goes well...
    await unbon.edit("`Quitando ban...`")

    user = await get_user_from_event(unbon)
    user = user[0]
    if user:
        pass
    else:
        return

    try:
        await unbon.client(EditBannedRequest(unbon.chat_id, user.id, UNBAN_RIGHTS))
        await unbon.edit("```Puede volver al grupo...```")

        if BOTLOG:
            await unbon.client.send_message(
                BOTLOG_CHATID,
                "#UNBAN\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {unbon.chat.title}(`{unbon.chat_id}`)",
            )
    except UserIdInvalidError:
        await unbon.edit("`Error :/ !`")


@register(outgoing=True, pattern="^.mute(?: |$)(.*)")
async def spider(spdr):
    """
    This function is basically muting peeps
    """
    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.spam_mute_sql import mute
    except AttributeError:
        await spdr.edit(NO_SQL)
        return

    # Admin or creator check
    chat = await spdr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        await spdr.edit(NO_ADMIN)
        return

    user, reason = await get_user_from_event(spdr)
    if user:
        pass
    else:
        return

    self_user = await spdr.client.get_me()

    if user.id == self_user.id:
        await spdr.edit("`Manos demasiado cortas, no puedo pegarme con cinta adhesiva...\n(ヘ･_･)ヘ┳━┳`")
        return

    # If everything goes well, do announcing and mute
    await spdr.edit("`shht...🤫 !`")
    if mute(spdr.chat_id, user.id) is False:
        return await spdr.edit("`¡Error! El usuario probablemente ya esté silenciado.`")
    else:
        try:
            await spdr.client(EditBannedRequest(spdr.chat_id, user.id, MUTE_RIGHTS))

            # Announce that the function is done
            if reason:
                await spdr.edit(f"`shht...🤫 !!`\nReason: {reason}")
            else:
                await spdr.edit("`shht...🤫 !!`")

            # Announce to logging group
            if BOTLOG:
                await spdr.client.send_message(
                    BOTLOG_CHATID,
                    "#MUTE\n"
                    f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                    f"CHAT: {spdr.chat.title}(`{spdr.chat_id}`)",
                )
        except UserIdInvalidError:
            return await spdr.edit("`Uh oh my mute logic broke!`")


@register(outgoing=True, pattern="^.unmute(?: |$)(.*)")
async def unmoot(unmot):
    """ El comando .unmute, reactivar el sonido de la persona respondida / etiquetada """
    # Admin or creator check
    chat = await unmot.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        await unmot.edit(NO_ADMIN)
        return

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.spam_mute_sql import unmute
    except AttributeError:
        await unmot.edit(NO_SQL)
        return

    # If admin or creator, inform the user and start unmuting
    await unmot.edit("```Puedes escribir...```")
    user = await get_user_from_event(unmot)
    user = user[0]
    if user:
        pass
    else:
        return

    if unmute(unmot.chat_id, user.id) is False:
        return await unmot.edit("`Error! User probably already unmuted.`")
    else:

        try:
            await unmot.client(EditBannedRequest(unmot.chat_id, user.id, UNBAN_RIGHTS))
            await unmot.edit("```Puedes hablar...```")

        except UserIdInvalidError:
            await unmot.edit("`Uh oh my unmute logic broke!`")
            return

        if BOTLOG:
            await unmot.client.send_message(
                BOTLOG_CHATID,
                "#UNMUTE\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {unmot.chat.title}(`{unmot.chat_id}`)",
            )


@register(incoming=True, disable_errors=True)
async def muter(moot):
    """ Se utiliza para eliminar los mensajes de personas silenciadas. """
    try:
        from userbot.modules.sql_helper.gmute_sql import is_gmuted
        from userbot.modules.sql_helper.spam_mute_sql import is_muted
    except AttributeError:
        return
    muted = is_muted(moot.chat_id)
    gmuted = is_gmuted(moot.sender_id)
    rights = ChatBannedRights(
        until_date=None,
        send_messages=True,
        send_media=True,
        send_stickers=True,
        send_gifs=True,
        send_games=True,
        send_inline=True,
        embed_links=True,
    )
    if muted:
        for i in muted:
            if str(i.sender) == str(moot.sender_id):
                try:
                    await moot.delete()
                    await moot.client(
                        EditBannedRequest(moot.chat_id, moot.sender_id, rights)
                    )
                except (
                    BadRequestError,
                    UserAdminInvalidError,
                    ChatAdminRequiredError,
                    UserIdInvalidError,
                ):
                    await moot.client.send_read_acknowledge(moot.chat_id, moot.id)
    for i in gmuted:
        if i.sender == str(moot.sender_id):
            await moot.delete()


@register(outgoing=True, pattern="^.ungmute(?: |$)(.*)")
async def ungmoot(un_gmute):
    """ El comando .ungmute, desmutea al usuario """
    # Admin or creator check
    chat = await un_gmute.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        await un_gmute.edit(NO_ADMIN)
        return

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.gmute_sql import ungmute
    except AttributeError:
        await un_gmute.edit(NO_SQL)
        return

    user = await get_user_from_event(un_gmute)
    user = user[0]
    if user:
        pass
    else:
        return

    # If pass, inform and start ungmuting
    await un_gmute.edit("```Ungmuting...```")

    if ungmute(user.id) is False:
        await un_gmute.edit("`¡Error! Probablemente el usuario no este silenciado.`")
    else:
        # Inform about success
        await un_gmute.edit("```Puedes hablar...```")

        if BOTLOG:
            await un_gmute.client.send_message(
                BOTLOG_CHATID,
                "#UNGMUTE\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {un_gmute.chat.title}(`{un_gmute.chat_id}`)",
            )


@register(outgoing=True, pattern="^.gmute(?: |$)(.*)")
async def gspider(gspdr):
    """ El comando .gmute, silencia globalmente a la persona respondida / etiquetada """
    # Admin or creator check
    chat = await gspdr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        await gspdr.edit(NO_ADMIN)
        return

    # Check if the function running under SQL mode
    try:
        from userbot.modules.sql_helper.gmute_sql import gmute
    except AttributeError:
        await gspdr.edit(NO_SQL)
        return

    user, reason = await get_user_from_event(gspdr)
    if user:
        pass
    else:
        return

    # If pass, inform and start gmuting
    await gspdr.edit("`Grabs a huge, sticky duct tape!`")
    if gmute(user.id) is False:
        await gspdr.edit("¡Error! El usuario probablemente ya esta silenciado.`")
    else:
        if reason:
            await gspdr.edit(f"`Silenciado globalmente!`Reason: {reason}")
        else:
            await gspdr.edit("`Silenciado globalmente!`")

        if BOTLOG:
            await gspdr.client.send_message(
                BOTLOG_CHATID,
                "#GMUTE\n"
                f"USER: [{user.first_name}](tg://user?id={user.id})\n"
                f"CHAT: {gspdr.chat.title}(`{gspdr.chat_id}`)",
            )


@register(outgoing=True, pattern="^.zombies(?: |$)(.*)", groups_only=False)
async def rm_deletedacc(show):
    """ El comando .zombies, enumera todas las cuentas fantasmas / eliminadas / zombies en un chat. """

    con = show.pattern_match.group(1).lower()
    del_u = 0
    del_status = "`No se encontraron cuentas eliminadas, el grupo está limpio`"

    if con != "clean":
        await show.edit("`Buscando de cuentas fantasmas / eliminadas / zombies...`")
        async for user in show.client.iter_participants(show.chat_id):

            if user.deleted:
                del_u += 1
                await sleep(1)
        if del_u > 0:
            del_status = f"`Encontré` **{del_u}** `Cuentas eliminadas en este grupo,\
            \nlímpialos usando .zombies clean`"
        await show.edit(del_status)
        return

    # Here laying the sanity check
    chat = await show.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # Well
    if not admin and not creator:
        await show.edit("`No soy un administrador aquí!`")
        return

    await show.edit("`expulsando cuentas eliminadas...")
    del_u = 0
    del_a = 0

    async for user in show.client.iter_participants(show.chat_id):
        if user.deleted:
            try:
                await show.client(
                    EditBannedRequest(show.chat_id, user.id, BANNED_RIGHTS)
                )
            except ChatAdminRequiredError:
                await show.edit("`No tengo permisos de prohibición en este grupo.`")
                return
            except UserAdminInvalidError:
                del_u -= 1
                del_a += 1
            await show.client(EditBannedRequest(show.chat_id, user.id, UNBAN_RIGHTS))
            del_u += 1

    if del_u > 0:
        del_status = f"Expulsando **{del_u}** cuentas eliminadas"

    if del_a > 0:
        del_status = f"Expulsando **{del_u}** cuentas eliminadas \
        \n**{del_a}** las cuentas de administrador eliminadas no se eliminan"

    await show.edit(del_status)
    await sleep(2)
    await show.delete()

    if BOTLOG:
        await show.client.send_message(
            BOTLOG_CHATID,
            "#CLEANUP\n"
            f"Cleaned **{del_u}** deleted account(s) !!\
            \nCHAT: {show.chat.title}(`{show.chat_id}`)",
        )


@register(outgoing=True, pattern="^.all$")
async def tagaso(event):
    """ El comando .all, mencione a todos los miembros del grupo chat"""
    if event.fwd_from:
        return
    await event.delete()
    mentions = "@all"
    chat = await event.get_input_chat()
    async for user in bot.iter_participants(chat, 500):
        mentions += f"[\u2063](tg://user?id={user.id})"
    await bot.send_message(chat, mentions, reply_to=event.message.reply_to_msg_id)


@register(outgoing=True, pattern="^.admins(?: |$)(.*)")
async def _(event):
    if event.fwd_from:
        return
    info = await event.client.get_entity(event.chat_id)
    title = info.title if info.title else "this chat"
    mentions = "**Admins On {} Group**: \n".format(title)
    should_mention_admins = False
    reply_message = None
    pattern_match_str = event.pattern_match.group(1)
    if "m" in pattern_match_str:
        should_mention_admins = True
        if event.reply_to_msg_id:
            reply_message = await event.get_reply_message()
    input_str = event.pattern_match.group(1)
    to_write_chat = await event.get_input_chat()
    chat = None
    if not input_str:
        chat = to_write_chat
    else:
        try:
            chat = await bot.get_entity(input_str)
        except Exception as e:
            await event.edit(str(e))
            return None
    try:
        async for x in bot.iter_participants(chat, filter=ChannelParticipantsAdmins):
            if not x.deleted:
                if isinstance(x.participant, ChannelParticipantCreator):
                    mentions += "\n 👑 [{}](tg://user?id={}) `{}`".format(
                        x.first_name, x.id, x.id
                    )
        mentions += "\n"
        async for x in bot.iter_participants(chat, filter=ChannelParticipantsAdmins):
            if not x.deleted:
                if isinstance(x.participant, ChannelParticipantAdmin):
                    mentions += "\n 🔰 [{}](tg://user?id={}) `{}`".format(
                        x.first_name, x.id, x.id
                    )

    #  mentions += "\n 💘 [Deleted Account](tg://user?id=689811472) `689811472`"

    except Exception as e:
        mentions += " " + str(e) + "\n"
    if should_mention_admins:
        if reply_message:
            await reply_message.reply(mentions)
        else:
            await event.reply(mentions)
        await event.delete()
    else:
        await event.edit(mentions)


@register(outgoing=True, pattern="^.pin(?: |$)(.*)")
async def pin(msg):
    """ El comando .pin, fija el mensaje respondido / etiquetado en la parte superior del chat. """
    # Admin or creator check
    chat = await msg.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        await msg.edit(NO_ADMIN)
        return

    to_pin = msg.reply_to_msg_id

    if not to_pin:
        await msg.edit("`Responde a un mensaje para fijarlo.`")
        return

    options = msg.pattern_match.group(1)

    is_silent = True

    if options.lower() == "loud":
        is_silent = False

    try:
        await msg.client(UpdatePinnedMessageRequest(msg.to_id, to_pin, is_silent))
    except BadRequestError:
        await msg.edit(NO_PERM)
        return

    await msg.edit("`Fijado correctamente!`")

    user = await get_user_from_id(msg.from_id, msg)

    if BOTLOG:
        await msg.client.send_message(
            BOTLOG_CHATID,
            "#PIN\n"
            f"ADMIN: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {msg.chat.title}(`{msg.chat_id}`)\n"
            f"LOUD: {not is_silent}",
        )


@register(outgoing=True, pattern="^.kick(?: |$)(.*)")
async def kick(usr):
    """ El comando .kick, expulsa a la persona respondida / etiquetada del grupo. """
    # Admin or creator check
    chat = await usr.get_chat()
    admin = chat.admin_rights
    creator = chat.creator

    # If not admin and not creator, return
    if not admin and not creator:
        await usr.edit(NO_ADMIN)
        return

    user, reason = await get_user_from_event(usr)
    if not user:
        await usr.edit("`No se pudo recuperar el usuario.`")
        return

    await usr.edit("`Expulsando...`")

    try:
        await usr.client.kick_participant(usr.chat_id, user.id)
        await sleep(1)
    except Exception as e:
        await usr.edit(NO_PERM + f"\n{str(e)}")
        return

    if reason:
        await usr.edit(
            f"`Kicked` [{user.first_name}](tg://user?id={user.id})`!`\nReason: {reason}"
        )
    else:
        await usr.edit(f"`Kicked` [{user.first_name}](tg://user?id={user.id})`!`")

    if BOTLOG:
        await usr.client.send_message(
            BOTLOG_CHATID,
            "#KICK\n"
            f"USER: [{user.first_name}](tg://user?id={user.id})\n"
            f"CHAT: {usr.chat.title}(`{usr.chat_id}`)\n",
        )


@register(outgoing=True, pattern="^.users ?(.*)")
async def get_users(show):
    """ For .users command, list all of the users in a chat. """
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "this chat"
    mentions = "**Users in {} Group**: \n".format(title)
    try:
        if not show.pattern_match.group(1):
            async for user in show.client.iter_participants(show.chat_id):
                if not user.deleted:
                    mentions += (
                        f"\n ⚜️ [{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
                else:
                    mentions += f"\nCuenta eliminada `{user.id}`"
        else:
            searchq = show.pattern_match.group(1)
            async for user in show.client.iter_participants(
                show.chat_id, search=f"{searchq}"
            ):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
                else:
                    mentions += f"\nCuenta eliminada `{user.id}`"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    try:
        await show.edit(mentions)
    except MessageTooLongError:
        await show.edit("Maldita sea, este es un grupo enorme. Subire la lista de usuarios como archivo.")
        file = open("userslist.txt", "w+")
        file.write(mentions)
        file.close()
        await show.client.send_file(
            show.chat_id,
            "userslist.txt",
            caption="Users in {}".format(title),
            reply_to=show.id,
        )
        remove("userslist.txt")


async def get_user_from_event(event):
    """ Obtener el usuario del mensaje respondido. """
    args = event.pattern_match.group(1).split(" ", 1)
    extra = None
    if event.reply_to_msg_id and not len(args) == 2:
        previous_message = await event.get_reply_message()
        user_obj = await event.client.get_entity(previous_message.from_id)
        extra = event.pattern_match.group(1)
    elif args:
        user = args[0]
        if len(args) == 2:
            extra = args[1]

        if user.isnumeric():
            user = int(user)

        if not user:
            await event.edit("`Pass the user's username, id or reply!`")
            return

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        try:
            user_obj = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            await event.edit(str(err))
            return None

    return user_obj, extra


async def get_user_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        await event.edit(str(err))
        return None

    return user_obj


@register(outgoing=True, pattern="^.usersdel ?(.*)")
async def get_usersdel(show):
    """ El comando .usersdel, enumera a todos los usuarios eliminados en un chat. """
    info = await show.client.get_entity(show.chat_id)
    title = info.title if info.title else "this chat"
    mentions = "deletedUsers in {}: \n".format(title)
    try:
        if not show.pattern_match.group(1):
            async for user in show.client.iter_participants(show.chat_id):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
        #       else:
        #                mentions += f"\nDeleted Account `{user.id}`"
        else:
            searchq = show.pattern_match.group(1)
            async for user in show.client.iter_participants(
                show.chat_id, search=f"{searchq}"
            ):
                if not user.deleted:
                    mentions += (
                        f"\n[{user.first_name}](tg://user?id={user.id}) `{user.id}`"
                    )
        #       else:
    #              mentions += f"\nDeleted Account `{user.id}`"
    except ChatAdminRequiredError as err:
        mentions += " " + str(err) + "\n"
    try:
        await show.edit(mentions)
    except MessageTooLongError:
        await show.edit(
            "Maldita sea, este es un grupo enorme. Subire la lista de usuarios eliminados como archivo."
        )
        file = open("userslist.txt", "w+")
        file.write(mentions)
        file.close()
        await show.client.send_file(
            show.chat_id,
            "deleteduserslist.txt",
            caption="Users in {}".format(title),
            reply_to=show.id,
        )
        remove("deleteduserslist.txt")


async def get_userdel_from_event(event):
    """ Obtener el usuario eliminado del mensaje respondido. """
    args = event.pattern_match.group(1).split(" ", 1)
    extra = None
    if event.reply_to_msg_id and not len(args) == 2:
        previous_message = await event.get_reply_message()
        user_obj = await event.client.get_entity(previous_message.from_id)
        extra = event.pattern_match.group(1)
    elif args:
        user = args[0]
        if len(args) == 2:
            extra = args[1]

        if user.isnumeric():
            user = int(user)

        if not user:
            await event.edit("`Pase el nombre de usuario, el ID o la respuesta del usuario eliminado!`")
            return

        if event.message.entities is not None:
            probable_user_mention_entity = event.message.entities[0]

            if isinstance(probable_user_mention_entity, MessageEntityMentionName):
                user_id = probable_user_mention_entity.user_id
                user_obj = await event.client.get_entity(user_id)
                return user_obj
        try:
            user_obj = await event.client.get_entity(user)
        except (TypeError, ValueError) as err:
            await event.edit(str(err))
            return None

    return user_obj, extra


async def get_userdel_from_id(user, event):
    if isinstance(user, str):
        user = int(user)

    try:
        user_obj = await event.client.get_entity(user)
    except (TypeError, ValueError) as err:
        await event.edit(str(err))
        return None

    return user_obj


@register(outgoing=True, pattern="^.bots(?: |$)(.*)")
async def _(event):
    """ El comando .listbot, enumera todos los bots del chat. """
    if event.fwd_from:
        return
    info = await event.client.get_entity(event.chat_id)
    title = info.title if info.title else "this chat"
    mentions = "**Bots in {} Group**: \n".format(title)
    input_str = event.pattern_match.group(1)
    to_write_chat = await event.get_input_chat()
    chat = None
    if not input_str:
        chat = to_write_chat
    else:
        try:
            chat = await bot.get_entity(input_str)
        except Exception as e:
            await event.edit(str(e))
            return None
    try:
        async for x in bot.iter_participants(chat, filter=ChannelParticipantsBots):
            if isinstance(x.participant, ChannelParticipantAdmin):
                mentions += "\n 👑 [{}](tg://user?id={}) `{}`".format(
                    x.first_name, x.id, x.id
                )
            else:
                mentions += "\n [{}](tg://user?id={}) `{}`".format(
                    x.first_name, x.id, x.id
                )
    except Exception as e:
        mentions += " " + str(e) + "\n"
    await event.edit(mentions)


CMD_HELP.update(
    {
        "admin": ".promote <username/reply> <custom rank (optional)>\
\nUo: Proporciona derechos de administrador a la persona en el chat.\
\n\n.demote <username/reply>\
\nUso: Revoca los permisos de administrador de la persona en el chat.\
\n\n.ban <username/reply> <reason (optional)>\
\nUso: Bloquea a la persona de tu chat.\
\n\n.unban <username/reply>\
\nUso: Elimina la prohibición de la persona en el chat..\
\n\n.mute <username/reply> <reason (optional)>\
\nUso: Silencia a la persona en el chat, también funciona con administradores.\
\n\n.unmute <username/reply>\
\nUso: Elimina a la persona de la lista silenciada.\
\n\n.gmute <username/reply> <reason (optional)>\
\nUso: Silencia a la persona en todos los grupos que tiene en común con ella.\
\n\n.ungmute <username/reply>\
\nUso: Responda el mensaje de alguien con .ungmute para eliminarlo de la lista gmuted.\
\n\n.zombies\
\nUso: Busca cuentas eliminadas en un grupo. Use .zombies clean para eliminar cuentas eliminadas del grupo.\
\n\n.all\
\nUso: Etiqueta a todos los miembros en el chat .\
\n\n.admins\
\nUso: Recupera una lista de administradores en el chat..\
\n\n.bots\
\nUso: Recupera una lista de bots en el chat..\
\n\n.users or .users <name of member>\
\nUso: Recupera a todos los usuarios en el chat.\
\n\n.setgppic <reply to image>\
\nUso: Cambia la imagen de perfil del grupo."
    }
)
