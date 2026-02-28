from aiogram import Router, F, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import ReplyKeyboardRemove
from aiogram.utils.keyboard import InlineKeyboardBuilder 

from services.hh_api import HHService
from keyboards.builders import pagination_kb, main_menu, items_kb, skip_city_kb
from database.orm import add_favorite, get_favorites

router = Router()

# === КОНСТАНТЫ ДЛЯ ВЫБОРА ===
IT_ROLES = [
    "Python Developer", "Frontend Developer", "Java Developer", 
    "Data Scientist", "QA Engineer", "DevOps", 
    "System Analyst", "Project Manager", "C++ Developer", "Go Developer"
]

SALARY_RANGES = {
    "Не важно": None,
    "от 50.000 ₽": 50000,
    "от 100.000 ₽": 100000,
    "от 150.000 ₽": 150000,
    "от 200.000 ₽": 200000,
    "от 300.000 ₽": 300000
}

# FSM
class SearchFSM(StatesGroup):
    choosing_role = State()   
    choosing_salary = State() 
    choosing_city = State()   
    viewing_results = State() 

# 1. Запуск поиска
@router.callback_query(F.data == "start_search")
async def start_search_flow(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "👨‍💻 **Выберите IT-специальность из списка:**", 
        reply_markup=items_kb(IT_ROLES, "role"),
        parse_mode="Markdown"
    )
    await state.set_state(SearchFSM.choosing_role)

# 2. Обработка выбора роли
@router.callback_query(SearchFSM.choosing_role, F.data.startswith("role_"))
async def role_chosen(callback: types.CallbackQuery, state: FSMContext):
    role = callback.data.split("_")[1]
    await state.update_data(role=role)
    
    salary_keys = list(SALARY_RANGES.keys())
    await callback.message.edit_text(
        f"Выбрано: **{role}**.\n\n💰 **Укажите желаемую зарплату:**",
        reply_markup=items_kb(salary_keys, "salary"),
        parse_mode="Markdown"
    )
    await state.set_state(SearchFSM.choosing_salary)

# 3. Обработка выбора зарплаты
@router.callback_query(SearchFSM.choosing_salary, F.data.startswith("salary_"))
async def salary_chosen(callback: types.CallbackQuery, state: FSMContext):
    salary_label = callback.data.split("_")[1]
    salary_value = SALARY_RANGES.get(salary_label)
    
    await state.update_data(salary=salary_value)
    
    await callback.message.delete()
    await callback.message.answer(
        "🏙️ **Введите город поиска** (например: Москва, Казань).\n"
        "Или нажмите 'Пропустить', чтобы искать по всей России.",
        reply_markup=skip_city_kb()
    )
    await state.set_state(SearchFSM.choosing_city)

# 4. Обработка ввода города
@router.message(SearchFSM.choosing_city)
async def city_chosen(message: types.Message, state: FSMContext):
    city = message.text.strip()
    if city.lower() == "пропустить":
        city = ""
    
    await state.update_data(city=city)
    
    loading_msg = await message.answer("⏳ Ищу лучшие вакансии...", reply_markup=ReplyKeyboardRemove())
    
    await show_vacancy_page(message, state, page=0, is_new=True)

# ЛОГИКА ОТОБРАЖЕНИЯ

@router.callback_query(F.data.startswith("page_"))
async def process_pagination(callback: types.CallbackQuery, state: FSMContext):
    page = int(callback.data.split("_")[1])
    await show_vacancy_page(callback.message, state, page=page, is_new=False)

@router.callback_query(F.data == "stop_search")
async def stop_search(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Поиск завершен.", reply_markup=main_menu())

async def show_vacancy_page(message_obj, state: FSMContext, page: int, is_new: bool):
    data = await state.get_data()
    role = data.get("role")
    salary = data.get("salary")
    city = data.get("city")
    
    query_text = f"{role} {city}".strip()
    
    hh_data = await HHService.search_vacancies(query_text, salary=salary, page=page)
    
    if not hh_data or not hh_data['items']:
        text = f"😔 По запросу **{role}** ничего не найдено."
        if not is_new:
            await message_obj.edit_text(text, reply_markup=main_menu(), parse_mode="Markdown")
        else:
            await message_obj.answer(text, reply_markup=main_menu(), parse_mode="Markdown")
        return

    # Данные о вакансии
    item = hh_data['items'][0]
    total_pages = hh_data['pages']
    
    vac_name = item['name']
    vac_url = item['alternate_url']
    employer = item['employer']['name']
    salary_str = HHService.format_salary(item['salary'])
    snippet = item['snippet']['requirement'] or "Нет описания"
    snippet = snippet.replace("<highlighttext>", "").replace("</highlighttext>", "")
    
    text_response = (
        f"🔎 **{vac_name}**\n"
        f"🏢 **Компания:** {employer}\n"
        f"🏙 **Город:** {item['area']['name']}\n"
        f"💰 **Зарплата:** {salary_str}\n\n"
        f"📝 **Требования:**\n_{snippet}_\n"
    )
    
    await state.update_data(current_vacancy={
        "name": vac_name,
        "url": vac_url,
        "salary": salary_str
    })
    
    kb = pagination_kb(vac_url, page, total_pages, query_text)
    
    if is_new:
        await message_obj.answer(text_response, reply_markup=kb, parse_mode="Markdown")
    else:
        await message_obj.edit_text(text_response, reply_markup=kb, parse_mode="Markdown")

# ОБРАБОТКА ИЗБРАННОГО

@router.callback_query(F.data == "save_vacancy")
async def save_to_favorites(callback: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    vac = data.get("current_vacancy")
    
    if vac:
        await add_favorite(
            tg_id=callback.from_user.id,
            name=vac['name'],
            url=vac['url'],
            salary=vac['salary']
        )
        await callback.answer("✅ Вакансия сохранена в базу!", show_alert=False)
    else:
        await callback.answer("Ошибка: не удалось найти данные о вакансии.", show_alert=True)

@router.callback_query(F.data == "show_favorites")
async def show_favorites_handler(callback: types.CallbackQuery):
    favs = await get_favorites(callback.from_user.id)
    if not favs:
        await callback.answer("В избранном пока пусто.", show_alert=True)
        return
    
    text = "📂 **Ваши сохраненные вакансии:**\n\n"
    for i, f in enumerate(favs, 1):
        text += f"{i}. [{f.vacancy_name}]({f.vacancy_url})\n💰 {f.salary}\n\n"
    
    builder = InlineKeyboardBuilder()
    builder.button(text="🔙 Назад в меню", callback_data="back_to_menu")
    
    await callback.message.edit_text(
        text, 
        reply_markup=builder.as_markup(), 
        parse_mode="Markdown", 
        disable_web_page_preview=True
    )

@router.callback_query(F.data == "back_to_menu")
async def back_menu(callback: types.CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text("Главное меню", reply_markup=main_menu())
