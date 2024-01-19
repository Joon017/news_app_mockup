from flask import Flask, request, jsonify
import time
import json
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from transformers import GPT2Tokenizer
import torch
import spacy
import requests
from celery import Celery

app = Flask(__name__)
app.config.from_object('celery_config')

celery = Celery(app.name)
celery.config_from_object('celery_config')



# COMMON CONFIGURATIONS
date_format = "%d-%m-%Y"
max_pages = 50
topics = ["Generative AI"]



# COMMON METHODS
# SPACY FOR STOPWORD REMOVAL
nlp = spacy.load("en_core_web_sm")

def remove_stopwords_spacy(text):
    doc = nlp(text)
    tokens = [token.text for token in doc if not token.is_stop]
    return ' '.join(tokens)

def count_tokens(text, model_name="gpt2"):
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    tokens = tokenizer.tokenize(tokenizer.decode(tokenizer.encode(text)))
    num_tokens = len(tokens)
    return num_tokens



#METHOD TO FETCH HTML USING BEAUTIFULSOUP
def fetch_html(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # print(soup.prettify())
            return soup
        else:
            print(f"Failed to retrieve content. Status Code: {response.status_code}")
            return False

    except Exception as e:
        print(f"An error occurred: {e}")


celery = Celery(__name__)
celery.config_from_object('celery_config')

# VENTUREBEAT SCRAPER (DEFAULT)
@celery.task
def venturebeat_scraping(cutoff_date, pages):

    scraped_articles = []
    print("---Scraping VentureBeat.com---")
    venturebeat_base_url = "https://venturebeat.com/"

    for topic in topics:

        cutoff = False
        print(f"---Scraping venturebeat.com for topic: {topic}")
        
        while not cutoff:

            for page in range(1, pages):
                if cutoff:
                    break
                try:
                    # Convert topic from topics (list) into URL query format 
                    print(f"---Scraping venturebeat.com page {page} for topic: {topic}")
                    search_query = topic.replace(" ", "+")
                    search_url = f"{venturebeat_base_url}/page/{page}/?s={search_query}"
                    print(search_url)
                    print("")
                    # fetch HTML using the formatted search URL
                    page_html_soup = fetch_html(search_url)

                    # HTML tags finding
                    if page_html_soup:
                        # get all article tags
                        article_tags = page_html_soup.find_all('article')
                        if article_tags:
                            for article_tag in article_tags:
                                # get current article title
                                title_element = article_tag.find_all(class_="ArticleListing__title-link")[0]
                                title = title_element.text
                                print(title)
                                link_tags = article_tag.find_all("a")
                                time_elements = article_tag.find_all(class_='ArticleListing__time')
                                if len(time_elements) > 0:
                                    time_element = time_elements[0]
                                    article_datetime = time_element.get('datetime')
                                    print(article_datetime)

                                    parsed_date = datetime.fromisoformat(article_datetime).date()
                                    article_datetime = parsed_date.strftime("%d-%m-%Y")
                                    print(article_datetime)

                                    cutoff_date_obj = datetime.strptime(cutoff_date, date_format)
                                    article_datetime_obj = datetime.strptime(article_datetime, date_format)
                                    if article_datetime_obj >= cutoff_date_obj:
                                        print("Article datetime within target timeframe")
                                    else:
                                        print("Article datetime beyond target timeframe")
                                        cutoff = True
                                        print("Cutoff scraping for topic")
                                        break

                                    link_tag = link_tags[0]
                                    href = link_tag.get('href')
                                    if href:
                                        print(href)
                                        print('')
                                        print("---Proceeding to scrape article content---")
                                        sub_page_html_soup = fetch_html(href)
                                        article_content_element = sub_page_html_soup.find('div', class_="article-content")
                                        if article_content_element:
                                            article_text = article_content_element.get_text(separator='\n')
                                            cleaned_text = re.sub(r'\s+', ' ', article_text).strip()
                                            # print(cleaned_text)
                                            print("Scraped content: ")
                                            print(cleaned_text)
                                            tokens_cleaned_text = count_tokens(cleaned_text)
                   

                                            print("Scraped content (Stopwords removed): ")
                                            cleaned_text_stopwords_removed = remove_stopwords_spacy(cleaned_text)
                                            print(cleaned_text_stopwords_removed)
                                            tokens_cleaned_text_stopwords_removed = count_tokens(cleaned_text_stopwords_removed)
                                            print(f"Num of tokens before stopwords removal: {tokens_cleaned_text}")
                                            print(f"Num of tokens after stopwords removal: {tokens_cleaned_text_stopwords_removed}")

                                            current_datetime = datetime.now()
                                            current_datetime = current_datetime.strftime("%d-%m-%Y")
                                            print(f"---Scraped on {current_datetime}---")

                                            #Adding entry into scraped article results
                                            scraped_article = {
                                                "title": title,
                                                "topic": topic,
                                                "source": "VentureBeat",
                                                "source_url": venturebeat_base_url,
                                                "article_url": href,
                                                "publish_date": article_datetime,
                                                "content": cleaned_text_stopwords_removed,
                                                "scraped_date": current_datetime
                                            }

                                            scraped_articles.append(scraped_article)
                                    else:
                                        print("Article has no href, unable to scrape further")

                except:
                    print(f"---Page {page} is out of range---, ending scraping for topic {topic}")
                    break

    scraped_articles_json = json.dumps(scraped_articles, indent=2)
    return scraped_articles_json

# VENTUREBEAT SCRAPER (BASED ON SEARCHED TOPIC)
def venturebeat_scraping_search(cutoff_date, pages, searchedTopic):

    scraped_articles = []
    print("---Scraping VentureBeat.com---")
    venturebeat_base_url = "https://venturebeat.com/"

    

    cutoff = False
    print(f"---Scraping venturebeat.com for topic: {searchedTopic}")
    
    while not cutoff:

        for page in range(1, pages):
            if cutoff:
                break
            try:
                # Convert topic from topics (list) into URL query format 
                search_query = searchedTopic.replace(" ", "+")
                search_url = f"{venturebeat_base_url}/page/{page}/?s={search_query}"
           
                # fetch HTML using the formatted search URL
                page_html_soup = fetch_html(search_url)
                if page_html_soup:
                    # get all article tags
                    article_tags = page_html_soup.find_all('article')
                    if article_tags:
                        for article_tag in article_tags:
                            # get current article title
                            title_element = article_tag.find_all(class_="ArticleListing__title-link")[0]
                            title = title_element.text
                            print(title)
                            link_tags = article_tag.find_all("a")
                            time_elements = article_tag.find_all(class_='ArticleListing__time')
                            if len(time_elements) > 0:
                                time_element = time_elements[0]
                                article_datetime = time_element.get('datetime')
                                print(article_datetime)

                                parsed_date = datetime.fromisoformat(article_datetime).date()
                                article_datetime = parsed_date.strftime("%d-%m-%Y")
                                print(article_datetime)

                                cutoff_date_obj = datetime.strptime(cutoff_date, date_format)
                                article_datetime_obj = datetime.strptime(article_datetime, date_format)
                                if article_datetime_obj >= cutoff_date_obj:
                                    print("Article datetime within target timeframe")
                                else:
                                    print("Article datetime beyond target timeframe")
                                    cutoff = True
                                    print("Cutoff scraping for topic")
                                    break

                                link_tag = link_tags[0]
                                href = link_tag.get('href')
                                if href:
                                    print(href)
                                    print('')
                                    print("---Proceeding to scrape article content---")
                                    sub_page_html_soup = fetch_html(href)
                                    article_content_element = sub_page_html_soup.find('div', class_="article-content")
                                    if article_content_element:
                                        article_text = article_content_element.get_text(separator='\n')
                                        cleaned_text = re.sub(r'\s+', ' ', article_text).strip()
                                        print("Scraped content: ")
                                        print(cleaned_text)
                                        tokens_cleaned_text = count_tokens(cleaned_text)
                

                                        print("Scraped content (Stopwords removed): ")
                                        cleaned_text_stopwords_removed = remove_stopwords_spacy(cleaned_text)
                                        print(cleaned_text_stopwords_removed)
                                        tokens_cleaned_text_stopwords_removed = count_tokens(cleaned_text_stopwords_removed)
                                        print(f"Num of tokens before stopwords removal: {tokens_cleaned_text}")
                                        print(f"Num of tokens after stopwords removal: {tokens_cleaned_text_stopwords_removed}")

                                        current_datetime = datetime.now()
                                        current_datetime = current_datetime.strftime("%d-%m-%Y")
                                        print(f"---Scraped on {current_datetime}---")

                                        #Adding entry into scraped article results
                                        scraped_article = {
                                            "title": title,
                                            "topic": searchedTopic,
                                            "source": "VentureBeat",
                                            "source_url": venturebeat_base_url,
                                            "article_url": href,
                                            "publish_date": article_datetime,
                                            "content": cleaned_text_stopwords_removed,
                                            "scraped_date": current_datetime
                                        }

                                        scraped_articles.append(scraped_article)
                                else:
                                    print("Article has no href, unable to scrape further")

            except:
                print(f"---Page {page} is out of range---, ending scraping for topic {searchedTopic}")
                break

    scraped_articles_json = json.dumps(scraped_articles, indent=2)
    return scraped_articles_json


# TECHXPLORE SCRAPER (DEFAULT)
def techxplore_scraping(cutoff_date, pages):
    scraped_articles = []
    #SCRAPING TECHXPLORE.COM

    print("---Scraping techxplore.com---")
    techxplore_base_url = "https://techxplore.com/"
    for topic in topics:
        cutoff = False
        print(f"---Scraping techxplore.com for topic: {topic}")
        while not cutoff:
            for page in range(1, pages):
                if cutoff:
                    break
                try:
                    print(f"---Scraping techxplore.com page {page} for topic: {topic}")
                    search_query = topic.replace(" ", "+")
                    search_url = f"{techxplore_base_url}/search/page{page}.html?search={search_query}"
                    print(search_url)
                    print("")
                    page_html_soup = fetch_html(search_url)
                    if page_html_soup:
                        article_tags = page_html_soup.find_all('article')
                        if article_tags:
                            for article_tag in article_tags:
                                title_element = article_tag.find_all(class_="news-link")[0]
                                title = title_element.text
                                print(title)
                                link_tags = article_tag.find_all("a")
                                time_elements = article_tag.find_all(class_='text-uppercase text-low')
                                if len(time_elements) > 0:
                                    time_element = time_elements[0]
                                    article_datetime_raw = (time_element.text).upper().strip()
                                    if "HOURS AGO" in article_datetime_raw:
                                        current_date = datetime.now()
                                        article_datetime = current_date.strftime("%d-%m-%Y")
                                    else:
                                        parsed_date = datetime.strptime(article_datetime_raw, "%b %d, %Y")
                                        article_datetime = parsed_date.strftime("%d-%m-%Y")

                                    print(article_datetime)

                                    cutoff_date_obj = datetime.strptime(cutoff_date, date_format)
                                    article_datetime_obj = datetime.strptime(article_datetime, date_format)
                                    if article_datetime_obj >= cutoff_date_obj:
                                        print("Article datetime within target timeframe")
                                    else:
                                        print("Article datetime beyond target timeframe")
                                        cutoff = True
                                        print("Cutoff scraping for topic")
                                        break

                                    link_tag = link_tags[0]
                                    href = link_tag.get('href')
                                    if href:
                                        print(href)
                                        print('')
                                        print("---Proceeding to scrape article content---")
                                        sub_page_html_soup = fetch_html(href)
                                        article_content_element = sub_page_html_soup.find('div', class_="mt-4 text-low-up text-regular article-main")
                                        if article_content_element:
                                            article_text = article_content_element.get_text(separator='\n')
                                            cleaned_text = re.sub(r'\s+', ' ', article_text).strip()
                                            # print(cleaned_text)
                                            print(cleaned_text)

                                            current_datetime = datetime.now()
                                            current_datetime = current_datetime.strftime("%d-%m-%Y")
                                            print(f"---Scraped on {current_datetime}---")

                                            #Adding entry into scraped article results
                                            scraped_article = {
                                                "title": title,
                                                "topic": topic,
                                                "source": "Techxplore",
                                                "source_url": "Techxplore.com",
                                                "article_url": href,
                                                "publish_date": article_datetime,
                                                "content": cleaned_text,
                                                "scraped_date": current_datetime
                                            }

                                            scraped_articles.append(scraped_article)
                                    else:
                                        print("Article has no href, unable to scrape further")

                except:
                    print(f"---Page {page} is out of range---, ending scraping for topic {topic}")
                    break

    scraped_articles_json = json.dumps(scraped_articles, indent=2)
    return scraped_articles_json


# TECHXPLORE SCRAPER (BASED ON SEARCHED TOPIC)
def techxplore_scraping_search(cutoff_date, pages, searchedTopic):

    scraped_articles = []
    techxplore_base_url = "https://techxplore.com/"


    cutoff = False
    print(f"---Scraping techxplore.com for topic: {searchedTopic}")

    while not cutoff:
        for page in range(1, pages):
            if cutoff:
                break
            try:
                print(f"---Scraping techxplore.com page {page} for topic: {searchedTopic}")
                search_query = searchedTopic.replace(" ", "+")
                search_url = f"{techxplore_base_url}/search/page{page}.html?search={search_query}"
                print(search_url)
                print("")
                page_html_soup = fetch_html(search_url)
                if page_html_soup:
                    article_tags = page_html_soup.find_all('article')
                    if article_tags:
                        for article_tag in article_tags:
                            title_element = article_tag.find_all(class_="news-link")[0]
                            title = title_element.text
                            print(title)
                            link_tags = article_tag.find_all("a")
                            time_elements = article_tag.find_all(class_='text-uppercase text-low')
                            if len(time_elements) > 0:
                                time_element = time_elements[0]
                                article_datetime_raw = (time_element.text).upper().strip()
                                if "HOURS AGO" in article_datetime_raw:
                                    current_date = datetime.now()
                                    article_datetime = current_date.strftime("%d-%m-%Y")
                                else:
                                    parsed_date = datetime.strptime(article_datetime_raw, "%b %d, %Y")
                                    article_datetime = parsed_date.strftime("%d-%m-%Y")

                                print(article_datetime)

                                cutoff_date_obj = datetime.strptime(cutoff_date, date_format)
                                article_datetime_obj = datetime.strptime(article_datetime, date_format)
                                if article_datetime_obj >= cutoff_date_obj:
                                    print("Article datetime within target timeframe")
                                else:
                                    print("Article datetime beyond target timeframe")
                                    cutoff = True
                                    print("Cutoff scraping for topic")
                                    break

                                link_tag = link_tags[0]
                                href = link_tag.get('href')
                                if href:
                                    print(href)
                                    print('')
                                    print("---Proceeding to scrape article content---")
                                    sub_page_html_soup = fetch_html(href)
                                    article_content_element = sub_page_html_soup.find('div', class_="mt-4 text-low-up text-regular article-main")
                                    if article_content_element:
                                        article_text = article_content_element.get_text(separator='\n')
                                        cleaned_text = re.sub(r'\s+', ' ', article_text).strip()
                                        # print(cleaned_text)
                                        print(cleaned_text)

                                        current_datetime = datetime.now()
                                        current_datetime = current_datetime.strftime("%d-%m-%Y")
                                        print(f"---Scraped on {current_datetime}---")

                                        #Adding entry into scraped article results
                                        scraped_article = {
                                            "title": title,
                                            "topic": searchedTopic,
                                            "source": "Techxplore",
                                            "source_url": techxplore_base_url,
                                            "article_url": href,
                                            "publish_date": article_datetime,
                                            "content": cleaned_text,
                                            "scraped_date": current_datetime
                                        }

                                        scraped_articles.append(scraped_article)
                                else:
                                    print("Article has no href, unable to scrape further")

            except:
                print(f"---Page {page} is out of range---, ending scraping for topic {searchedTopic}")
                break

    scraped_articles_json = json.dumps(scraped_articles, indent=2)
    return scraped_articles_json


# ZDNET SCRAPER (DEFAULT)
def zdnet_scraping(cutoff_date, pages):
    scraped_articles = []
    #SCRAPING ZDNET.COM

    print("---Scraping zdnet.com---")
    zdnet_base_url = "https://zdnet.com"
    for topic in topics:
        cutoff = False
        print(f"---Scraping zdnet.com for topic: {topic}")
        while not cutoff:
            for page in range(1, pages):
                if cutoff:
                    break
                try:
                    print(f"---Scraping zdnet.com page {page} for topic: {topic}")
                    search_query = topic.replace(" ", "%20")
                    if page == 1:
                        search_url = f"{zdnet_base_url}/search/?o=1&q={search_query}&t=16"
                    else:
                        search_url = f"{zdnet_base_url}/search/{page}/?o=1&q={search_query}&t=16"
                    print(search_url)
                    print("")
                    page_html_soup = fetch_html(search_url)
                    if page_html_soup:
                        article_tags = page_html_soup.find_all('article')
                        if article_tags:
                            for article_tag in article_tags:

                                content_element = article_tag.find_all(class_="content")[0]
                                h3_title_element = content_element.find("h3")
                                title = h3_title_element.text

                                print(title)

                                link_tags = article_tag.find_all("a")
                                time_elements = article_tag.find_all(class_="meta")
                                if len(time_elements) > 0:
                                    time_element = time_elements[0]
                                    time_element = time_element.find("span")

                                    article_datetime_raw = (time_element.text).upper().strip()
                                    print(article_datetime_raw)

                                    if "HOURS AGO" in article_datetime_raw:
                                        current_date = datetime.now()
                                        article_datetime = current_date.strftime("%d-%m-%Y")
                                    elif "DAY" in article_datetime_raw :
                                        days = int(article_datetime_raw.split(" ")[0])
                                        current_date = datetime.now()
                                        calc_article_datetime = current_date - timedelta(days=days)
                                        article_datetime = calc_article_datetime.strftime("%d-%m-%Y")
                                    else:
                                        parsed_date = datetime.strptime(article_datetime_raw, "%B %d, %Y")
                                        article_datetime = parsed_date.strftime("%d-%m-%Y")

                                    cutoff_date_obj = datetime.strptime(cutoff_date, date_format)
                                    article_datetime_obj = datetime.strptime(article_datetime, date_format)
                                    if article_datetime_obj >= cutoff_date_obj:
                                        print("Article datetime within target timeframe")
                                    else:
                                        print("Article datetime beyond target timeframe")
                                        cutoff = True
                                        print("Cutoff scraping for topic")
                                        break

                                    link_tag = link_tags[0]
                                    print(link_tag)
                                    href = link_tag.get('href')
                                    if href:
                                        href = zdnet_base_url + href
                                        print(href)
                                        print('')
                                        print("---Proceeding to scrape article content---")
                                        sub_page_html_soup = fetch_html(href)
                                        article_content_element = sub_page_html_soup.find('div', class_="c-ShortcodeContent")
                                        # print(article_content_element)
                                        if article_content_element:
                                            article_text = article_content_element.get_text(separator='\n')
                                            cleaned_text = re.sub(r'\s+', ' ', article_text).strip()
                                            # print(cleaned_text)
                                            print(cleaned_text)


                                            current_datetime = datetime.now()
                                            current_datetime = current_datetime.strftime("%d-%m-%Y")
                                            print(f"---Scraped on {current_datetime}---")
                                            print(" ")

                                            #Adding entry into scraped article results
                                            scraped_article = {
                                                "title": title,
                                                "topic": topic,
                                                "source": "zdnet",
                                                "source_url": "zdnet.com",
                                                "article_url": href,
                                                "publish_date": article_datetime,
                                                "content": cleaned_text,
                                                "scraped_date": current_datetime
                                            }

                                            scraped_articles.append(scraped_article)
                                    else:
                                        print("Article has no href, unable to scrape further")

                except:
                    print(f"---Page {page} is out of range---, ending scraping for topic {topic}")
                    break

    scraped_articles_json = json.dumps(scraped_articles, indent=2)
    return scraped_articles_json


# ZDNET SCRAPER (BASED ON SEARCHED TOPIC)
def zdnet_scraping_search(cutoff_date, pages, searchedTopic):

    scraped_articles = []
    zdnet_base_url = "https://zdnet.com"

 
    cutoff = False
    print(f"---Scraping zdnet.com for topic: {searchedTopic}")
    while not cutoff:
        for page in range(1, pages):
            if cutoff:
                break
            try:
                print(f"---Scraping zdnet.com page {page} for topic: {searchedTopic}")
                search_query = searchedTopic.replace(" ", "%20")
                if page == 1:
                    search_url = f"{zdnet_base_url}/search/?o=1&q={search_query}&t=16"
                else:
                    search_url = f"{zdnet_base_url}/search/{page}/?o=1&q={search_query}&t=16"
              

                page_html_soup = fetch_html(search_url)
                if page_html_soup:
                    article_tags = page_html_soup.find_all('article')
                    if article_tags:
                        for article_tag in article_tags:

                            content_element = article_tag.find_all(class_="content")[0]
                            h3_title_element = content_element.find("h3")
                            title = h3_title_element.text

                            print(title)

                            link_tags = article_tag.find_all("a")
                            time_elements = article_tag.find_all(class_="meta")
                            if len(time_elements) > 0:
                                time_element = time_elements[0]
                                time_element = time_element.find("span")

                                article_datetime_raw = (time_element.text).upper().strip()
                                print(article_datetime_raw)

                                if "HOURS AGO" in article_datetime_raw:
                                    current_date = datetime.now()
                                    article_datetime = current_date.strftime("%d-%m-%Y")
                                elif "DAY" in article_datetime_raw :
                                    days = int(article_datetime_raw.split(" ")[0])
                                    current_date = datetime.now()
                                    calc_article_datetime = current_date - timedelta(days=days)
                                    article_datetime = calc_article_datetime.strftime("%d-%m-%Y")
                                else:
                                    parsed_date = datetime.strptime(article_datetime_raw, "%B %d, %Y")
                                    article_datetime = parsed_date.strftime("%d-%m-%Y")

                                cutoff_date_obj = datetime.strptime(cutoff_date, date_format)
                                article_datetime_obj = datetime.strptime(article_datetime, date_format)
                                if article_datetime_obj >= cutoff_date_obj:
                                    print("Article datetime within target timeframe")
                                else:
                                    print("Article datetime beyond target timeframe")
                                    cutoff = True
                                    print("Cutoff scraping for topic")
                                    break

                                link_tag = link_tags[0]
                                print(link_tag)
                                href = link_tag.get('href')
                                if href:
                                    href = zdnet_base_url + href
                                    print(href)
                                    print('')
                                    print("---Proceeding to scrape article content---")
                                    sub_page_html_soup = fetch_html(href)
                                    article_content_element = sub_page_html_soup.find('div', class_="c-ShortcodeContent")

                                    if article_content_element:
                                        article_text = article_content_element.get_text(separator='\n')
                                        cleaned_text = re.sub(r'\s+', ' ', article_text).strip()
                                        # print(cleaned_text)
                                        print(cleaned_text)


                                        current_datetime = datetime.now()
                                        current_datetime = current_datetime.strftime("%d-%m-%Y")
                                        print(f"---Scraped on {current_datetime}---")
                                        print(" ")

                                        #Adding entry into scraped article results
                                        scraped_article = {
                                            "title": title,
                                            "topic": searchedTopic,
                                            "source": "zdnet",
                                            "source_url": "zdnet.com",
                                            "article_url": href,
                                            "publish_date": article_datetime,
                                            "content": cleaned_text,
                                            "scraped_date": current_datetime
                                        }

                                        scraped_articles.append(scraped_article)
                                else:
                                    print("Article has no href, unable to scrape further")

            except:
                print(f"---Page {page} is out of range---, ending scraping for topic {searchedTopic}")
                break

    scraped_articles_json = json.dumps(scraped_articles, indent=2)
    return scraped_articles_json




# ANALYSER URL FOR UPLOAD
analyser_url = "http://127.0.0.1:5002/upload"

# SCRAPE_DEFAULT ROUTE
@app.route('/scrape_default', methods=['GET','POST'])
def scrape_default():
    try:
        # Get the current date
        current_date = datetime.now().date()

        # Calculate the date exactly one week ago
        cutoff_date = current_date - timedelta(days=7)

        # Convert the date to "%d-%m-%Y" format
        formatted_date = cutoff_date.strftime("%d-%m-%Y")

        ####### starting scraping across ALL sites #######
        scraped_articles_venturebeat = venturebeat_scraping(cutoff_date=formatted_date, pages=max_pages)
        # scraped_articles_techxplore = techxplore_scraping(cutoff_date=cutoffDate, pages=max_pages)
        # scraped_articles_zdnet = zdnet_scraping(cutoff_date=cutoffDate, pages=max_pages)

        ####### RESULTS (JSON) #######
        combined_results = json.loads(scraped_articles_venturebeat)
        # combined_results.extend(json.loads(scraped_articles_techxplore))
        # combined_results.extend(json.loads(scraped_articles_zdnet))
        print(combined_results)

        ####### Send the combined results to the analyser.py app (upload route) ######
        response = requests.post(
            analyser_url,
            json={"scraped_articles": combined_results}
        )

        ####### Check the response from the analyser.py app #######
        if response.status_code == 200:
            return jsonify({"success": "Data sent to analyser.py successfully"})
        else:
            return jsonify({"error": f"Failed to send data. Status Code: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# SCRAPE_CUSTOM ROUTE
@app.route('/scrape_custom', methods=['GET','POST'])
def scrape_custom():
    try:
        # Get the current date
        current_date = datetime.now().date()
        # Calculate the date exactly one week ago
        cutoff_date = current_date - timedelta(days=7)

        # Get the search query from the request
        search_query = request.form.get('search_query')

        if not search_query:
            return jsonify({"error": "Search query is missing"}), 400

        ####### starting scraping for ALL sites #######
        scraped_articles_venturebeat = venturebeat_scraping_search(cutoff_date=cutoff_date, pages=max_pages, searchedTopic=search_query)
        # scraped_articles_techxplore = techxplore_scraping_search(cutoff_date=cutoff_date, pages=max_pages, searchedTopic=search_query)
        # scraped_articles_zdnet = zdnet_scraping_search(cutoff_date=cutoff_date, pages=max_pages, searchedTopic=search_query)

        ####### RESULTS (JSON) #######
        combined_results = json.loads(scraped_articles_venturebeat)
        # combined_results.extend(json.loads(scraped_articles_techxplore))
        # combined_results.extend(json.loads(scraped_articles_zdnet))

        ####### Send the combined results to the analyser.py app #######
        response = requests.post(
            analyser_url,  
            json={"scraped_articles": combined_results}
        )

        ####### Check the response from the analyser.py app #######
        if response.status_code == 200:
            return jsonify({"success": "Data sent to analyser.py successfully"})
        else:
            return jsonify({"error": f"Failed to send data. Status Code: {response.status_code}"}), 500

    except Exception as e:
        return jsonify({"error": str(e)})


if __name__ == '__main__':
    app.run(port=5001, debug=True)
