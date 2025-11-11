/**
 * TON Connect Manual Implementation
 * Custom UI without @tonconnect/ui bugs
 */

class TONConnectManual {
    constructor(manifestUrl) {
        this.manifestUrl = manifestUrl;
        this.connector = null;
        this.connected = false;
        this.address = null;
        this.onConnectionChange = () => {};

        this.initPromise = this.init();
    }

    async init() {
        console.log('🚀 TON Connect Manual: Initializing...');

        // Wait for SDK to load - the SDK exports as TonConnectSDK.TonConnect
        if (!window.TonConnectSDK) {
            console.log('⏳ Waiting for TonConnectSDK...');
            await new Promise((resolve, reject) => {
                let attempts = 0;
                const maxAttempts = 50; // 5 seconds
                const check = setInterval(() => {
                    attempts++;

                    if (window.TonConnectSDK) {
                        console.log('✅ Found TonConnectSDK');
                        clearInterval(check);
                        resolve();
                    } else if (attempts >= maxAttempts) {
                        clearInterval(check);
                        console.error('❌ TonConnectSDK not found after 5 seconds');
                        reject(new Error('TonConnectSDK failed to load'));
                    }
                }, 100);
            });
        }

        console.log('🔧 Creating TonConnect instance...');
        console.log('TonConnectSDK object:', window.TonConnectSDK);

        // The actual class is TonConnectSDK.TonConnect
        this.connector = new window.TonConnectSDK.TonConnect({
            manifestUrl: this.manifestUrl
        });

        // Listen to status changes
        this.connector.onStatusChange((wallet) => {
            console.log('🔔 Status changed:', wallet);

            if (wallet) {
                this.connected = true;
                this.address = wallet.account.address;
                console.log('✅ Connected:', this.address);
                this.onConnectionChange(true, this.address);
            } else {
                this.connected = false;
                this.address = null;
                console.log('❌ Disconnected');
                this.onConnectionChange(false, null);
            }
        });

        // Restore connection from localStorage if exists
        console.log('🔄 Attempting to restore previous connection...');
        try {
            await this.connector.restoreConnection();

            // Check if connection was restored
            if (this.connector.connected && this.connector.wallet) {
                this.connected = true;
                this.address = this.connector.wallet.account.address;
                console.log('✅ Connection restored:', this.address);
                // Trigger callback immediately
                this.onConnectionChange(true, this.address);
            } else {
                console.log('ℹ️ No previous connection found');
            }
        } catch (error) {
            console.log('ℹ️ Could not restore connection:', error.message);
        }

        console.log('🎉 TON Connect Manual initialized');
    }

    /**
     * Show custom wallet selection modal
     */
    async connect() {
        console.log('🔌 Opening wallet selection...');
        await this.initPromise;

        // Create and show custom modal
        this.showWalletModal();
    }

