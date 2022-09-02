from flask import Flask
import os
from app import register_auth_routes, register_dash, register_routes
from app.dash import init_dash

server = Flask(__name__)
init_dash(server)
server.secret_key = os.urandom(24)
register_routes(server)
register_dash(server)
register_auth_routes(server)

if __name__ == '__main__':
    server.run()