/**
 * TON Wallet Integration Module
 *
 * Handles TON Connect integration for deposits
 */

class TONWallet {
    constructor() {
        this.tonConnectUI = null;
        this.connected = false;
        this.address = null;
        this.modalJustOpened = false; // Track if modal just opened
        this.initPromise = this.init();
    }

    /**
     * Initialize TON Connect UI
     */
    async init() {
        try {
            console.log('🚀 TON Wallet: Initializing...');

            // Wait for TON_CONNECT_UI to be available
            if (typeof TON_CONNECT_UI === 'undefined') {
                console.error('❌ TON_CONNECT_UI not loaded');
                return;
            }

            console.log('✅ TON_CONNECT_UI library loaded');
            console.log('🔧 Creating TonConnectUI instance...');

            // Check if we're in Telegram WebApp
            const tg = window.Telegram?.WebApp;
            const isTelegramWebApp = !!tg;

            if (isTelegramWebApp) {
                console.log('🔵 Telegram WebApp detected');
                console.log('📍 WebApp version:', tg.version);
                console.log('📍 Platform:', tg.platform);
            }

            // Initialize TON Connect UI
            this.tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
                manifestUrl: 'https://thepred.tech/static/tonconnect-manifest.json',
                buttonRootId: null, // We'll create custom button
                uiPreferences: {
                    theme: 'DARK'
                },
                walletsListConfiguration: {
                    includeWallets: [
                        {
                            appName: 'telegram-wallet',
                            name: 'Wallet',
                            imageUrl: 'https://wallet.tg/images/logo-288.png',
                            aboutUrl: 'https://wallet.tg/',
                            universalLink: 'https://t.me/wallet?attach=wallet',
                            bridgeUrl: 'https://bridge.ton.space/bridge',
                            platforms: ['ios', 'android', 'macos', 'windows', 'linux'],
                            jsBridgeKey: 'telegram-wallet'
                        },
                        {
                            appName: 'tonkeeper',
                            name: 'Tonkeeper',
                            imageUrl: 'https://tonkeeper.com/assets/tonconnect-icon.png',
                            aboutUrl: 'https://tonkeeper.com',
                            universalLink: 'https://app.tonkeeper.com/ton-connect',
                            bridgeUrl: 'https://bridge.tonapi.io/bridge',
                            platforms: ['ios', 'android', 'chrome', 'firefox', 'safari']
                        },
                        {
                            appName: 'mytonwallet',
                            name: 'MyTonWallet',
                            imageUrl: 'https://static.mytonwallet.io/icon-256.png',
                            aboutUrl: 'https://mytonwallet.io',
                            universalLink: 'https://connect.mytonwallet.org',
                            bridgeUrl: 'https://tonconnectbridge.mytonwallet.org/bridge',
                            platforms: ['chrome', 'ios', 'android', 'firefox', 'safari']
                        }
                    ]
                },
                actionsConfiguration: {
                    // Use format: https://t.me/BOT_NAME/APP_NAME
                    twaReturnUrl: 'https://t.me/The_Pred_Bot/app',
                    // CRITICAL: Force return after connection
                    returnStrategy: 'back',
                    // Modals configuration
                    modals: 'all'
                }
            });

