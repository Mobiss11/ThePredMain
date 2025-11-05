# Быстрый Деплой - ThePred

## 🎯 Что Готово к Деплою

### ✅ Исправления Критических Багов
1. Загрузка фото при создании события
2. Approve/Reject кнопки в админке
3. Редактирование пользователя в админке
4. Баланс "..." в Telegram
5. Ошибка enum "all" в фильтрах
6. Resolve события (PUT method)

### ✅ Новая Функциональность
1. Система миссий (7 дефолтных)
2. Иконки для миссий
3. Progress bar и зеленая кнопка claim
4. Таб "Cancelled" в админке
5. Фильтр "Approved Markets"
6. Реальный ранг в профиле
7. Реальные события пользователя

---

## 🚀 Команды для Деплоя

### 1. Локально: Коммит и Push

```bash
cd /Users/alluc/Documents/ThePred

# Добавить все изменения
git add backend/app/init_missions.py \
        backend/app/main.py \
        backend/app/models/mission.py \
        backend/app/api/endpoints/missions.py \
        backend/app/api/endpoints/admin.py \
        backend/alembic/versions/ \
        webapp/main.py \
        webapp/templates/missions.html \
        webapp/templates/profile.html \
        admin/main.py \
        admin/templates/markets.html \
        admin/templates/missions.html \
        DEPLOYMENT_GUIDE.md \
        QUICK_DEPLOY.md \
        MISSIONS_SUMMARY.md

# Коммит
git commit -m "feat: Add missions system and critical fixes

- Add 7 default missions with auto-initialization
- Add icon field to Mission model
- Fix photo upload in event creation
- Fix admin panel tabs and resolve function
- Update profile with real rank and events
- Add Telegram WebApp authentication improvements
"

# Push
git push origin main
```

### 2. На Сервере: Backup

```bash
ssh root@your-server
cd /root/ThePred

# ВАЖНО: Создать backup перед деплоем
docker-compose exec -T postgres pg_dump -U thepred thepred > backup_$(date +%Y%m%d_%H%M%S).sql

# Проверить
ls -lh backup_*.sql
```

### 3. На Сервере: Деплой

```bash
# Pull изменений
git pull origin main

# Остановить сервисы (кроме БД)
docker-compose stop backend webapp admin bot

# Применить миграцию
docker-compose exec backend alembic upgrade head

# Запустить все сервисы
docker-compose up -d backend webapp admin bot

# Подождать 10 секунд
sleep 10

# Проверить статус
docker-compose ps
```

### 4. На Сервере: Проверка

```bash
# Проверить миссии созданы
docker-compose logs backend | grep missions

# Должно быть:
# "✓ Created 7 default missions"
# или
# "✓ Missions already exist (7 missions found)"

# Проверить API
curl http://localhost:8000/health

# Проверить ошибки
docker-compose logs backend | grep ERROR
docker-compose logs webapp | grep ERROR
docker-compose logs admin | grep ERROR
```

---

## ✅ Чеклист Проверки

### Backend
- [ ] Миграция применена
- [ ] 7 миссий созданы
- [ ] `/health` отвечает OK
- [ ] Логи без ERROR

### Webapp
- [ ] Главная страница загружается
- [ ] Можно создать событие с фото
- [ ] `/missions` показывает 7 миссий с progress bar
- [ ] `/profile` показывает реальный ранг
- [ ] Баланс не "..." в Telegram

### Admin
- [ ] 3 таба: Pending, Approved Markets, Cancelled
- [ ] Approve/Reject работает
- [ ] После апрува кнопки исчезают
- [ ] Resolve работает
- [ ] `/admin/missions` показывает 7 миссий
- [ ] Редактирование пользователя сохраняет данные

### Bot
- [ ] Бот отвечает на /start
- [ ] WebApp открывается
- [ ] Можно делать ставки

---

## 🔧 Если Что-то Сломалось

### Откатить Код
```bash
# На сервере
git log --oneline -5
git reset --hard <previous-commit-hash>
docker-compose restart backend webapp admin bot
```

### Откатить Миграцию
```bash
docker-compose exec backend alembic downgrade -1
docker-compose restart backend
```

### Восстановить БД
```bash
docker-compose stop backend
docker-compose exec -T postgres psql -U thepred -d thepred < backup_20251104_120000.sql
docker-compose up -d backend
```

---

## 📝 Полная Документация

Подробные инструкции см. в:
- `DEPLOYMENT_GUIDE.md` - Полное руководство по деплою
- `MISSIONS_SUMMARY.md` - Детали системы миссий
- `CLAUDE.md` - Общая документация проекта

---

**Время деплоя**: ~10 минут
**Downtime**: ~30 секунд (только backend/webapp/admin restart)
