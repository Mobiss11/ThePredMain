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
        this.isRestoringConnection = false; // Flag to prevent alert on restore
        this.isLoadedFromDatabase = false; // Flag to track if wallet loaded from DB (not connected via SDK)

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
            this.isRestoringConnection = true; // Set flag to prevent alert
            await this.connector.restoreConnection();

            // Check if connection was restored
            if (this.connector.connected && this.connector.wallet) {
                this.connected = true;
                this.address = this.connector.wallet.account.address;
                console.log('✅ Connection restored:', this.address);
                // Trigger callback immediately (without showing alert)
                this.onConnectionChange(true, this.address);
            } else {
                console.log('ℹ️ No previous connection found');
            }
        } catch (error) {
            console.log('ℹ️ Could not restore connection:', error.message);
        } finally {
            this.isRestoringConnection = false; // Reset flag
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

        // If wallet was loaded from database (not connected via SDK)
        if (this.isLoadedFromDatabase) {
            console.log('💾 Disconnecting via API (wallet loaded from DB)');

            const userId = window.userProfile?.id;
            if (!userId) {
                console.error('❌ No user_id found');
                throw new Error('User ID not found');
            }

            try {
                const response = await fetch(`/api/wallet/disconnect/${userId}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });

                if (response.ok) {
                    console.log('✅ Wallet disconnected via API');
                    this.connected = false;
                    this.address = null;
                    this.isLoadedFromDatabase = false;
                } else {
                    const error = await response.json();
                    console.error('❌ Failed to disconnect via API:', error);
                    throw new Error(error.error || 'Failed to disconnect wallet');
                }
            } catch (error) {
                console.error('❌ Disconnect error:', error);
                throw error;
            }
        }
        // If wallet is connected via SDK
        else if (this.connector && this.connected) {
            console.log('🔗 Disconnecting via TON Connect SDK');
            await this.connector.disconnect();
            this.connected = false;
            this.address = null;
            this.isLoadedFromDatabase = false;
        } else {
            console.warn('⚠️ No wallet connected');
        }
    }

    /**
     * Send transaction via TON Connect
     */
    async sendTransaction(transaction) {
        console.log('📤 sendTransaction called with:', transaction);
        await this.initPromise;

        if (!this.connector || !this.connected) {
            throw new Error('Wallet not connected');
        }

        // Send transaction via TON Connect SDK
        // This will automatically open the wallet app in Telegram
        try {
            console.log('🔗 Calling connector.sendTransaction...');
            console.log('🔗 Connector state:', {
                connected: this.connector.connected,
                wallet: this.connector.wallet,
                account: this.connector.account,
                provider: this.connector.provider
            });

            // Log detailed wallet info
            if (this.connector.wallet) {
                console.log('👛 Wallet details:', {
                    device: this.connector.wallet.device,
                    provider: this.connector.wallet.provider,
                    account: this.connector.wallet.account
                });
            }

            // Log detailed provider info
            if (this.connector.provider) {
                console.log('🔌 Provider details:', {
                    type: this.connector.provider.constructor.name,
                    connection: this.connector.provider.connection,
                    // Try to access provider methods
                    hasSendTransaction: typeof this.connector.provider.sendTransaction === 'function',
                    hasConnect: typeof this.connector.provider.connect === 'function'
                });
            }

            // Check if we're in Telegram WebApp
            const tg = window.Telegram?.WebApp;
            if (tg) {
                console.log('📱 Running in Telegram WebApp');
                console.log('📱 Telegram version:', tg.version);
                console.log('📱 Platform:', tg.platform);
            }

            // Add timeout to prevent infinite waiting
            const timeoutMs = 60000; // 60 seconds
            const timeoutPromise = new Promise((_, reject) => {
                setTimeout(() => {
                    console.error('⏰ Transaction timeout after 60 seconds');
                    reject(new Error('Transaction timeout - wallet did not respond'));
                }, timeoutMs);
            });

            console.log('⏳ Waiting for wallet response (timeout: 60s)...');
            console.log('📦 Transaction payload:', JSON.stringify(transaction, null, 2));

            // Intercept window.open to catch transaction URL
            const originalOpen = window.open;
            const originalTgOpenLink = window.Telegram?.WebApp?.openLink;
            const originalTgOpenTelegramLink = window.Telegram?.WebApp?.openTelegramLink;

            let transactionUrlCaught = false;

            // Override window.open
            window.open = function(...args) {
                console.log('🔗 window.open intercepted:', args);
                transactionUrlCaught = true;

                // Use Telegram WebApp methods if available
                if (tg && args[0]) {
                    const url = args[0].toString();
                    console.log('📱 Opening via Telegram WebApp:', url);

                    // For Telegram Wallet links, use openTelegramLink
                    if (url.includes('ton://') || url.includes('tg://')) {
                        console.log('💎 Using openTelegramLink');
                        tg.openTelegramLink(url);
                    } else {
                        console.log('🌐 Using openLink');
                        tg.openLink(url);
                    }
                    return null;
                }

                return originalOpen.apply(window, args);
            };

            // Override Telegram WebApp methods too
            if (tg) {
                window.Telegram.WebApp.openLink = function(...args) {
                    console.log('📱 Telegram.WebApp.openLink intercepted:', args);
                    transactionUrlCaught = true;
                    return originalTgOpenLink.apply(window.Telegram.WebApp, args);
                };

                window.Telegram.WebApp.openTelegramLink = function(...args) {
                    console.log('💎 Telegram.WebApp.openTelegramLink intercepted:', args);
                    transactionUrlCaught = true;
                    return originalTgOpenTelegramLink.apply(window.Telegram.WebApp, args);
                };
            }

            // Try to call sendTransaction and monitor what happens
            let transactionPromise;
            try {
                console.log('🚀 Initiating sendTransaction...');
                transactionPromise = this.connector.sendTransaction(transaction);
                console.log('📨 sendTransaction promise created');

                // Wait a bit to see if URL was caught
                await new Promise(resolve => setTimeout(resolve, 1000));
                console.log('🔍 Transaction URL caught:', transactionUrlCaught);

                // If URL was not caught and we're using HTTP bridge, use manual fallback
                if (!transactionUrlCaught && this.connector.wallet.provider === 'http') {
                    console.warn('⚠️ SDK did not generate transaction URL, using manual fallback');

                    // Log full wallet device info to find the right URL
                    console.log('🔍 Full wallet object:', this.connector.wallet);
                    console.log('🔍 Wallet device:', this.connector.wallet.device);

                    // Build transaction URL manually
                    const walletUrl = this.connector.wallet.device?.universalLink ||
                                     this.connector.wallet.device?.deepLink ||
                                     this.connector.wallet.device?.appName;

                    console.log('🔍 Extracted wallet URL:', walletUrl);

                    // Always try to create transaction, even if walletUrl is not found
                    // We'll use TON transfer deep link format
                    const address = transaction.messages[0].address;
                    const amount = transaction.messages[0].amount;

                    // Convert nanoTON to TON for display
                    const tonAmount = (parseInt(amount) / 1_000_000_000).toString();

                    // Create TON deep link (works in Telegram)
                    // Format: ton://transfer/<address>?amount=<nanotons>
                    const txUrl = `ton://transfer/${address}?amount=${amount}`;

                    console.log('🔗 Manual transaction URL (TON deep link):', txUrl);
                    console.log('💰 Amount:', tonAmount, 'TON (', amount, 'nanoTON)');

                    // Open via Telegram WebApp
                    if (tg) {
                        console.log('💎 Opening transaction via Telegram WebApp');
                        console.log('📱 Using openTelegramLink for ton:// URL');

                        try {
                            tg.openTelegramLink(txUrl);
                            console.log('✅ Transaction link opened');

                            // Don't throw error, just show message
                            console.log('⏳ Transaction sent to Telegram Wallet. Waiting for user confirmation...');

                            // Close the modal after a delay
                            setTimeout(() => {
                                alert('Транзакция отправлена в Telegram Wallet. Пожалуйста, подтвердите в кошельке.');
                            }, 500);

                            // Cancel the SDK promise since we handled it manually
                            throw new Error('Transaction handled manually via TON deep link');
                        } catch (openError) {
                            console.error('❌ Error opening transaction link:', openError);
                            throw openError;
                        }
                    } else {
                        console.error('❌ Telegram WebApp not available');
                        throw new Error('Telegram WebApp not available');
                    }
                }
            } catch (syncError) {
                console.error('❌ Synchronous error in sendTransaction:', syncError);
                // Restore original functions
                window.open = originalOpen;
                if (tg) {
                    window.Telegram.WebApp.openLink = originalTgOpenLink;
                    window.Telegram.WebApp.openTelegramLink = originalTgOpenTelegramLink;
                }
                throw syncError;
            }

            // Race between transaction and timeout
            const result = await Promise.race([
                transactionPromise,
                timeoutPromise
            ]);

            // Restore original functions
            window.open = originalOpen;
            if (tg) {
                window.Telegram.WebApp.openLink = originalTgOpenLink;
                window.Telegram.WebApp.openTelegramLink = originalTgOpenTelegramLink;
            }

            console.log('✅ Transaction result:', result);
            return result;
        } catch (error) {
            console.error('❌ sendTransaction error:', error);
            console.error('Error details:', {
                message: error.message,
                code: error.code,
                stack: error.stack
            });
            throw error;
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
        if (!this.address) {
            console.warn('⚠️ No address to save');
            return;
        }

        // Wait for userProfile to load (max 5 seconds)
        console.log('⏳ Waiting for window.userProfile...');
        let attempts = 0;
        while (!window.userProfile && attempts < 50) {
            await new Promise(resolve => setTimeout(resolve, 100));
            attempts++;
        }

        // Get user_id from global userProfile
        const userId = window.userProfile?.id;
        if (!userId) {
            console.error('❌ No user_id found in window.userProfile after waiting');
            console.error('window.userProfile:', window.userProfile);
            return;
        }

        console.log('💾 Saving address to backend:', this.address, 'for user:', userId);

        try {
            const response = await fetch(`/api/wallet/connect/${userId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ton_address: this.address
                })
            });

            if (response.ok) {
                const result = await response.json();
                console.log('✅ Address saved to database:', result);
            } else {
                const error = await response.json();
                console.error('❌ Failed to save address:', response.status, error);
            }
        } catch (error) {
            console.error('❌ Save error:', error);
        }
    }
}

// Initialize on load
console.log('TON Connect Manual module loaded');
