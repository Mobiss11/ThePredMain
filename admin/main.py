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
app.config['S3_PUBLIC_URL'] = os.getenv('S3_PUBLIC_URL', 'https://thepred.store')
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


@app.route('/support')
@login_required
async def support():
    return await render_template('support.html')


@app.route('/support/ticket/<int:ticket_id>')
@login_required
async def support_ticket_detail(ticket_id):
    return await render_template('ticket_detail.html', ticket_id=ticket_id)


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


@app.route('/admin/missions', methods=['GET', 'POST'])
@login_required
async def api_admin_missions():
    """Proxy missions request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            if request.method == 'POST':
                data = await request.get_json()
                async with session_http.post(
                    f"{app.config['API_URL']}/admin/missions",
                    json=data
                ) as response:
                    result = await response.json()
                    return jsonify(result)
            else:
                type_filter = request.args.get('type', '')
                url = f"{app.config['API_URL']}/admin/missions"
                if type_filter:
                    url += f"?type={type_filter}"

                async with session_http.get(url) as response:
                    result = await response.json()
                    return jsonify(result)
    except Exception as e:
        print(f"Error with missions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/missions/<int:mission_id>', methods=['PUT', 'DELETE'])
@login_required
async def api_admin_mission_action(mission_id):
    """Proxy mission update/delete request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            if request.method == 'PUT':
                data = await request.get_json()
                async with session_http.put(
                    f"{app.config['API_URL']}/admin/missions/{mission_id}",
                    json=data
                ) as response:
                    result = await response.json()
                    return jsonify(result)
            elif request.method == 'DELETE':
                async with session_http.delete(
                    f"{app.config['API_URL']}/admin/missions/{mission_id}"
                ) as response:
                    result = await response.json()
                    return jsonify(result)
    except Exception as e:
        print(f"Error with mission action: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/missions/stats', methods=['GET'])
@login_required
async def api_admin_missions_stats():
    """Proxy mission stats request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/missions/stats"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching mission stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/leaderboard', methods=['GET'])
@login_required
async def api_admin_leaderboard():
    """Proxy leaderboard request to backend"""
    try:
        period = request.args.get('period', 'week')
        limit = request.args.get('limit', 100)

        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/leaderboard?period={period}&limit={limit}"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching leaderboard: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/leaderboard/rewards', methods=['GET', 'POST'])
@login_required
async def api_admin_rewards():
    """Proxy rewards request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            if request.method == 'POST':
                data = await request.get_json()
                async with session_http.post(
                    f"{app.config['API_URL']}/admin/leaderboard/rewards",
                    json=data
                ) as response:
                    result = await response.json()
                    return jsonify(result)
            else:
                period = request.args.get('period', '')
                url = f"{app.config['API_URL']}/admin/leaderboard/rewards"
                if period:
                    url += f"?period={period}"

                async with session_http.get(url) as response:
                    result = await response.json()
                    return jsonify(result)
    except Exception as e:
        print(f"Error with rewards: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/leaderboard/rewards/<int:reward_id>', methods=['PUT', 'DELETE'])
@login_required
async def api_admin_reward_action(reward_id):
    """Proxy reward update/delete request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            if request.method == 'PUT':
                data = await request.get_json()
                async with session_http.put(
                    f"{app.config['API_URL']}/admin/leaderboard/rewards/{reward_id}",
                    json=data
                ) as response:
                    result = await response.json()
                    return jsonify(result)
            elif request.method == 'DELETE':
                async with session_http.delete(
                    f"{app.config['API_URL']}/admin/leaderboard/rewards/{reward_id}"
                ) as response:
                    result = await response.json()
                    return jsonify(result)
    except Exception as e:
        print(f"Error with reward action: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/leaderboard/close-period', methods=['POST'])
@login_required
async def api_admin_close_period():
    """Proxy close period request to backend"""
    try:
        # Get period_type from query params
        period_type = request.args.get('period_type')
        if not period_type:
            return jsonify({"error": "period_type is required"}), 400

        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(
                f"{app.config['API_URL']}/admin/leaderboard/close-period?period_type={period_type}"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error closing period: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/leaderboard/periods', methods=['GET'])
@login_required
async def api_admin_periods():
    """Proxy periods history request to backend"""
    try:
        period_type = request.args.get('period_type', '')
        limit = request.args.get('limit', 50)

        url = f"{app.config['API_URL']}/admin/leaderboard/periods?limit={limit}"
        if period_type:
            url += f"&period_type={period_type}"

        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(url) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching periods: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/leaderboard/current-stats', methods=['GET'])
@login_required
async def api_admin_current_stats():
    """Proxy current period stats request to backend"""
    try:
        period_type = request.args.get('period_type', 'week')

        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/leaderboard/current-stats?period_type={period_type}"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching current stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/admin/notifications/queue-stats', methods=['GET'])
@login_required
async def api_admin_queue_stats():
    """Proxy notification queue stats request to backend"""
    try:
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/admin/notifications/queue-stats"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching queue stats: {e}")
        return jsonify({"error": str(e)}), 500


# ============ Support API Routes ============

@app.route('/api/admin/support/tickets', methods=['GET'])
@login_required
async def api_admin_support_tickets():
    """Proxy support tickets request to backend"""
    try:
        status = request.args.get('status', '')
        priority = request.args.get('priority', '')
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)

        url = f"{app.config['API_URL']}/support/admin/tickets?limit={limit}&offset={offset}"
        if status:
            url += f"&status={status}"
        if priority:
            url += f"&priority={priority}"

        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(url) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching support tickets: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/support/tickets/<int:ticket_id>/reply', methods=['POST'])
@login_required
async def api_admin_support_reply(ticket_id):
    """Proxy support reply request to backend"""
    try:
        form = await request.form
        files = await request.files

        data = aiohttp.FormData()
        data.add_field('message', form.get('message'))

        if 'attachment' in files and files['attachment'].filename:
            attachment = files['attachment']
            attachment_bytes = attachment.read()
            data.add_field('attachment', attachment_bytes,
                          filename=attachment.filename,
                          content_type=attachment.content_type)

        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(
                f"{app.config['API_URL']}/support/admin/tickets/{ticket_id}/reply",
                data=data
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error sending reply: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/support/tickets/<int:ticket_id>/status', methods=['PUT'])
@login_required
async def api_admin_support_status(ticket_id):
    """Proxy support status update request to backend"""
    try:
        status = request.args.get('status')
        async with aiohttp.ClientSession() as session_http:
            async with session_http.put(
                f"{app.config['API_URL']}/support/admin/tickets/{ticket_id}/status?status={status}"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error updating ticket status: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/support/tickets/<int:ticket_id>/messages', methods=['GET'])
@login_required
async def api_support_messages(ticket_id):
    """Proxy support messages request to backend"""
    try:
        user_id = request.args.get('user_id')
        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(
                f"{app.config['API_URL']}/support/tickets/{ticket_id}/messages?user_id={user_id}"
            ) as response:
                result = await response.json()
                return jsonify(result)
    except Exception as e:
        print(f"Error fetching messages: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8002)
