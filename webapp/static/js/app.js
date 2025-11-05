// API_URL is defined in base.html

// Global state
let userBalance = {
    pred: 0,
    ton: 0
};

let userProfile = null;
window.userProfile = null;

// Load user profile
async function loadUserProfile() {
    try {
        console.log('Loading user profile from:', `${API_URL}/profile`);
        const response = await fetch(`${API_URL}/profile`);
        console.log('Profile response status:', response.status);

        if (response.ok) {
            userProfile = await response.json();
            window.userProfile = userProfile;
            console.log('User profile loaded successfully:', userProfile);

            // Update balance
            userBalance.pred = userProfile.pred_balance;
            userBalance.ton = userProfile.ton_balance;

            // Update balance displays
            const predBalance = document.getElementById('pred-balance');
            if (predBalance) {
                console.log('Updating pred-balance to:', userProfile.pred_balance);
                predBalance.innerText = formatNumber(userProfile.pred_balance);
            }

            const predBalanceDisplay = document.getElementById('pred-balance-display');
            if (predBalanceDisplay) {
                console.log('Updating pred-balance-display to:', userProfile.pred_balance);
                predBalanceDisplay.innerText = formatNumber(userProfile.pred_balance);
            }

            const tonBalanceDisplay = document.getElementById('ton-balance-display');
            if (tonBalanceDisplay) {
                console.log('Updating ton-balance-display to:', userProfile.ton_balance);
                tonBalanceDisplay.innerText = formatNumber(userProfile.ton_balance);
            }

            // Update avatar in header
            const avatar = document.getElementById('user-avatar');
            const avatarPlaceholder = document.getElementById('user-avatar-placeholder');
            if (userProfile.photo_url) {
                if (avatar) {
                    avatar.src = userProfile.photo_url;
                    avatar.style.display = 'block';
                }
                if (avatarPlaceholder) {
                    avatarPlaceholder.style.display = 'none';
                }
            }

            // Also update profile page avatar if exists
            const profileAvatar = document.getElementById('profile-avatar');
            const profileAvatarPlaceholder = document.getElementById('profile-avatar-placeholder');
            if (userProfile.photo_url) {
                if (profileAvatar) {
                    profileAvatar.src = userProfile.photo_url;
                    profileAvatar.style.display = 'block';
                }
                if (profileAvatarPlaceholder) {
                    profileAvatarPlaceholder.style.display = 'none';
                }
            }

            return userProfile;
        } else {
            const errorData = await response.text();
            console.error('Failed to load profile - Status:', response.status);
            console.error('Failed to load profile - Response:', errorData);

            if (response.status === 401) {
                console.error('Not authenticated! User needs to login through Telegram or dev_login');
                // Don't show alert in production - let user see empty state
            } else {
                alert('Ошибка загрузки профиля: ' + errorData);
            }
        }
    } catch (error) {
        console.error('Failed to load profile (exception):', error);
        alert('Ошибка загрузки профиля: ' + error.message);
    }
    return null;
}

// Load user balance (backward compatibility)
async function loadUserBalance() {
    return await loadUserProfile();
}

// Format numbers
function formatNumber(num) {
    if (num === null || num === undefined) {
        return '0.00';
    }
    // Convert to number if it's a string
    const n = typeof num === 'string' ? parseFloat(num) : num;
    if (isNaN(n)) {
        return '0.00';
    }
    if (n >= 1000000) {
        return (n / 1000000).toFixed(1) + 'M';
    } else if (n >= 1000) {
        return (n / 1000).toFixed(1) + 'K';
    }
    return n.toFixed(2);
}

// Place bet
async function placeBet(marketId, position, amount) {
    try {
        window.tgHaptic?.light();

        const response = await fetch(`${API_URL}/bets`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                market_id: marketId,
                position: position,
                amount: amount,
                currency: 'PRED'
            })
        });

        if (response.ok) {
            const bet = await response.json();
            window.tgHaptic?.success();
            window.showTgAlert(`✅ Прогноз принят!\n💰 Потенциальный выигрыш: ${formatNumber(bet.potential_win)} PRED`);

            // Reload user balance
            await loadUserBalance();

            // Reload user's active bets
            await loadUserActiveBets();

            // Trigger markets reload if the function exists
            if (typeof window.reloadMarkets === 'function') {
                window.reloadMarkets();
            }

            return true;
        } else {
            const error = await response.json();
            window.tgHaptic?.error();
            window.showTgAlert('❌ ' + (error.error || error.detail || 'Ошибка при размещении прогноза'));
            return false;
        }
    } catch (error) {
        console.error('Bet error:', error);
        window.tgHaptic?.error();
        window.showTgAlert('❌ Ошибка сети. Попробуйте снова.');
        return false;
    }
}

// Load user's active bets
let userActiveBets = [];
async function loadUserActiveBets() {
    try {
        // Wait for user profile to be loaded
        if (!userProfile || !userProfile.id) {
            console.log('User profile not loaded yet, skipping active bets load');
            return [];
        }

        const response = await fetch(`${API_URL}/bets/active/${userProfile.id}`);
        if (response.ok) {
            userActiveBets = await response.json();
            window.userActiveBets = userActiveBets;
            console.log('Loaded active bets:', userActiveBets);
            return userActiveBets;
        }
        return [];
    } catch (error) {
        console.error('Failed to load active bets:', error);
        return [];
    }
}

// Check if user has active bet on market
function hasActiveBetOnMarket(marketId) {
    return userActiveBets.some(bet => bet.market_id === marketId);
}

// Load markets
async function loadMarkets(category = null) {
    try {
        const url = category ? `${API_URL}/markets?category=${category}` : `${API_URL}/markets`;
        const response = await fetch(url);

        if (response.ok) {
            const markets = await response.json();
            return markets;
        }
        return [];
    } catch (error) {
        console.error('Failed to load markets:', error);
        return [];
    }
}

// Get market details
async function getMarket(marketId) {
    try {
        const response = await fetch(`${API_URL}/markets/${marketId}`);
        if (response.ok) {
            return await response.json();
        }
        return null;
    } catch (error) {
        console.error('Failed to load market:', error);
        return null;
    }
}

// Copy to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        window.tgHaptic?.success();
        window.showTgAlert('Copied to clipboard!');
    }).catch(() => {
        window.tgHaptic?.error();
        window.showTgAlert('Failed to copy');
    });
}

// Add button click handlers
document.addEventListener('DOMContentLoaded', async () => {
    // Load initial data (profile first, then bets)
    await loadUserBalance();
    await loadUserActiveBets();

    // Add haptic feedback to all buttons
    document.querySelectorAll('button, a').forEach(element => {
        element.addEventListener('click', () => {
            window.tgHaptic?.light();
        });
    });

    // Refresh balance and active bets every 30 seconds
    setInterval(async () => {
        await loadUserBalance();
        await loadUserActiveBets();
    }, 30000);
});

// Export functions
window.placeBet = placeBet;
window.copyToClipboard = copyToClipboard;
window.formatNumber = formatNumber;
window.loadUserBalance = loadUserBalance;
window.loadMarkets = loadMarkets;
window.getMarket = getMarket;
window.loadUserActiveBets = loadUserActiveBets;
window.hasActiveBetOnMarket = hasActiveBetOnMarket;
