from quart import Quart, render_template
import os
from dotenv import load_dotenv

load_dotenv()

app = Quart(__name__)


@app.route('/')
async def index():
    """Main landing page"""
    return await render_template('index_last.html')


@app.route('/privacy')
async def privacy():
    """Privacy policy page"""
    return await render_template('privacy.html')


@app.route('/terms')
async def terms():
    """Terms of service page"""
    return await render_template('terms.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8003)
