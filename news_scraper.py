import json
import time
import json5
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta
from transformers import BartTokenizer, BartForConditionalGeneration
import torch
import spacy
from transformers import GPT2Tokenizer
from apscheduler.schedulers.blocking import BlockingScheduler

#IMPORTING BART SUMMARISATION MODEL
# model_name = "facebook/bart-large-cnn"
# tokenizer = BartTokenizer.from_pretrained(model_name)
# model = BartForConditionalGeneration.from_pretrained(model_name)

#COMMON CONFIGURATIONS
date_format = "%d-%m-%Y"
max_pages = 50
topics = ["Generative AI"]

#COMMON METHODS
#SPACY FOR STOPWORD REMOVAL
nlp = spacy.load("en_core_web_sm")

def remove_stopwords_spacy(text):
    doc = nlp(text)
    tokens = [token.text for token in doc if not token.is_stop]
    return ' '.join(tokens)

#METHOD TO COUNT NUMBER OF TOKENS
def count_tokens(text, model_name="gpt2"):
    # Load the GPT-2 tokenizer
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)

    # Tokenize the text
    tokens = tokenizer.tokenize(tokenizer.decode(tokenizer.encode(text)))

    # Count the number of tokens
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



# VENTUREBEAT SCRAPER
def venturebeat_scraping(cutoff_date, pages):
    scraped_articles = []
    #SCRAPING VENTUREBEAT.COM

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
                    print(f"---Scraping venturebeat.com page {page} for topic: {topic}")
                    search_query = topic.replace(" ", "+")
                    search_url = f"{venturebeat_base_url}/page/{page}/?s={search_query}"
                    print(search_url)
                    print("")
                    page_html_soup = fetch_html(search_url)
                    if page_html_soup:
                        article_tags = page_html_soup.find_all('article')
                        if article_tags:
                            for article_tag in article_tags:
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
                                            #
                                            # #FEDDING CLEAN TEXT INTO SUMMARISER
                                            # print("---Performing article summarisation using BART---")
                                            # input_id = tokenizer.encode(cleaned_text, return_tensors="pt", max_length=1024, truncation=True)
                                            # with torch.no_grad():
                                            #     summary_ids = model.generate(input_id, max_length=700, num_beams=5, length_penalty=2.0, early_stopping=True)
                                            # decoded_summmary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
                                            # print("---Summarisation done with BART---")

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



#TECHXPLORE SCRAPER
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



#TECHXPLORE SCRAPER
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


# LAUNCHING SCRAPER OF VENTUREBEATS
start_time = time.time()
print(venturebeat_scraping(cutoff_date="10-01-2024", pages=max_pages))
end_time = time.time()
elapsed_time = end_time - start_time
print(f"Time taken: {elapsed_time} seconds")

#LAUNCHING SCRAPER OF TECHXPLORE
# print(techxplore_scraping(cutoff_date="15-12-2023", pages=max_pages))

#LAUNCHING SCRAPER OF ZDNET
# print(zdnet_scraping(cutoff_date="15-12-2023", pages=max_pages))







