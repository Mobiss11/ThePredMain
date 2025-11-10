module.exports = {
  apps: [
    // Backend API
    {
      name: 'backend',
      script: 'backend/app/main.py',
      interpreter: 'python3',
      cwd: '/home/ThePredMain',
      env: {
        POSTGRES_HOST: 'localhost'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      error_file: '/root/.pm2/logs/backend-error.log',
      out_file: '/root/.pm2/logs/backend-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z'
    },

    // Telegram Bot
    {
      name: 'bot',
      script: 'bot/main.py',
      interpreter: 'python3',
      cwd: '/home/ThePredMain',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M'
    },

    // Telegram Worker (notifications queue)
    {
      name: 'telegram-worker',
      script: 'backend/telegram_worker.py',
      interpreter: 'python3',
      cwd: '/home/ThePredMain',
      env: {
        POSTGRES_HOST: 'localhost'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M'
    },

    // Broadcast Scheduler
    {
      name: 'broadcast-scheduler',
      script: 'backend/broadcast_scheduler.py',
      interpreter: 'python3',
      cwd: '/home/ThePredMain',
      env: {
        POSTGRES_HOST: 'localhost'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M',
      error_file: '/root/.pm2/logs/broadcast-scheduler-error.log',
      out_file: '/root/.pm2/logs/broadcast-scheduler-out.log'
    },

    // Mini App (Webapp)
    {
      name: 'webapp',
      script: 'webapp/main.py',
      interpreter: 'python3',
      cwd: '/home/ThePredMain',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },

    // Admin Panel
    {
      name: 'admin',
      script: 'admin/main.py',
      interpreter: 'python3',
      cwd: '/home/ThePredMain',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    },

    // Landing Page
    {
      name: 'landing',
      script: 'landing/main.py',
      interpreter: 'python3',
      cwd: '/home/ThePredMain',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '150M'
    },

    // Leaderboard Scheduler
    {
      name: 'leaderboard-scheduler',
      script: 'backend/leaderboard_scheduler.py',
      interpreter: 'python3',
      cwd: '/home/ThePredMain',
      env: {
        POSTGRES_HOST: 'localhost'
      },
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '200M'
    }
  ]
};
