"""
API Client for Backend communication
Handles all HTTP requests to the FastAPI backend
"""
import aiohttp
import os
from typing import Optional, Dict, List, Any


class BackendAPIClient:
    """Async HTTP client for Backend API"""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or os.getenv('API_URL', 'http://backend:8000')
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _get(self, endpoint: str) -> Dict[str, Any]:
        """Make GET request"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}{endpoint}"
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    async def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}{endpoint}"
        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    # ============ Markets ============

    async def get_markets(self, category: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Get list of markets"""
        endpoint = f"/markets/"
        if category:
            endpoint += f"?category={category}"
        return await self._get(endpoint)

    async def get_market(self, market_id: int) -> Dict:
        """Get market details"""
        return await self._get(f"/markets/{market_id}")

    # ============ Bets ============

    async def create_bet(
        self,
        user_id: int,
        market_id: int,
        position: str,  # "YES" or "NO"
        amount: float,
        currency: str = "PRED"
    ) -> Dict:
        """Create a new bet"""
        data = {
            "market_id": market_id,
            "position": position,
            "amount": amount,
            "currency": currency
        }
        return await self._post(f"/bets/?user_id={user_id}", data)

    async def get_bet_history(self, user_id: int) -> List[Dict]:
        """Get user's bet history"""
        return await self._get(f"/bets/history/{user_id}")

    # ============ Users ============

    async def get_user_profile(self, user_id: int) -> Dict:
        """Get user profile"""
        return await self._get(f"/users/profile/{user_id}")

    async def get_user_balance(self, user_id: int) -> Dict:
        """Get user balance"""
        return await self._get(f"/users/balance/{user_id}")

    async def activate_referral(self, user_id: int, referral_code: str) -> Dict:
        """Activate referral code"""
        data = {"referral_code": referral_code}
        return await self._post(f"/users/referral/{user_id}", data)

    # ============ Auth ============

    async def telegram_auth(
        self,
        telegram_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        photo_url: Optional[str] = None
    ) -> Dict:
        """Authenticate user via Telegram"""
        data = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "photo_url": photo_url
        }
        # Use simple register endpoint - returns user info
        result = await self._post("/auth/register", data)
        # Convert to expected format with 'id' field
        return {
            "id": result["user_id"],
            "telegram_id": result["telegram_id"],
            "username": result.get("username"),
            "first_name": result["first_name"],
            "photo_url": result.get("photo_url"),
            "pred_balance": result["pred_balance"],
            "referral_code": result["referral_code"]
        }

    # ============ Missions ============

    async def get_missions(self, user_id: int) -> List[Dict]:
        """Get user's missions"""
        return await self._get(f"/missions/{user_id}")

    async def claim_mission_reward(self, user_id: int, mission_id: int) -> Dict:
        """Claim mission reward"""
        return await self._post(f"/missions/claim/{user_id}/{mission_id}", {})

    # ============ Leaderboard ============

    async def get_leaderboard(
        self,
        limit: int = 100,
        sort_by: str = "profit"  # profit, win_rate, win_streak, total_wins
    ) -> List[Dict]:
        """Get leaderboard rankings"""
        endpoint = f"/leaderboard/?limit={limit}&sort_by={sort_by}"
        return await self._get(endpoint)

    async def get_user_rank(self, user_id: int) -> Dict:
        """Get user's rank in leaderboard"""
        return await self._get(f"/leaderboard/user/{user_id}")

    # ============ Admin ============

    async def get_platform_stats(self) -> Dict:
        """Get platform statistics"""
        return await self._get("/admin/stats")

    async def create_market(
        self,
        title: str,
        category: str,
        description: Optional[str] = None,
        resolve_date: Optional[str] = None,
        is_promoted: str = "none",
        promoted_until: Optional[str] = None
    ) -> Dict:
        """Create a new market (admin only)"""
        data = {
            "title": title,
            "category": category,
            "description": description,
            "resolve_date": resolve_date,
            "is_promoted": is_promoted,
            "promoted_until": promoted_until
        }
        return await self._post("/admin/markets", data)

    async def get_all_markets_admin(self, status: Optional[str] = None, limit: int = 50) -> List[Dict]:
        """Get all markets for admin panel"""
        endpoint = f"/admin/markets?limit={limit}"
        if status:
            endpoint += f"&status={status}"
        return await self._get(endpoint)

    async def resolve_market(self, market_id: int, outcome: str) -> Dict:
        """Resolve a market (admin only)"""
        data = {"outcome": outcome}
        return await self._post(f"/admin/markets/{market_id}/resolve", data)

    async def delete_market(self, market_id: int) -> Dict:
        """Delete a market (admin only)"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/admin/markets/{market_id}"
        async with self.session.delete(url) as response:
            response.raise_for_status()
            return await response.json()

    async def promote_market(
        self,
        market_id: int,
        promotion_level: str,
        hours: int = 24
    ) -> Dict:
        """Promote a market (admin only)"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/admin/markets/{market_id}/promote?promotion_level={promotion_level}&hours={hours}"
        async with self.session.put(url) as response:
            response.raise_for_status()
            return await response.json()

    async def get_all_users_admin(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        """Get all users for admin panel"""
        return await self._get(f"/admin/users?limit={limit}&offset={offset}")

    async def update_user_balance(
        self,
        user_id: int,
        pred_balance: Optional[float] = None,
        ton_balance: Optional[float] = None
    ) -> Dict:
        """Update user balance (admin only)"""
        data = {}
        if pred_balance is not None:
            data["pred_balance"] = pred_balance
        if ton_balance is not None:
            data["ton_balance"] = ton_balance

        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/admin/users/{user_id}/balance"
        async with self.session.put(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def update_user_rank(self, user_id: int, rank: str) -> Dict:
        """Update user rank (admin only)"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/admin/users/{user_id}/rank?rank={rank}"
        async with self.session.put(url) as response:
            response.raise_for_status()
            return await response.json()

    async def get_user_activity(self, user_id: int) -> Dict:
        """Get detailed user activity"""
        return await self._get(f"/admin/users/{user_id}/activity")

    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None


# Global API client instance
api_client = BackendAPIClient()
