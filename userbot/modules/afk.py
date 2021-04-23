# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module which contains afk-related commands """

import time
from datetime import datetime
from random import choice, randint

from telethon.events import StopPropagation

from userbot import (
    AFKREASON,
    COUNT_MSG,
    CMD_HELP,
    ISAFK,
    BOTLOG,
    BOTLOG_CHATID,
    USERS,
    PM_AUTO_BAN)  # pylint: disable=unused-imports

from userbot.events import register

# ========================= CONSTANTS ============================
AFKSTR = [
    "Estoy AFK ahora",
]

global USER_AFK  # pylint:disable=E0602
global afk_time  # pylint:disable=E0602
global afk_start
global afk_end
USER_AFK = {}
afk_time = None
afk_start = {}

# =================================================================


@register(outgoing=True, pattern="^.afk(?: |$)(.*)", disable_errors=True)
async def set_afk(afk_e):
    """ el comando .afk, le permite informar a las personas que está afk cuando le envían un mensaje """
    afk_e.text
    string = afk_e.pattern_match.group(1)
    global ISAFK
    global AFKREASON
    global USER_AFK  # pylint:disable=E0602
    global afk_time  # pylint:disable=E0602
    global afk_start
    global afk_end
    global reason
    USER_AFK = {}
    afk_time = None
    afk_end = {}
    start_1 = datetime.now()
    afk_start = start_1.replace(microsecond=0)
    if string:
        AFKREASON = string
        await afk_e.edit(
            f"Estoy AFK!\
        \nMotivo: `{string}`"
        )
    else:
        await afk_e.edit("Me voy de aquí!")
    if BOTLOG:
        await afk_e.client.send_message(BOTLOG_CHATID, "#AFK\nEstas AFK!")
    ISAFK = True
    afk_time = datetime.now()  # pylint:disable=E0602
    raise StopPropagation


@register(outgoing=True)
async def type_afk_is_not_true(notafk):
    """ Esto establece su estado como no afk automáticamente cuando escribe algo mientras está afk """
    global ISAFK
    global COUNT_MSG
    global USERS
    global AFKREASON
    global USER_AFK  # pylint:disable=E0602
    global afk_time  # pylint:disable=E0602
    global afk_start
    global afk_end
    back_alive = datetime.now()
    afk_end = back_alive.replace(microsecond=0)
    if ISAFK:
        ISAFK = False
        msg = await notafk.respond("ㅤ")
        time.sleep(0)
        await msg.delete()
        if BOTLOG:
            await notafk.client.send_message(
                BOTLOG_CHATID,
                "Recibiste "
                + str(COUNT_MSG)
                + " mensajes de "
                + str(len(USERS))
                + " chats cuando estabas AFK",
            )
            for i in USERS:
                if str(i).isnumeric():
                    name = await notafk.client.get_entity(i)
                    name0 = str(name.first_name)
                    await notafk.client.send_message(
                        BOTLOG_CHATID,
                        "[" + name0 + "](tg://user?id=" + str(i) + ")" +
                        " te envio " + "`" + str(USERS[i]) + " mensaje(s)`",
                    )
                else:  # anon admin
                    await notafk.client.send_message(
                        BOTLOG_CHATID,
                        "Admin anonimo en `" + i + "` te envio " + "`" +
                        str(USERS[i]) + " mensaje(s)`",
                    )
        COUNT_MSG = 0
        USERS = {}
        AFKREASON = None


