from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from os import environ
import json
import pymongo
from bson import ObjectId
from openai import OpenAI
from sentence_transformers import SentenceTransformer
import time


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
            
            print(type(trend_obj))

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


if __name__ == '__main__':
    app.run(port=5000, debug=True)