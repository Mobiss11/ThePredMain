/**
 * TON Wallet Integration Module
 *
 * Handles TON Connect integration for deposits
 */

class TONWallet {
    constructor() {
        this.tg = window.Telegram?.WebApp;
        this.connected = false;
        this.address = null;
        this.initPromise = this.init();
    }

    /**
     * Initialize TON Wallet
     */
    async init() {
        try {
            console.log('TON Wallet: Initializing...');

            if (!this.tg) {
                console.warn('TON Wallet: Telegram WebApp not available');
                return;
            }

            console.log('TON Wallet: Telegram WebApp available');
            console.log('TON Wallet: Platform:', this.tg.platform);
            console.log('TON Wallet: Version:', this.tg.version);

            // Check if wallet button is available (Telegram 7.2+)
            if (typeof this.tg.requestWalletAccess === 'function') {
                console.log('TON Wallet: Wallet access API available');
            } else {
                console.log('TON Wallet: Wallet access API not available in this Telegram version');
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
     * Connect wallet using Telegram WebApp API
     */
    async connect() {
        await this.initPromise;

        console.log('TON Wallet: Starting connection...');

        if (!this.tg) {
            console.error('TON Wallet: Telegram WebApp not available');
            this.tg?.showAlert('Telegram WebApp не доступен. Откройте приложение через Telegram.');
            return;
        }

        try {
            // Show Telegram's built-in wallet button
            // This will open the wallet selection modal
            console.log('TON Wallet: Opening wallet connection...');

            // Use Telegram's showPopup to explain to user
            this.tg.showPopup({
                title: 'Подключение кошелька',
                message: 'Для пополнения баланса вам нужен TON кошелек. Используйте @wallet в Telegram или установите Tonkeeper.',
                buttons: [
                    {
                        id: 'open_wallet',
                        type: 'default',
                        text: 'Открыть @wallet'
                    },
                    {
                        id: 'enter_manual',
                        type: 'default',
                        text: 'Ввести адрес вручную'
                    },
                    {
                        type: 'cancel'
                    }
                ]
            }, (buttonId) => {
                if (buttonId === 'open_wallet') {
                    // Open @wallet bot
                    this.tg.openTelegramLink('https://t.me/wallet');
                } else if (buttonId === 'enter_manual') {
                    // Show input for manual address
                    this.showManualAddressInput();
                }
            });

            // Success - popup shown, user will select an option
            console.log('TON Wallet: Popup shown, waiting for user selection');

        } catch (error) {
            console.error('TON Wallet: Connection error:', error);
            this.tg?.showAlert('Ошибка: ' + error.message);
        }
    }

    /**
     * Show manual address input
     */
    showManualAddressInput() {
        const address = prompt('Введите ваш TON адрес (начинается с EQ или UQ):');

        if (!address) {
            return;
        }

        // Validate address format
        if (!address.match(/^(EQ|UQ)[A-Za-z0-9_-]{46}$/)) {
            this.tg?.showAlert('Неверный формат адреса. Адрес должен начинаться с EQ или UQ и содержать 48 символов.');
            return;
        }

        // Save address
        this.connected = true;
        this.address = address;
        console.log('TON Wallet: Manual address set:', address);

        // Trigger callback
        this.onConnectionChange(true, address);

        // Save to backend
        this.saveAddress().then(() => {
            this.tg?.showAlert('✅ Кошелек успешно подключен!');
        }).catch((error) => {
            this.tg?.showAlert('❌ Ошибка сохранения адреса: ' + error.message);
        });
    }

    /**
     * Disconnect wallet
     */
    async disconnect() {
        await this.initPromise;

        try {
            // Clear local state
            this.connected = false;
            this.address = null;

            // Trigger callback
            this.onConnectionChange(false, null);

            console.log('TON Wallet: Disconnected');
            this.tg?.showAlert('Кошелек отключен');
        } catch (error) {
            console.error('Failed to disconnect wallet:', error);
            this.tg?.showAlert('Ошибка отключения кошелька: ' + error.message);
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
