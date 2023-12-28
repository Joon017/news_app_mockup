# app.py
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def homepage():
    return render_template("index.html")

@app.route('/vision')
def vision_page():
    return render_template("vision.html")

if __name__ == '__main__':
    app.run(port=5000, debug=True)