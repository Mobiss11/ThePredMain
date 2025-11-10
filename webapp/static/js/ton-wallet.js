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
            // Initialize TON Connect UI
            this.tonConnectUI = new TON_CONNECT_UI.TonConnectUI({
                manifestUrl: 'https://thepred.tech/static/tonconnect-manifest.json',
                buttonRootId: null, // We'll create custom button
                uiPreferences: {
                    theme: 'DARK'
                }
            });

            // Subscribe to connection status
            this.tonConnectUI.onStatusChange((wallet) => {
                if (wallet) {
                    this.connected = true;
                    this.address = wallet.account.address;
                    console.log('TON Wallet connected:', this.address);
                    this.onConnectionChange(true, this.address);
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
            }

            console.log('TON Connect initialized successfully');
        } catch (error) {
            console.error('Failed to initialize TON Connect:', error);
            throw error;
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

        try {
            // Open wallet connection modal
            const walletConnectionSource = await this.tonConnectUI.connectWallet();

            console.log('Wallet connection initiated');

            // Wait for connection with timeout
            return new Promise((resolve, reject) => {
                let resolved = false;

                const checkConnection = setInterval(() => {
                    if (this.connected && this.address && !resolved) {
                        resolved = true;
                        clearInterval(checkConnection);
                        console.log('Wallet connected successfully:', this.address);
                        resolve({
                            success: true,
                            address: this.address
                        });
                    }
                }, 100);

                // Timeout after 60 seconds
                setTimeout(() => {
                    if (!resolved) {
                        resolved = true;
                        clearInterval(checkConnection);

                        if (!this.connected) {
                            console.log('Connection timeout or cancelled by user');
                            resolve({
                                success: false,
                                error: 'Connection cancelled or timeout'
                            });
                        }
                    }
                }, 60000);
            });
        } catch (error) {
            console.error('Wallet connection error:', error);

            // Check if user cancelled
            if (error.message && error.message.includes('cancel')) {
                return {
                    success: false,
                    error: 'Connection cancelled by user'
                };
            }

            return {
                success: false,
                error: error.message || 'Failed to connect wallet'
            };
        }
    }

    /**
     * Disconnect wallet
     */
    async disconnect() {
        await this.initPromise;

        try {
            await this.tonConnectUI.disconnect();
            return { success: true };
        } catch (error) {
            console.error('Failed to disconnect wallet:', error);
            return {
                success: false,
                error: error.message
            };
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
