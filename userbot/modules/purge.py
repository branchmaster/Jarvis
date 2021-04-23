# Copyright (C) 2019 The Raphielscape Company LLC.
#
# Licensed under the Raphielscape Public License, Version 1.d (the "License");
# you may not use this file except in compliance with the License.
#
""" Userbot module for purging unneeded messages(usually spam or ot). """

from asyncio import sleep

from telethon.errors import rpcbaseerrors

from userbot import BOTLOG, BOTLOG_CHATID, CMD_HELP
from userbot.events import register


@register(outgoing=True, pattern="^.purge$")
async def fastpurger(purg):
    """ El comando .purge, borra todos los mensajes a partir de la respuesta. """
    chat = await purg.get_input_chat()
    msgs = []
    itermsg = purg.client.iter_messages(chat, min_id=purg.reply_to_msg_id)
    count = 0

    if purg.reply_to_msg_id is not None:
        async for msg in itermsg:
            msgs.append(msg)
            count = count + 1
            msgs.append(purg.reply_to_msg_id)
            if len(msgs) == 100:
                await purg.client.delete_messages(chat, msgs)
                msgs = []
    else:
        await purg.edit("`Necesito un mesaje para empezar a purgar.`")
        return

    if msgs:
        await purg.client.delete_messages(chat, msgs)
    done = await purg.client.send_message(
        purg.chat_id,
        f"`Fast purge complete!`\
        \nPurged {str(count)} messages",
    )

    if BOTLOG:
        await purg.client.send_message(
            BOTLOG_CHATID, "Purga de " + str(count) + " mensajes realizados con éxito."
        )
    await sleep(2)
    await done.delete()

@register(outgoing=True, pattern="^.purgeme")
async def purgeme(delme):
    """ El comando .purgeme, elimina x mensajes que tu enviaste."""
    message = delme.text
    count = int(message[9:])
    i = 1

    async for message in delme.client.iter_messages(delme.chat_id, from_user="me"):
        if i > count + 1:
            break
        i = i + 1
        await message.delete()

    smsg = await delme.client.send_message(
        delme.chat_id,
        "`Purga completa!` " + str(count) + " mensajes borrados.",
    )
    if BOTLOG:
        await delme.client.send_message(
            BOTLOG_CHATID, "Purga de " + str(count) + " mensajes realizada con exito."
        )
    await sleep(2)
    i = 1
    await smsg.delete()


@register(outgoing=True, pattern="^.del$")
async def delete_it(delme):
    """ El comando .del, elimina el mensaje respondido. """
    msg_src = await delme.get_reply_message()
    if delme.reply_to_msg_id:
        try:
            await msg_src.delete()
            await delme.delete()
            if BOTLOG:
                await delme.client.send_message(
                    BOTLOG_CHATID, "La eliminación del mensaje se realizó correctamente"
                )
        except rpcbaseerrors.BadRequestError:
            if BOTLOG:
                await delme.client.send_message(
                    BOTLOG_CHATID, "Bueno, no puedo borrar el mensaje"
                )


    
CMD_HELP.update(
    {
        "purge": ".purge\
        \nUso: Elimina todos los mensajes a partir de la respuesta."
    }
)

CMD_HELP.update(
    {
        "purgeme": ".purgeme <x>\
        \nUso: Elimina x cantidad de sus últimos mensajes."
    }
)

CMD_HELP.update(
    {
        "del": ".del\
        \nUso: Elimina el mensaje al que respondiste."
    }
)
