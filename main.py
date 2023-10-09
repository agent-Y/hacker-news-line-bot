import feedparser
import requests
import logging
from summarizer import Summarizer
from bs4 import BeautifulSoup
from local_env import *


hn_rss_url = 'https://hnrss.org/show?points=100&comments=25'
channel_id = CHANNEL_ID
channel_secret = CHANNEL_SECRET
line_user_id = LINE_USER_ID

access_token_url = 'https://api.line.me/v2/oauth/accessToken'

logging.basicConfig(filename='app.log', filemode='w',
                    format='%(name)s - %(levelname)s - %(message)s')


def get_access_token():
    try:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {'grant_type': 'client_credentials',
                'client_id': channel_id, 'client_secret': channel_secret}
        response = requests.post(access_token_url, headers=headers, data=data)
        access_token = response.json().get('access_token')
        return access_token
    except Exception as e:
        logging.error("Error getting access token: %s", e)
        return None


def get_article_content(article_link):
    try:
        # 記事のリンクから記事の本文を取得
        response = requests.get(article_link)
        soup = BeautifulSoup(response.text, 'html.parser')
        paragraphs = soup.find_all('p')  # 記事の段落を取得
        article_content = '\n'.join([p.get_text() for p in paragraphs])
        return article_content
    except Exception as e:
        return None


def get_latest_hacker_news():
    try:
        hn_feed = feedparser.parse(hn_rss_url)
        if hn_feed.entries:
            latest_news = hn_feed.entries[0]
            title = latest_news.title
            link = latest_news.link
            article_content = get_article_content(link)

            # BERTモデルを使用してニュースの要約を生成
            model = Summarizer()
            summary = model(article_content)

            return f"{title}\n{link}\n\n要約：\n{summary}"
        else:
            return "Hacker Newsからニュースを取得できませんでした。"
    except Exception as e:
        logging.error("Error getting latest Hacker News: %s", e)
        return None


def create_message_data(message):
    return {
        'to': line_user_id,
        'messages': [{'type': 'text', 'text': message}]
    }


def send_line_message(message_data, access_token):
    try:
        headers = {'Content-Type': 'application/json',
                   'Authorization': f'Bearer {access_token}'}
        response = requests.post(
            'https://api.line.me/v2/bot/message/push', headers=headers, json=message_data)
        return response.status_code, response.text
    except Exception as e:
        logging.error("Error sending LINE message: %s", e)
        return None, None


if __name__ == '__main__':
    access_token = get_access_token()
    if access_token is None:
        print("Failed to get access token.")
    else:
        latest_news = get_latest_hacker_news()
        if latest_news is None:
            print("Failed to get latest Hacker News.")
        else:
            message_data = create_message_data(latest_news)
            status_code, response_text = send_line_message(
                message_data, access_token)
            if status_code == 200:
                print("LINEにメッセージを送信しました。")
            else:
                print(
                    f"LINEにメッセージを送信できませんでした。エラーコード: {status_code}, レスポンス: {response_text}")