    /**
     * Create custom wallet modal UI
     */
    showWalletModal() {
        // Remove existing modal if any
        const existing = document.getElementById('ton-wallet-modal');
        if (existing) existing.remove();

        // Create modal HTML
        const modal = document.createElement('div');
        modal.id = 'ton-wallet-modal';
        modal.innerHTML = `
            <div class="ton-modal-overlay">
                <div class="ton-modal-content">
                    <div class="ton-modal-header">
                        <h3>Connect TON Wallet</h3>
                        <button class="ton-modal-close" onclick="window.tonConnectManual.closeModal()">✕</button>
                    </div>

                    <div class="ton-wallet-list">
                        <!-- Telegram Wallet (for Mini Apps) -->
                        <div class="ton-wallet-item" onclick="window.tonConnectManual.connectWallet('telegram-wallet')">
                            <div class="ton-wallet-icon">💎</div>
                            <div class="ton-wallet-info">
                                <div class="ton-wallet-name">Wallet in Telegram</div>
                                <div class="ton-wallet-desc">Use wallet built into Telegram</div>
                            </div>
                        </div>

                        <!-- Tonkeeper -->
                        <div class="ton-wallet-item" onclick="window.tonConnectManual.connectWallet('tonkeeper')">
                            <div class="ton-wallet-icon">
                                <img src="https://tonkeeper.com/assets/tonconnect-icon.png" width="40" height="40" />
                            </div>
                            <div class="ton-wallet-info">
                                <div class="ton-wallet-name">Tonkeeper</div>
                                <div class="ton-wallet-desc">Popular TON wallet</div>
                            </div>
                        </div>

                        <!-- MyTonWallet -->
                        <div class="ton-wallet-item" onclick="window.tonConnectManual.connectWallet('mytonwallet')">
                            <div class="ton-wallet-icon">
                                <img src="https://static.mytonwallet.io/icon-256.png" width="40" height="40" />
                            </div>
                            <div class="ton-wallet-info">
                                <div class="ton-wallet-name">MyTonWallet</div>
                                <div class="ton-wallet-desc">Web wallet for TON</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Add styles
        this.injectStyles();

        // Animate in
        setTimeout(() => {
            modal.classList.add('ton-modal-visible');
        }, 10);
    }

    /**
     * Connect to specific wallet
     */
    async connectWallet(walletId) {
        console.log('🔌 Connecting to wallet:', walletId);

        try {
            // Get wallet list
            const wallets = await this.connector.getWallets();
            console.log('📋 Available wallets:', wallets.map(w => ({
                name: w.name,
                appName: w.appName,
                jsBridgeKey: w.jsBridgeKey
            })));

            // Find wallet with better matching logic
            let wallet = null;

            // Priority 1: Exact appName match
            wallet = wallets.find(w => w.appName === walletId);

            // Priority 2: Exact jsBridgeKey match
            if (!wallet) {
                wallet = wallets.find(w => w.jsBridgeKey === walletId);
            }

            // Priority 3: Name contains walletId (case-insensitive)
            if (!wallet) {
                const normalizedId = walletId.toLowerCase().replace('-', '').replace('_', '');
                wallet = wallets.find(w => {
                    const normalizedName = w.name.toLowerCase().replace('-', '').replace('_', '').replace(' ', '');
                    const normalizedAppName = (w.appName || '').toLowerCase().replace('-', '').replace('_', '');
                    return normalizedName.includes(normalizedId) || normalizedAppName.includes(normalizedId);
                });
            }

            // Special case: telegram-wallet
            if (!wallet && walletId === 'telegram-wallet') {
                wallet = wallets.find(w => w.name === 'Wallet' || w.appName === 'telegram-wallet');
            }

            if (!wallet) {
                console.error('❌ Wallet not found:', walletId);
                console.log('Available wallet IDs:', wallets.map(w => w.appName || w.name));
                alert('Кошелёк не найден: ' + walletId);
                return;
            }

            console.log('✅ Found wallet:', {
                name: wallet.name,
                appName: wallet.appName,
                universalLink: wallet.universalLink,
                bridgeUrl: wallet.bridgeUrl
            });

            // Close modal immediately
            this.closeModal();

            const tg = window.Telegram?.WebApp;
            const isTelegramWebApp = !!tg;

            // Connect to wallet
            console.log('🔗 Initiating connection...');
            let connectionUrl = await this.connector.connect({
                universalLink: wallet.universalLink,
                bridgeUrl: wallet.bridgeUrl
            });

            console.log('✅ Connection URL (before return URL):', connectionUrl);

            // Add return URL for auto-return to Telegram after connection
            if (isTelegramWebApp) {
                // Use proper twaReturnUrl format for Telegram Mini Apps
                // Format: tg://resolve?domain=BOT_USERNAME&appname=APP_SHORT_NAME
                const returnUrl = 'tg://resolve?domain=The_Pred_Bot&appname=app';
                const separator = connectionUrl.includes('?') ? '&' : '?';
                connectionUrl = `${connectionUrl}${separator}ret=${encodeURIComponent(returnUrl)}`;
                console.log('✅ Connection URL (with return URL):', connectionUrl);
            }

            // Special handling for Telegram Wallet - use openTelegramLink to stay inside Telegram
            if (walletId === 'telegram-wallet' && isTelegramWebApp && tg.openTelegramLink) {
                console.log('💎 Opening Telegram Wallet via openTelegramLink (stays inside Telegram)');
                tg.openTelegramLink(connectionUrl);
            }
            // Other wallets - use openLink
            else if (isTelegramWebApp && tg.openLink) {
                console.log('📱 Opening via Telegram.WebApp.openLink');
                tg.openLink(connectionUrl);
            }
            // Fallback for non-Telegram environments
            else {
                console.log('🌐 Opening via window.open');
                window.open(connectionUrl, '_blank');
            }

            console.log('✅ Wallet opened');

        } catch (error) {
            console.error('❌ Connection error:', error);
            alert('Ошибка подключения: ' + error.message);
        }
    }

    /**
     * Close modal
     */
    closeModal() {
        const modal = document.getElementById('ton-wallet-modal');
        if (modal) {
            modal.classList.remove('ton-modal-visible');
            setTimeout(() => modal.remove(), 300);
        }
    }

    /**
     * Disconnect wallet
     */
    async disconnect() {
        console.log('🔌 Disconnecting...');
        await this.initPromise;

        if (this.connector) {
            await this.connector.disconnect();
            this.connected = false;
            this.address = null;
        }
    }

    /**
     * Inject modal styles
     */
    injectStyles() {
        if (document.getElementById('ton-modal-styles')) return;

        const style = document.createElement('style');
        style.id = 'ton-modal-styles';
        style.textContent = `
            .ton-modal-overlay {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.8);
                display: flex;
                align-items: center;
                justify-content: center;
                z-index: 10000;
                opacity: 0;
                transition: opacity 0.3s ease;
                padding: 20px;
            }

