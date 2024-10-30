import requests
from bs4 import BeautifulSoup

website = 'https://bolshayastrana.com/dostoprimechatelnosti/kaliningradskaya-oblast'

try:

    result = requests.get(website)
    result.raise_for_status()


    content = result.text
    soup = BeautifulSoup(content, 'lxml')


    cards = soup.find_all('div', class_='article_card')
    
    if not cards:
        print("Не найдено статьи в Kaliningradской области")
        

    with open('kaliningrad_articles.txt', 'w', encoding='utf-8') as file:
        for card in cards:
            title = card.find('div', class_='article-card__title')
            text = card.find('div', class_='article-card__text')
            
            if title and text:
                title_text = title.get_text(strip=True)
                text_content = text.get_text(strip=True)
                

                file.write(f"Заголовок: {title_text}\n")
                file.write(f"Текст: {text_content}\n\n")

    print("Данные записаны в kaliningrad_articles.txt")

except Exception as e:
    print(f"Произошла ошибка: {e}")