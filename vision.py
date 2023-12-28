# app.py
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from os import environ
import json
import pymongo
from bson import ObjectId
from openai import OpenAI

# Packages required for Vision:
import requests 
import json
import base64
from PIL import Image
from io import BytesIO


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload_vision', methods=['POST'])
def upload():

    # GET PROMPT FROM FORM 
    prompt = request.form['user_prompt']

    # GET IMAGE FROM FORM
    image = request.files['uploaded_image']
    image_filename = image.filename

    # SAVE IMAGE TO UPLOADS FOLDER
    image.save('static/images/uploads/' + image_filename)

    # CONVERT IMAGE TO BASE64
    path = 'static/images/uploads/' + image_filename
    with open(path, "rb") as image_file:
        sImagedata = base64.b64encode(image_file.read()).decode('ascii')\
        
    


    api_base = "https://chatgpt4vision.openai.azure.com/" 
    deployment_name = "GPT-4-Vision"
    API_KEY = "1f0880c2f35c418b9b50489e485093a4"

    base_url = f"{api_base}openai/deployments/{deployment_name}" 
    headers = {   
        "Content-Type": "application/json",   
        "api-key": API_KEY 
    } 

    # Prepare endpoint, headers, and request body 
    endpoint = f"{base_url}/chat/completions?api-version=2023-12-01-preview" 
    data = { 
        "messages": [ 
            { "role": "system", "content": "You are a helpful assistant." }, 
            { "role": "user", "content": [  
                { 
                    "type": "text", 
                    "text": prompt
                },
                { 
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{sImagedata}"
                    }
                }
            ] } 
        ], 
        "max_tokens": 2000 
    }   

    # Make the API call   
    response = requests.post(endpoint, headers=headers, data=json.dumps(data))   

    print(f"Status Code: {response.status_code}")   
    print("-----")
    # print(response.json()['choices'][0]['message']['content'])
    print(response.json())

    # print(image.filename)
    return render_template('vision_response.html')



if __name__ == '__main__':
    app.run(port=5003,debug=True)


# TO DO:
# 1. Shift all of this to app.py
# 2. Display answer and image on vision_response.html (find out how to pass image and answer to html through render_template)
# 3. Find out how to keep and display previous questions and answers on vision_response.html