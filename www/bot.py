import time
import feedparser
import requests
from dotenv import load_dotenv
import os
from bs4 import BeautifulSoup

load_dotenv()  # Load environment variables from .env file

# Линкът към Google News RSS (примерно за PHP новини на английски или български)
RSS_URL = os.getenv('RSS_URL')

# Webhook URL-а, който вземаш от настройките на Discord канала -> Integrations -> Webhooks
DISCORD_WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')

# Множество за памет на вече пратените статии (за рестарт на бота може да се пази в JSON/SQLite)
sent_articles = set()

def get_article_image(url):
    """ Опитва се да извади Open Graph картинката (og:image) от целевата статия """
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        # Слагаме кратки таймаути, за да не забие бота, ако сайтът бави
        response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            img_tag = soup.find('meta', property='og:image')
            if img_tag and img_tag.get('content'):
                return img_tag['content']
    except Exception:
        pass
    return None

def fetch_and_push():
    print("Проверка за нови статии...")
    feed = feedparser.parse(RSS_URL)
    
    # Обръщаме ги, за да пускаме най-старите от новите в правилен ред, ако са много
    for entry in reversed(feed.entries[:1]): # Взимаме топ 1 най-свежи
        article_id = entry.id if 'id' in entry else entry.link
        
        if article_id not in sent_articles:
            # Добавяме го към изпратените
            sent_articles.add(article_id)
            
            # Скрапваме картинката от линка на статията
            image_url = get_article_image(entry.link)
            
            # Форматираме Discord Embed съобщение с картинка отдясно/долу
            embed = {
                "title": entry.title[:256], # Discord лимит за заглавие
                "url": entry.link,
                "color": 3447003, # Приятно синьо встрани
                "footer": {"text": "IT BASTION BG • Tech News Bot"}
            }
            
            if image_url:
                embed["image"] = {"url": image_url}
                
            payload = {
                "embeds": [embed]
            }
            
            response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
            
            if response.status_code == 204:
                print(f"Успешно пратено: {entry.title}")
            else:
                print(f"Грешка при пращане: {response.status_code}")

if __name__ == "__main__":
    print("RSS ботът стартира...")
    while True:
        try:
            fetch_and_push()
        except Exception as e:
            print(f"Възникна грешка: {e}")
        
        # Проверява на всеки 30 минути (1800 секунди)
        time.sleep(1800)