from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from solidAPI import emoji

from base.player import player
from utils.pyro_utils import music_result
from solidAPI.chat import set_lang, add_chat
from solidAPI.other import get_message
from pyrogram import Client, filters


def play_next_keyboard(user_id: int):
    i = 5
    for j in range(5):
        i += 1
        yield InlineKeyboardButton(f"{i}", callback_data=f"nextplay {j}|{user_id}")
        j += 1


def play_back_keyboard(user_id: int):
    i = 0
    for j in range(5):
        i += 1
        yield InlineKeyboardButton(f"{i}", callback_data=f"play {j}|{user_id}")
        j += 1


def res_music(k, music, bot_username):
    results = "\n"
    for i in music:
        k += 1
        results += f"{k}. [{i['title'][:35]}...]({i['url']})\n"
        results += f"┣ {emoji.LIGHT_BULB} duration - {i['duration']}\n"
        results += f"┣ {emoji.FIRE} [More Information](https://t.me/{bot_username}?start=ytinfo_{i['id']})\n"
        results += "┗ powered by solid project\n\n"
    return results


async def edit_inline_text(
        inline_board,
        temp,
        keyboard,
        cb,
        user_id,
        stats,
        k,
        music,
        bot_username
):
    results = res_music(k, music, bot_username)
    for count, j in enumerate(inline_board, start=1):
        temp.append(j)
        if count % 3 == 0:
            keyboard.append(temp)
            temp = []
        if count == len(inline_board):
            keyboard.append(temp)
    await cb.edit_message_text(
        f"{results}", reply_markup=InlineKeyboardMarkup(
            [
                keyboard[0],
                keyboard[1],
                [
                    InlineKeyboardButton(f"next {emoji.RIGHT_ARROW}", f"next|{user_id}") if
                    stats == "next" else
                    InlineKeyboardButton(f"back {emoji.LEFT_ARROW}", callback_data=f"back|{user_id}"),
                    InlineKeyboardButton(f"close {emoji.WASTEBASKET}", f"close|{user_id}")
                ]
            ]
        ),
        disable_web_page_preview=True
    )


@Client.on_callback_query(filters.regex(pattern=r"close"))
async def close_button(_, cb: CallbackQuery):
    callback = cb.data.split("|")
    user_id = int(callback[1])
    message = cb.message
    from_user_id = cb.from_user.id
    chat_id = message.chat.id
    person = await message.chat.get_member(from_user_id)
    if from_user_id != user_id:
        return await cb.answer("this is not for you.", show_alert=True)
    music_result[chat_id].clear()
    if person.status in ["creator", "administrator"]:
        return await message.delete()
    return await message.delete()


@Client.on_callback_query(filters.regex(pattern=r"cls"))
async def close_private_button(_, cb: CallbackQuery):
    return await cb.message.delete()


@Client.on_callback_query(filters.regex(pattern=r"set_lang_(.*)"))
async def change_language_(_, cb: CallbackQuery):
    lang = cb.matches[0].group(1)
    chat = cb.message.chat
    try:
        set_lang(chat.id, lang)
        await cb.edit_message_text(get_message(chat.id, "lang_changed"))
    except KeyError:
        add_chat(chat.id, lang)
        await cb.edit_message_text(get_message(chat.id, "lang_changed"))


@Client.on_callback_query(filters.regex(pattern=r"(.*)play"))
async def play_music(_, cb: CallbackQuery):
    match = cb.matches[0].group(1)
    data = cb.data.split("|")
    user_id = int(data[1])
    index = int(data[0].split(" ")[1])
    chat_id = cb.message.chat.id
    from_id = cb.from_user.id
    if from_id != user_id:
        return await cb.answer("this is not for u", show_alert=True)
    if not match:
        music = music_result[chat_id][0]
        title: str = music[index]["title"]
        uri: str = music[index]["url"]
        result = {
            "title": title,
            "uri": uri
        }

        music_result[chat_id].clear()
        await player.play(cb, result)
    if match:
        music = music_result[chat_id][1]
        title: str = music[index]["title"]
        uri: str = music[index]["url"]
        result = {
            "title": title,
            "uri": uri
        }
        music_result[chat_id].clear()
        await player.play(cb, result)


@Client.on_callback_query(filters.regex(pattern=r"next"))
async def next_music_(client: Client, cb: CallbackQuery):
    bot_username = (await client.get_me()).username
    user_id = int(cb.data.split("|")[1])
    chat_id = cb.message.chat.id
    music = music_result[chat_id][1]
    from_id = cb.from_user.id
    if from_id != user_id:
        return await cb.answer("you not allowed", show_alert=True)

    k = 5
    temp = []
    keyboard = []
    inline_board = list(play_next_keyboard(user_id))
    await edit_inline_text(inline_board, temp, keyboard, cb, user_id, "back", k, music, bot_username)


@Client.on_callback_query(filters.regex(pattern=r"back"))
async def back_music_(client: Client, cb: CallbackQuery):
    bot_username = (await client.get_me()).username
    user_id = int(cb.data.split("|")[1])
    chat_id = cb.message.chat.id
    music = music_result[chat_id][0]
    k = 0
    temp = []
    keyboard = []
    inline_board = list(play_back_keyboard(user_id))
    await edit_inline_text(inline_board, temp, keyboard, cb, user_id, "next", k, music, bot_username)
