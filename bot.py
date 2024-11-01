from imports import *
from banner import banner
import re
import random
import os

API_TOKEN = '7999577438:AAF-WBB8_ABAbEa-MhuR-4wTKL3s4xaUUm4' 
GIGACHAT_API_URL = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions' 
GIGACHAT_API_KEY = 'YmZlNGMwYWQtM2E0ZS00NzQ3LWIzMzQtZWYxN2NjNTYxODEyOmZjOWQ0ZDNlLTlhMzctNGRiMi1iNTVmLTMzMjYwNmI2MzBjZg=='


logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

async def db_connect():
    return await aiosqlite.connect('case2giga.db')

reagents = ['маршрут', 'путь', 'маршут', 'мршрут', 'маршрт', 'мршрт', 'маршрyт', 'план', 'плн', 'программу', 'програму', 'прогу', 'распорядок', 'расписание', 'распсание' ]
async def get_places_from_db():
    db = await db_connect()  
    places = []
    try:
        async with db.execute("SELECT name, average_time, tags FROM giga") as cursor:
            async for row in cursor:
                name = row[0].strip()  
                average_time = row[1]  
                tags = row[2].split(',') if row[2] else [] 

                places.append({
                    'name': name,
                    'average_time': average_time,
                    'tags': [tag.strip() for tag in tags]  
                })
    except Exception as e:
        print(f"Ошибка при извлечении данных: {e}") 
    finally:
        await db.close()  
    return places

def extract_days(user_query: str) -> int:
    match = re.search(r'на (\d+) (дня|день|дней)', user_query)
    return int(match.group(1)) if match else 1

async def create_itinerary(days: int, preferences: list) -> str:
    total_hours_per_day = 8
    max_places_per_day = 3  
    itinerary = []
    
    if len(preferences) < days:
        return "Недостаточно предпочтений для каждого дня."

    random.shuffle(preferences)

    used_places = set()  
    beach_added_today = False  

    for day in range(days):
        available_time = total_hours_per_day
        daily_places = []
        day_total_time = 0

        for place in preferences:
            if place['name'] not in used_places:
                average_time = float(place['average_time'])
                if len(daily_places) < max_places_per_day:
                    if 'пляж' in place['tags']:
                        if not beach_added_today: 
                            daily_places.append(place)
                            used_places.add(place['name'])

                            available_time -= average_time  
                            day_total_time += average_time  
                            beach_added_today = True 
                        
                    else: 
                        if available_time >= average_time:  
                            daily_places.append(place)
                            used_places.add(place['name'])

                            available_time -= average_time  
                            day_total_time += average_time  
        if daily_places:
            day_itinerary = ', '.join([f"{place['name']} ({place['average_time']}ч)" for place in daily_places])
            daily_tags = '; '.join(['; '.join(place['tags']) for place in daily_places])

            itinerary.append(
                f"🌟 **День {day + 1}** 🌟\n\n"
                f"🗺️ **Места для посещения:**\n"
                f"{day_itinerary}\n"
                f"**Теги:** {daily_tags}\n"
                f"⏰ **Общее время**: {day_total_time:.1f} ч\n"
            )
        else:
            itinerary.append(f"🌟 **День {day + 1}**: Нет доступных мероприятий.")
        beach_added_today = False 

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
                # print(f"Ответ от GigaChat: {content}")

                database_places = await get_places_from_db()
                print(database_places)
                # preferences = extract_places_from_text(content, database_places)
                
                # print('#'*10)
                # print(preferences)
                # print(f"Извлdеченные предпочтения: {preferences}")
                return database_places
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

def extract_places_from_text(text: str, database_places: list) -> list:
    found_places = []
    print(f"Текст для обработки: {text}")

    lines = text.splitlines()

    for line in lines:
        line = line.strip()
        if len(line) > 0:
        
            for place in database_places:  
                place_name = place['name']  
                if place_name in line.lower():  
                    found_places.append(place)  
                    print(f"Добавлено место: {place_name}, данные: {place}")
                    break  

    return found_places

@dp.message_handler(commands=['start', 'restart'])
async def send_welcome(message: types.Message):

    photo_path = os.path.abspath('img/starter.png')  

    
    with open(photo_path, 'rb') as photo:  
        await message.answer_photo(photo=photo, caption="""
Здравствуйте! 🌟

Я здесь, чтобы помочь вам создать незабываемое путешествие! ✈️ Чтобы подобрать оптимальное количество дней для вашей поездки и предложить вам самые интересные места для посещения, мне нужно несколько деталей:

🌍 Куда вы планируете поехать?  

💖 Какие у вас интересы?  

🎉 Есть ли какие-то конкретные достопримечательности или мероприятия, которые вы мечтаете посетить?  

Ваши предпочтения позволят мне предложить наиболее подходящие варианты для вашего путешествия. Давайте создадим вместе ваше идеальное приключение! 🌅✨
""")
@dp.message_handler(commands=['help'])
async def help(message: types.Message):
    await message.answer("""
        Для использования бота напишите ваш запрос.\n
        Пример запроса: Составь маршрут на 5 дней. 

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
        pass
    else:
        days = extract_days(user_query)
        preferences = await get_gigachat_response(user_query)
        itinerary = await create_itinerary(days, preferences)
        await message.answer(itinerary)

if __name__ == '__main__':
    print(banner)
    executor.start_polling(dp, skip_updates=True)