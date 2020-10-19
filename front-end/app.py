from flask import Flask, render_template, request, session, redirect
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import logging
import messaging
import os

app = Flask(__name__)
app.secret_key = os.environ['FLASK_SECRET_KEY']

logging.basicConfig(level=logging.INFO)

def login_required(f):

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'name' not in session:
            return redirect('/login')
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def index():
	return render_template('index.html')

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html')
    
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        msg = messaging.Messaging()
        msg.send(
            'REGISTER',
            {
                'name': name,
                'hash': generate_password_hash(password)
            }
        )
        response = msg.receive()
        if response['success']:
            session['name'] = name
            return redirect('/')
        else:
            return f"{response['message']}"
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        msg = messaging.Messaging()
        msg.send('GETHASH', { 'name': name })
        response = msg.receive()
        if response['success'] != True:
            return "Login failed."
        if check_password_hash(response['hash'], password):
            session['name'] = name
            return redirect('/')
        else:
            return "Login failed."
    return render_template('login.html')
    
@app.route('/logout')
def logout():
    session.pop('name', None)
    return redirect('/')

if __name__ == '__main__':
	app.run(debug=True, host='0.0.0.0')
