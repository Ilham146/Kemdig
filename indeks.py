from flask import Flask, request

app = Flask(__name__)

def index():
    return 'Hello from Flask on Vercel!'

def handler(environ, start_response):
    return app(environ, start_response)