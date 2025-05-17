from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMIN_IDS
from users_db import get_all_user_ids

import asyncio

router = Router()

class BroadcastState(StatesGroup):
    waiting_for_text = State()
    waiting_for_media_choice = State()
    waiting_for_photo = State()
    waiting_for_video_note = State()
    waiting_for_button_text = State()
    waiting_for_button_url = State()
    confirming = State()
    waiting_for_additional_broadcast = State()
    waiting_for_delay_minutes = State()

@router.message(F.text == "/broadcast")
async def start_broadcast(msg: Message, state: FSMContext):
    if msg.from_user.id not in ADMIN_IDS:
        await msg.answer("У вас нет прав для этой команды.")
        return
    await state.clear()
    await state.update_data(broadcasts=[])
    await msg.answer(
        "<b>Начинаем создание рассылки.</b>\n\n"
        "Пожалуйста, отправьте текст рассылки.\n\n"
        "Пример HTML-разметки для рассылки (пишите именно так):\n"
        "<pre>"
        "&lt;b&gt;Жирный текст&lt;/b&gt; — жирный шрифт\n"
        "&lt;i&gt;Курсив&lt;/i&gt; — курсив\n"
        "&lt;u&gt;Подчёркнутый&lt;/u&gt; — подчёркивание\n"
        "&lt;s&gt;Зачёркнутый&lt;/s&gt; — зачёркнутый текст\n"
        "&lt;a href=&quot;URL&quot;&gt;Ссылка&lt;/a&gt; — гиперссылка\n"
        "&lt;tg-spoiler&gt;Текст&lt;/tg-spoiler&gt; — спойлер\n"
        "&lt;blockquote&gt;Цитата&lt;/blockquote&gt; — текст в цитате\n"
        "</pre>\n\n"
        "<b>Отправьте /cancel для отмены в любой момент.</b>",
        parse_mode="HTML"
    )
    await state.set_state(BroadcastState.waiting_for_text)

@router.message(F.text == "/cancel")
async def cancel_broadcast(msg: Message, state: FSMContext):
    await state.clear()
    await msg.answer("<b>Рассылка отменена.</b>")

@router.message(F.text == "/help")
async def admin_help(msg: Message):
    if msg.from_user.id not in ADMIN_IDS:
        return
    await msg.answer(
        "Доступные команды:\n\n"
        "/broadcast - создать автоматическую рассылку пользователям.\n"
        "/help - показать это сообщение."
    )

@router.message(BroadcastState.waiting_for_text)
async def get_text(msg: Message, state: FSMContext):
    if msg.text == "/cancel":
        await cancel_broadcast(msg, state)
        return

    # Сохраняем text и entities (форматирование)
    await state.update_data(current_broadcast={
        'text': msg.text or "",
        'entities': msg.entities or []
    })

    await msg.answer(
        "<b>Хотите прикрепить изображение или «кружок»?</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Фото", callback_data="photo"),
             InlineKeyboardButton(text="Кружок", callback_data="video_note")],
            [InlineKeyboardButton(text="Нет", callback_data="no_media")]
        ])
    )
    await state.set_state(BroadcastState.waiting_for_media_choice)

