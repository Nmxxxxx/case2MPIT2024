
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

reagents = ['маршрут', 'путь', 'маршут', 'мршрут', 'маршрт', 'мршрт', 'маршрyт']

async def get_places_from_db():
    db = await db_connect()
    places = []
    try:
        async with db.execute("SELECT name, average_time, tags FROM giga") as cursor:
            async for row in cursor:
                name = row[0].strip().lower()
                average_time = row[1]

                tags = row[2].split(',') if row[2] else []
                tags = [tag.strip() for tag in tags]  

                places.append({
                    'name': name,
                    'average_time': average_time,
                    'tags': tags
                })

                print(f"Загружено место: {name}, время: {average_time}, теги: {tags}")

    finally:
        await db.close()

    return places



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
                return content
            else:
                logging.error("Ошибка запроса к GigaChat: %s", await response.text())
                return []

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


@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    user_query = message.text
    
    preferences = await get_gigachat_response(user_query)
    await message.answer(preferences)


if __name__ == '__main__':
    print(banner)
    executor.start_polling(dp, skip_updates=True)