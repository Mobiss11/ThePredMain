from quart import Quart, render_template, request, jsonify, session, redirect, url_for
import os
import json
import hmac
import hashlib
from urllib.parse import unquote, parse_qsl
from dotenv import load_dotenv
from functools import wraps
from api_client import api_client

load_dotenv()

app = Quart(__name__)
app.secret_key = os.getenv('WEBAPP_SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['API_URL'] = os.getenv('API_URL', 'http://backend:8000')
app.config['DEV_MODE'] = os.getenv('DEV_MODE', 'true').lower() == 'true'
app.config['BOT_TOKEN'] = os.getenv('BOT_TOKEN', '')
app.config['BOT_USERNAME'] = os.getenv('BOT_USERNAME', 'The_Pred_Bot')
app.config['S3_PUBLIC_URL'] = os.getenv('S3_PUBLIC_URL', 'https://thepred.store')
app.config['S3_BUCKET'] = os.getenv('S3_BUCKET', 'thepred-events')

# Session configuration for Telegram WebApp
# CRITICAL: These settings are required for sessions to work in Telegram WebApp
app.config['SESSION_COOKIE_SAMESITE'] = 'None'  # Required for iframe/WebApp
app.config['SESSION_COOKIE_SECURE'] = not app.config['DEV_MODE']  # True in production
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Log configuration on startup
print("=" * 50)
print("WEBAPP CONFIGURATION:")
print(f"DEV_MODE: {app.config['DEV_MODE']} (from env: {os.getenv('DEV_MODE')})")
print(f"API_URL: {app.config['API_URL']}")
print(f"BOT_USERNAME: {app.config['BOT_USERNAME']}")
print("=" * 50)

# Configure API client
api_client.base_url = app.config['API_URL']


def validate_telegram_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram WebApp init data"""
    try:
        # Parse init_data
        parsed_data = dict(parse_qsl(init_data))

        # Extract hash
        received_hash = parsed_data.pop('hash', None)
        if not received_hash:
            return None

        # Create data check string
        data_check_arr = [f"{k}={v}" for k, v in sorted(parsed_data.items())]
        data_check_string = '\n'.join(data_check_arr)

        # Calculate hash
        secret_key = hmac.new(
            key=b"WebAppData",
            msg=bot_token.encode(),
            digestmod=hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            key=secret_key,
            msg=data_check_string.encode(),
            digestmod=hashlib.sha256
        ).hexdigest()

        # Verify hash
        if calculated_hash != received_hash:
            return None

        # Parse user data
        if 'user' in parsed_data:
            user_data = json.loads(unquote(parsed_data['user']))
            return user_data

        return None
    except Exception as e:
        print(f"Error validating Telegram data: {e}")
        return None


def auth_required(f):
    """Middleware for authentication (dev or Telegram)"""
    @wraps(f)
    async def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        user_id = session.get('user_id')
        print(f"[auth_required] DEV_MODE: {app.config['DEV_MODE']}, user_id: {user_id}")

        if not user_id:
            # Not authenticated - redirect based on mode
            if app.config['DEV_MODE']:
                print("[auth_required] Redirecting to dev_login")
                return redirect(url_for('dev_login'))
            else:
                # Production mode - redirect to Telegram bot
                print("[auth_required] Production mode, showing redirect_to_telegram")
                bot_username = app.config['BOT_USERNAME']
                return await render_template('redirect_to_telegram.html', bot_username=bot_username)

        print(f"[auth_required] User authenticated: {user_id}")
        return await f(*args, **kwargs)
    return decorated_function


@app.route('/')
async def index():
    """Main page - Auto-login from Telegram or redirect"""
    print(f"[/] DEV_MODE: {app.config['DEV_MODE']}, Session user_id: {session.get('user_id')}")

    # Check if request is from Telegram WebApp (even in DEV_MODE)
    # Telegram WebApp passes tgWebAppData or tgWebAppStartParam in URL
    is_from_telegram = (
        request.args.get('tgWebAppStartParam') or
        request.args.get('tgWebAppData') or
        request.headers.get('Referer', '').find('telegram') != -1
    )

    # If coming from Telegram, check if already authenticated or need to auth
    if is_from_telegram:
        # If already authenticated via Telegram, don't clear session
        if session.get('telegram_authed'):
            print(f"[/] Already authenticated via Telegram: user_id={session.get('user_id')}")
            # Continue to check authentication below
        else:
            # Not authenticated yet - clear any old session and show auth page
            if not app.config['DEV_MODE']:
                if session:
                    print(f"[/] Production mode: Clearing old session data: {dict(session)}")
                    session.clear()
                else:
                    print("[/] Production mode: No existing session")
            print("[/] Request from Telegram WebApp, showing auth.html")
            return await render_template('auth.html', bot_username=app.config['BOT_USERNAME'])

    # Check if already authenticated (not from Telegram)
    if session.get('user_id'):
        print("[/] User authenticated, redirecting to markets")
        return redirect(url_for('markets'))

    # Dev mode - redirect to dev login (only for browser access)
    if app.config['DEV_MODE']:
        print("[/] DEV_MODE is ON, redirecting to dev_login")
        return redirect(url_for('dev_login'))

    # Production mode - try to get Telegram WebApp data from URL
    print("[/] Production mode, showing auth.html")
    return await render_template('auth.html', bot_username=app.config['BOT_USERNAME'])


@app.route('/auth/telegram', methods=['POST'])
async def auth_telegram():
    """Authenticate user from Telegram WebApp"""
    print("[/auth/telegram] ===== TELEGRAM AUTH REQUEST =====")
    try:
        data = await request.get_json()
        init_data = data.get('initData')
        print(f"[/auth/telegram] initData received: {bool(init_data)}, length: {len(init_data) if init_data else 0}")

        if not init_data:
            print("[/auth/telegram] ERROR: No initData provided")
            return jsonify({"error": "No initData provided"}), 400

        # Check BOT_TOKEN
        bot_token = app.config.get('BOT_TOKEN')
        print(f"[/auth/telegram] BOT_TOKEN configured: {bool(bot_token)}, length: {len(bot_token) if bot_token else 0}")

        if not bot_token:
            print("[/auth/telegram] ERROR: BOT_TOKEN not configured!")
            return jsonify({"error": "Server configuration error: BOT_TOKEN not set"}), 500

        # Validate Telegram data
        print("[/auth/telegram] Validating Telegram initData...")
        user_data = validate_telegram_data(init_data, bot_token)

        if not user_data:
            print("[/auth/telegram] ERROR: Invalid Telegram data (validation failed)")
            return jsonify({"error": "Invalid Telegram data"}), 401

        print(f"[/auth/telegram] Telegram data validated! User ID: {user_data.get('id')}, Username: {user_data.get('username')}")

        # Register/login user via backend
        telegram_id = user_data.get('id')
        username = user_data.get('username', '')
        first_name = user_data.get('first_name', '')
        last_name = user_data.get('last_name', '')
        photo_url = user_data.get('photo_url', None)

        print(f"[/auth/telegram] Calling backend to register/login user: telegram_id={telegram_id}, username={username}")

        # Call backend to register or get user
        try:
            user = await api_client.telegram_auth(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                photo_url=photo_url
            )

            print(f"[/auth/telegram] Backend returned user: id={user.get('id')}, username={user.get('username')}")

            # Store user in session
            session.permanent = True  # Make session persistent
            session['user_id'] = user['id']
            session['telegram_id'] = telegram_id
            session['username'] = username
            session['telegram_authed'] = True  # Mark that Telegram auth completed

            print(f"[/auth/telegram] Session created: user_id={user['id']}, telegram_id={telegram_id}")
            print(f"[/auth/telegram] Session permanent: True, Session data: {dict(session)}")
            print("[/auth/telegram] ===== AUTH SUCCESS =====")

            return jsonify({"success": True, "user": user})
        except Exception as e:
            print(f"[/auth/telegram] ERROR: Backend error: {e}")
            return jsonify({"error": f"Backend error: {str(e)}"}), 500

    except Exception as e:
        print(f"[/auth/telegram] ERROR: Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/dev/login', methods=['GET', 'POST'])
async def dev_login():
    """Dev mode login page"""
    print(f"[/dev/login] DEV_MODE: {app.config['DEV_MODE']}, method: {request.method}")

    if not app.config['DEV_MODE']:
        print("[/dev/login] Dev mode is disabled!")
        return "Dev mode is disabled", 403

    if request.method == 'POST':
        form = await request.form
        user_id = int(form.get('user_id', '1'))  # Convert to int
        session['user_id'] = user_id
        session['username'] = form.get('username', 'DevUser')
        session['telegram_id'] = int(form.get('telegram_id', '123456'))  # Convert to int
        print(f"[/dev/login] User logged in: {user_id}, redirecting to markets")
        return redirect(url_for('markets'))

    print("[/dev/login] Showing dev_login.html")
    return await render_template('dev_login.html')


@app.route('/logout')
async def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('index'))


@app.route('/debug/session')
async def debug_session():
    """Debug: Show current session"""
    return jsonify({
        "session": dict(session),
        "dev_mode": app.config['DEV_MODE']
    })


@app.route('/debug/clear-session')
async def debug_clear_session():
    """Debug: Force clear session"""
    old_session = dict(session)
    session.clear()
    return jsonify({
        "success": True,
        "message": "Session cleared. Please refresh and re-authenticate.",
        "old_session": old_session
    })


@app.route('/markets')
@auth_required
async def markets():
    """Markets list page"""
    user_id = session.get('user_id')
    print(f"[/markets] Rendering markets page for user_id: {user_id}")
    print(f"[/markets] Full session: {dict(session)}")
    return await render_template('index.html', user_id=user_id)


@app.route('/market/<int:market_id>')
@auth_required
async def market_detail(market_id):
    """Market detail page"""
    user_id = session.get('user_id')
    return await render_template('market.html', market_id=market_id, user_id=user_id)


@app.route('/profile')
@auth_required
async def profile():
    """User profile page"""
    user_id = session.get('user_id')
    return await render_template('profile.html', user_id=user_id)


@app.route('/leaderboard')
@auth_required
async def leaderboard():
    """Leaderboard page"""
    user_id = session.get('user_id')
    return await render_template('leaderboard.html', user_id=user_id)


@app.route('/missions')
@auth_required
async def missions():
    """Missions page"""
    user_id = session.get('user_id')
    return await render_template('missions.html', user_id=user_id)


@app.route('/create-event')
@auth_required
async def create_event():
    """Create event page"""
    user_id = session.get('user_id')
    return await render_template('create_event.html', user_id=user_id)


@app.route('/support')
async def support():
    """Support page - accessible for banned users"""
    user_id = session.get('user_id')
    return await render_template('support.html', user_id=user_id)


@app.route('/banned')
async def banned():
    """Banned user page - no auth required"""
    user_id = session.get('user_id')
    return await render_template('banned.html', user_id=user_id)


# ============ API Routes ============

@app.route('/api/markets')
async def api_markets():
    """Get markets from backend API"""
    try:
        category = request.args.get('category')
        markets = await api_client.get_markets(category=category)
        return jsonify(markets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/markets/<int:market_id>')
async def api_market_detail(market_id):
    """Get market details from backend API"""
    try:
        market = await api_client.get_market(market_id)
        return jsonify(market)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/markets/user/<int:user_id>')
async def api_user_markets(user_id):
    """Get markets created by a specific user"""
    try:
        import aiohttp

        status = request.args.get('status')
        url = f"{api_client.base_url}/markets/user/{user_id}"
        params = {}
        if status:
            params['status'] = status

        print(f"[/api/markets/user/{user_id}] Fetching markets for user_id: {user_id}, status: {status}")
        print(f"[/api/markets/user/{user_id}] URL: {url}, params: {params}")

        async with aiohttp.ClientSession() as session_http:
            async with session_http.get(url, params=params) as response:
                print(f"[/api/markets/user/{user_id}] Response status: {response.status}")
                if response.status == 200:
                    markets = await response.json()
                    print(f"[/api/markets/user/{user_id}] Found {len(markets)} markets")
                    return jsonify(markets)
                else:
                    error_text = await response.text()
                    print(f"[/api/markets/user/{user_id}] Error: {error_text}")
                    return jsonify({"error": error_text}), response.status
    except Exception as e:
        print(f"[/api/markets/user/{user_id}] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/markets/promote', methods=['POST'])
async def api_promote_market():
    """Promote a market (purchase promotion)"""
    try:
        data = await request.get_json()
        url = f"{api_client.base_url}/markets/promote"

        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(url, json=data) as response:
                result = await response.json()
                if response.status == 200:
                    return jsonify(result)
                else:
                    return jsonify({"error": result.get('detail', 'Failed to promote market')}), response.status
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/bets', methods=['POST'])
async def api_create_bet():
    """Create bet via backend API"""
    try:
        data = await request.get_json()
        user_id = session.get('user_id', 1)

        bet = await api_client.create_bet(
            user_id=int(user_id),
            market_id=data['market_id'],
            position=data['position'],
            amount=float(data['amount']),
            currency=data.get('currency', 'PRED')
        )
        return jsonify(bet)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/bets/history')
async def api_bet_history():
    """Get bet history from backend API"""
    try:
        user_id = session.get('user_id', 1)
        bets = await api_client.get_bet_history(int(user_id))
        return jsonify(bets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/bets/active/<int:user_id>')
async def api_active_bets(user_id):
    """Get user's active bets from backend API"""
    try:
        response = await api_client._get(f"/bets/active/{user_id}")
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/profile')
async def api_profile():
    """Get user profile from backend API"""
    try:
        user_id = session.get('user_id')
        print(f"[/api/profile] Session user_id: {user_id}, All session: {dict(session)}")
        print(f"[/api/profile] Session permanent: {session.permanent}")
        print(f"[/api/profile] Request headers: {dict(request.headers)}")

        if not user_id:
            print("[/api/profile] ERROR: No user_id in session! User not authenticated.")
            print(f"[/api/profile] Cookie header: {request.headers.get('Cookie')}")
            return jsonify({"error": "Not authenticated"}), 401

        print(f"[/api/profile] Fetching profile for user_id: {user_id}")
        profile = await api_client.get_user_profile(int(user_id))
        print(f"[/api/profile] Profile loaded: {profile.get('id') if profile else None}")
        print(f"[/api/profile] Profile data: pred_balance={profile.get('pred_balance')}, ton_balance={profile.get('ton_balance')}, rank={profile.get('rank')}, total_bets={profile.get('total_bets')}")
        print(f"[/api/profile] Full profile response: {profile}")
        return jsonify(profile)
    except Exception as e:
        print(f"[/api/profile] Error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/balance')
async def api_balance():
    """Get user balance from backend API"""
    try:
        user_id = session.get('user_id', 1)
        balance = await api_client.get_user_balance(int(user_id))
        return jsonify(balance)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ Wallet API Routes ============

@app.route('/api/wallet/connect/<int:user_id>', methods=['POST'])
async def api_wallet_connect(user_id):
    """Connect TON wallet to user account"""
    try:
        data = await request.get_json()
        print(f"[/api/wallet/connect] Connecting wallet for user_id: {user_id}")
        print(f"[/api/wallet/connect] Address: {data.get('ton_address')}")

        result = await api_client._post(f"/wallet/connect/{user_id}", data)
        print(f"[/api/wallet/connect] ✅ Wallet connected successfully")
        return jsonify(result)
    except Exception as e:
        print(f"[/api/wallet/connect] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/wallet/balance/<int:user_id>')
async def api_wallet_balance(user_id):
    """Get wallet balance and connection status"""
    try:
        print(f"[/api/wallet/balance] Fetching wallet info for user_id: {user_id}")
        result = await api_client._get(f"/wallet/balance/{user_id}")
        print(f"[/api/wallet/balance] ✅ Wallet connected: {result.get('wallet_connected')}, Address: {result.get('ton_address')}")
        return jsonify(result)
    except Exception as e:
        print(f"[/api/wallet/balance] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/wallet/convert/<int:user_id>', methods=['POST'])
async def api_wallet_convert(user_id):
    """Convert TON to PRED (internal balance conversion)"""
    try:
        data = await request.get_json()
        print(f"[/api/wallet/convert] Converting TON to PRED for user_id: {user_id}, amount: {data.get('amount_ton')}")
        result = await api_client._post(f"/wallet/convert/{user_id}", data)
        print(f"[/api/wallet/convert] ✅ Converted: {result.get('ton_converted')} TON → {result.get('pred_credited')} PRED")
        return jsonify(result)
    except Exception as e:
        print(f"[/api/wallet/convert] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/wallet/disconnect/<int:user_id>', methods=['POST'])
async def api_wallet_disconnect(user_id):
    """Disconnect TON wallet from user account"""
    try:
        print(f"[/api/wallet/disconnect] Disconnecting wallet for user_id: {user_id}")
        result = await api_client._post(f"/wallet/disconnect/{user_id}", {})
        print(f"[/api/wallet/disconnect] ✅ Wallet disconnected successfully")
        return jsonify(result)
    except Exception as e:
        print(f"[/api/wallet/disconnect] Exception: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route('/api/wallet/info')
async def api_wallet_info():
    """Get wallet info (conversion rate, limits, etc.)"""
    try:
        result = await api_client._get("/wallet/info")
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/missions')
async def api_missions():
    """Get missions from backend API"""
    try:
        user_id = session.get('user_id', 1)
        missions = await api_client.get_missions(int(user_id))
        return jsonify(missions)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/missions/<int:user_id>')
async def api_missions_by_user(user_id):
    """Get missions for specific user"""
    try:
        response = await api_client._get(f"/missions/{user_id}")
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/missions/claim/<int:user_id>/<int:mission_id>', methods=['POST'])
async def api_claim_mission_new(user_id, mission_id):
    """Claim mission reward via backend API"""
    try:
        response = await api_client._post(f"/missions/claim/{user_id}/{mission_id}", {})
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/missions/check-subscription/<int:user_id>/<int:mission_id>', methods=['POST'])
async def api_check_subscription(user_id, mission_id):
    """Check channel subscription for mission"""
    try:
        response = await api_client._post(f"/missions/check-subscription/{user_id}/{mission_id}", {})
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/missions/claim/<int:mission_id>', methods=['POST'])
async def api_claim_mission(mission_id):
    """Claim mission reward via backend API (legacy)"""
    try:
        user_id = session.get('user_id', 1)

        result = await api_client.claim_mission_reward(
            user_id=int(user_id),
            mission_id=mission_id
        )
        return jsonify(result)
    except Exception as e:
        print(f"Error claiming mission: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/leaderboard')
async def api_leaderboard():
    """Get leaderboard from backend API"""
    try:
        limit = request.args.get('limit', 100, type=int)
        period = request.args.get('period', 'week')
        sort_by = request.args.get('sort_by', 'profit')

        leaderboard = await api_client.get_leaderboard(limit=limit, period=period, sort_by=sort_by)
        return jsonify(leaderboard)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/leaderboard/rank')
async def api_user_rank():
    """Get user's rank in leaderboard from backend API"""
    try:
        user_id = session.get('user_id', 1)
        rank_info = await api_client.get_user_rank(int(user_id))
        return jsonify(rank_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/leaderboard/rewards/<period>')
async def api_leaderboard_rewards(period):
    """Get leaderboard rewards for a period from backend API"""
    try:
        rewards = await api_client.get_leaderboard_rewards(period=period)
        return jsonify(rewards)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ Admin Routes ============

@app.route('/admin')
@auth_required
async def admin_panel():
    """Admin panel page"""
    user_id = session.get('user_id')
    return await render_template('admin.html', user_id=user_id)


@app.route('/api/admin/stats')
async def api_admin_stats():
    """Get platform stats"""
    try:
        stats = await api_client.get_platform_stats()
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/markets', methods=['GET', 'POST'])
async def api_admin_markets():
    """Get all markets or create new market"""
    try:
        if request.method == 'POST':
            data = await request.get_json()
            result = await api_client.create_market(
                title=data['title'],
                category=data['category'],
                description=data.get('description'),
                resolve_date=data.get('resolve_date'),
                is_promoted=data.get('is_promoted', 'none'),
                promoted_until=data.get('promoted_until')
            )
            return jsonify(result)
        else:
            status = request.args.get('status')
            limit = request.args.get('limit', 50, type=int)
            markets = await api_client.get_all_markets_admin(status=status, limit=limit)
            return jsonify(markets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/markets/<int:market_id>/resolve', methods=['POST'])
async def api_admin_resolve_market(market_id):
    """Resolve market"""
    try:
        data = await request.get_json()
        result = await api_client.resolve_market(market_id, data['outcome'])
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/markets/<int:market_id>', methods=['DELETE'])
async def api_admin_delete_market(market_id):
    """Delete market"""
    try:
        result = await api_client.delete_market(market_id)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/markets/<int:market_id>/promote', methods=['PUT'])
async def api_admin_promote_market(market_id):
    """Promote market"""
    try:
        promotion_level = request.args.get('promotion_level', 'basic')
        hours = request.args.get('hours', 24, type=int)
        result = await api_client.promote_market(market_id, promotion_level, hours)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users')
async def api_admin_users():
    """Get all users"""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        users = await api_client.get_all_users_admin(limit=limit, offset=offset)
        return jsonify(users)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/balance', methods=['PUT'])
async def api_admin_update_balance(user_id):
    """Update user balance"""
    try:
        data = await request.get_json()
        result = await api_client.update_user_balance(
            user_id,
            pred_balance=data.get('pred_balance'),
            ton_balance=data.get('ton_balance')
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/rank', methods=['PUT'])
async def api_admin_update_rank(user_id):
    """Update user rank"""
    try:
        rank = request.args.get('rank')
        result = await api_client.update_user_rank(user_id, rank)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/users/<int:user_id>/activity')
async def api_admin_user_activity(user_id):
    """Get user activity"""
    try:
        activity = await api_client.get_user_activity(user_id)
        return jsonify(activity)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/users/<int:user_id>/referrals')
async def api_user_referrals(user_id):
    """Get user's referral statistics"""
    try:
        stats = await api_client._get(f"/users/{user_id}/referrals")
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/markets/create-event', methods=['POST'])
async def api_create_event():
    """Create user event - proxy to backend"""
    try:
        # Get form data
        form = await request.form
        files = await request.files

        user_id = session.get('user_id', 1)

        # Prepare data for backend
        import aiohttp
        data = aiohttp.FormData()
        data.add_field('user_id', str(user_id))
        data.add_field('title', form.get('title'))
        data.add_field('description', form.get('description'))
        data.add_field('category', form.get('category'))
        data.add_field('resolve_date', form.get('resolve_date'))

        # Add photo if exists
        if 'photo' in files:
            photo = files['photo']
            photo_bytes = photo.read()  # NOT async in Quart
            data.add_field('photo', photo_bytes,
                          filename=photo.filename,
                          content_type=photo.content_type)

        # Send to backend
        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(
                f"{app.config['API_URL']}/markets/create-event",
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return jsonify(result)
                else:
                    error_text = await response.text()
                    return jsonify({"error": error_text}), response.status

    except Exception as e:
        print(f"Error creating event: {e}")
        return jsonify({"error": str(e)}), 500


# ============ Support API Routes ============

@app.route('/api/support/tickets', methods=['POST'])
async def api_create_ticket():
    """Create support ticket - proxy to backend"""
    try:
        form = await request.form
        files = await request.files
        user_id = session.get('user_id', 1)

        # Prepare form data for backend
        import aiohttp
        data = aiohttp.FormData()
        data.add_field('user_id', str(user_id))
        data.add_field('subject', form.get('subject'))
        data.add_field('message', form.get('message'))
        data.add_field('priority', form.get('priority', 'medium'))

        # Add attachment if exists
        if 'attachment' in files and files['attachment'].filename:
            attachment = files['attachment']
            attachment_bytes = attachment.read()
            data.add_field('attachment', attachment_bytes,
                          filename=attachment.filename,
                          content_type=attachment.content_type)

        # Send to backend
        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(
                f"{app.config['API_URL']}/support/tickets",
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return jsonify(result)
                else:
                    error_text = await response.text()
                    return jsonify({"error": error_text}), response.status

    except Exception as e:
        print(f"Error creating ticket: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/support/tickets/<int:user_id>')
async def api_get_tickets(user_id):
    """Get user's tickets"""
    try:
        tickets = await api_client._get(f"/support/tickets/{user_id}")
        return jsonify(tickets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/support/tickets/<int:ticket_id>/messages')
async def api_get_ticket_messages(ticket_id):
    """Get ticket messages"""
    try:
        user_id = session.get('user_id', 1)
        messages = await api_client._get(f"/support/tickets/{ticket_id}/messages?user_id={user_id}")
        return jsonify(messages)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/support/tickets/<int:ticket_id>/messages', methods=['POST'])
async def api_send_message(ticket_id):
    """Send message in ticket - proxy to backend"""
    try:
        form = await request.form
        files = await request.files
        user_id = session.get('user_id', 1)

        # Prepare form data
        import aiohttp
        data = aiohttp.FormData()
        data.add_field('user_id', str(user_id))
        data.add_field('message', form.get('message'))

        # Add attachment if exists
        if 'attachment' in files and files['attachment'].filename:
            attachment = files['attachment']
            attachment_bytes = attachment.read()
            data.add_field('attachment', attachment_bytes,
                          filename=attachment.filename,
                          content_type=attachment.content_type)

        # Send to backend
        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(
                f"{app.config['API_URL']}/support/tickets/{ticket_id}/messages",
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return jsonify(result)
                else:
                    error_text = await response.text()
                    return jsonify({"error": error_text}), response.status

    except Exception as e:
        print(f"Error sending message: {e}")
        return jsonify({"error": str(e)}), 500


# ============ Admin Support API Routes ============

@app.route('/api/admin/support/tickets')
async def api_admin_get_all_tickets():
    """Get all support tickets for admin"""
    try:
        status = request.args.get('status')
        priority = request.args.get('priority')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)

        url = f"/support/admin/tickets?limit={limit}&offset={offset}"
        if status:
            url += f"&status={status}"
        if priority:
            url += f"&priority={priority}"

        tickets = await api_client._get(url)
        return jsonify(tickets)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/support/tickets/<int:ticket_id>/reply', methods=['POST'])
async def api_admin_reply_ticket(ticket_id):
    """Admin reply to ticket - proxy to backend"""
    try:
        form = await request.form
        files = await request.files

        # Prepare form data
        import aiohttp
        data = aiohttp.FormData()
        data.add_field('message', form.get('message'))

        # Add attachment if exists
        if 'attachment' in files and files['attachment'].filename:
            attachment = files['attachment']
            attachment_bytes = attachment.read()
            data.add_field('attachment', attachment_bytes,
                          filename=attachment.filename,
                          content_type=attachment.content_type)

        # Send to backend
        async with aiohttp.ClientSession() as session_http:
            async with session_http.post(
                f"{app.config['API_URL']}/support/admin/tickets/{ticket_id}/reply",
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return jsonify(result)
                else:
                    error_text = await response.text()
                    return jsonify({"error": error_text}), response.status

    except Exception as e:
        print(f"Error replying to ticket: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/admin/support/tickets/<int:ticket_id>/status', methods=['PUT'])
async def api_admin_update_ticket_status(ticket_id):
    """Update ticket status"""
    try:
        status = request.args.get('status')
        result = await api_client._put(f"/support/admin/tickets/{ticket_id}/status?status={status}", {})
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/static/tonconnect-manifest.json')
async def tonconnect_manifest():
    """Serve TON Connect manifest with CORS headers"""
    from quart import send_from_directory, make_response

    response = await make_response(await send_from_directory('static', 'tonconnect-manifest.json'))
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    response.headers['Content-Type'] = 'application/json'
    return response


# ============ CryptoCloud Payment Pages ============

@app.route('/successful-payment')
async def successful_payment():
    """
    Success page after CryptoCloud payment

    URL: https://thepred.tech/successful-payment

    User is redirected here after successful payment.
    Actual balance update happens via webhook.
    """
    user_id = session.get('user_id')
    return await render_template('payment_success.html', user_id=user_id)


@app.route('/failed-payment')
async def failed_payment():
    """
    Failed page after CryptoCloud payment failure

    URL: https://thepred.tech/failed-payment

    User is redirected here if payment fails or is cancelled.
    """
    user_id = session.get('user_id')
    return await render_template('payment_failed.html', user_id=user_id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8001, debug=app.config['DEV_MODE'])
