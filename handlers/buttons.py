from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

admin_welcome = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🗄 Kategoriyalar paneli")
        ]
    ],
    resize_keyboard=True,
    one_time_keyboard=True
)

welcome_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🇺🇿 O'zbek tili", callback_data="lang_uz")
        ],
        [
            InlineKeyboardButton(text="🇷🇺 Русский язык", callback_data="lang_ru")
        ]
    ]
)

main_admin = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="📑 Qabul qilingan arizalar", callback_data="spisok")
        ],
        [
            InlineKeyboardButton(text="🔙 Ortga", callback_data="back")
        ]
    ]
)

admin = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data="admit")
        ],
        [
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel")
        ]
    ]
)

