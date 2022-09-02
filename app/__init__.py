import flask 
from flask import render_template
from dash import Dash
import dash_core_components as dcc
import dash_html_components as html
from app.auth import auth_routes, isAuthenticated
from app.dash import init_dash


def register_routes(app):
    
    @app.route('/')
    @isAuthenticated
    def hello():
        return 'hello world!'

def register_dash(app):

    @app.route('/app')
    @isAuthenticated
    def dash():
        init_dash(app)
        return flask.redirect('/dash')   
        



def register_auth_routes(app):
    auth_routes(app)        