@router.callback_query(BroadcastState.waiting_for_media_choice)
async def media_choice(call: CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()
    current_broadcast = data.get('current_broadcast', {})

    if call.data == "photo":
        await call.message.answer("<b>Отправьте фото.</b>")
        await state.set_state(BroadcastState.waiting_for_photo)
    elif call.data == "video_note":
        await call.message.answer("<b>Отправьте кружок (видео note).</b>")
        await state.set_state(BroadcastState.waiting_for_video_note)
    else:
        # no media
        await state.update_data(current_broadcast=current_broadcast)
        await ask_for_button(call.message, state)

@router.message(BroadcastState.waiting_for_photo, F.photo)
async def get_photo(msg: Message, state: FSMContext):
    data = await state.get_data()
    current_broadcast = data.get('current_broadcast', {})
    current_broadcast['photo'] = msg.photo[-1].file_id
    await state.update_data(current_broadcast=current_broadcast)
    await ask_for_button(msg, state)

@router.message(BroadcastState.waiting_for_video_note, F.video_note)
async def get_video_note(msg: Message, state: FSMContext):
    data = await state.get_data()
    current_broadcast = data.get('current_broadcast', {})
    current_broadcast['video_note'] = msg.video_note.file_id
    await state.update_data(current_broadcast=current_broadcast)
    await ask_for_button(msg, state)

async def ask_for_button(msg_or_call, state: FSMContext):
    await msg_or_call.answer(
        "<b>Хотите добавить кнопку со ссылкой?</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="yes_button"),
             InlineKeyboardButton(text="Нет", callback_data="no_button")]
        ])
    )
    await state.set_state(BroadcastState.waiting_for_button_text)

@router.callback_query(F.data == "yes_button")
async def button_yes(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await call.message.answer("<b>Введите текст для кнопки:</b>")
    await state.set_state(BroadcastState.waiting_for_button_text)

@router.callback_query(F.data == "no_button")
async def button_no(call: CallbackQuery, state: FSMContext):
    await call.answer()
    await save_current_broadcast_and_ask_additional(call.message, state)

@router.message(BroadcastState.waiting_for_button_text)
async def button_text(msg: Message, state: FSMContext):
    if msg.text == "/cancel":
        await cancel_broadcast(msg, state)
        return

    data = await state.get_data()
    current_broadcast = data.get('current_broadcast', {})

    current_broadcast['button_text'] = msg.text
    await state.update_data(current_broadcast=current_broadcast)

    await msg.answer(
        "<b>Теперь введите ссылку.</b>\n\n"
        "Поддерживаются ссылки на каналы/сайты/чаты.\n"
        "Также ссылки формата: www.domain, для перехода в личные сообщения - t.me/юзернейм (БЕЗ @)."
    )
    await state.set_state(BroadcastState.waiting_for_button_url)

@router.message(BroadcastState.waiting_for_button_url)
async def button_url(msg: Message, state: FSMContext):
    if msg.text == "/cancel":
        await cancel_broadcast(msg, state)
        return

    data = await state.get_data()
    current_broadcast = data.get('current_broadcast', {})
    current_broadcast['button_url'] = msg.text
    await state.update_data(current_broadcast=current_broadcast)

    await save_current_broadcast_and_ask_additional(msg, state)

async def save_current_broadcast_and_ask_additional(msg_or_call, state: FSMContext):
    data = await state.get_data()
    current_broadcast = data.get('current_broadcast', {})
    broadcasts = data.get('broadcasts', [])

    broadcasts.append(current_broadcast)
    await state.update_data(broadcasts=broadcasts)
    await state.update_data(current_broadcast={})

    await show_preview_for_broadcast(msg_or_call, current_broadcast)

    if len(broadcasts) >= 2:
        await msg_or_call.answer(
            "<b>Максимум 2 рассылки. Отправить рассылки сейчас или отложить?</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Сейчас", callback_data="confirm_send")],
                [InlineKeyboardButton(text="Отложить", callback_data="delay_send")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_send")]
            ])
        )
        await state.set_state(BroadcastState.confirming)
        return

    await msg_or_call.answer(
        "<b>Хотите добавить ещё одну рассылку?</b>",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Да", callback_data="add_more_yes"),
             InlineKeyboardButton(text="Нет", callback_data="add_more_no")]
        ])
    )
    await state.set_state(BroadcastState.waiting_for_additional_broadcast)

