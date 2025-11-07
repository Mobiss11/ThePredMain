// API_URL is defined in base.html

// Show that JS loaded - visual indicator
console.log('APP.JS LOADED - Version 2025110702');

// Add visual indicator in page
setTimeout(() => {
    const indicator = document.createElement('div');
    indicator.id = 'js-loaded-indicator';
    indicator.style.cssText = 'position:fixed;top:60px;left:10px;background:green;color:white;padding:4px 8px;border-radius:4px;font-size:10px;z-index:9999;';
    indicator.textContent = 'JS ✓';
    document.body.appendChild(indicator);

    // Remove after 3 seconds
    setTimeout(() => {
        indicator.remove();
    }, 3000);
}, 500);

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
        console.log('[loadUserProfile] Starting...');
        console.log('[loadUserProfile] API_URL:', API_URL);
        console.log('[loadUserProfile] Fetching from:', `${API_URL}/profile`);

        const response = await fetch(`${API_URL}/profile`);
        console.log('[loadUserProfile] Response status:', response.status);
        console.log('[loadUserProfile] Response ok:', response.ok);

        if (response.ok) {
            userProfile = await response.json();
            window.userProfile = userProfile;
            console.log('[loadUserProfile] ✅ Profile loaded successfully:', userProfile);
            console.log('[loadUserProfile] pred_balance:', userProfile.pred_balance, 'type:', typeof userProfile.pred_balance);
            console.log('[loadUserProfile] ton_balance:', userProfile.ton_balance, 'type:', typeof userProfile.ton_balance);

            // Update balance
            userBalance.pred = userProfile.pred_balance;
            userBalance.ton = userProfile.ton_balance;
            console.log('[loadUserProfile] userBalance updated:', userBalance);

            // Update balance displays
            const predBalance = document.getElementById('pred-balance');
            console.log('[loadUserProfile] pred-balance element:', predBalance);
            if (predBalance) {
                const formattedBalance = formatNumber(userProfile.pred_balance);
                console.log('[loadUserProfile] Formatted pred_balance:', formattedBalance);
                predBalance.innerText = formattedBalance;
                console.log('[loadUserProfile] ✅ Updated pred-balance to:', formattedBalance);
            } else {
                console.error('[loadUserProfile] ❌ pred-balance element NOT FOUND!');
            }

            const predBalanceDisplay = document.getElementById('pred-balance-display');
            console.log('[loadUserProfile] pred-balance-display element:', predBalanceDisplay);
            if (predBalanceDisplay) {
                const formattedBalance = formatNumber(userProfile.pred_balance);
                console.log('[loadUserProfile] ✅ Updated pred-balance-display to:', formattedBalance);
                predBalanceDisplay.innerText = formattedBalance;
            } else {
                console.log('[loadUserProfile] pred-balance-display element not found (this is OK if not on profile page)');
            }

            const tonBalanceDisplay = document.getElementById('ton-balance-display');
            console.log('[loadUserProfile] ton-balance-display element:', tonBalanceDisplay);
            if (tonBalanceDisplay) {
                const formattedBalance = formatNumber(userProfile.ton_balance);
                console.log('[loadUserProfile] ✅ Updated ton-balance-display to:', formattedBalance);
                tonBalanceDisplay.innerText = formattedBalance;
            } else {
                console.log('[loadUserProfile] ton-balance-display element not found (this is OK if not on profile page)');
            }

            // Show success indicator
            showSuccessIndicator('Профиль загружен');

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
            console.error('[loadUserProfile] ❌ Failed - Status:', response.status);
            console.error('[loadUserProfile] ❌ Response:', errorData);

            // Show visual error
            showErrorIndicator('Profile load failed: ' + response.status);

            if (response.status === 401) {
                console.error('[loadUserProfile] ❌ Not authenticated! User needs to login');
            }
        }
    } catch (error) {
        console.error('[loadUserProfile] ❌ Exception:', error);
        console.error('[loadUserProfile] ❌ Stack:', error.stack);

        // Show visual error
        showErrorIndicator('Profile exception: ' + error.message);
    }
    return null;
}

// Show error indicator in UI
function showErrorIndicator(message) {
    const indicator = document.createElement('div');
    indicator.style.cssText = 'position:fixed;bottom:80px;left:10px;right:10px;background:red;color:white;padding:8px;border-radius:8px;font-size:12px;z-index:9999;';
    indicator.textContent = '❌ ' + message;
    document.body.appendChild(indicator);

    setTimeout(() => {
        indicator.remove();
    }, 5000);
}

// Show success indicator in UI
function showSuccessIndicator(message) {
    const indicator = document.createElement('div');
    indicator.style.cssText = 'position:fixed;top:60px;right:10px;background:#10B981;color:white;padding:6px 12px;border-radius:8px;font-size:11px;z-index:9999;';
    indicator.textContent = '✅ ' + message;
    document.body.appendChild(indicator);

    setTimeout(() => {
        indicator.remove();
    }, 2000);
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
window.userActiveBets = [];  // Initialize immediately
async function loadUserActiveBets() {
    try {
        // Wait for user profile to be loaded
        if (!userProfile || !userProfile.id) {
            console.log('[loadUserActiveBets] User profile not loaded yet, setting empty array');
            userActiveBets = [];
            window.userActiveBets = [];
            return [];
        }

        console.log('[loadUserActiveBets] Fetching active bets for user:', userProfile.id);
        const response = await fetch(`${API_URL}/bets/active/${userProfile.id}`);
        if (response.ok) {
            userActiveBets = await response.json();
            window.userActiveBets = userActiveBets;
            console.log('[loadUserActiveBets] ✅ Loaded active bets:', userActiveBets);
            return userActiveBets;
        }
        console.log('[loadUserActiveBets] Response not OK, returning empty array');
        userActiveBets = [];
        window.userActiveBets = [];
        return [];
    } catch (error) {
        console.error('[loadUserActiveBets] ❌ Exception:', error);
        userActiveBets = [];
        window.userActiveBets = [];
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

// Force update balance in DOM
function forceUpdateBalance() {
    if (window.userProfile) {
        const predBalance = document.getElementById('pred-balance');
        if (predBalance) {
            predBalance.innerText = formatNumber(window.userProfile.pred_balance);
        }

        const predBalanceDisplay = document.getElementById('pred-balance-display');
        if (predBalanceDisplay) {
            predBalanceDisplay.innerText = formatNumber(window.userProfile.pred_balance);
        }

        const tonBalanceDisplay = document.getElementById('ton-balance-display');
        if (tonBalanceDisplay) {
            tonBalanceDisplay.innerText = formatNumber(window.userProfile.ton_balance);
        }
    }
}

// Add button click handlers
document.addEventListener('DOMContentLoaded', async () => {
    console.log('[DOMContentLoaded] ===== APP.JS INITIALIZED =====');
    console.log('[DOMContentLoaded] API_URL:', API_URL);
    console.log('[DOMContentLoaded] Document ready, loading user data...');

    // Load initial data (profile first, then bets)
    console.log('[DOMContentLoaded] Loading user balance...');
    await loadUserBalance();
    console.log('[DOMContentLoaded] Loading active bets...');
    await loadUserActiveBets();

    // Force update balance after small delay to ensure DOM is ready
    setTimeout(() => {
        forceUpdateBalance();
    }, 100);

    // Also try updating immediately
    forceUpdateBalance();

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
        forceUpdateBalance();
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
