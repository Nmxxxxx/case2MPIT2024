import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor
import uuid
import requests
import json

API_TOKEN = '7999577438:AAF-WBB8_ABAbEa-MhuR-4wTKL3s4xaUUm4' 
GIGACHAT_API_URL = 'https://gigachat.devices.sberbank.ru/api/v1/chat/completions' 
GIGACHAT_API_KEY = 'YmZlNGMwYWQtM2E0ZS00NzQ3LWIzMzQtZWYxN2NjNTYxODEyOmZjOWQ0ZDNlLTlhMzctNGRiMi1iNTVmLTMzMjYwNmI2MzBjZg=='


logging.basicConfig(level=logging.INFO)


bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

def get_access_token():
    master_token = "YmZlNGMwYWQtM2E0ZS00NzQ3LWIzMzQtZWYxN2NjNTYxODEyOmZjOWQ0ZDNlLTlhMzctNGRiMi1iNTVmLTMzMjYwNmI2MzBjZg=="  # Задайте ваш токен здесь
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

async def get_gigachat_response(query: str) -> str:
    access_token = get_access_token()
    payload = json.dumps({
        "model": "GigaChat",
        "messages": [
            {
            "role": "user",
            "content": query,
            }
        ],
        "stream": False,
        "repetition_penalty": 1
        })
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }
    print('123')
    
    async with aiohttp.ClientSession() as session:
        async with session.post(GIGACHAT_API_URL, headers=headers, data=payload, ssl=False) as response:
            if response.status == 200:
                json_response = await response.json()
                print(json_response)
                return json_response['choices'][0]['message']['content']
            else:
                logging.error("Ошибка запроса к GigaChat: %s", await response.text())
                return 'Ошибка: не удалось получить ответ от GigaChatAI.'

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    await message.reply("""
Здравствуйте! 🌟

Я здесь, чтобы помочь вам создать незабываемое путешествие! ✈️ Чтобы подобрать оптимальное количество дней для вашей поездки и предложить вам самые интересные места для посещения, мне нужно несколько деталей:

🌍 Куда вы планируете поехать?  
Каждое направление уникально, и я хочу знать, куда поведет вас ваше сердечное желание!

💖 Какие у вас интересы?  
Предпочитаете ли вы культурный отдых с погружением в историю, восхитительные природные пейзажи, или, возможно, гастрономические приключения, где вы сможете попробовать локальные деликатесы? Дайте знать, что вас вдохновляет!

🎉 Есть ли какие-то конкретные достопримечательности или мероприятия, которые вы мечтаете посетить?  
Будь то знаменитый музей, уютное кафе с потрясающими десертами или захватывающее событие, я помогу вам включить это в ваш план!

Ваши предпочтения позволят мне предложить наиболее подходящие варианты для вашего путешествия. Давайте создадим вместе ваше идеальное приключение! 🌅✨
""")


@dp.message_handler(content_types=['text'])
async def handle_text(message: types.Message):
    user_query = message.text
    response = await get_gigachat_response(user_query)
    await message.answer(response)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)