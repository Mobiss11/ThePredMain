# Deployment Guide: Leaderboard System Updates

## Изменения

### 1. База данных
- Создана новая таблица `leaderboard_rewards`
- Добавлены дефолтные награды для недельного и месячного лидерборда

### 2. Backend API
**Новые эндпоинты:**
- `GET /leaderboard?period=week|month` - лидерборд с периодами (обновлен)
- `GET /leaderboard/rewards/{period}` - получить награды для периода
- `GET /admin/leaderboard?period=week|month` - админский лидерборд
- `GET /admin/leaderboard/rewards` - получить все награды
- `POST /admin/leaderboard/rewards` - создать награду
- `PUT /admin/leaderboard/rewards/{id}` - обновить награду
- `DELETE /admin/leaderboard/rewards/{id}` - удалить награду

### 3. Frontend (Webapp)
**Обновлен `/leaderboard`:**
- Табы Неделя/Месяц
- Отображение Telegram аватаров
- Отображение наград для каждого места
- Таймер обратного отсчета до конца периода
- Top 3 с особым дизайном

### 4. Admin Panel
**Обновлен `/leaderboard` в админке:**
- Просмотр недельного и месячного лидерборда
- CRUD интерфейс для управления наградами
- Модальное окно для создания/редактирования наград

---

## Шаги для деплоя

### 1. Pull изменений
```bash
cd /path/to/ThePred
git pull origin main
```

### 2. Применить миграцию БД
```bash
cd backend

# Запустить миграцию
POSTGRES_HOST=localhost alembic upgrade head
```

**Что создаст миграция:**
- Таблицу `leaderboard_rewards`
- Enum тип `rewardperiod` (WEEK, MONTH)
- 5 дефолтных недельных наград:
  - 1-е место: 50,000 PRED
  - 2-е место: 30,000 PRED
  - 3-е место: 20,000 PRED
  - 4-10 места: 10,000 PRED каждому
  - 11-50 места: 5,000 PRED каждому
- 6 дефолтных месячных наград:
  - 1-е место: 200,000 PRED
  - 2-е место: 120,000 PRED
  - 3-е место: 80,000 PRED
  - 4-10 места: 40,000 PRED каждому
  - 11-50 места: 20,000 PRED каждому
  - 51-100 места: 10,000 PRED каждому

### 3. Перезапустить сервисы
```bash
# Через Docker Compose
docker-compose restart backend webapp admin

# Или полный перезапуск
docker-compose down
docker-compose up -d
```

### 4. Проверить работоспособность

#### Проверка backend API:
```bash
# Проверить лидерборд (неделя)
curl http://localhost:8000/api/leaderboard?period=week

# Проверить лидерборд (месяц)
curl http://localhost:8000/api/leaderboard?period=month

# Проверить награды (неделя)
curl http://localhost:8000/api/leaderboard/rewards/week

# Проверить награды (месяц)
curl http://localhost:8000/api/leaderboard/rewards/month
```

#### Проверка webapp:
1. Открыть http://localhost:8001/leaderboard
2. Проверить что:
   - Табы Week/Month работают
   - Показываются аватары пользователей
   - Отображаются награды рядом с позициями
   - Таймер обратного отсчета работает

#### Проверка admin panel:
1. Открыть http://localhost:8002/leaderboard
2. Проверить что:
   - Табы Week/Month работают
   - Показывается таблица лидеров
   - Показываются настроенные награды
   - Кнопка "+ Добавить" открывает модальное окно
   - Можно создать новую награду
   - Можно редактировать награды (кнопка Edit)
   - Можно удалить награды (кнопка Delete)

---

## Использование админки

### Создание награды:
1. Выбрать период (Неделя/Месяц)
2. Нажать "+ Добавить"
3. Заполнить форму:
   - **Период**: неделя или месяц
   - **Ранг от**: начальный ранг (например, 1)
   - **Ранг до**: конечный ранг (например, 1 для первого места, 3 для 1-3 мест)
   - **Награда (PRED)**: сумма награды
   - **Активна**: чекбокс (по умолчанию включен)
4. Нажать "Сохранить"

### Редактирование награды:
1. Выбрать период награды
2. Нажать "Edit" на нужной награде
3. Изменить данные
4. Нажать "Сохранить"

### Удаление награды:
1. Выбрать период награды
2. Нажать "Delete" на нужной награде
3. Подтвердить удаление

---

## Логика работы наград

### Расчет лидерборда:
- **Неделя**: последние 7 дней
- **Месяц**: последние 30 дней
- **Сортировка**: по profit (выигрыши - проигрыши)
- **Вторичная сортировка**: по total_wins

### Profit расчет:
```
profit = sum(payouts from won bets) - sum(amounts from lost bets)
```
Только для ставок в выбранном периоде!

### Награды:
- Награды показываются на основе rank пользователя
- Если rank попадает в диапазон [rank_from, rank_to], показывается reward_amount
- Неактивные награды (`is_active=false`) не показываются пользователям

---

## Troubleshooting

### Миграция не применяется:
```bash
# Проверить текущую версию БД
POSTGRES_HOST=localhost alembic current

# Показать историю миграций
POSTGRES_HOST=localhost alembic history

# Применить конкретную миграцию
POSTGRES_HOST=localhost alembic upgrade b8c9d4e5f6a7
```

### Backend не видит таблицу rewards:
```bash
# Войти в PostgreSQL
docker exec -it thepred-postgres psql -U thepred -d thepred

# Проверить таблицу
\dt leaderboard_rewards
SELECT * FROM leaderboard_rewards;
\q
```

### Награды не показываются в webapp:
1. Проверить что миграция применилась
2. Проверить endpoint: `curl http://localhost:8000/api/leaderboard/rewards/week`
3. Проверить консоль браузера на ошибки
4. Проверить что rewards имеют `is_active=true`

### Лидерборд пустой:
- Проверить что у пользователей есть ставки за последние 7/30 дней
- Проверить логи backend на ошибки
- Проверить endpoint: `curl http://localhost:8000/api/leaderboard?period=week`

---

## Файлы изменены

### Backend:
- `backend/app/models/leaderboard_reward.py` (создан)
- `backend/alembic/versions/b8c9d4e5f6a7_add_leaderboard_rewards.py` (создан)
- `backend/app/api/endpoints/leaderboard.py` (обновлен)
- `backend/app/api/endpoints/admin.py` (обновлен)

### Frontend:
- `webapp/templates/leaderboard.html` (полностью переписан)

### Admin:
- `admin/main.py` (добавлены proxy routes)
- `admin/templates/leaderboard.html` (полностью переписан)

---

## Commits:
1. `ade18ed` - Добавлена система наград лидерборда с периодами
2. `0b9d0ef` - Добавлена админ-панель для управления лидербордом и наградами

---

## Готово ✅

Все функции реализованы:
1. ✅ Показываются иконки пользователей из Telegram
2. ✅ Правильно отображается место и награда
3. ✅ Табы Week/Month работают
4. ✅ В админке есть раздел для настройки наград
5. ✅ В админке отображается таблица лидеров

---

**Дата обновления**: 6 ноября 2025
**Автор**: Claude Code
