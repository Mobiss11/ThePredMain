.PHONY: help build up down restart logs ps clean test dev prod db-migrate db-shell redis-shell backend-shell bot-shell webapp-shell admin-shell landing-shell backup prod-rebuild-app prod-rebuild-all prod-restart prod-status prod-clean

# Colors for output
GREEN  := \033[0;32m
YELLOW := \033[0;33m
RED    := \033[0;31m
NC     := \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)ThePred - Makefile Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# Development Commands
build: ## Build all Docker images
	@echo "$(GREEN)Building Docker images...$(NC)"
	docker-compose build

up: ## Start all services
	@echo "$(GREEN)Starting all services...$(NC)"
	docker-compose up -d
	@echo "$(GREEN)Services started!$(NC)"
	@echo "$(YELLOW)Backend API:$(NC)    http://localhost:8000/docs"
	@echo "$(YELLOW)Mini App:$(NC)       http://localhost:8001"
	@echo "$(YELLOW)Admin Panel:$(NC)    http://localhost:8002"
	@echo "$(YELLOW)Landing Page:$(NC)   http://localhost:8003"
	@echo "$(YELLOW)Telegram Bot:$(NC)   @The_Pred_Bot"

down: ## Stop all services
	@echo "$(RED)Stopping all services...$(NC)"
	docker-compose down

restart: ## Restart all services
	@echo "$(YELLOW)Restarting all services...$(NC)"
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-bot: ## Show bot logs
	docker-compose logs -f bot

logs-webapp: ## Show webapp logs
	docker-compose logs -f webapp

logs-admin: ## Show admin logs
	docker-compose logs -f admin

logs-landing: ## Show landing logs
	docker-compose logs -f landing

ps: ## Show running containers
	docker-compose ps

# Service-specific commands
backend-restart: ## Restart backend service
	docker-compose restart backend

bot-restart: ## Restart bot service
	docker-compose restart bot

webapp-restart: ## Restart webapp service
	docker-compose restart webapp

admin-restart: ## Restart admin service
	docker-compose restart admin

landing-restart: ## Restart landing service
	docker-compose restart landing

# Shell access
backend-shell: ## Open backend container shell
	docker-compose exec backend /bin/sh

bot-shell: ## Open bot container shell
	docker-compose exec bot /bin/sh

webapp-shell: ## Open webapp container shell
	docker-compose exec webapp /bin/sh

admin-shell: ## Open admin container shell
	docker-compose exec admin /bin/sh

landing-shell: ## Open landing container shell
	docker-compose exec landing /bin/sh

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U thepred -d thepred

redis-shell: ## Open Redis CLI
	docker-compose exec redis redis-cli

# Database commands
db-migrate: ## Run database migrations
	docker-compose exec backend alembic upgrade head

db-reset: ## Reset database (WARNING: deletes all data)
	@echo "$(RED)WARNING: This will delete all data!$(NC)"
	@read -p "Are you sure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		docker-compose down -v; \
		docker-compose up -d postgres; \
		sleep 5; \
		docker-compose up -d; \
	fi

backup: ## Backup database
	@echo "$(GREEN)Creating database backup...$(NC)"
	@mkdir -p backups
	docker-compose exec -T postgres pg_dump -U thepred thepred > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Backup created in backups/ directory$(NC)"

restore: ## Restore database from backup (usage: make restore FILE=backups/backup_xxx.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(RED)Error: Please specify backup file. Usage: make restore FILE=backups/backup_xxx.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Restoring database from $(FILE)...$(NC)"
	docker-compose exec -T postgres psql -U thepred -d thepred < $(FILE)
	@echo "$(GREEN)Database restored!$(NC)"

# Testing commands
test: ## Run tests
	@echo "$(GREEN)Running tests...$(NC)"
	docker-compose exec backend pytest

test-backend: ## Run backend tests
	docker-compose exec backend pytest tests/

test-coverage: ## Run tests with coverage
	docker-compose exec backend pytest --cov=app tests/

# Development helpers
dev: ## Start services in development mode with logs
	@echo "$(GREEN)Starting in development mode...$(NC)"
	docker-compose up

dev-build: ## Rebuild and start in development mode
	@echo "$(GREEN)Rebuilding and starting in development mode...$(NC)"
	docker-compose up --build

clean: ## Remove all containers, volumes, and images
	@echo "$(RED)Removing all containers, volumes, and images...$(NC)"
	docker-compose down -v --rmi all

clean-cache: ## Clean Python cache files
	@echo "$(GREEN)Cleaning Python cache...$(NC)"
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)Cache cleaned!$(NC)"

# Health checks
health: ## Check health of all services
	@echo "$(GREEN)Checking services health...$(NC)"
	@echo "$(YELLOW)PostgreSQL:$(NC)"
	@docker-compose exec postgres pg_isready -U thepred && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo "$(YELLOW)Redis:$(NC)"
	@docker-compose exec redis redis-cli ping && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo "$(YELLOW)Backend API:$(NC)"
	@curl -s http://localhost:8000/health > /dev/null && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo "$(YELLOW)Mini App:$(NC)"
	@curl -s http://localhost:8001 > /dev/null && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo "$(YELLOW)Admin Panel:$(NC)"
	@curl -s http://localhost:8002 > /dev/null && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"
	@echo "$(YELLOW)Landing Page:$(NC)"
	@curl -s http://localhost:8003 > /dev/null && echo "$(GREEN)✓ Healthy$(NC)" || echo "$(RED)✗ Unhealthy$(NC)"

stats: ## Show container resource usage
	docker stats --no-stream

# Quick setup
setup: ## Initial setup (create .env, build, start)
	@echo "$(GREEN)Setting up ThePred...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Creating .env file...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN).env created! Please edit it with your values.$(NC)"; \
	fi
	@make build
	@make up
	@echo "$(GREEN)Setup complete!$(NC)"

# Production commands
PROD_COMPOSE := docker compose -f docker-compose.prod.yml
APP_SERVICES := backend bot webapp admin landing

prod-build: ## Build for production
	@echo "$(GREEN)Building for production...$(NC)"
	$(PROD_COMPOSE) build --no-cache

prod-up: ## Start in production mode
	@echo "$(GREEN)Starting in production mode...$(NC)"
	$(PROD_COMPOSE) up -d

prod-logs: ## Show production logs
	$(PROD_COMPOSE) logs -f --tail=100

prod-rebuild-app: ## Rebuild production app services without cache (backend, bot, webapp, admin, landing)
	@echo "$(YELLOW)🔄 Stopping app services...$(NC)"
	$(PROD_COMPOSE) stop $(APP_SERVICES)
	@echo "$(RED)🗑️  Removing containers...$(NC)"
	$(PROD_COMPOSE) rm -f $(APP_SERVICES)
	@echo "$(RED)🗑️  Removing images...$(NC)"
	@docker images | grep 'thepredmain' | grep -E '(backend|bot|webapp|admin|landing)' | awk '{print $$3}' | xargs -r docker rmi -f 2>/dev/null || true
	@echo "$(GREEN)🔨 Rebuilding without cache...$(NC)"
	$(PROD_COMPOSE) build --no-cache $(APP_SERVICES)
	@echo "$(GREEN)🚀 Starting app services...$(NC)"
	$(PROD_COMPOSE) up -d $(APP_SERVICES)
	@echo "$(GREEN)✅ Done! Check logs: make prod-logs$(NC)"

prod-rebuild-all: ## Rebuild ALL production services without cache (including nginx)
	@echo "$(YELLOW)🔄 Stopping all services...$(NC)"
	$(PROD_COMPOSE) stop
	@echo "$(RED)🗑️  Removing containers...$(NC)"
	$(PROD_COMPOSE) rm -f
	@echo "$(RED)🗑️  Removing images...$(NC)"
	@docker images | grep 'thepredmain' | awk '{print $$3}' | xargs -r docker rmi -f 2>/dev/null || true
	@echo "$(GREEN)🔨 Rebuilding without cache...$(NC)"
	$(PROD_COMPOSE) build --no-cache
	@echo "$(GREEN)🚀 Starting all services...$(NC)"
	$(PROD_COMPOSE) up -d
	@echo "$(GREEN)✅ Done! Check logs: make prod-logs$(NC)"

prod-restart: ## Restart production app services
	@echo "$(YELLOW)🔄 Restarting app services...$(NC)"
	$(PROD_COMPOSE) restart $(APP_SERVICES)
	@echo "$(GREEN)✅ Done!$(NC)"

prod-status: ## Show production status
	@echo "$(GREEN)📊 Production Status$(NC)"
	@echo ""
	@echo "$(YELLOW)Containers:$(NC)"
	@docker ps -a --filter "name=thepred_" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
	@echo ""
	@echo "$(YELLOW)Disk Usage:$(NC)"
	@docker system df
	@echo ""
	@echo "$(YELLOW)HTTPS Check:$(NC)"
	@curl -s -o /dev/null -w "  thepred.com:  %{http_code}\n" https://thepred.com 2>/dev/null || echo "  thepred.com:  $(RED)FAILED$(NC)"
	@curl -s -o /dev/null -w "  thepred.tech: %{http_code}\n" https://thepred.tech 2>/dev/null || echo "  thepred.tech: $(RED)FAILED$(NC)"

prod-clean: ## Stop and remove production containers (keeps volumes)
	@echo "$(RED)⚠️  Stopping and removing all containers...$(NC)"
	$(PROD_COMPOSE) down
	@echo "$(GREEN)✅ Done! Volumes preserved.$(NC)"

# Monitoring
monitor: ## Show real-time logs and stats
	@gnome-terminal --tab --title="Logs" -- bash -c "make logs" \
		--tab --title="Stats" -- bash -c "watch -n 2 make stats" 2>/dev/null || \
	(echo "$(YELLOW)Opening logs in current terminal...$(NC)" && make logs)

# Quick actions
quick-test: up health ## Quick test - start and check health
	@echo "$(GREEN)Quick test completed!$(NC)"

quick-restart: down clean-cache up ## Quick restart - clean and restart
	@echo "$(GREEN)Quick restart completed!$(NC)"

# Info
info: ## Show project info
	@echo "$(GREEN)ThePred - Prediction Markets Platform$(NC)"
	@echo ""
	@echo "$(YELLOW)Services:$(NC)"
	@echo "  - Backend API (FastAPI)"
	@echo "  - Telegram Bot (aiogram)"
	@echo "  - Mini App (Quart + Jinja2)"
	@echo "  - Admin Panel (Quart + Jinja2)"
	@echo "  - Landing Page (Quart + Jinja2)"
	@echo "  - PostgreSQL 15"
	@echo "  - Redis 7"
	@echo ""
	@echo "$(YELLOW)URLs:$(NC)"
	@echo "  Backend:  http://localhost:8000/docs"
	@echo "  Mini App: http://localhost:8001"
	@echo "  Admin:    http://localhost:8002"
	@echo "  Landing:  http://localhost:8003"
	@echo "  Bot:      @The_Pred_Bot"
	@echo ""
	@echo "$(YELLOW)Quick Commands:$(NC)"
	@echo "  make up      - Start all services"
	@echo "  make down    - Stop all services"
	@echo "  make logs    - Show logs"
	@echo "  make health  - Check health"
	@echo "  make help    - Show all commands"