            // Subscribe to connection status
            this.tonConnectUI.onStatusChange(async (wallet) => {
                console.log('🔔 TON Wallet: Status changed', wallet);

                if (wallet) {
                    this.connected = true;
                    this.address = wallet.account.address;

                    // Detect wallet type
                    const walletType = wallet.device?.appName || wallet.provider || 'unknown';
                    const isTelegramWallet = walletType.includes('telegram') ||
                                            wallet.device?.platform === 'telegram' ||
                                            (wallet.connectItems?.tonProof?.name || '').includes('telegram');

                    console.log('✅ TON Wallet connected:', this.address);
                    console.log('📍 Wallet details:', {
                        address: wallet.account.address,
                        chain: wallet.account.chain,
                        publicKey: wallet.account.publicKey,
                        walletType: walletType,
                        isTelegramWallet: isTelegramWallet,
                        device: wallet.device
                    });

                    // Show visual feedback
                    this.showConnectionStatus('Wallet connected!', 'success');

                    console.log('💥 FORCE CLOSE - Removing ALL TON Connect elements NOW');

                    // AGGRESSIVE NUCLEAR OPTION: Delete EVERYTHING
                    const nukeModal = () => {
                        let removedCount = 0;

                        // 1. Remove tc-root (main TON Connect container)
                        document.querySelectorAll('tc-root').forEach(el => {
                            el.remove();
                            removedCount++;
                        });

                        // 2. Remove by class patterns
                        document.querySelectorAll('[class*="tc-"], [class*="ton-connect-"], [class*="tonconnect"]').forEach(el => {
                            if (el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE') {
                                el.remove();
                                removedCount++;
                            }
                        });

                        // 3. Remove by ID patterns
                        document.querySelectorAll('[id*="tc-"], [id*="ton-connect-"], [id*="tonconnect"]').forEach(el => {
                            if (el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE') {
                                el.remove();
                                removedCount++;
                            }
                        });

                        // 4. Remove iframes (TON Connect uses iframes)
                        document.querySelectorAll('iframe').forEach(iframe => {
                            const src = iframe.src || '';
                            if (src.includes('ton') || src.includes('wallet') || src.includes('bridge')) {
                                iframe.remove();
                                removedCount++;
                            }
                        });

                        // 5. Remove any modal overlays/backdrops
                        document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="backdrop"]').forEach(el => {
                            const classes = el.className || '';
                            if (typeof classes === 'string' && (classes.includes('tc') || classes.includes('ton'))) {
                                el.remove();
                                removedCount++;
                            }
                        });

                        // 6. Nuclear option - find anything with TON/wallet in data attributes
                        document.querySelectorAll('[data-tc-modal], [data-tonconnect]').forEach(el => {
                            el.remove();
                            removedCount++;
                        });

                        console.log(`💥 Nuked ${removedCount} TON Connect elements`);
                    };

                    // STEP 1: Close via API (might not work, but try)
                    try {
                        console.log('🚪 Attempting closeModal()...');
                        this.tonConnectUI.closeModal();
                        console.log('✅ closeModal() called');
                    } catch (e) {
                        console.log('⚠️ closeModal() failed:', e.message);
                    }

                    // STEP 2: Immediate nuke (no delay)
                    nukeModal();

                    // STEP 3: Nuke again at different intervals
                    setTimeout(nukeModal, 50);
                    setTimeout(nukeModal, 150);
                    setTimeout(nukeModal, 300);
                    setTimeout(nukeModal, 600);
                    setTimeout(nukeModal, 1000);
                    setTimeout(nukeModal, 2000); // Extra nuke after 2 seconds

                    // Reset flag
                    this.modalJustOpened = false;

                    // CRITICAL: Use Telegram WebApp API to force return to app
                    const tg = window.Telegram?.WebApp;
                    if (tg) {
                        console.log('📱 Using Telegram WebApp API to return to app...');

                        try {
                            // Hide back button if visible
                            if (tg.BackButton && tg.BackButton.isVisible) {
                                console.log('🔙 Hiding Telegram BackButton');
                                tg.BackButton.hide();
                            }

                            // Expand to full screen (forces focus back to WebApp)
                            if (tg.expand) {
                                console.log('📱 Expanding WebApp to full screen');
                                tg.expand();
                            }

                            // Call ready() to signal WebApp is ready (might trigger return)
                            if (tg.ready) {
                                console.log('✅ Calling WebApp.ready()');
                                tg.ready();
                            }

                            // Hide MainButton if visible
                            if (tg.MainButton && tg.MainButton.isVisible) {
                                console.log('🔘 Hiding MainButton');
                                tg.MainButton.hide();
                            }

                            // Trigger haptic feedback (shows we're back in app)
                            if (tg.HapticFeedback) {
                                console.log('📳 Triggering success haptic');
                                tg.HapticFeedback.notificationOccurred('success');
                            }

                            // Show popup instead of alert (doesn't block UI)
                            if (tg.showPopup) {
                                setTimeout(() => {
                                    tg.showPopup({
                                        title: '✅ Успешно!',
                                        message: 'Кошелек подключен\n\n' + this.address.substring(0, 8) + '...' + this.address.substring(this.address.length - 6),
                                        buttons: [{type: 'ok'}]
                                    });
                                }, 500);
                            }
                        } catch (e) {
                            console.log('⚠️ Telegram API calls failed:', e);
                        }
                    }

