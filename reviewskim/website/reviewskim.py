#!/usr/bin/env python
import os

from flask import Flask
from flask import render_template

app = Flask(__name__)

app.debug=True

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about.html')
def about():
    return render_template('about.html')

@app.route('/contact.html')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run()
