from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from os import environ
import json
import pymongo
from bson import ObjectId
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import time
from openai import AzureOpenAI

client = AzureOpenAI(api_key="cfd349e9242e4495bad6aa347a16b0c9", 
                    azure_endpoint="https://chatbotapi1.openai.azure.com",
                    api_version='2023-05-15')


embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

# FLASK APP
app = Flask(__name__)

# CROSS ORIGIN RESOURCE SHARING
CORS(app)

# CONNECT TO MONGO
mongo_client = pymongo.MongoClient("mongodb+srv://ckoh2021:MGk9TVzCl4RgRYHN@cluster0.euvgj72.mongodb.net/")

# CONNECT TO NEWSSCRAPER DB
news_scraper_db = mongo_client.get_database('NewsScraper')

# COLLECTIONS IN DB
articles_collection = news_scraper_db.get_collection('Articles')

@app.route('/')
def homepage():
    return render_template("index.html")

@app.route('/vision')
def gpt_vision():
    return render_template("vision.html")

@app.route('/get_trends', methods=['GET'])
def get_trends():

    # CREATE OBJECT TO STORE TRENDS
    unique_trends_obj = {}

    # ITERATE THROUGH ALL THE DOCUMENTS IN THE COLLECTION
    # AND GET THE TRENDS FROM EACH DOCUMENT
    for document in articles_collection.find():
        
        # GET TRENDS ARRAY FROM DOCUMENT
        trends_array = document['trends']

        # ITERATE THROUGH TRENDS ARRAY - ARRAY OF TREND OBJECTS
        for trend_obj in trends_array:
            
            # GET TREND NAME FROM TREND OBJECT
            trend_name = trend_obj['trend']

            # CREATE SIMPLIFIED DOCUMENT OBJECT
            simplified_document = {
                "title": document["title"],
                "topic": document["topic"],
                "content": document["content"],
                "source": document["source"],
                "source_url": document["source_url"],
                "article_url": document["article_url"],
                "publish_date": document["publish_date"],
                "scraped_date": document["scraped_date"]
            }

            # CHECK IF THERE IS AN OBJECT IN THE UNIQUE TRENDS OBJECT THAT HAS THE SAME TREND NAME
            if trend_name in unique_trends_obj:

                # ADD ARTICLE TO THE ARTICLES ARRAY IN THE OBJECT
                unique_trends_obj[trend_name]['articles'].append(simplified_document)

            else:
                # IF THERE ISN'T, CREATE A NEW OBJECT WITH THE TREND NAME AS THE KEY
                unique_trends_obj[trend_name] = {
                    'write_up' : trend_obj['write_up'],
                    'articles': [simplified_document],
                    'date_generated': document['scraped_date']
                }
            

    return unique_trends_obj

@app.route('/generate_newsletter', methods=['GET'])
def generate_newsletter():
    # CREATE OBJECT TO STORE TRENDS
    unique_trends_obj = {}

    # ITERATE THROUGH ALL THE DOCUMENTS IN THE COLLECTION
    # AND GET THE TRENDS FROM EACH DOCUMENT
    for document in articles_collection.find():
        
        # GET TRENDS ARRAY FROM DOCUMENT
        trends_array = document['trends']

        # ITERATE THROUGH TRENDS ARRAY - ARRAY OF TREND OBJECTS
        for trend_obj in trends_array:
            
            # GET TREND NAME FROM TREND OBJECT
            trend_name = trend_obj['trend']

            # CREATE SIMPLIFIED DOCUMENT OBJECT
            simplified_document = {
                "title": document["title"],
                "topic": document["topic"],
                "content": document["content"],
                "source": document["source"],
                "source_url": document["source_url"],
                "article_url": document["article_url"],
                "publish_date": document["publish_date"],
                "scraped_date": document["scraped_date"]
            }

            # CHECK IF THERE IS AN OBJECT IN THE UNIQUE TRENDS OBJECT THAT HAS THE SAME TREND NAME
            if trend_name in unique_trends_obj:

                # ADD ARTICLE TO THE ARTICLES ARRAY IN THE OBJECT
                unique_trends_obj[trend_name]['articles'].append(simplified_document)

            else:
                # IF THERE ISN'T, CREATE A NEW OBJECT WITH THE TREND NAME AS THE KEY
                unique_trends_obj[trend_name] = {
                    'write_up' : trend_obj['write_up'],
                    'articles': [simplified_document],
                    'date_generated': document['scraped_date']
                }
    
    # EMPTY NEWSLETTER STRING
    newsletter_string = ""

    # ITERATE THROUGH THE TRENDS IN THE UNIQUE TRENDS OBJECT
    for trend in unique_trends_obj:

        # TEMPORARY CONTEXT STRING
        context_string = ""

        # ADD THE TREND TO THE CONTEXT STRING
        context_string += trend + "\n\n"

        # GET THE WRITE UP FOR THE TREND
        write_up = unique_trends_obj[trend]['write_up']

        # ADD THE WRITE UP TO THE CONTEXT STRING
        context_string += write_up + "\n\n"

        # GET THE ARTICLES FOR THE TREND
        articles = unique_trends_obj[trend]['articles']

        context_string += "Contributing Articles:\n\n"

        count = 1
        # ITERATE THROUGH THE ARTICLES
        for article in articles:
            # GET THE TITLE OF THE ARTICLE
            title = article['title']

            # GET THE CONTENT OF THE ARTICLE
            content = article['content']

            context_string += str(count) + ". " + title + "\n" + content + "\n\n"

        newsletter_string += context_string

    completion = client.chat.completions.create(
        model="chatgpt4_32_v2", # The deployment name you chose when you deployed the GPT-35-Turbo or GPT-4 model.
        messages=[
            {"role": "system", "content": "You are an assistant helping a user with their technology update newsletter. You are up to date on the latest trends and are insightful with your analysis."}, 
            {"role": "user", "content": "Given the following trend, its write up, and contributing articles, please write a newsletter that totals 1000 words or more. It should talk about the following items, and elaborate about them in detail: 1. Current Technology used for the Main Topic of the Trend, 2. Positive impacts of the Topic, 3. Negative impacts of the Topic, 4. Remedies and possible solutions for the Negative Impacts of the Topic, 5. Final Conclusions. Stick strictly to these items.\n\n\n Trends, Articles and Write-ups: \n\n" + newsletter_string},
        ]
    )    

    # GET RESPONSE AS JSON OBJECT
    response = json.loads(completion.model_dump_json(indent=2))

    newsletter = response['choices'][0]['message']['content']

    # RETURN JSON OBJECT with the newsletter and status code
    return jsonify({
        'newsletter': newsletter,
        'status': 200
    })
    


if __name__ == '__main__':
    app.run(port=5000, debug=True)