                    // Trigger callback first
                    this.onConnectionChange(true, this.address);

                    // Auto-save to backend (without blocking UI)
                    try {
                        console.log('💾 Attempting to save address to backend...');
                        await this.saveAddress();
                        console.log('✅ Address saved successfully');
                    } catch (error) {
                        console.error('❌ Failed to save address (non-critical):', error);
                        // Don't show alert here - it blocks UI
                        // Just log the error
                    }
                } else {
                    this.connected = false;
                    this.address = null;
                    this.modalJustOpened = false; // Reset flag on disconnect
                    console.log('❌ TON Wallet disconnected');
                    this.onConnectionChange(false, null);
                }
            });

            console.log('✅ TonConnectUI instance created successfully');
            console.log('🔍 Checking for existing connection...');

            // Check if already connected
            const currentWallet = this.tonConnectUI.wallet;
            if (currentWallet) {
                this.connected = true;
                this.address = currentWallet.account.address;
                console.log('✅ TON Wallet: Already connected', this.address);
                console.log('📍 Wallet details:', {
                    address: currentWallet.account.address,
                    chain: currentWallet.account.chain
                });
            } else {
                console.log('ℹ️ No existing wallet connection found');
            }

            console.log('🎉 TON Wallet: Initialized successfully');
            console.log('📊 Final state:', {
                connected: this.connected,
                address: this.address,
                hasUI: !!this.tonConnectUI
            });
        } catch (error) {
            console.error('TON Wallet: Initialization failed:', error);
        }
    }

    /**
     * Connection status change callback
     * Override this in your code
     */
    onConnectionChange(connected, address) {
        // To be overridden
        console.log('Connection changed:', connected, address);
    }

    /**
     * Connect wallet
     */
    async connect() {
        console.log('🔌 TON Wallet: connect() called');
        await this.initPromise;

        if (!this.tonConnectUI) {
            console.error('❌ TON Connect UI not initialized');
            return;
        }

        try {
            // Check if we're in Telegram WebApp
            const tg = window.Telegram?.WebApp;
            const isTelegramWebApp = !!tg;

            console.log('📱 Environment:', {
                isTelegramWebApp,
                platform: tg?.platform,
                version: tg?.version
            });

            // CRITICAL: Check for embedded wallet (runs inside Telegram)
            if (isTelegramWebApp) {
                console.log('🔍 Checking for embedded wallet...');
                console.log('📱 Telegram WebApp data:', {
                    platform: tg.platform,
                    version: tg.version,
                    initData: tg.initData ? 'exists' : 'missing'
                });

                try {
                    const walletsList = await this.tonConnectUI.getWallets();
                    console.log('📋 Total wallets found:', walletsList.length);

                    // Find Telegram Wallet by appName
                    const telegramWallet = walletsList.find(wallet =>
                        wallet.appName === 'telegram-wallet' ||
                        wallet.name === 'Wallet'
                    );

                    if (telegramWallet) {
                        console.log('✅ Found Telegram Wallet:', {
                            name: telegramWallet.name,
                            appName: telegramWallet.appName,
                            embedded: telegramWallet.embedded,
                            jsBridgeKey: telegramWallet.jsBridgeKey,
                            bridgeUrl: telegramWallet.bridgeUrl,
                            universalLink: telegramWallet.universalLink
                        });

                        console.log('🎯 Opening single wallet modal for Telegram Wallet...');

                        // Use openSingleWalletModal to connect directly to Telegram Wallet
                        await this.tonConnectUI.openSingleWalletModal(telegramWallet.appName);

                        console.log('✅ Telegram Wallet modal opened - should auto-close after connection');
                        return; // Exit - no selection modal
                    } else {
                        console.log('⚠️ Telegram Wallet not found in wallet list');
                        console.log('Available wallets:', walletsList.map(w => ({
                            name: w.name,
                            appName: w.appName
                        })));
                    }
                } catch (embeddedError) {
                    console.error('❌ Telegram Wallet connection failed:', embeddedError);
                    console.error('Error stack:', embeddedError.stack);
                }
            } else {
                console.log('⚠️ NOT running in Telegram WebApp, will show modal');
            }

            // FALLBACK: Show modal if embedded wallet not found or not in Telegram
            console.log('📱 Opening modal (fallback)...');
            this.modalJustOpened = true;

            // Auto-reset flag after 30 seconds
            setTimeout(() => {
                if (this.modalJustOpened) {
                    console.log('⏰ 30s timeout - resetting modalJustOpened flag');
                    this.modalJustOpened = false;
                }
            }, 30000);

            // Open modal
            await this.tonConnectUI.openModal();

            console.log('✅ Modal opened');

        } catch (error) {
            console.error('❌ Connection error:', error);
            this.showConnectionStatus('Connection failed: ' + error.message, 'error');

            if (!error.message || !error.message.includes('cancel')) {
                const tg = window.Telegram?.WebApp;
                tg?.showAlert('Ошибка подключения: ' + (error.message || 'Unknown error'));
            }
        }
    }

    /**
     * Disconnect wallet
     */
    async disconnect() {
        await this.initPromise;

        if (!this.tonConnectUI) {
            console.error('TON Connect UI not initialized');
            return;
        }

        try {
            await this.tonConnectUI.disconnect();
            console.log('TON Wallet: Disconnected');

            // Don't show alert - UI will update automatically via onStatusChange
        } catch (error) {
            console.error('TON Wallet: Disconnect error:', error);
        }
    }

    /**
     * Save wallet address to backend
     */
    async saveAddress() {
        if (!this.connected || !this.address) {
            throw new Error('Wallet not connected');
        }

        if (!window.userProfile || !window.userProfile.id) {
            throw new Error('User not authenticated');
        }

        try {
            const response = await fetch(`/api/wallet/connect?user_id=${window.userProfile.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ton_address: this.address
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to save address');
            }

            const data = await response.json();
            console.log('TON Wallet: Address saved to backend', data);

            // Don't show alert here - it can block the UI during connection
            // Success notification will be shown in the UI callback instead

            return data;
        } catch (error) {
            console.error('Failed to save address:', error);
            throw error;
        }
    }

    /**
     * Create deposit request
     */
    async createDeposit(amountTON) {
        if (!this.connected) {
            throw new Error('Wallet not connected');
        }

        if (!window.userProfile || !window.userProfile.id) {
            throw new Error('User not authenticated');
        }

        try {
            const response = await fetch(`/api/wallet/deposit/create?user_id=${window.userProfile.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    amount_ton: amountTON.toString()
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to create deposit');
            }

            const depositData = await response.json();
            return depositData;
        } catch (error) {
            console.error('Failed to create deposit:', error);
            throw error;
        }
    }

    /**
     * Send TON transaction
     */
    async sendTransaction(toAddress, amountTON, comment = '') {
        await this.initPromise;

        if (!this.connected) {
            throw new Error('Wallet not connected');
        }

        try {
            const transaction = {
                validUntil: Math.floor(Date.now() / 1000) + 1800, // 30 minutes
                messages: [
                    {
                        address: toAddress,
                        amount: (parseFloat(amountTON) * 1e9).toString(), // Convert to nanotons
                        payload: comment ? btoa(comment) : undefined
                    }
                ]
            };

            const result = await this.tonConnectUI.sendTransaction(transaction);
            return {
                success: true,
                boc: result.boc
            };
        } catch (error) {
            console.error('Transaction failed:', error);
            throw error;
        }
    }

    /**
     * Verify deposit on backend
     */
    async verifyDeposit(transactionId, txHash) {
        if (!window.userProfile || !window.userProfile.id) {
            throw new Error('User not authenticated');
        }

        try {
            const response = await fetch(`/api/wallet/deposit/verify?user_id=${window.userProfile.id}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    transaction_id: transactionId,
                    tx_hash: txHash
                })
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Verification failed');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to verify deposit:', error);
            throw error;
        }
    }

    /**
     * Full deposit flow
     */
    async deposit(amountTON) {
        try {
            // Step 1: Create deposit request
            console.log('Creating deposit request...');
            const depositData = await this.createDeposit(amountTON);

            // Step 2: Send transaction
            console.log('Sending transaction...');
            const txResult = await this.sendTransaction(
                depositData.deposit_address,
                depositData.amount_ton,
                `ThePred Deposit #${depositData.transaction_id}`
            );

            if (!txResult.success) {
                throw new Error('Transaction failed');
            }

            // Step 3: Verify on backend
            console.log('Verifying transaction...');
            const verifyResult = await this.verifyDeposit(
                depositData.transaction_id,
                txResult.boc
            );

            return {
                success: true,
                ...verifyResult
            };

        } catch (error) {
            console.error('Deposit failed:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Poll deposit status
     */
    async pollDepositStatus(transactionId, maxAttempts = 40) {
        if (!window.userProfile || !window.userProfile.id) {
            throw new Error('User not authenticated');
        }

        let attempts = 0;

        while (attempts < maxAttempts) {
            try {
                const response = await fetch(
                    `/api/wallet/deposit/${transactionId}/status?user_id=${window.userProfile.id}`
                );

                if (!response.ok) {
                    throw new Error('Failed to get status');
                }

                const status = await response.json();

                if (status.status === 'completed') {
                    return status;
                }

                if (status.status === 'failed') {
                    throw new Error('Deposit failed');
                }

                if (status.expired) {
                    throw new Error('Deposit expired');
                }

                attempts++;
                await new Promise(resolve => setTimeout(resolve, 3000)); // Wait 3 seconds

            } catch (error) {
                console.error('Error polling status:', error);
                throw error;
            }
        }

        throw new Error('Deposit timeout');
    }

    /**
     * Get wallet info from backend
     */
    async getWalletInfo() {
        try {
            const response = await fetch('/api/wallet/info');

            if (!response.ok) {
                throw new Error('Failed to get wallet info');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to get wallet info:', error);
            throw error;
        }
    }

    /**
     * Get user balance
     */
    async getBalance() {
        if (!window.userProfile || !window.userProfile.id) {
            throw new Error('User not authenticated');
        }

        try {
            const response = await fetch(`/api/wallet/balance?user_id=${window.userProfile.id}`);

            if (!response.ok) {
                throw new Error('Failed to get balance');
            }

            const data = await response.json();
            return data;
        } catch (error) {
            console.error('Failed to get balance:', error);
            throw error;
        }
    }

    /**
     * Show connection status (visual feedback)
     */
    showConnectionStatus(message, type = 'info') {
        console.log(`[${type.toUpperCase()}] ${message}`);

        // Create or update status indicator
        let indicator = document.getElementById('ton-wallet-status-indicator');
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = 'ton-wallet-status-indicator';
            indicator.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: rgba(0, 0, 0, 0.9);
                color: white;
                padding: 20px 30px;
                border-radius: 15px;
                font-size: 16px;
                font-weight: bold;
                z-index: 999999;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            `;
            document.body.appendChild(indicator);
        }

        // Set color based on type
        const colors = {
            success: '#4CAF50',
            error: '#f44336',
            warning: '#ff9800',
            info: '#2196F3'
        };
        indicator.style.borderLeft = `5px solid ${colors[type] || colors.info}`;
        indicator.textContent = message;
        indicator.style.display = 'block';

        // Auto-hide after 3 seconds
        setTimeout(() => {
            if (indicator) {
                indicator.style.display = 'none';
            }
        }, 3000);
    }
}

// Create global instance
window.tonWallet = new TONWallet();

// Helper function to format TON amount
function formatTON(amount, decimals = 2) {
    return parseFloat(amount).toFixed(decimals);
}

// Helper function to format PRED amount
function formatPRED(amount) {
    return parseInt(amount).toLocaleString();
}

console.log('TON Wallet module loaded');
