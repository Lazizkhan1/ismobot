from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from Config import DEFAULT_LANGUAGE, FAST_DELIVERY, SLOW_DELIVERY
from database.Categories import CategoriesService
from handlers.Translation import _
from aiogram.utils.keyboard import InlineKeyboardBuilder, KeyboardBuilder, ReplyKeyboardBuilder

categories_service = CategoriesService()
_lang = DEFAULT_LANGUAGE


async def all_categories(prefix=""):
    categories = await categories_service.getAll()
    rows = []
    for category in categories:
        row = [InlineKeyboardButton(text=f"🏛️ {category['name']}", callback_data=f"{prefix}category:{category['id']}")]
        rows.append(row)
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_categories_main_menu(lang_=_lang):
    row1 = [
        InlineKeyboardButton(text=_('Все категории', lang_), callback_data='all_categories'),
        InlineKeyboardButton(text=_('Добавить категорию', lang_), callback_data='add_category'),
        InlineKeyboardButton(text=_('Удалить категорию', lang_), callback_data='remove_category')
    ]
    row2 = [
        InlineKeyboardButton(text=_('Главное меню', lang_), callback_data='main_menu')
    ]
    rows = [row1, row2]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_main_menu(lang_=_lang):
    row1 = [
        InlineKeyboardButton(text=_('Категории', lang_), callback_data='categories'),
    ]
    row2 = [
        InlineKeyboardButton(text=_('Заказы', lang_), callback_data='orders'),
    ]
    row3 = [
        InlineKeyboardButton(text=_('Отмена', lang_), callback_data='cancel')
    ]
    rows = [row1, row2, row3]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def back_to_categories_menu(lang_=_lang):
    row = [InlineKeyboardButton(text=_('Назад', lang_), callback_data='categories')]
    rows = [row]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def cancel_button(lang_=_lang):
    row = [InlineKeyboardButton(text=_('Отмена', lang_), callback_data='cancel')]
    rows = [row]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def rate_the_service(lang_=_lang):
    builder = InlineKeyboardBuilder()
    builder.button(text="😡", callback_data="rate:1", style="danger")
    builder.button(text="🙁", callback_data="rate:2", style="primary")
    builder.button(text="😐", callback_data="rate:3")
    builder.button(text="🙂", callback_data="rate:4", style="primary")
    builder.button(text="😍", callback_data="rate:5", style="success")
    builder.adjust(5)
    return builder.as_markup()


def delivery_type(lang_=_lang):
    fast_text = f"{FAST_DELIVERY:,} {_("сум", lang_)}".replace(",", " ")
    slow_text = f"{_('От 24 часов🕒', lang_)} - {SLOW_DELIVERY:,} so'm".replace(",", " ")
    row = [
        [InlineKeyboardButton(text=f"{fast_text}", callback_data='delivery_fast', style="success")],
        # [InlineKeyboardButton(text=f"🕒 {slow_text}", callback_data='delivery_slow')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=row)


def order_accept(order_id, lang_=_lang):
    row = [
        [InlineKeyboardButton(text=_('Принять', lang_), callback_data=f'accept_order:{order_id}', style="success")],
        [InlineKeyboardButton(text=_('Отклонить', lang_), callback_data=f'cancel_order_admin:{order_id}', style="danger")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=row)


def language_markup():
    rows = [
        [
            InlineKeyboardButton(text='🇺🇿 O\'zbek tili', callback_data='lang_uz'),
            InlineKeyboardButton(text='🇷🇺 Русский язык', callback_data='lang_ru')
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)



def main_menu_keyboard(lang_=_lang) -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.button(text=_("📸 Заказать фото", lang_), callback_data="order_photo")
    builder.button(text=_("👥 Пригласить друзей", lang_), callback_data="referral_menu")
    builder.button(text=_("📞 Связаться с администратором", lang_), callback_data="contact_admin")
    builder.adjust(1)
    return builder.as_markup()


def invite_friends_menu_keyboard(lang_=_lang) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=_("🎁 Мои скидки", lang_), callback_data="referral_discounts")],
        [InlineKeyboardButton(text=_("📤 Пригласить друзей", lang_), callback_data="referral_invite")],
        [InlineKeyboardButton(text=_("🏠 Главное меню", lang_), callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def discount_picker_keyboard(summary: dict, lang_=_lang) -> InlineKeyboardMarkup:
    rows = []
    if summary.get("percentage"):
        d = summary["percentage"]
        rows.append([
            InlineKeyboardButton(
                text=f"🎁 {d['label']}",
                callback_data=f"apply_discount:pct:{d['id']}",
            )
        ])
    if summary.get("discrete"):
        d = summary["discrete"]
        ids_str = ",".join(str(i) for i in d["ids"])
        rows.append([
            InlineKeyboardButton(
                text=f"💵 {d['label']}",
                callback_data=f"apply_discount:dis:{ids_str}",
            )
        ])
    rows.append([
        InlineKeyboardButton(
            text=_("❌ Оплатить без скидки", lang_),
            callback_data="skip_discount",
        )
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def pay_now_keyboard(total_amount: int, lang_=_lang) -> InlineKeyboardMarkup:
    amount_str = f"{total_amount:,}".replace(",", " ")
    button_text = _("✅ Оплатить: {amount} сум", lang_).format(amount=amount_str)
    rows = [
        [InlineKeyboardButton(text=button_text, callback_data="confirm_pay")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def use_discount_keyboard(lang_=_lang) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=_("🎁 Использовать скидку", lang_), callback_data="use_earned_discount")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)

