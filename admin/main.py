from quart import Quart, render_template, request, jsonify, redirect, url_for, session
import os
import aiohttp
from dotenv import load_dotenv
from functools import wraps

load_dotenv()

app = Quart(__name__)
app.secret_key = os.getenv('ADMIN_SECRET_KEY', 'change-me-in-production')
app.config['API_URL'] = os.getenv('API_URL', 'http://backend:8000')
app.config['ADMIN_PASSWORD'] = os.getenv('ADMIN_PASSWORD', 'admin')
app.config['S3_PUBLIC_URL'] = os.getenv('S3_PUBLIC_URL', 'http://localhost:9000')
app.config['S3_BUCKET'] = os.getenv('S3_BUCKET', 'thepred-events')


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


@app.route('/missions/create')
@login_required
async def create_mission():
    return await render_template('mission_form.html', mission=None)


@app.route('/missions/edit/<int:mission_id>')
@login_required
async def edit_mission(mission_id):
    # Fetch mission from API
    async with aiohttp.ClientSession() as session_http:
        async with session_http.get(
            f"{app.config['API_URL']}/admin/missions"
        ) as response:
            if response.status == 200:
                missions = await response.json()
                mission = next((m for m in missions if m['id'] == mission_id), None)
                if mission:
                    return await render_template('mission_form.html', mission=mission)

    return "Mission not found", 404


@app.route('/leaderboard')
@login_required
async def leaderboard():
    return await render_template('leaderboard.html')


@app.route('/broadcast')
@login_required
async def broadcast():
    return await render_template('broadcast.html')


# ============ API Proxy Routes ============

@app.route('/admin/users', methods=['GET'])
@login_required
async def api_admin_users():
    """Proxy admin users request to backend"""
    try:
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)

        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/users?limit={limit}&offset={offset}"
            ) as response:
                data = await response.json()
                return jsonify(data)
    except Exception as e:
        print(f"Error fetching users: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/stats', methods=['GET'])
@login_required
async def api_admin_stats():
    """Proxy admin stats request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/stats"
            ) as response:
                data = await response.json()
                return jsonify(data)
    except Exception as e:
        print(f"Error fetching stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets', methods=['GET', 'POST'])
@login_required
async def api_admin_markets():
    """Proxy admin markets request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            if request.method == 'POST':
                data = await request.get_json()
                async with session_http.post(
                    f"{app.config['API_URL']}/admin/markets",
                    json=data
                ) as response:
                    result = await response.json()
                    return jsonify(result)
            else:
                status = request.args.get('status', 'all')
                limit = request.args.get('limit', 50)
                async with session_http.get(
                    f"{app.config['API_URL']}/admin/markets?status={status}&limit={limit}"
                ) as response:
                    data = await response.json()
                    return jsonify(data)
    except Exception as e:
        print(f"Error with markets: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets/<int:market_id>/resolve', methods=['PUT'])
@login_required
async def api_admin_resolve_market(market_id):
    """Proxy market resolve request to backend"""
    try:
        data = await request.get_json()
        async with aiohttp.ClientSession() as session_http:
            async with session_http.put(
                f"{app.config['API_URL']}/admin/markets/{market_id}/resolve",
                json=data
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error resolving market: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>/balance', methods=['PUT'])
@login_required
async def api_admin_update_balance(user_id):
    """Proxy user balance update request to backend"""
    try:
        data = await request.get_json()
        async with aiohttp.ClientSession() as session_http:
            async with session_http.put(
                f"{app.config['API_URL']}/admin/users/{user_id}/balance",
                json=data
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error updating user balance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>/rank', methods=['PUT'])
@login_required
async def api_admin_update_rank(user_id):
    """Proxy user rank update request to backend"""
    try:
        rank = request.args.get('rank')
        async with aiohttp.ClientSession() as session_http:
            async with session_http.put(
                f"{app.config['API_URL']}/admin/users/{user_id}/rank?rank={rank}"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error updating user rank: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/users/<int:user_id>/activity', methods=['GET'])
@login_required
async def api_admin_user_activity(user_id):
    """Proxy user activity request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/users/{user_id}/activity"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching user activity: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets/pending', methods=['GET'])
@login_required
async def api_admin_pending_markets():
    """Proxy pending markets request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/markets/pending"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching pending markets: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets/approved', methods=['GET'])
@login_required
async def api_admin_approved_markets():
    """Proxy approved markets request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/markets/approved"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching approved markets: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets/cancelled', methods=['GET'])
@login_required
async def api_admin_cancelled_markets():
    """Proxy cancelled markets request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/markets/cancelled"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching cancelled markets: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets/<int:market_id>/moderate', methods=['PUT'])
@login_required
async def api_admin_moderate_market(market_id):
    """Proxy market moderation request to backend"""
    try:
        action = request.args.get('action')
        async with aiohttp.ClientSession() as session_http:
            async with session_http.put(
                f"{app.config['API_URL']}/admin/markets/{market_id}/moderate?action={action}"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error moderating market: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets/<int:market_id>/close', methods=['PUT'])
@login_required
async def api_admin_close_market(market_id):
    """Proxy market close request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.put(
                f"{app.config['API_URL']}/admin/markets/{market_id}/close"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error closing market: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets/<int:market_id>/cancel', methods=['PUT'])
@login_required
async def api_admin_cancel_market(market_id):
    """Proxy market cancel request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.put(
                f"{app.config['API_URL']}/admin/markets/{market_id}/cancel"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error cancelling market: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/markets/generate-test', methods=['POST'])
@login_required
async def api_admin_generate_test_markets():
    """Proxy generate test markets request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(
                f"{app.config['API_URL']}/admin/markets/generate-test"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error generating test markets: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/missions', methods=['GET'])
@login_required
async def api_admin_missions():
    """Proxy missions request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/missions"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching missions: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
