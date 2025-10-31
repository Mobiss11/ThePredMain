from quart import Quart, render_template, request, jsonify, redirect, url_for, session
import os
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Quart(__name__)
app.secret_key = os.getenv('ADMIN_SECRET_KEY', 'change-me-in-production')
app.config['API_URL'] = os.getenv('API_URL', 'http://localhost:8000')
app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD', 'admin')


def login_required(f):
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return await f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
async def login():
    if request.method == 'POST':
        form = await request.form
        password = form.get('password')

        if password == app.config['ADMIN_PASSWORD']:
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return await render_template('login.html', error='Invalid password')

    return await render_template('login.html')


@app.route('/logout')
async def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/')
@login_required
async def dashboard():
    return await render_template('dashboard.html')


@app.route('/users')
@login_required
async def users():
    return await render_template('users.html')


@app.route('/markets')
@login_required
async def markets():
    return await render_template('markets.html')


@app.route('/missions')
@login_required
async def missions():
    return await render_template('missions.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