@register(incoming=True, disable_edited=True)
async def mention_afk(mention):
    """ Esta función se encarga de notificar a las personas que te mencionan que estás AFK."""
    global COUNT_MSG
    global USERS
    global ISAFK
    global USER_AFK  # pylint:disable=E0602
    global afk_time  # pylint:disable=E0602
    global afk_start
    global afk_end
    back_alivee = datetime.now()
    afk_end = back_alivee.replace(microsecond=0)
    afk_since = "Hace "
    if ISAFK and mention.message.mentioned:
            now = datetime.now()
            datime_since_afk = now - afk_time  # pylint:disable=E0602
            time = float(datime_since_afk.seconds)
            days = time // (24 * 3600)
            time = time % (24 * 3600)
            hours = time // 3600
            time %= 3600
            minutes = time // 60
            time %= 60
            seconds = time
            if days == 1:
                afk_since = "Ayer"
            elif days > 1:
                if days > 6:
                    date = now + datetime.timedelta(
                        days=-days, hours=-hours, minutes=-minutes
                    )
                    afk_since = date.strftime("%A, %Y %B %m, %H:%I")
                else:
                    wday = now + datetime.timedelta(days=-days)
                    afk_since = wday.strftime("%A")
            elif hours > 1:
                afk_since = f"`{int(hours)}h{int(minutes)}m`"
            elif minutes > 0:
                afk_since = f"`{int(minutes)}m{int(seconds)}s`"
            else:
                afk_since = f"`{int(seconds)}s`"
            
            is_bot = False
            if (sender := await mention.get_sender()):
                is_bot = sender.bot
                if is_bot: return  # ignore bot

            chat_obj = await mention.client.get_entity(mention.chat_id)
            chat_title = chat_obj.title

            if mention.sender_id not in USERS or chat_title not in USERS:
                if AFKREASON:
                    await mention.reply(
                        f"Estoy AFK hace {afk_since}.\
                        \nMotivo: `{AFKREASON}`"
                    )
                else:
                    await mention.reply(str(choice(AFKSTR)))
                if mention.sender_id is not None:
                    USERS.update({mention.sender_id: 1})
                else:
                    USERS.update({chat_title: 1})
            else:
                if USERS[mention.sender_id] % randint(2, 4) == 0:
                    if AFKREASON:
                        await mention.reply(
                            f"Estoy AFK hace {afk_since}.\
                            \nMotivo: `{AFKREASON}`"
                        )
                    else:
                        await mention.reply(str(choice(AFKSTR)))
                    if mention.sender_id is not None:
                        USERS[mention.sender_id] += 1
                    else:
                        USERS[chat_title] += 1
                COUNT_MSG += 1


@register(incoming=True, disable_errors=True)
async def afk_on_pm(sender):
    """ Función que informa a las personas que estás AFK en PM """
    global ISAFK
    global USERS
    global COUNT_MSG
    global COUNT_MSG
    global USERS
    global ISAFK
    global USER_AFK  # pylint:disable=E0602
    global afk_time  # pylint:disable=E0602
    global afk_start
    global afk_end
    back_alivee = datetime.now()
    afk_end = back_alivee.replace(microsecond=0)
    afk_since = "Hace"
    if (
        sender.is_private
        and sender.sender_id != 777000
        and not (await sender.get_sender()).bot
    ):
        if PM_AUTO_BAN:
            try:
                from userbot.modules.sql_helper.pm_permit_sql import is_approved

                apprv = is_approved(sender.sender_id)
            except AttributeError:
                apprv = True
        else:
            apprv = True
        if apprv and ISAFK:
            now = datetime.now()
            datime_since_afk = now - afk_time  # pylint:disable=E0602
            time = float(datime_since_afk.seconds)
            days = time // (24 * 3600)
            time = time % (24 * 3600)
            hours = time // 3600
            time %= 3600
            minutes = time // 60
            time %= 60
            seconds = time
            if days == 1:
                afk_since = "Ayer"
            elif days > 1:
                if days > 6:
                    date = now + datetime.timedelta(
                        days=-days, hours=-hours, minutes=-minutes
                    )
                    afk_since = date.strftime("%A, %Y %B %m, %H:%I")
                else:
                    wday = now + datetime.timedelta(days=-days)
                    afk_since = wday.strftime("%A")
            elif hours > 1:
                afk_since = f"`{int(hours)}h{int(minutes)}m`"
            elif minutes > 0:
                afk_since = f"`{int(minutes)}m{int(seconds)}s`"
            else:
                afk_since = f"`{int(seconds)}s`"
            if sender.sender_id not in USERS:
                if AFKREASON:
                    await sender.reply(
                        f"Estoy AFK hace {afk_since}.\
                        \nMotivo: `{AFKREASON}`"
                    )
                else:
                    await sender.reply(str(choice(AFKSTR)))
                USERS.update({sender.sender_id: 1})
                COUNT_MSG = COUNT_MSG + 1
            elif apprv and sender.sender_id in USERS:
                if USERS[sender.sender_id] % randint(2, 4) == 0:
                    if AFKREASON:
                        await sender.reply(
                            f"Estoy AFK hace {afk_since}.\
                            \nMotivo: `{AFKREASON}`"
                        )
                    else:
                        await sender.reply(str(choice(AFKSTR)))
                    USERS[sender.sender_id] = USERS[sender.sender_id] + 1
                    COUNT_MSG = COUNT_MSG + 1
                else:
                    USERS[sender.sender_id] = USERS[sender.sender_id] + 1
                    COUNT_MSG = COUNT_MSG + 1


CMD_HELP.update(
    {
        "afk": ".afk [Motivo opcional]\
\nUsage: Lo establece como afk.\nResponde a cualquier persona que lo etiquete/PM's \
les dices que estás AFK (Motivo).\n\nApaga AFK cuando escribe cualquier cosa, en cualquier lugar.\
"
    }
)
