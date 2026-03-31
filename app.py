#!/usr/bin/env python3
"""
Helseboliger.no — Flask backend
"""
import os
from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True, port=5001)
