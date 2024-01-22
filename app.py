# app.py
from flask import Flask, jsonify, request, render_template, flash
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

CORS(app)

api_base = "https://chatgpt4vision.openai.azure.com/" 
deployment_name = "GPT-4-Vision"
API_KEY = "1f0880c2f35c418b9b50489e485093a4"

base_url = f"{api_base}openai/deployments/{deployment_name}" 
headers = {   
    "Content-Type": "application/json",   
    "api-key": API_KEY 
} 

@app.route('/')
def homepage():
    return render_template("index.html")

@app.route('/vision')
def vision_page():
    return render_template("vision.html")

@app.route('/upload_vision', methods=['POST'])
def upload():

    # GET PROMPT FROM FORM 
    prompt = request.form['user_prompt']

    # GET IMAGE FROM FORM
    image = request.files['uploaded_image']
    image_filename = image.filename

    print(prompt)
    print(image)
    print(image_filename)

    # SAVE IMAGE TO UPLOADS FOLDER
    image.save('static/images/uploads/' + image_filename)

    # CONVERT IMAGE TO BASE64
    path = 'static/images/uploads/' + image_filename
    with open(path, "rb") as image_file:
        sImagedata = base64.b64encode(image_file.read()).decode('ascii')
        
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
    gpt_response = response.json()['choices'][0]['message']['content']

    # gpt_response = "Joon Xiang Yong"

    return render_template('vision_response.html', user_prompt=prompt, gpt_response=gpt_response, image_filename=image_filename)

@app.route('/new_query', methods=['POST'])
def new_query():
    data = request.get_json()
    prompt = data['user_prompt']
    image_filename = data['image_filename']
    chat_history = data['chat_history']

    print(prompt)
    print(image_filename)

    # CONVERT IMAGE TO BASE64
    path = 'static/images/uploads/' + image_filename
    with open(path, "rb") as image_file:
        sImagedata = base64.b64encode(image_file.read()).decode('ascii')

    # Prepare endpoint, headers, and request body 
    endpoint = f"{base_url}/chat/completions?api-version=2023-12-01-preview" 
    data = { 
        "messages": [ 
            { "role": "system", "content": "You are a helpful assistant. The following HTML is the chat history prior to the new user query: \n\n" + chat_history + "\n\n form your responses based on the user query, the image and the chat history." }, 
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
    gpt_response = response.json()['choices'][0]['message']['content']
    # gpt_response = "Joon Xiang Yong"
    

    # Return the prompt and response to the page
    return jsonify({'gpt_response': gpt_response})


@app.route('/upload_vision_dxc', methods=['POST'])
def upload_vision_dxc():

    print("upload_vision_dxc called")

    # GET PROMPT AND UPLOADED FROM REQUEST
    user_prompt = request.form['user_prompt']
    uploaded_image = request.files['uploaded_image']

    # GET IMAGE FILENAME FROM REQUEST
    image_filename = uploaded_image.filename

    # SAVE IMAGE TO UPLOADS FOLDER
    uploaded_image.save('static/images/uploads/' + image_filename)

    # # CONVERT IMAGE TO BASE64
    path = 'static/images/uploads/' + image_filename
    with open(path, "rb") as image_file:
        sImagedata = base64.b64encode(image_file.read()).decode('ascii')
        
    # Prepare endpoint, headers, and request body 
    endpoint = f"{base_url}/chat/completions?api-version=2023-12-01-preview" 
    data = { 
        "messages": [ 
            { "role": "system", "content": "You are a helpful assistant." }, 
            { "role": "user", "content": [  
                { 
                    "type": "text", 
                    "text": user_prompt
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
    gpt_response = response.json()['choices'][0]['message']['content']
    print(gpt_response)
    print("-----")
    print(image_filename)
    print("-----")
    print(user_prompt)

    # return render_template('vision_response.html', user_prompt=prompt, gpt_response=gpt_response, image_filename=image_filename)
    return jsonify({'gpt_response': gpt_response,
                    'image_filename': image_filename,
                    'image_data': sImagedata,
                    'user_prompt': user_prompt
                    })

@app.route('/vision_new_query_dxc', methods=['POST'])
def vision_new_query_dxc():

    print("vision_new_query_dxc called")

    # GET PROMPT AND UPLOADED FROM REQUEST
    user_prompt = request.form['user_prompt']
    image_data = request.form['image_data']
    image_filename = request.form['image_filename']

    # # GET IMAGE FILENAME FROM REQUEST
    # image_filename = uploaded_image.filename

    # SAVE IMAGE TO UPLOADS FOLDER
    # uploaded_image.save('static/images/uploads/' + image_filename)

    # # CONVERT IMAGE TO BASE64
    path = 'static/images/uploads/' + image_filename
    with open(path, "rb") as image_file:
        sImagedata = base64.b64encode(image_file.read()).decode('ascii')
        
    # Prepare endpoint, headers, and request body 
    endpoint = f"{base_url}/chat/completions?api-version=2023-12-01-preview" 
    data = { 
        "messages": [ 
            { "role": "system", "content": "You are a helpful assistant." }, 
            { "role": "user", "content": [  
                { 
                    "type": "text", 
                    "text": user_prompt
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
    gpt_response = response.json()['choices'][0]['message']['content']
    print(gpt_response)
    print("-----")
    print(user_prompt)

    # return render_template('vision_response.html', user_prompt=prompt, gpt_response=gpt_response, image_filename=image_filename)
    return jsonify({'gpt_response': gpt_response,
                    'image_data': image_data,
                    'user_prompt': user_prompt
                    })

if __name__ == '__main__':
    app.run(port=5004, debug=True)