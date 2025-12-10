import aiohttp
import logging

class HHService:
    BASE_URL = "https://api.hh.ru/vacancies"

    @staticmethod
    async def search_vacancies(text: str, salary: int = None, only_with_salary: bool = False, page: int = 0):
        """
        text: поисковой запрос (роль + город)
        salary: желаемая зарплата
        """
        params = {
            "text": text,
            "area": 113,  # Поиск по России, но фильтр по городу будет в тексте
            "page": page,
            "per_page": 1, # Берем по 1 шт, чтобы удобно листать в чате
            "currency": "RUR"
        }
        
        if salary:
            params["salary"] = salary
            params["only_with_salary"] = "true"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(HHService.BASE_URL, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    logging.error(f"HH API Error: {response.status}")
                    return None
            except Exception as e:
                logging.error(f"Connection Error: {e}")
                return None

    @staticmethod
    def format_salary(salary_data):
        if not salary_data:
            return "Не указана"
        _from = salary_data.get('from')
        _to = salary_data.get('to')
        curr = salary_data.get('currency', 'RUR')
        
        if _from and _to:
            return f"от {_from} до {_to} {curr}"
        elif _from:
            return f"от {_from} {curr}"
        elif _to:
            return f"до {_to} {curr}"
        return "Не указана"