# -*- coding: utf-8 -*-
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import logging
import os
from aiogram.types import InputFile
from openpyxl import load_workbook
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiogram.types import ParseMode
import gettext
_ = gettext.gettext  # Tilni tarjima qilish uchun o'rnatilgan
from database import get_connection, get_region_report_sql, get_regions_sql, get_republic_report_sql, get_total_users_count
from database import add_user  # Postgres'ga ma'lumotlarni saqlash uchun
import importlib
import content_urls
from content_urls import  faq_video_ids, help_video_url, help_text, yotoq_urls, org_urls, personal_urls, surovlar_urls, dispetcher_urls, ombor_urls, news_
from database import get_user_by_id, log_url_action, get_user_from_url_log
import pandas as pd
import asyncio
from aiogram.contrib.middlewares.fsm import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import ReplyKeyboardRemove

# Ro'yxatdan o'tish jarayonida foydalanadigan holatlar
class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()  # To'liq ismni kiritishni kutayotgan holat


TOKEN = '7782043394:AAHi3sEHt8Ok-F1aN6CQySS_TR1uIDi5Dg8'

# MemoryStorage o'rnatish
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(bot, storage=storage)
# Logger middleware
dp.middleware.setup(LoggingMiddleware())
# Parolni saqlash
SECRET_PASSWORD = "Pa$$w0rd2023"

# Loggingni yoqish
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_main_reply_keyboard():
    
    buttons = [
        KeyboardButton("🏠Asosiy menyu"),  # Emoji + matn
        KeyboardButton("❓Savollar"),  # Emoji + matn
        KeyboardButton("📗Yordam"),  # Emoji + matn
        KeyboardButton("📩Yangiliklar"),
        KeyboardButton("📈Foydalanuvchilar soni")

    ]
    return ReplyKeyboardMarkup(resize_keyboard=True).add(*buttons)
    
@dp.message_handler(lambda message: message.text == "📩Yangiliklar")
async def send_news(message: types.Message):
    user_id = message.from_user.id

    # Foydalanuvchini tekshirish (users va url_log jadvallaridan)
    user_in_users = get_user_by_id(user_id)  # users jadvalidan foydalanuvchini izlash
    user_in_url_log = get_user_from_url_log(user_id)  # url_log jadvalidan foydalanuvchini izlash

    if user_in_users is None and user_in_url_log is None:
        # Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa, ro'yxatdan o'tish jarayonini boshlaymiz
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_register = InlineKeyboardButton("🟢Davom etish", callback_data='register')  # Registration button
        button_cancel = InlineKeyboardButton("🔴Bekor qilish", callback_data='cancel')  # Cancel button
        keyboard.add(button_register, button_cancel)
        await message.answer("Siz ro'yxatdan o'tmagansiz yoki bazadan o'chirilgansiz. Ro'yxatdan o'tish uchun 'Davom etish' tugmasini bosing:", reply_markup=keyboard)
    else:
        print("Yangiliklar tugmasi bosildi!")  # Foydalanuvchi tugmani bosganini tekshirish
        await message.answer(news_)  # Yangiliklar matnini yuborish 

# "Users" tugmasi bosilganda foydalanuvchilar sonini ko'rsatish
@dp.message_handler(lambda message: message.text == "📈Foydalanuvchilar soni")
async def send_users_count(message: types.Message):
    user_id = message.from_user.id
    users_count = get_total_users_count()
    # Foydalanuvchini tekshirish (users va url_log jadvallaridan)
    user_in_users = get_user_by_id(user_id)  # users jadvalidan foydalanuvchini izlash
    user_in_url_log = get_user_from_url_log(user_id)  # url_log jadvalidan foydalanuvchini izlash

    if user_in_users is None and user_in_url_log is None:
        # Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa, ro'yxatdan o'tish jarayonini boshlaymiz
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_register = InlineKeyboardButton("🟢Davom etish", callback_data='register')  # Registration button
        button_cancel = InlineKeyboardButton("🔴Bekor qilish", callback_data='cancel')  # Cancel button
        keyboard.add(button_register, button_cancel)
        await message.answer("Siz ro'yxatdan o'tmagansiz yoki bazadan o'chirilgansiz. Ro'yxatdan o'tish uchun 'Davom etish' tugmasini bosing:", reply_markup=keyboard) 
    else:
        # Agar foydalanuvchilar soni to'g'ri o'qilgan bo'lsa
        if isinstance(users_count, int):
            await message.answer(f"📊 Jami foydalanuvchilar soni: {users_count}", reply_markup=get_main_reply_keyboard())
        else:
            # Agar xatolik yuz bersa, foydalanuvchiga xabar berish
            await message.answer(f"❌ Xatolik yuz berdi: {users_count}", reply_markup=get_main_reply_keyboard())

# Ro'yxatdan o'tish jarayonida foydalanadigan holatlar
class RegistrationStates(StatesGroup):
    waiting_for_full_name = State()  # To'liq ismni kiritishni kutayotgan holat
    waiting_for_lavozim = State()  # Lavozimni kiritishni kutayotgan holat
    confirmation = State()  # Tasdiqlash uchun

# Ma'lumotlar saqlash uchun xotira
user_viloyat = {}
user_tuman = {}
user_full_name = {}
user_lavozim = {}
    
# 1. Start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id

    # Foydalanuvchini tekshirish (users va url_log jadvallaridan)
    user_in_users = get_user_by_id(user_id)  # users jadvalidan foydalanuvchini izlash
    user_in_url_log = get_user_from_url_log(user_id)  # url_log jadvalidan foydalanuvchini izlash

    if user_in_users is None and user_in_url_log is None:
        # Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa, ro'yxatdan o'tish jarayonini boshlaymiz
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_register = InlineKeyboardButton("🟢Davom etish", callback_data='register')  # Registration button
        button_cancel = InlineKeyboardButton("🔴Bekor qilish", callback_data='cancel')  # Cancel button
        keyboard.add(button_register, button_cancel)
        await message.answer("Ro'yxatdan o'tish uchun ' Davom etish ' tugmasini bosing:", reply_markup=keyboard)
    else:
        # Agar foydalanuvchi ro'yxatdan o'tgan bo'lsa, asosiy menyuni ko'rsatamiz
        await message.answer("Siz avval ro'yxatdan o'tgansiz.✅\n Botdan foydalana olasiz!:", reply_markup=get_main_reply_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'cancel')
