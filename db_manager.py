from flask import Flask, jsonify, request
from flask_cors import CORS
from os import environ
import json
import pymongo
from bson import ObjectId
from openai import OpenAI
from sentence_transformers import SentenceTransformer

embedding_model = SentenceTransformer('sentence-transformers/all-mpnet-base-v2')

# CONNECT TO MONGO
mongo_client = pymongo.MongoClient("mongodb+srv://ckoh2021:MGk9TVzCl4RgRYHN@cluster0.euvgj72.mongodb.net/")

# CONNECT TO NEWSSCRAPER DB
news_scraper_db = mongo_client.get_database('NewsScraper')

# CONNECT TO ARTICLES COLLECTION
articles_collection = news_scraper_db.get_collection('Articles')

# # DELETE ALL DOCUMENTS FROM ARTICLES COLLECTION
# articles_collection.delete_many({})
# print("All documents deleted from Articles collection")

# Create the Atlas Search index for the vector field (article_embedding)
articles_collection.create_index(
    [("article_embedding", "text")],
    weights={"article_embedding": 1},
    default_language="english"
)

print("Vector search index created for 'article_embedding'")


# Create the Atlas Search index for the vector field
articles_collection.create_index(
    [("article_embedding", "text")],
    weights={"article_embedding": 1},
    default_language="english"
)
# Get the list of indexes for the collection
indexes = articles_collection.list_indexes()
print("List of indexes for the collection:")
print(list(indexes))


query_sentence = "AI is advancing rapidly and is going to take over the world."

query_vector = (embedding_model.encode(query_sentence)).tolist()
# Perform a vector search
result = articles_collection.find(
    {
        "article_embedding": {
            "$vector": {
                "$search": {"$vector": query_vector},
                "$score": {"$meta": "searchScore"}
            }
        }
    }
).sort([("score", {"$meta": "searchScore"})])

# Print the result
# for doc in result:
#     print(doc)


# results = articles_collection.aggregate([
#   {"$vectorSearch": {
#     "queryVector": query_vector,
#     "path": "article_embedding",
#     "numCandidates": 100,
#     "limit": 4,
#     "index": "article_embedding_text",
#       }}
# ])

# for document in results:
#     print("hello")


# query = "Ethical considerations"
# query_vector = (embedding_model.encode(query)).tolist()

results = articles_collection.aggregate([
  {"$vectorSearch": {
    "queryVector": query_vector,
    "path": "article_embedding",
    "numCandidates": 100,
    "limit": 5,
    "index": "vector_index",
      }}
])

for document in results:
    # print(document.get('title'))
    # GET THE OBJECT ID OF THE DOCUMENT
    document_id = document.get('_id')

    # GET THE DOCUMENT FROM THE COLLECTION
    curr_document = articles_collection.find_one({'_id': ObjectId(document_id)})

    # GET THE TRENDS FROM THE DOCUMENT
    curr_document_trends = curr_document.get('trends')