// API Configuration
// Use webapp's own API routes which proxy to backend
const API_URL = '/api';

// Global state
let userBalance = {
    pred: 0,
    ton: 0
};

// Load user balance
async function loadUserBalance() {
    try {
        const response = await fetch(`${API_URL}/balance`);

        if (response.ok) {
            const data = await response.json();
            userBalance = data;

            // Update UI
            const predBalance = document.getElementById('pred-balance');
            if (predBalance) {
                predBalance.innerText = formatNumber(data.pred_balance);
            }

            const predBalanceDisplay = document.getElementById('pred-balance-display');
            if (predBalanceDisplay) {
                predBalanceDisplay.innerText = formatNumber(data.pred_balance);
            }

            const tonBalanceDisplay = document.getElementById('ton-balance-display');
            if (tonBalanceDisplay) {
                tonBalanceDisplay.innerText = formatNumber(data.ton_balance);
            }
        }
    } catch (error) {
        console.error('Failed to load balance:', error);
    }
}

// Format numbers
function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toFixed(2);
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
            window.showTgAlert(`Bet placed! Potential win: ${bet.potential_win} PRED`);
            await loadUserBalance();
            return true;
        } else {
            const error = await response.json();
            window.tgHaptic?.error();
            window.showTgAlert(error.error || error.detail || 'Failed to place bet');
            return false;
        }
    } catch (error) {
        console.error('Bet error:', error);
        window.tgHaptic?.error();
        window.showTgAlert('Network error. Please try again.');
        return false;
    }
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
document.addEventListener('DOMContentLoaded', () => {
    // Load initial data
    loadUserBalance();

    // Add haptic feedback to all buttons
    document.querySelectorAll('button, a').forEach(element => {
        element.addEventListener('click', () => {
            window.tgHaptic?.light();
        });
    });

    // Refresh balance every 30 seconds
    setInterval(loadUserBalance, 30000);
});

// Export functions
window.placeBet = placeBet;
window.copyToClipboard = copyToClipboard;
window.formatNumber = formatNumber;
window.loadUserBalance = loadUserBalance;
window.loadMarkets = loadMarkets;
window.getMarket = getMarket;
