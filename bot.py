from imports import *
from banner import banner
import re
import random

API_TOKEN = '7999577438:AAF-WBB8_ABAbEa-MhuR-4wTKL3s4xaUUm4' 
GIGACHAT_API_URL = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions' 
GIGACHAT_API_KEY = 'YmZlNGMwYWQtM2E0ZS00NzQ3LWIzMzQtZWYxN2NjNTYxODEyOmZjOWQ0ZDNlLTlhMzctNGRiMi1iNTVmLTMzMjYwNmI2MzBjZg=='


logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

async def db_connect():
    return await aiosqlite.connect('case2giga.db')

reagents = ['маршрут', 'путь', 'маршут', 'мршрут', 'маршрт', 'мршрт', 'маршрyт', '']

async def get_places_from_db():
    db = await db_connect()
    places = {}
    try:
        async with db.execute("SELECT name, average_time FROM giga") as cursor:
            async for row in cursor:
                name = row[0].strip().lower()
                average_time = row[1]
                places[name] = average_time
                print(f"Загружено место: {name}, время: {average_time}")
    finally:
        await db.close()
    return places

def extract_days(user_query: str) -> int:
    match = re.search(r'на (\d+) (дня|день|дней)', user_query)
    return int(match.group(1)) if match else 1

async def create_itinerary(days: int, preferences: list) -> str:
    print(days)
    if not preferences:
        return "Нет доступных мероприятий."

    total_hours_per_day = 12 
    used_places = set()  
    itinerary = []
    num_places = len(preferences)  
    places_per_day = max(1, num_places // days - 1)  

    random.shuffle(preferences)

    print(preferences)
    for day in range(days):
        available_time = total_hours_per_day
        daily_places = []
        daily_count = 0  

        for place_name, average_time in preferences:
            if daily_count >= places_per_day:  
                break
            if place_name not in used_places:  
                average_time_float = float(average_time)

                if available_time >= average_time_float:  
                    daily_places.append((place_name, average_time_float))
                    used_places.add(place_name)  
                    available_time -= average_time_float
                    daily_count += 1 

        if daily_places:
            day_itinerary = ', '.join([f"{place[0]} ({place[1]}ч)" for place in daily_places])
            daily_total_time = sum(place[1] for place in daily_places)
            
            itinerary.append(f"🌟 **День {day + 1}** 🌟\n\n"
                 f"🗺️ **Места для посещения:**\n"
                 f"{day_itinerary}\n\n"
                 f"⏰ **Общее время**: {daily_total_time:.1f} ч\n\n")
        else:
            itinerary.append(f"День {day + 1}: Нет доступных мероприятий.")

    return "\n".join(itinerary)

def get_access_token():
    master_token = "YmZlNGMwYWQtM2E0ZS00NzQ3LWIzMzQtZWYxN2NjNTYxODEyOmZjOWQ0ZDNlLTlhMzctNGRiMi1iNTVmLTMzMjYwNmI2MzBjZg=="
    headers = {
        'Authorization': f'Bearer {master_token}',
        'RqUID': str(uuid.uuid4()),
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'scope': 'GIGACHAT_API_CORP'}
    base_url = 'https://ngw.devices.sberbank.ru:9443/api/v2/oauth'

    response = requests.post(url=base_url, headers=headers, data=data, verify=False)

    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        logging.error("Ошибка получения access_token: %s", response.text)
        return None

async def get_gigachat_response(query: str) -> list:
    access_token = get_access_token()
    if not access_token:
        return []

    payload = json.dumps({
        "model": "GigaChat",
        "messages": [{"role": "user", "content": query}],
        "stream": False,
        "repetition_penalty": 1
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(GIGACHAT_API_URL, headers=headers, data=payload, ssl=False) as response:
            if response.status == 200:
                json_response = await response.json()
                content = json_response['choices'][0]['message']['content']
                print(f"Ответ от GigaChat: {content}")

                database_places = await get_places_from_db()
                preferences = extract_places_from_text(content, database_places)

                print(f"Извлеченные предпочтения: {preferences}")
                return preferences
            else:
                logging.error("Ошибка запроса к GigaChat: %s", await response.text())
                return []


async def get_message_from_gigachat(query: str) -> list:
    access_token = get_access_token()
    if not access_token:
        return []

    payload = json.dumps({
        "model": "GigaChat",
        "messages": [{"role": "user", "content": query}],
        "stream": False,
        "repetition_penalty": 1
    })

    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(GIGACHAT_API_URL, headers=headers, data=payload, ssl=False) as response:
            if response.status == 200:
                json_response = await response.json()
                content = json_response['choices'][0]['message']['content']
                print(f"Ответ от GigaChat: {content}")                
                return content
            else:
                logging.error("Ошибка запроса к GigaChat: %s", await response.text())
                return []

def extract_places_from_text(text: str, database_places: dict) -> list:
    found_places = []

    print(f"Текст для обработки: {text}")

    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if len(line) > 0:
            for place_name in database_places.keys():
                if place_name in line.lower():  
                    found_places.append((place_name, str(database_places[place_name])))
                    print(f"Добавлено место: {place_name}, время: {database_places[place_name]}ч")
                    break  

    return found_places

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("""
Здравствуйте! 🌟
Я здесь, чтобы помочь вам создать незабываемое путешествие! ✈️ Чтобы подобрать оптимальное количество дней для вашей поездки и предложить вам самые интересные места для посещения, мне нужно несколько деталей:
🌍 Куда вы планируете поехать?  
💖 Какие у вас интересы?  
🎉 Есть ли какие-то конкретные достопримечательности или мероприятия, которые вы мечтаете посетить?  
Ваши предпочтения позволят мне предложить наиболее подходящие варианты для вашего путешествия. Давайте создадим вместе ваше идеальное приключение! 🌅✨
""")

@dp.message_handler(commands=['get_items'])
async def get_items(message: types.Message):
    db = await db_connect()
    try:
        async with db.execute("SELECT * FROM giga") as cursor:
            items = await cursor.fetchall()
            item_list = "\n".join([f"ID: {item[0]}\n◉ Название: {item[1]}\n◉ Описание: {item[2]}\n◉Среднее времяпровождение: {item[3]}ч\n◉ Теги: {item[4]}\n" for item in items])
            await message.answer(f"Элементы:\n{item_list}" if item_list else "Нет элементов.")
    finally:
        await db.close()

@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    user_query = message.text
    if not any(reagent in user_query for reagent in reagents):
        response = await get_message_from_gigachat(user_query)

        if response:
            await message.answer(response)
        else:
            days = extract_days(user_query)
            preferences = await get_gigachat_response(user_query)
            itinerary = await create_itinerary(days, preferences)
            await message.answer(itinerary)
    else:
        days = extract_days(user_query)
        preferences = await get_gigachat_response(user_query)
        itinerary = await create_itinerary(days, preferences)
        await message.answer(itinerary)

if __name__ == '__main__':
    print(banner)
    executor.start_polling(dp, skip_updates=True)