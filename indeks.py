from flask import Flask, request

app = Flask(_name_)

def index():
    return 'Hello from Flask on Vercel!'

def handler(environ, start_response):
    return app(environ, start_response)