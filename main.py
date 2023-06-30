

# from googleapiclient.discovery import build
# from googleapiclient.errors import HttpError
# from youtube_transcript_api import YouTubeTranscriptApi
import urllib
import openai
import requests
from bs4 import BeautifulSoup

import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize, sent_tokenize
import heapq
import telebot
from urllib.parse import urlparse
import vk_api


bot = telebot.TeleBot('')
openai.api_key = "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"

#https://oauth.vk.com/authorize?client_id=&redirect_uri=https://api.vk.com/blank.html&scope=offline.wall&response_type=token



nltk.download('punkt')

QUESTION = 0


def start(update, context):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Привет! Хочешь опубликовать статью в группе ВК? "
                                                                    "Введи текст статьи или ссылку на сайт:")
    return QUESTION

@bot.message_handler(func=lambda _: True)
def handle_message(url):
    parsed_url = urllib.parse.urlparse(url.text)

    if not any([parsed_url.scheme, parsed_url.netloc]):
        bot.send_message(chat_id=url.from_user.id, text="Ваша запись будет опубликована в группу вк")
        publish_post( url.text, url)

    # elif 'youtube' in parsed_url.netloc:
    #     video(url)
    #
    #
    # elif any(ext in parsed_url.path for ext in ['.mp4', '.avi']):
    #     return "Ссылка на видео файл"

    else:
        generate_handler(url)


def publish_post( text_post, message):
    # Авторизация
    vk_access_token = 'your_vk_access_token'
    url="https://api.vk.com/method/wall.post"
    group_id = 'id_group'
    from_group = 1
    version_vk = "5.131"
    try:
        response = requests.post(
            url=url,
            params={
                'access_token': vk_access_token,
                'from_group': from_group,
                'owner_id': group_id,
                'message': text_post,
                'v': version_vk,
            }
        )


        print(response)

        bot.send_message(chat_id=message.from_user.id, text="Пост успешно опубликован.")
    except vk_api.exceptions.ApiError as e:
        print(e)
        bot.send_message(chat_id=message.from_user.id, text="Ошибка при публикации поста ")

def generate_handler(message):
    try:
        response = requests.get(message.text)
        soup = BeautifulSoup(response.content, 'html.parser')
        all_p_tags = soup.find_all('p')
        all_title = soup.find_all('title')
        text_page=""
        title_page=""
        for tag in all_p_tags:
            text_page += tag.text.strip()+"\n"  # удаляем лишние пробелы в начале и конце текста
        for tag in all_title:
            title_page += tag.text.strip() + "\n"
        summary = summarize(text_page, 2)
        # text2 = ''.join(map(str, soup.findAll(string=True)))

        prompt = title_page+" "+summary[:1000]  # Для ограничения длины запроса
        print(prompt)
        completions = openai.Completion.create(
            model="text-davinci-003",
             prompt="Сгенерируй статью, используя данный текст: "+title_page+" "+prompt,
            max_tokens=2000,
            n=1,
            stop=None,
            temperature=0.2,

        )
        print(completions['choices'][0])

        title = openai.Completion.create(
            model="text-davinci-003",
            prompt="Сгенерируй краткий заголовок для данного текста: "+completions['choices'][0].text[:2500],
            max_tokens=2000,
            n=1,
            stop=None,
            temperature=0.2,
        )
        bot.send_message(chat_id=message.from_user.id,
                         text="<b>" + title['choices'][0].text.strip() + "</b>\n" +completions['choices'][0].text[:2500],
                         parse_mode='HTML')
        publish_post(title['choices'][0].text.strip() + "\n" +completions['choices'][0].text[:2500],message)

    except Exception as e:
        bot.send_message(chat_id=message.from_user.id, text="Не удалось установить соединение с сервером:(")
        print(str(e))

def summarize(text, n):
    stemmer = PorterStemmer()
    stop_words = set(stopwords.words("english"))
    words = word_tokenize(text)

    freq_table = {}
    for word in words:
        word = stemmer.stem(word)
        if word in stop_words:
            continue
        if word in freq_table:
            freq_table[word] += 1
        else:
            freq_table[word] = 1

    sentences = sent_tokenize(text)
    sentence_scores = {}
    for sentence in sentences:
        for word, freq in freq_table.items():
            if word in sentence.lower():
                if sentence in sentence_scores:
                    sentence_scores[sentence] += freq
                else:
                    sentence_scores[sentence] = freq
    summary_sentences = heapq.nlargest(n, sentence_scores, key=sentence_scores.get)
    summary = ' '.join(summary_sentences)
    return summary


    #


bot.polling(none_stop=True)




# message.from_user.id
