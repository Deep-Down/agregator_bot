from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def main_menu():
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Поиск вакансий", callback_data="start_search")
    builder.button(text="📂 Избранное", callback_data="show_favorites")
    return builder.as_markup()

def items_kb(items: list[str], prefix: str):
    """
    Универсальный генератор кнопок для выбора из списка.
    items: список строк (например, названия профессий)
    prefix: префикс для callback_data (например, 'role_')
    """
    builder = InlineKeyboardBuilder()
    for item in items:
        # callback_data не может быть очень длинным, поэтому обрезаем если что
        builder.button(text=item, callback_data=f"{prefix}_{item[:20]}")
    builder.adjust(2) # Делаем по 2 кнопки в ряд
    return builder.as_markup()

def pagination_kb(url: str, page: int, total_pages: int, query: str):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔗 Откликнуться / Подробнее", url=url))
    builder.row(InlineKeyboardButton(text="⭐ В избранное", callback_data="save_vacancy"))
    
    buttons = []
    if page > 0:
        buttons.append(InlineKeyboardButton(text="⬅️", callback_data=f"page_{page-1}")) # query храним в FSM, тут упростим
    
    buttons.append(InlineKeyboardButton(text=f"Стр. {page+1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        buttons.append(InlineKeyboardButton(text="➡️", callback_data=f"page_{page+1}"))
        
    builder.row(*buttons)
    builder.row(InlineKeyboardButton(text="❌ Остановить поиск", callback_data="stop_search"))
    return builder.as_markup()

def skip_city_kb():
    """Клавиатура для пропуска ввода города"""
    builder = ReplyKeyboardBuilder()
    builder.button(text="Пропустить")
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)