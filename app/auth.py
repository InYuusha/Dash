
from crypt import methods
from logging import error
import firebase_admin
import pyrebase
from firebase_admin import credentials, auth
import json
import flask
from flask import Flask, request,render_template,redirect,url_for,session
from functools import wraps
import os
from requests.exceptions import HTTPError


cred = credentials.Certificate(os.getcwd()+'/admin.json')
firebase = firebase_admin.initialize_app(cred)
fb= pyrebase.initialize_app(json.load(open(os.getcwd()+'/fbconfig.json')))

auth = fb.auth()

def isAuthenticated(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        #check for the variable that pyrebase creates
        if not auth.current_user != None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def auth_routes(app):
    @app.route('/signup',methods=['POST','GET'])
    def signup():
        if request.method=='GET':
            return render_template('signup.html')
        email = request.form["email"]
        password = request.form["password"]
        try:
        #create the user
            auth.create_user_with_email_and_password(email, password);
        #login the user right away
            user = auth.sign_in_with_email_and_password(email, password)   
            #session
            user_id = user['idToken']
            user_email = email
            session['usr'] = user_id
            session["email"] = user_email
            return render_template('login.html', msg='Successfully created user')
        except Exception as e:
            print(e)
            return render_template('signup.html', msg='Failed to register')

    @app.route('/login',methods=['POST','GET'])
    def token():
        if request.method=='GET':
            return render_template('login.html')

        email = request.form.get('email')
        password = request.form.get('password')
        if email is None or password is None:
            return render_template('login.html', msg='Missing Fields')
        try:
            user = auth.sign_in_with_email_and_password(email, password)

            user_id = user['idToken']
            user_email = email
            session['usr'] = user_id
            session["email"] = user_email

            return redirect("/dash")
            
        except HTTPError as e:
            print(e)
            return render_template('login.html', msg="Invalid credentials")


    @app.route("/logout")
    def logout():
    #remove the token setting the user to None
        auth.current_user = None
 
        session.clear()
        return redirect("/login");