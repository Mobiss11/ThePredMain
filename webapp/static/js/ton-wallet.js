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
        this.initPromise = this.init();
    }

    /**
     * Initialize TON Connect UI
     */
    async init() {
        try {
            console.log('TON Wallet: Initializing...');

            // Wait for TON_CONNECT_UI to be available
            if (typeof TON_CONNECT_UI === 'undefined') {
                console.error('TON_CONNECT_UI not loaded');
                return;
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
                            platforms: ['ios', 'android', 'macos', 'windows', 'linux']
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
                    twaReturnUrl: 'https://t.me/The_Pred_Bot/app'
                }
            });

            // Subscribe to connection status
            this.tonConnectUI.onStatusChange((wallet) => {
                console.log('TON Wallet: Status changed', wallet);

                if (wallet) {
                    this.connected = true;
                    this.address = wallet.account.address;
                    console.log('TON Wallet connected:', this.address);

                    // Trigger callback
                    this.onConnectionChange(true, this.address);

                    // Auto-save to backend
                    this.saveAddress().catch(error => {
                        console.error('Failed to save address:', error);
                    });
                } else {
                    this.connected = false;
                    this.address = null;
                    console.log('TON Wallet disconnected');
                    this.onConnectionChange(false, null);
                }
            });

            // Check if already connected
            const currentWallet = this.tonConnectUI.wallet;
            if (currentWallet) {
                this.connected = true;
                this.address = currentWallet.account.address;
                console.log('TON Wallet: Already connected', this.address);
            }

            console.log('TON Wallet: Initialized successfully');
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
        await this.initPromise;

        if (!this.tonConnectUI) {
            console.error('TON Connect UI not initialized');
            return;
        }

        try {
            console.log('TON Wallet: Opening connection modal...');

            // Open wallet connection modal
            await this.tonConnectUI.openModal();

            console.log('TON Wallet: Modal opened');
            // Connection result will be handled by onStatusChange callback

        } catch (error) {
            console.error('TON Wallet: Connection error:', error);

            // Show error to user only if it's not a user cancellation
            if (!error.message || !error.message.includes('cancel')) {
                const tg = window.Telegram?.WebApp;
                tg?.showAlert('Ошибка подключения кошелька: ' + (error.message || 'Unknown error'));
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

            const tg = window.Telegram?.WebApp;
            tg?.showAlert('Кошелек отключен');
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

            // Show success message
            const tg = window.Telegram?.WebApp;
            tg?.showAlert('✅ Кошелек успешно подключен!');

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
