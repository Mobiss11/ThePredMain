// Telegram Web App SDK initialization
const tg = window.Telegram?.WebApp;

if (tg) {
    // Expand to full height
    tg.expand();

    // Enable closing confirmation
    tg.enableClosingConfirmation();

    // Set header color
    tg.setHeaderColor('#0A0E1A');
    tg.setBackgroundColor('#0A0E1A');

    // Ready signal
    tg.ready();

    console.log('Telegram WebApp initialized:', {
        version: tg.version,
        platform: tg.platform,
        colorScheme: tg.colorScheme,
        user: tg.initDataUnsafe?.user
    });

    // Get user data
    window.tgUser = tg.initDataUnsafe?.user;
    window.tgInitData = tg.initData;

    // Get user photo URL from Telegram
    if (window.tgUser?.photo_url) {
        window.tgUserPhotoUrl = window.tgUser.photo_url;
    }
}

// Helper functions
window.showTgAlert = (message) => {
    if (tg) {
        tg.showAlert(message);
    } else {
        alert(message);
    }
};

window.showTgConfirm = (message, callback) => {
    if (tg) {
        tg.showConfirm(message, callback);
    } else {
        const result = confirm(message);
        callback(result);
    }
};

window.closeTgApp = () => {
    if (tg) {
        tg.close();
    }
};

// Haptic feedback
window.tgHaptic = {
    light: () => tg?.HapticFeedback?.impactOccurred('light'),
    medium: () => tg?.HapticFeedback?.impactOccurred('medium'),
    heavy: () => tg?.HapticFeedback?.impactOccurred('heavy'),
    success: () => tg?.HapticFeedback?.notificationOccurred('success'),
    error: () => tg?.HapticFeedback?.notificationOccurred('error'),
    warning: () => tg?.HapticFeedback?.notificationOccurred('warning')
};
