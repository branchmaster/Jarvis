# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Módulo de userbot que contiene comandos id de usuario, id de chat y log"""

from asyncio import sleep

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP, bot
from userbot.events import register
from userbot.modules.admin import get_user_from_event


@register(outgoing=True, pattern="^.userid$")
async def useridgetter(target):
    """ El comando .userid, devuelve el ID del usuario de destino. """
    message = await target.get_reply_message()
    if message:
        if not message.forward:
            user_id = message.sender.id
            if message.sender.username:
                name = "@" + message.sender.username
            else:
                name = "**" + message.sender.first_name + "**"
        else:
            user_id = message.forward.sender.id
            if message.forward.sender.username:
                name = "@" + message.forward.sender.username
            else:
                name = "*" + message.forward.sender.first_name + "*"
        await target.edit("**Name:** {} \n**User ID:** `{}`".format(name, user_id))


@register(outgoing=True, pattern="^.link(?: |$)(.*)")
async def permalink(mention):
    """ El comando .link, genera un enlace al PM del usuario con un texto personalizado. """
    user, custom = await get_user_from_event(mention)
    if not user:
        return
    if custom:
        await mention.edit(f"[{custom}](tg://user?id={user.id})")
    else:
        tag = (
            user.first_name.replace("\u2060", "") if user.first_name else user.username
        )
        await mention.edit(f"[{tag}](tg://user?id={user.id})")


@register(outgoing=True, pattern="^.chatid$")
async def chatidgetter(chat):
    """ El comando .chatid, devuelve el ID del chat en el que se encuentra en ese momento. """
    await chat.edit("Chat ID: `" + str(chat.chat_id) + "`")


@register(outgoing=True, pattern=r"^.log(?: |$)([\s\S]*)")
async def log(log_text):
    """ El comando .log, reenvía un mensaje o el argumento del comando al grupo de registros del bot """
    if BOTLOG:
        if log_text.reply_to_msg_id:
            reply_msg = await log_text.get_reply_message()
            await reply_msg.forward_to(BOTLOG_CHATID)
        elif log_text.pattern_match.group(1):
            user = f"#LOG / Chat ID: {log_text.chat_id}\n\n"
            textx = user + log_text.pattern_match.group(1)
            await bot.send_message(BOTLOG_CHATID, textx)
        else:
            await log_text.edit("`¿Qué se supone que debo registrar??`")
            return
        await log_text.edit("`Registrado exitosamente`")
    else:
        await log_text.edit("`Esta función requiere que el registro esté habilitado!`")
    await sleep(2)
    await log_text.delete()


@register(outgoing=True, pattern="^.kickme$")
async def kickme(leave):
    """ Básicamente es el comando .kickme """
    await leave.edit("Me voy de aquí")
    await leave.client.kick_participant(leave.chat_id, "me")


@register(outgoing=True, pattern="^.unmutechat$")
async def unmute_chat(unm_e):
    """ El comando .unmutechat, reactivar un chat silenciado. """
    try:
        from userbot.modules.sql_helper.keep_read_sql import unkread
    except AttributeError:
        await unm_e.edit("`Non-SQL Mode!`")
        return
    unkread(str(unm_e.chat_id))
    await unm_e.edit("```Se activó el sonido de este chat con éxito```")
    await sleep(2)
    await unm_e.delete()


@register(outgoing=True, pattern="^.mutechat$")
async def mute_chat(mute_e):
    """ El comando .mutechat, silencia cualquier chat. """
    try:
        from userbot.modules.sql_helper.keep_read_sql import kread
    except AttributeError:
        await mute_e.edit("`Non-SQL mode!`")
        return
    await mute_e.edit(str(mute_e.chat_id))
    kread(str(mute_e.chat_id))
    await mute_e.edit("`Shht..! Este chat será silenciado!`")
    await sleep(2)
    await mute_e.delete()
    if BOTLOG:
        await mute_e.client.send_message(
            BOTLOG_CHATID, str(mute_e.chat_id) + " was silenced."
        )


@register(incoming=True, disable_errors=True)
async def keep_read(message):
    """ The mute logic. """
    try:
        from userbot.modules.sql_helper.keep_read_sql import is_kread
    except AttributeError:
        return
    kread = is_kread()
    if kread:
        for i in kread:
            if i.groupid == str(message.chat_id):
                await message.client.send_read_acknowledge(message.chat_id)


# Regex-Ninja module by @Kandnub
regexNinja = False


@register(outgoing=True, pattern="^s/")
async def sedNinja(event):
    """Para el módulo regex-ninja, comando de borrado automático que comienza con s/"""
    if regexNinja:
        await sleep(0.5)
        await event.delete()


@register(outgoing=True, pattern="^.regexninja (on|off)$")
async def sedNinjaToggle(event):
    """ Enables or disables the regex ninja module. """
    global regexNinja
    if event.pattern_match.group(1) == "encendido":
        regexNinja = True
        await event.edit("`Modo ninja habilitado con éxito para Regexbot.`")
        await sleep(1)
        await event.delete()
    elif event.pattern_match.group(1) == "apagado":
        regexNinja = False
        await event.edit("`Modo ninja desactivado con éxito para Regexbot.`")
        await sleep(1)
        await event.delete()


CMD_HELP.update(
    {
        "chat": ".chatid\
\nUso: Fetches the current chat's ID\
\n\n.userid\
\nUso: Obtiene el ID del usuario en respuesta, si es un mensaje reenviado, encuentra el ID de la fuente.\
\n\n.log\
\nUso: Reenvía el mensaje que ha respondido en su grupo de registros de bot.\
\n\n.kickme\
\nUso: Salir de un grupo objetivo.\
\n\n.unmutechat\
\nUso: Activa un chat silenciado.\
\n\n.mutechat\
\nUso: Te permite silenciar cualquier chat.\
\n\n.link <username/userid> : <texto opcional> o responder al mensaje de alguien con .link <texto opcional>\
\nUso: Genera un enlace permanente al perfil del usuario con texto personalizado opcional.\
\n\n.regexninja on/off\
\nUso: Habilitar / deshabilitar globalmente el módulo regex ninja.\
\nRegex El módulo Ninja ayuda a eliminar los mensajes de activación del bot de expresiones regulares."
    }
)