async def cancel_registration(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()  # Delete the "Start" message with buttons

    # Inform the user that the registration process was canceled
    await bot.send_message(user_id, "Ro'yxatdan o'tish jarayoni bekor qilindi. Agar qaytadan ro'yxatdan o'tishni xohlasangiz, /start komandasini bosing.")
    await callback_query.answer()  # Acknowledge the button click

@dp.callback_query_handler(lambda c: c.data == 'register')
async def register(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # Step 1: Ask for the user's region (Viloyat)
    keyboard = InlineKeyboardMarkup(row_width=2)
    button_viloyat = InlineKeyboardButton("Viloyatni tanlang", callback_data='viloyat_select')
    keyboard.add(button_viloyat)

    await callback_query.message.delete()  # Delete the registration prompt message
    await callback_query.message.answer("Ro'yxatdan o'tish jarayonini boshlaymiz. Viloyatingizni tanlang⤵️", reply_markup=keyboard)
    await callback_query.answer()

# 2. Viloyat tanlash
@dp.callback_query_handler(lambda c: c.data == 'viloyat_select')
async def select_viloyat(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()  # Oldingi xabarni o'chirish

    # Viloyatlar ro'yxati
    viloyatlar = ["Toshkent", "Toshkent shahar", "Samarqand", "Andijon", "Buxoro", "Farg'ona",
    "Namangan", "Qashqadaryo", "Sirdaryo", "Jizzax", "Surxandaryo",
    "Xorazim", "Navoiy", "Qorqalpog'iston Respublikasi"]

    keyboard = InlineKeyboardMarkup(row_width=2)
    for viloyat in viloyatlar:
        keyboard.add(InlineKeyboardButton(viloyat, callback_data=f'viloyat_{viloyat}'))
    button_back = InlineKeyboardButton("🔙Orqaga", callback_data='back_to_start')  # "Back" button
    keyboard.add(button_back)

    await bot.send_message(user_id, "Viloyatni tanlang⤵️", reply_markup=keyboard)
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == 'back_to_start')
async def back_to_start(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await callback_query.message.delete()  # Delete the current message with the region selection

    # Send the start menu back to the user
    keyboard = InlineKeyboardMarkup(row_width=2)
    button_register = InlineKeyboardButton("🟢Davom etish", callback_data='register')  # Registration button
    button_cancel = InlineKeyboardButton("🔴Bekor qilish", callback_data='cancel')  # Cancel button
    keyboard.add(button_register, button_cancel)  # Add both buttons to the keyboard

    await bot.send_message(user_id, "Ro'yxatdan o'tish uchun '🟢' tugmasini bosing yoki '🔴' tugmasini bosing:", reply_markup=keyboard)
    await callback_query.answer()  # Acknowledge the "Back" button press

# 3. Tuman tanlash
@dp.callback_query_handler(lambda c: c.data.startswith('viloyat_'))
async def select_tuman(callback_query: types.CallbackQuery):
    viloyat = callback_query.data.split('_')[1]  # Viloyat nomini callback_data dan ajratib olish
    user_id = callback_query.from_user.id
    user_viloyat[user_id] = viloyat  # Foydalanuvchi ID sini viloyat bilan bog'lash

    tumanlar = {
        "Toshkent shahar": ["Yunusobod", "Mirzo Ulugbek", "Mirobod", "Chilonzor", "Shayxontohur", "Sergeli", "Yakkasaroy", "Bektemir", "Yashnobod", "Yangihayot", "Olmazor", "Uchtepa"],
        "Toshkent": ["Angren", "Bekabad", "Buka", "Chinoz", "Jizzax", "Keles", "Olmaliq", "Parkent", "Piskent", "Quyi Chirchiq", "Tashkent", "Yakkabog"],
        "Andijon": ["Andijon", "Asaka", "Buloqboshi", "Jaloliddin Rumi", "Izboskan", "Khanabad", "Kurgan-Tube", "Marhamat", "Pakhtabad", "Shahrixon", "Xonobod", "Ulugnor", "Tursunzoda", "Chust", "Bo'z", "Oltinsoy"],
        "Samarqand": ["Akdarya", "Bulung'ur", "G'allaorol", "Jomboy", "Kattakurgan", "Narpay", "Nurobod", "Oqdarya", "Paxtachi", "Pishpek", "Samarkand", "Toytepa", "Urgut"],
        "Buxoro": ["Buxoro", "G'ijduvon", "Jondor", "Kogon", "Qorako'l", "Romitan", "Shofirkon", "Vobkent"],
        "Farg'ona": ["Farg'ona", "Bag'dod", "Beshariq", "Dang'ara", "Furqat", "Quva", "Oltiariq", "Rishton", "Toshloq", "Yozyovon"],
        "Namangan": ["Namangan", "Chortoq", "Davlatabad", "Kosonsoy", "Mingbuloq", "Nurabad", "Pop", "Tuqaymoyin", "Uchqo'rg'on", "Uychi"],
        "Navoiy": ["Oltintopkan", "Karmana", "Navoiy", "Navbahor", "Tomdi", "Uchquduq", "Zafarobod"],
        "Qashqadaryo": ["Chiroqchi", "Dehqonobod", "G'uzor", "Kasbi", "Muborak", "Nishon", "Shahrisabz", "Yakkabog'"],
        "Sirdaryo": ["Baxt", "Guliston", "Miriqech", "Sardoba", "Sirdaryo", "Yangiyer"],
        "Jizzax": ["Arnasoy", "Baxmal", "Jizzax", "Zafarobod", "Sharaf Rashidov", "Yangiobod", "Pakhtakor", "Dashtobod", "Samarqand"],
        "Surxandaryo": ["Angor", "Boysun", "Denov", "Jarqo'rg'on", "Muzrobod", "Oltinsoy", "Sariosiyo", "Sangzor", "Shahrisabz", "Termiz", "Uzun", "Sherobod", "Kizirik"],
        "Xorazim": ["Bog'ot", "Gurlan", "Hazorasp", "Xonqa", "Shovot", "Urganch", "Yangibozor", "Yangiariq", "Jazirat", "Xiva"],
        "Qorqalpog'iston Respublikasi": ["Amudaryo", "Beruniy", "Bo'zatov", "Ellikqal'a", "Kegeyli", "Qanliko'l", "Qo'ng'irot", "Qorauzak", "Shumanay", "Turtkul", "Xo'jayli", "Shahrisabz", "Nukus", "Chimboy", "Muynak", "Toshkent", "Xiva", "Urgench", "Shahrixon", "Tog'oq"]
}

    keyboard = InlineKeyboardMarkup(row_width=2)
    await callback_query.message.delete()  # Oldingi xabarni o'chirish

    for tuman in tumanlar.get(viloyat, []):
        keyboard.add(InlineKeyboardButton(tuman, callback_data=f'tuman_{tuman}'))

    # Orqaga tugmasi qo'shish
    back_button = InlineKeyboardButton("🔙Orqaga", callback_data="back_to_viloyat")
    keyboard.add(back_button)
    await bot.send_message(user_id, f"{viloyat} viloyatidagi tumaningizni tanlang⤵️", reply_markup=keyboard)

# Orqaga qaytish tugmasi bosilganda viloyat tanlash menyusiga qaytish
@dp.callback_query_handler(lambda c: c.data == "back_to_viloyat")
async def back_to_viloyat(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    # Foydalanuvchi tanlagan viloyatni olish
    viloyat = user_viloyat.get(user_id)

    if viloyat:
        # Viloyatni qayta tanlash menyusini ko'rsatish
        keyboard = InlineKeyboardMarkup(row_width=2)
        await callback_query.message.delete()  # Oldingi xabarni o'chirish
        viloyatlar = ["Toshkent", "Toshkent shahar", "Samarqand", "Andijon", "Buxoro", "Farg'ona", "Namangan", "Qashqadaryo", "Sirdaryo", "Jizzax", "Surxandaryo", "Xorazim", "Navoiy", "Qorqalpog'iston Respublikasi"]
        for v in viloyatlar:
            keyboard.add(InlineKeyboardButton(v, callback_data=f'viloyat_{v}'))

        # Orqaga tugmasi
        button_back_to_start = InlineKeyboardButton("🔙Orqaga", callback_data='back_to_start')
        keyboard.add(button_back_to_start)

        await bot.send_message(user_id, "Viloyatni tanlang⤵️", reply_markup=keyboard)
        await callback_query.answer()
    else:
        await bot.send_message(user_id, "Viloyat tanlashda xatolik yuz berdi.")



# 4. Tuman nomini aniqlab olish
@dp.callback_query_handler(lambda c: c.data.startswith('tuman_'))
async def confirm_registration(callback_query: types.CallbackQuery):
    tuman = callback_query.data.split('_')[1]  # Tuman nomini callback_data dan ajratib olish
    user_id = callback_query.from_user.id
    user_tuman[user_id] = tuman

    # Ask for the user's full name
    await callback_query.message.delete()  # Delete the previous message
    await bot.send_message(user_id, "Ism va Familyangizni quyidagi tartibda kiriting📝: Aliyev Alimardon ")

    # FSM holatini o'zgartirish
    await RegistrationStates.waiting_for_full_name.set()  # To'liq ismni kiritishni kutish holati
    await callback_query.answer()  # Tanlovni tasdiqlash

# To'liq ismni so'ragandan so'ng, lavozimni so'rash
@dp.message_handler(state=RegistrationStates.waiting_for_full_name, content_types=types.ContentTypes.TEXT)
async def handle_full_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    full_name = message.text.strip()
    user_full_name[user_id] = full_name

    # Foydalanuvchidan to'liq ismni olish
    if not full_name:  # Agar to'liq ism kiritilmagan bo'lsa
        await message.answer("Ism va Familyangizni quyidagi tartibda kiriting📝: Aliyev Alimardon ")
        return

    # Eski xabarni o'chirish (To'liq ismni so'rash xabari)
    await message.delete()  # Foydalanuvchidan oldingi xabarni o'chirish

    # Lavozimni so'rash
    await message.answer(f"{full_name}, Lavozimingizni kiriting📝:")

    # FSM holatini o'zgartirish
    await RegistrationStates.waiting_for_lavozim.set()

# 4. Lavozimni olish
@dp.message_handler(state=RegistrationStates.waiting_for_lavozim, content_types=types.ContentTypes.TEXT)
async def handle_lavozim(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lavozim = message.text.strip()
    user_lavozim[user_id] = lavozim

    if not lavozim:  # Agar lavozim kiritilmagan bo'lsa
        await message.answer(f"{full_name}, Lavozimingizni kiriting📝:")
        return

    # Ma'lumotlarni tasdiqlash
    full_name = user_full_name[user_id]
    tuman = user_tuman[user_id]
    viloyat = user_viloyat[user_id]
    # Ma'lumotlarni tasdiqlash
    keyboard = InlineKeyboardMarkup(row_width=2)

    # Tasdiqlash va Bekor qilish tugmalari
    button_confirm_registration = InlineKeyboardButton("✅Tasdiqlash", callback_data="confirm_registration")
    button_cancel = InlineKeyboardButton("❌Bekor qilish", callback_data="cancel_registration")

    keyboard.add(button_confirm_registration, button_cancel)  # Indentatsiyani to'g'ri saqlash
    await message.delete()  # Oldingi xabarni o'chirish

    max_len = max(len(full_name), len(lavozim), len(viloyat), len(tuman))  # eng uzun satrni aniqlash
  
    await message.answer(f"Sizning ma'lumotlaringiz:\n\n"
                         f"Ism, Familya:  {full_name.ljust(max_len)}\n"
                         f"Lavozim:       {lavozim.ljust(max_len)}\n"
                         f"Viloyat:        {viloyat.ljust(max_len)}\n"
                         f"Tuman:          {tuman.ljust(max_len)}\n\n"
                         "Ma'lumotlar to'g'ri bo'lsa tasdiqlashni bosib,\nro'yxatdan o'tishni tugating!", 
                         reply_markup=keyboard)


    await RegistrationStates.confirmation.set()

# 5. Tasdiqlash
@dp.callback_query_handler(lambda c: c.data == "confirm_registration", state=RegistrationStates.confirmation)
async def confirm_registration(callback_query: types.CallbackQuery, state: FSMContext):
    user_id = callback_query.from_user.id
    full_name = user_full_name[user_id]
    tuman = user_tuman[user_id]
    viloyat = user_viloyat[user_id]
    lavozim = user_lavozim[user_id]

    # Agar biror ma'lumot yo'q bo'lsa, xatolik yuborilsin
    if not all([user_id, viloyat, tuman, full_name, lavozim]):
        await callback_query.message.answer("Ba'zi ma'lumotlar yo'q, iltimos qaytadan kiriting.")
        await state.finish()
        return

    # Ma'lumotlarni bazaga saqlash
    conn = get_connection()  # Bu yerda bazaga ulanishni amalga oshiring
    if conn:
        add_user(user_id, viloyat, tuman, full_name, lavozim)  # add_user funktsiyasini to'ldirish
        await callback_query.message.answer(f"Siz {viloyat} viloyati, {tuman} tumanida ro'yxatdan o'tdingiz.✅\n\n"
                                           f"To'liq ism: {full_name}\n"
                                           f"Lavozim: {lavozim}", reply_markup=get_main_reply_keyboard())

        await callback_query.message.delete()  # Oldingi xabarni o'chirish

        # Asosiy menyuga yo'naltirish
        await send_main_menu(user_id)
        await state.finish()  # FSM holatini tugatish
    else:
        await callback_query.message.answer("Ma'lumotlar bazasiga ulanishda xatolik yuz berdi.")


# 6. Bekor qilish
@dp.callback_query_handler(lambda c: c.data == "cancel_registration", state=RegistrationStates.confirmation)
async def cancel_registration(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.delete()  # Oldingi xabarni o'chirish
    await callback_query.message.answer("Ro'yxatga olish bekor qilindi. Ro'yxatdan o'tish uchun /start buyrug'ini yuboring!📲")
    await state.finish()

# Bosh menyuga qaytish tugmasi
@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def return_main_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id  # message_id ni aniqlash
    await callback_query.message.delete()

    # Bosh menyu tugmalarini yuborish
    sent_message = await send_main_menu(user_id)  # bot.send_message() natijasini oling

    # Agar kerak bo'lsa, eski tugmalarni o'chirish
    if sent_message:
        await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.answer()

# 4. Asosiy menyu
async def send_main_menu(user_id):
    # Foydalanuvchining mavjudligini tekshirish (users va url_log jadvallari bo'yicha)
    user_in_users = get_user_by_id(user_id)  # users jadvalidan foydalanuvchini izlash
    user_in_url_log = get_user_from_url_log(user_id)  # url_log jadvalidan foydalanuvchini izlash

    # Agar foydalanuvchi ikkala jadvalda ham mavjud bo'lmasa, menyu ko'rsatilmasin
    if user_in_users is None and user_in_url_log is None:
        # Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa, ro'yxatdan o'tish jarayonini boshlaymiz
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_register = InlineKeyboardButton("🟢Davom etish", callback_data='register')  # Registration button
        button_cancel = InlineKeyboardButton("🔴Bekor qilish", callback_data='cancel')  # Cancel button
        keyboard.add(button_register, button_cancel)
        await bot.send_message(user_id, "Siz ro'yxatdan o'tmagansiz yoki bazadan o'chirilgansiz. Ro'yxatdan o'tish uchun 'Davom etish' tugmasini bosing:", reply_markup=keyboard)
        return  # Menyu ko'rsatilmaydi

    keyboard = InlineKeyboardMarkup(row_width=2)

    button_admin_panel = InlineKeyboardButton("🎖Administrator paneli", callback_data="section_admin")
    button_organization = InlineKeyboardButton("🏛Tashkilot boshqaruvi", callback_data="section_org")
    button_personnel = InlineKeyboardButton("📆Personallarni boshqarish", callback_data="section_personnel")
    button_requests = InlineKeyboardButton("⁉️So'rovlar", callback_data="section_requests")
    button_dispatch = InlineKeyboardButton("☎️Dispetcher - 103", callback_data="section_dispatch")
    button_warehouse = InlineKeyboardButton("📦Ombor", callback_data="section_warehouse")
    button_yotoq = InlineKeyboardButton("🏩Yotoq hisobi", callback_data="section_yotoq")

    keyboard.add(button_admin_panel, button_organization, button_personnel, button_requests, button_dispatch, button_warehouse, button_yotoq)

    # Bosh menyuni yuborish
    sent_message = await bot.send_message(user_id, "🏠Asosiy menyu:", reply_markup=keyboard)

    return sent_message

# Orqaga va bosh menyu tugmalari (InlineKeyboard orqali har bir bo‘lim uchun)
def add_navigation_buttons(keyboard):

    keyboard.add(InlineKeyboardButton(text="🔙Ortga", callback_data="main_menu"))
    return keyboard


# Bosh menyuga qaytish tugmasi
@dp.callback_query_handler(lambda c: c.data == "main_menu")
async def return_main_menu(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    message_id = callback_query.message.message_id  # message_id ni aniqlash
    # Bosh menyu tugmalarini yuborish
    await send_main_menu(user_id)
    await callback_query.answer()

# 1. Administrator paneli bo'limi
@dp.callback_query_handler(lambda c: c.data == "section_admin")
async def admin_panel(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        await callback_query.message.delete()  # Oldingi xabarni o'chirish

        keyboard = InlineKeyboardMarkup(row_width=2)

        button_global = InlineKeyboardButton("🌐Global Ma'lumotnomalar", callback_data="admin_global")
        button_malumotnoma = InlineKeyboardButton("🗂️Ma'lumotnomalar", callback_data="admin_malumotnoma")
        button_dinamik = InlineKeyboardButton("⚡️Dinamik Ma'lumotnomalar", callback_data="admin_dinamik")
        button_sozlama = InlineKeyboardButton("🛠️Sozlamalar", callback_data="admin_sozlamalar")
        button_xabarlar = InlineKeyboardButton("💬Xabarlar", callback_data="admin_xabarlar")
        button_sinx = InlineKeyboardButton("🌀Sinxronizatsiya", callback_data="admin_sinx")
        keyboard.add(button_global, button_malumotnoma, button_dinamik, button_sozlama, button_xabarlar)

        # Orqaga va Bosh menyu tugmalarini qo'shamiz
        keyboard = add_navigation_buttons(keyboard)
        await bot.send_message(user_id, "Administrator paneli:", reply_markup=keyboard)
        await callback_query.answer()

    except Exception as e:
        # Xatolik bo'lsa, foydalanuvchiga xabar berish
        await bot.send_message(user_id, f"Xatolik yuz berdi: {str(e)}")
        await callback_query.answer("Xatolik yuz berdi.")

# Video va file yuborish
@dp.callback_query_handler(lambda c: c.data.startswith("admin_"))
async def admin_panel_handler(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    section = callback_query.data  # Tanlangan bo'lim (masalan: "admin_global")
    
    try:
        # Tanlangan bo'lim uchun video va fayl ID larini olish
        video_info = faq_video_ids.get(section)

        if video_info:
            video_id = video_info.get("video_id")
            txt_file_id = video_info.get("txt_id")

            # Videoni chatga yuborish
            if video_id:
                # Kanalga yuborilgan video ID-ni chatga yuborish
                await bot.send_video(chat_id=user_id, video=video_id, caption="Mana sizning video!")

            # .txt faylini chatga yuborish
            if txt_file_id:
                # Kanalga yuborilgan .txt faylni chatga yuborish
                await bot.send_document(chat_id=user_id, document=txt_file_id, caption="Mana sizning faylingiz!")

        # Xabarni o'chirish
        await callback_query.message.delete()
        await callback_query.answer()

    except Exception as e:
        # Xatolik bo'lsa, foydalanuvchiga xabar berish
        await bot.send_message(user_id, f"Xatolik yuz berdi: {str(e)}")
        await callback_query.answer("Xatolik yuz berdi.")


# 2. Yotoq Hisobi bo'limi
@dp.callback_query_handler(lambda c: c.data == "section_yotoq")
async def yotoq_hisobi(callback_query: types.CallbackQuery):
    await callback_query.message.delete()  # Oldingi xabarni o'chirish
    keyboard = InlineKeyboardMarkup(row_width=2)

    button_foydalanuvchilar = InlineKeyboardButton("👨‍👩‍👧‍👦Foydalanuvchilar", callback_data="yotoq_foydalanuvchilar")
    button_bulimlar = InlineKeyboardButton("🏢️Bo'limlar", callback_data="yotoq_bulimlar")
    button_xonalar = InlineKeyboardButton("🏥Xonalar", callback_data="yotoq_xonalar")
    button_tushaklar = InlineKeyboardButton("🛌To'shaklar", callback_data="yotoq_tushaklar")
    button_yozuvlar = InlineKeyboardButton("📝Yozuvlar", callback_data="yotoq_yozuvlar")
    keyboard.add(button_foydalanuvchilar, button_bulimlar, button_xonalar, button_tushaklar, button_yozuvlar)

    # Orqaga va Bosh menyu tugmalarini qo'shamiz
    keyboard = add_navigation_buttons(keyboard)

    await bot.send_message(callback_query.from_user.id, "🏩Yotoq hisobi:", reply_markup=keyboard)

# Yotoq hisobi URl taqdim etish
@dp.callback_query_handler(lambda c: c.data.startswith('yotoq_'))
async def show_yotoq_content(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # callback_query.data orqali tugmani aniqlaymiz
    key = callback_query.data

    # Mazkur tugmaga tegishli URL ni yotoq_urls dan olamiz
    url = yotoq_urls.get(key)

    if url:
        # Agar URL mavjud bo'lsa, foydalanuvchiga yuboriladi
        await bot.send_message(user_id, f"Video manzil: {url}")
    else:
        # Agar URL topilmasa, xatolik haqida habar beradi
        await bot.send_message(user_id, "Video manzili topilmadi.")

    # Callbackni tasdiqlash
    await callback_query.answer()

# 2. Tashkilot boshqaruvi bo'limi
@dp.callback_query_handler(lambda c: c.data == "section_org")
async def organization_management(callback_query: types.CallbackQuery):
    await callback_query.message.delete()  # Oldingi xabarni o'chirish
    keyboard = InlineKeyboardMarkup(row_width=2)

    button_shifts = InlineKeyboardButton("📅Tashkilot smenalari", callback_data="org_shifts")
    button_transport = InlineKeyboardButton("🚑Tashkilot transportlari", callback_data="org_transport")
    button_brigadasi = InlineKeyboardButton("👷‍♂️️Tashkilot brigadasi", callback_data="org_brigadasi")
    button_xodimlari = InlineKeyboardButton("👷♂️👷♀️Tashkilot xodimlari", callback_data="org_xodimlari")
    button_ixtisos_guruhi = InlineKeyboardButton("🏬Tashkilotning ixtisoslashuv guruhi", callback_data="org_ixtisos_guruhi")
    button_ish_urni = InlineKeyboardButton("✔️Ish o'rinlari", callback_data="org_ish_urni")
    keyboard.add(button_shifts, button_transport, button_brigadasi, button_xodimlari, button_ixtisos_guruhi, button_ish_urni)

    # Orqaga va Bosh menyu tugmalarini qo'shamiz
    keyboard = add_navigation_buttons(keyboard)

    await bot.send_message(callback_query.from_user.id, "Tashkilot boshqaruvi:", reply_markup=keyboard)

# 3. Personallarni boshqarish bo'limi
@dp.callback_query_handler(lambda c: c.data == "section_personnel")
async def personnel_management(callback_query: types.CallbackQuery):
    await callback_query.message.delete()  # Oldingi xabarni o'chirish
    keyboard = InlineKeyboardMarkup(row_width=2)

    button_schedule = InlineKeyboardButton("🗓️Reja jadvali", callback_data="personnel_schedule")
    button_brigade = InlineKeyboardButton("📅Brigada jadvali", callback_data="personnel_brigade")
    button_tabel = InlineKeyboardButton("📑Tabel", callback_data="personnel_tabel")
    keyboard.add(button_schedule, button_brigade, button_tabel)

    # Orqaga va Bosh menyu tugmalarini qo'shamiz
    keyboard = add_navigation_buttons(keyboard)

    await bot.send_message(callback_query.from_user.id, "Personallarni boshqarish:", reply_markup=keyboard)

# 4. So'rovlar bo'limi
@dp.callback_query_handler(lambda c: c.data == "section_requests")
async def requests_management(callback_query: types.CallbackQuery):
    await callback_query.message.delete()  # Oldingi xabarni o'chirish
    keyboard = InlineKeyboardMarkup(row_width=2)

    button_incoming = InlineKeyboardButton("📬So'rovlar", callback_data="requests_incoming")
    keyboard.add(button_incoming)

    # Orqaga va Bosh menyu tugmalarini qo'shamiz
    keyboard = add_navigation_buttons(keyboard)

    await bot.send_message(callback_query.from_user.id, "So'rovlar bo'limi:", reply_markup=keyboard)

# 5. Dispetcher - 103 bo'limi
@dp.callback_query_handler(lambda c: c.data == "section_dispatch")
async def dispatch_management(callback_query: types.CallbackQuery):
    await callback_query.message.delete()  # Oldingi xabarni o'chirish
    keyboard = InlineKeyboardMarkup(row_width=2)

    button_call = InlineKeyboardButton("📞⬇️Chaqiruvni qabul qilish", callback_data="dispatch_call")
    button_direct = InlineKeyboardButton("📞⬆️Yo'naltirish", callback_data="dispatch_direct")
    button_jadvali = InlineKeyboardButton("📅Chaqiruv jadvali", callback_data="dispatch_jadvali")
    button_kartalari = InlineKeyboardButton("📔Chaqiruv kartalari jadvali", callback_data="dispatch_kartalari")
    keyboard.add(button_call, button_direct, button_jadvali, button_kartalari)

    # Orqaga va Bosh menyu tugmalarini qo'shamiz
    keyboard = add_navigation_buttons(keyboard)

    await bot.send_message(callback_query.from_user.id, "Dispetcher - 103:", reply_markup=keyboard)

# 6. Ombor bo'limi
@dp.callback_query_handler(lambda c: c.data == "section_warehouse")
async def warehouse_management(callback_query: types.CallbackQuery):
    await callback_query.message.delete()  # Oldingi xabarni o'chirish
    keyboard = InlineKeyboardMarkup(row_width=2)

    button_yiguvchi = InlineKeyboardButton("👝Yig'uvchi sumkasi", callback_data="warehouse_yiguvchi")
    button_serial = InlineKeyboardButton("📱Seriya raqami", callback_data="warehouse_serial")
    button_ombor = InlineKeyboardButton("📦Ombor", callback_data="warehouse_ombor")
    button_kirim = InlineKeyboardButton("📥Kirim", callback_data="warehouse_kirim")
    button_qoldiq = InlineKeyboardButton("📊Qoldiq", callback_data="warehouse_qoldiq")
    button_chiqim = InlineKeyboardButton("📤Chiqimlar", callback_data="warehouse_chiqim")
    button_suralgan_ehtiyoj = InlineKeyboardButton("⏫So'ralgan ehtiyojlar", callback_data="warehouse_suralgan_ehtiyoj")
    button_inventor = InlineKeyboardButton("▶️Inventorlash", callback_data="warehouse_inventor")
    button_qabul_ehtiyoj = InlineKeyboardButton("⏬Qabul qilingan ehtiyojlar", callback_data="warehouse_qabul_ehtiyoj")
    keyboard.add(button_yiguvchi, button_serial, button_kirim, button_chiqim, button_ombor, button_qoldiq, button_suralgan_ehtiyoj, button_qabul_ehtiyoj, button_inventor)

    # Orqaga va Bosh menyu tugmalarini qo'shamiz
    keyboard = add_navigation_buttons(keyboard)

    await bot.send_message(callback_query.from_user.id, "Ombor:", reply_markup=keyboard)

#Tashkilot boshqaruvi
@dp.callback_query_handler(lambda c: c.data.startswith('org_'))
async def show_admin_content(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    # callback_query.data orqali tugmani aniqlaymiz
    key = callback_query.data

    # Mazkur tugmaga tegishli URL ni content_urls dan olamiz
    url = org_urls.get(key)

    if url:
        # Agar URL mavjud bo'lsa, foydalanuvchiga yuboriladi
        await bot.send_message(user_id, f"Mana kerakli manzil: {url}")
    else:
        # Agar URL topilmasa, xatolik haqida habar beradi
        await bot.send_message(user_id, "Manzil topilmadi.")

    # Callbackni tasdiqlash
    await callback_query.answer()
    
# FAQ inline tugmalarini yaratish
def get_faq_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    #for key in faq_urls:
    for key, value in faq_video_ids.items():
        button = InlineKeyboardButton(text=key, callback_data=key)
        keyboard.add(button)
    return keyboard

# Help inline tugmalarini yaratish
async def get_help_keyboard(message: types.Message):
    await message.delete()  # Yordam xabarini o'chirish  
    keyboard = InlineKeyboardMarkup(row_width=2)
       
    button_videohelp = InlineKeyboardButton("Video qo'llanma", callback_data="help_video")
    button_texthelp = InlineKeyboardButton("Matnli qo'llanma", callback_data="help_text")
    keyboard.add(button_videohelp, button_texthelp)
    
    # Orqaga va Bosh menyu tugmalarini qo'shamiz
    keyboard = add_navigation_buttons(keyboard)
    await message.answer("📗Yordam menyusi:", reply_markup=keyboard)
    return keyboard
    
# FAQ menyusini qayta ishlash
@dp.message_handler(lambda message: message.text == "❓Savollar")
async def faq_menu(message: types.Message):
    user_id = message.from_user.id

    # Foydalanuvchi ro'yxatdan o'tganligini tekshirish
    user_in_users = get_user_by_id(user_id)  # users jadvalidan foydalanuvchini izlash
    user_in_url_log = get_user_from_url_log(user_id)  # url_log jadvalidan foydalanuvchini izlash

    if user_in_users is None and user_in_url_log is None:
        # Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa, ro'yxatdan o'tish jarayonini boshlaymiz
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_register = InlineKeyboardButton("🟢Davom etish", callback_data='register')  # Registration button
        button_cancel = InlineKeyboardButton("🔴Bekor qilish", callback_data='cancel')  # Cancel button
        keyboard.add(button_register, button_cancel)
        await message.answer("Siz ro'yxatdan o'tmagansiz yoki bazadan o'chirilgansiz. Ro'yxatdan o'tish uchun 'Davom etish' tugmasini bosing:",  reply_markup=keyboard)
    else:
        # Foydalanuvchi ro'yxatdan o'tgan bo'lsa, FAQ menyusini yuborish
        await message.answer("Savollarni tanlang:", reply_markup=get_faq_keyboard())

# Help menyusini qayta ishlash
@dp.message_handler(lambda message: message.text == "📗Yordam")
async def help_menu(message: types.Message):
    user_id = message.from_user.id

    # Foydalanuvchi ro'yxatdan o'tganligini tekshirish
    user_in_users = get_user_by_id(user_id)  # users jadvalidan foydalanuvchini izlash
    user_in_url_log = get_user_from_url_log(user_id)  # url_log jadvalidan foydalanuvchini izlash

    if user_in_users is None and user_in_url_log is None:
        # Agar foydalanuvchi ro'yxatdan o'tmagan bo'lsa, ro'yxatdan o'tish jarayonini boshlaymiz
        keyboard = InlineKeyboardMarkup(row_width=2)
        button_register = InlineKeyboardButton("🟢Davom etish", callback_data='register')  # Registration button
        button_cancel = InlineKeyboardButton("🔴Bekor qilish", callback_data='cancel')  # Cancel button
        keyboard.add(button_register, button_cancel)
        await message.answer("Siz ro'yxatdan o'tmagansiz yoki bazadan o'chirilgansiz. Ro'yxatdan o'tish uchun 'Davom etish' tugmasini bosing:",  reply_markup=keyboard)
    else:
        # Foydalanuvchi ro'yxatdan o'tgan bo'lsa, Help menyusini yuborish
        await get_help_keyboard(message)

# FAQ inline tugmasi bosilganda URL yuborish
@dp.callback_query_handler(lambda c: c.data in faq_video_ids)
async def faq_callback_handler(callback_query: types.CallbackQuery):
    question = callback_query.data
    user_id = callback_query.from_user.id
    await bot.answer_callback_query(callback_query.id)

    # FAQ menyusini o'chirish
    await bot.delete_message(callback_query.from_user.id, callback_query.message.message_id)
    
    # Fayl ID larni olish (video va txt file_id)
    video_id = faq_video_ids.get(question)[0] if isinstance(faq_video_ids.get(question), tuple) else faq_video_ids.get(question).get("video")
    txt_file_id = faq_video_ids.get(question)[1] if isinstance(faq_video_ids.get(question), tuple) else faq_video_ids.get(question).get("txt")
    
    if video_id:
        # Videoni yuborish
        await bot.send_video(chat_id=user_id, video=video_id, caption=f"Savol: {question}")
    
    if txt_file_id:
        # .txt faylni yuborish
        await bot.send_document(chat_id=user_id, document=txt_file_id, caption=f"Savol: {question} uchun matnli fayl")
    
    if not video_id and not txt_file_id:
        # Hech narsa topilmasa, xato xabarini yuborish
        await bot.send_message(chat_id=user_id, text="Kechirasiz, ushbu savolga javob mavjud emas.")


# Help video yoki matn yuborish
@dp.callback_query_handler(lambda c: c.data == 'help_video')
async def help_video(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    button_name = 'help_video'
    url = help_video_url
    # URL loglash
    log_url_action(user_id, button_name, url)
    await bot.answer_callback_query(callback_query.id)
    # Yordam xabarini o'chirish
    await callback_query.message.delete()
    await bot.send_message(callback_query.from_user.id, f"Video yordam: {help_video_url}")

@dp.callback_query_handler(lambda c: c.data == 'help_text')
async def help_text_response(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    button_name = 'help_text'
    url = "N/A" 
    # URL loglash
    log_url_action(user_id, button_name, url)
    await bot.answer_callback_query(callback_query.id)
    # Yordam xabarini o'chirish
    await callback_query.message.delete()
    await bot.send_message(callback_query.from_user.id, help_text)

    await callback_query.answer()
    

# Bosh menyuga qaytish tugmasi
@dp.message_handler(lambda message: message.text == "🏠Asosiy menyu")
async def return_main_menu(message: types.Message):
    user_id = message.from_user.id
    await send_main_menu(user_id)

# Orqaga qaytish tugmalari (inline keyboards orqali)
@dp.callback_query_handler(lambda c: c.data == "back")
async def go_back(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    await send_main_menu(user_id)
    await callback_query.answer()

# 2. /hisobot_admin komandasi va parolni so'rash
@dp.message_handler(commands=['hisobot_admin'])
async def hisobot_admin(message: types.Message):
    # Parolni so'rash
    await message.answer("Parolni kiriting:")

# 3. Parolni tekshirish va inline tugmalarni yuborish
@dp.message_handler(lambda message: message.text == SECRET_PASSWORD)
async def send_report_options(message: types.Message):
    # Inline tugmalarni yaratish
    keyboard = InlineKeyboardMarkup(row_width=2)
    await message.delete()  # Foydalanuvchidan oldingi xabarni o'chirish
    republic_button = InlineKeyboardButton(text="Respublika bo'yicha jami", callback_data="republic_report")
    region_button = InlineKeyboardButton(text="Viloyat bo'yicha", callback_data="region_report")
    keyboard.add(republic_button, region_button)
    

    # Foydalanuvchiga tanlovni yuborish
    await message.answer("Iltimos, hisobotni qanday shaklda olishni tanlang:", reply_markup=keyboard)

# Respublika bo'yicha umumiy hisobotni yuborish
@dp.callback_query_handler(lambda c: c.data == "republic_report")
async def republic_report(callback_query: types.CallbackQuery):
    query = get_republic_report_sql()  # Respublika hisobotini olish

    try:
        conn = get_connection()  # Postgres ma'lumotlar bazasiga ulanish
        df = pd.read_sql_query(query, conn)
        file_path = "/tmp/Respublika_boyicha_jami_hisobot.xlsx"
        df.to_excel(file_path, index=False)
        conn.close()

        # Hisobotni yuborish
        with open(file_path, "rb") as file:
            await bot.send_document(callback_query.from_user.id, file, caption="Respublika bo'yicha jami hisobot:")
        
        # Faylni o'chirish
        os.remove(file_path)

        # Javob yuborish
        await callback_query.answer("Respublika bo'yicha jami hisobot yuborildi!")

    except Exception as e:
        await callback_query.answer("Hisobotni yaratishda xatolik yuz berdi!")
        print(f"Error: {e}")

# Viloyat bo'yicha hisobotni tanlash
@dp.callback_query_handler(lambda c: c.data == "region_report")
async def region_report(callback_query: types.CallbackQuery):
    query = get_regions_sql()  # Viloyatlar ro'yxatini olish

    try:
        conn = get_connection()  # Postgres ma'lumotlar bazasiga ulanish
        if conn is None:
            await callback_query.answer("Viloyatlar ro'yxatini olishda xatolik yuz berdi!")
            print("Connection failed!")  # Ulanish muvaffaqiyatsiz bo'lsa
            return

        with conn.cursor() as cursor:
            cursor.execute(query)  # SQL so'rovini bajarish
            regions = cursor.fetchall()  # Viloyatlar ro'yxatini olish
            print(f"Regions: {regions}")  # Viloyatlar ro'yxatini tekshirish

        conn.close()

        if not regions:
            await callback_query.answer("Viloyatlar ro'yxati bo'sh!")
            return

        # Inline tugmalarni yaratish
        keyboard = InlineKeyboardMarkup(row_width=2)
        await callback_query.message.delete()
        for region in regions:
            # Viloyat nomini olamiz va inline tugmalarni yaratamiz
            region_name = region[0]
            keyboard.add(InlineKeyboardButton(text=region_name, callback_data=f"region_{region_name}"))

        # Foydalanuvchiga viloyatlarni yuborish
        await bot.send_message(callback_query.from_user.id, "Iltimos, viloyatni tanlang:", reply_markup=keyboard)

    except Exception as e:
        print(f"Error: {e}")  # Xatolikni konsolga chiqarish
        await callback_query.answer("Viloyatlar ro'yxatini olishda xatolik yuz berdi!")

@dp.callback_query_handler(lambda c: c.data.startswith("region_"))
async def region_report_detail(callback_query: types.CallbackQuery):
    region = callback_query.data.split("_")[1]  # Tanlangan viloyat nomini olish

    # Viloyat bo'yicha hisobotni olish uchun SQL so'rovi
    query = get_region_report_sql(region)  # Tanlangan viloyat bo'yicha hisobotni olish

    try:
        conn = get_connection()  # Postgres ma'lumotlar bazasiga ulanish
        df = pd.read_sql_query(query, conn, params=(region,))
        file_path = f"/tmp/{region}_viloyat_hisoboti.xlsx"
        df.to_excel(file_path, index=False)
        conn.close()

        # Hisobotni yuborish
        with open(file_path, "rb") as file:
            await bot.send_document(callback_query.from_user.id, file, caption=f"{region} viloyati bo'yicha hisobot:")
        
        # Faylni o'chirish
        os.remove(file_path)

        # Javob yuborish
        await callback_query.answer(f"{region} viloyati bo'yicha hisobot yuborildi!")

    except Exception as e:
        await callback_query.answer("Hisobotni yaratishda xatolik yuz berdi!")
        print(f"Error: {e}")

# 4. Xato parol yuborilganda xabar berish va buyruqni qayta yuborishni so'rash
@dp.message_handler(lambda message: message.text != SECRET_PASSWORD)
async def wrong_password(message: types.Message):
    await message.answer("Xato parol! Iltimos, qayta /hisobot_admin buyrug'ini yuboring.")

@dp.message_handler(content_types=[types.ContentType.VIDEO, types.ContentType.DOCUMENT])
async def handle_files(message: types.Message):
    if message.video:
        # Agar xabar turi video bo'lsa, file_id ni qaytarish
        video_id = message.video.file_id
        await message.reply(f"{video_id}")
    elif message.document and message.document.file_name.endswith(".txt"):
        # Agar fayl .txt bo'lsa, file_id ni qaytarish
        txt_file_id = message.document.file_id
        await message.reply(f"{txt_file_id}")


# Botni ishga tushirish
if __name__ == '__main__':

    # Botni ishga tushirish
    executor.start_polling(dp, skip_updates=True)