            #ton-wallet-modal.ton-modal-visible .ton-modal-overlay {
                opacity: 1;
            }

            .ton-modal-content {
                background: linear-gradient(135deg, #1a1f35 0%, #0a0e1a 100%);
                border-radius: 16px;
                max-width: 400px;
                width: 100%;
                max-height: 80vh;
                overflow: auto;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
                border: 1px solid rgba(255, 215, 0, 0.2);
                transform: scale(0.9) translateY(20px);
                transition: transform 0.3s ease;
            }

            #ton-wallet-modal.ton-modal-visible .ton-modal-content {
                transform: scale(1) translateY(0);
            }

            .ton-modal-header {
                padding: 20px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .ton-modal-header h3 {
                margin: 0;
                color: #FFD700;
                font-size: 20px;
                font-weight: 700;
            }

            .ton-modal-close {
                background: none;
                border: none;
                color: #999;
                font-size: 24px;
                cursor: pointer;
                padding: 0;
                width: 32px;
                height: 32px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 8px;
                transition: all 0.2s;
            }

            .ton-modal-close:hover {
                background: rgba(255, 255, 255, 0.1);
                color: #fff;
            }

            .ton-wallet-list {
                padding: 12px;
            }

            .ton-wallet-item {
                display: flex;
                align-items: center;
                padding: 16px;
                background: rgba(255, 255, 255, 0.05);
                border-radius: 12px;
                margin-bottom: 12px;
                cursor: pointer;
                transition: all 0.2s;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }

            .ton-wallet-item:hover {
                background: rgba(255, 215, 0, 0.1);
                border-color: rgba(255, 215, 0, 0.3);
                transform: translateX(4px);
            }

            .ton-wallet-icon {
                width: 48px;
                height: 48px;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 32px;
                margin-right: 16px;
                flex-shrink: 0;
            }

            .ton-wallet-icon img {
                border-radius: 12px;
            }

            .ton-wallet-info {
                flex: 1;
            }

            .ton-wallet-name {
                font-size: 16px;
                font-weight: 600;
                color: #E8E9ED;
                margin-bottom: 4px;
            }

            .ton-wallet-desc {
                font-size: 13px;
                color: #999;
            }
        `;

        document.head.appendChild(style);
    }

    /**
     * Save address to backend
     */
    async saveAddress() {
        if (!this.address) return;

        console.log('💾 Saving address to backend:', this.address);

        try {
            const response = await fetch('/api/wallet/address', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    address: this.address
                })
            });

            if (response.ok) {
                console.log('✅ Address saved');
            } else {
                console.error('❌ Failed to save address:', response.status);
            }
        } catch (error) {
            console.error('❌ Save error:', error);
        }
    }
}

// Initialize on load
console.log('TON Connect Manual module loaded');