async def show_preview_for_broadcast(msg_or_call, broadcast):
    keyboard = None
    if 'button_text' in broadcast and 'button_url' in broadcast:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=broadcast['button_text'], url=broadcast['button_url'])]
        ])

    await msg_or_call.answer("\U0001F4E2 Предпросмотр рассылки:")

    if 'photo' in broadcast:
        # Отправляем фото с caption и entities
        await msg_or_call.answer_photo(
            photo=broadcast['photo'],
            caption=broadcast['text'],
            caption_entities=broadcast.get('entities'),
            reply_markup=keyboard
        )
    elif 'video_note' in broadcast:
        await msg_or_call.answer_video_note(
            video_note=broadcast['video_note'],
            reply_markup=keyboard
        )
    else:
        await msg_or_call.answer(
            broadcast['text'],
            entities=broadcast.get('entities'),
            reply_markup=keyboard
        )

@router.callback_query(BroadcastState.waiting_for_additional_broadcast)
async def additional_broadcast_decision(call: CallbackQuery, state: FSMContext):
    await call.answer()
    if call.data == "add_more_yes":
        await call.message.answer(
            "<b>Пожалуйста, отправьте текст второй рассылки.</b>\n"
            "<b>Отправьте /cancel для отмены.</b>"
        )
        await state.set_state(BroadcastState.waiting_for_text)
    elif call.data == "add_more_no":
        await call.message.answer(
            "<b>Отправить рассылку сейчас или через определённое количество минут?</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="Сейчас", callback_data="confirm_send")],
                [InlineKeyboardButton(text="Отложить", callback_data="delay_send")],
                [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_send")]
            ])
        )
        await state.set_state(BroadcastState.confirming)

@router.callback_query(BroadcastState.confirming)
async def confirm_broadcast(call: CallbackQuery, state: FSMContext):
    await call.answer()
    if call.data == "cancel_send":
        await state.clear()
        await call.message.edit_text("<b>Рассылка отменена.</b>")
        return

    if call.data == "delay_send":
        await call.message.answer("<b>Через сколько минут отправить рассылку?</b>")
        await state.set_state(BroadcastState.waiting_for_delay_minutes)
        return

    if call.data == "confirm_send":
        await perform_broadcast(call.message, state)

@router.message(BroadcastState.waiting_for_delay_minutes)
async def delay_minutes(msg: Message, state: FSMContext):
    if msg.text == "/cancel":
        await cancel_broadcast(msg, state)
        return

    try:
        delay = int(msg.text)
        await msg.answer(f"Рассылка будет отправлена через {delay} минут.")
        await asyncio.sleep(delay * 60)
        await perform_broadcast(msg, state)
    except ValueError:
        await msg.answer("Пожалуйста, введите число — количество минут.")


async def perform_broadcast(msg_or_call, state: FSMContext):
    data = await state.get_data()
    broadcasts = data.get('broadcasts', [])
    users = await get_all_user_ids()

    count = 0
    for broadcast in broadcasts:
        keyboard = None
        if 'button_text' in broadcast and 'button_url' in broadcast:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=broadcast['button_text'], url=broadcast['button_url'])]
            ])

        for user_id in users:
            try:
                if 'photo' in broadcast:
                    await msg_or_call.bot.send_photo(
                        chat_id=user_id,
                        photo=broadcast['photo'],
                        caption=broadcast['text'],
                        caption_entities=broadcast.get('entities'),
                        reply_markup=keyboard
                    )
                elif 'video_note' in broadcast:
                    await msg_or_call.bot.send_video_note(
                        chat_id=user_id,
                        video_note=broadcast['video_note'],
                        reply_markup=keyboard
                    )
                else:
                    await msg_or_call.bot.send_message(
                        chat_id=user_id,
                        text=broadcast['text'],
                        entities=broadcast.get('entities'),
                        reply_markup=keyboard
                    )
                count += 1
                await asyncio.sleep(0.05)
            except Exception:
                continue

    await msg_or_call.answer(f"<b>Рассылка отправлена {count} пользователям.</b>")
    await state.clear()
