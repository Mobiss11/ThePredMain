# 🎨 Руководство по Иконкам Миссий - ThePred

**Дата**: 4 ноября 2025
**Версия**: 2.0

---

## ✅ Что Добавлено

### 1. Пиздатые SVG Иконки (7 штук)

Созданы красивые SVG иконки в стиле приложения (dark theme с золотыми градиентами):

1. **first_bet.svg** - Мишень со стрелкой (Первая Ставка)
2. **beginner.svg** - Звезда с искрами (Новичок)
3. **first_win.svg** - Золотой трофей (Первая Победа)
4. **win_streak.svg** - Пламя градиент (Серия Побед)
5. **active_trader.svg** - Портфель с графиком (Активный Трейдер)
6. **crypto_lover.svg** - Bitcoin символ (Любитель Крипты)
7. **referral.svg** - Подарок с людьми (Пригласи Друга)

**Путь**: `webapp/static/icons/missions/*.svg`

**Стиль**:
- Gold gradients (#FFD700 → #FFA500 → #FF8C00)
- Dark theme compatible
- Размер: 120x120px
- Glow эффекты

---

## 🎯 Функционал в Админке

### Создание Миссии

1. Перейти в `/admin/missions`
2. Нажать кнопку **"+ Create Mission"**
3. Заполнить форму:
   - **Title**: Название миссии
   - **Description**: Описание
   - **Icon**: Выбрать из 7 дефолтных иконок ИЛИ загрузить свою*
   - **Reward Amount**: Сумма награды
   - **Currency**: PRED или TON
   - **Type**: achievement, daily, weekly, special
   - **Requirements**: Тип требования и значение

4. Нажать **"Create Mission"**

### Редактирование Миссии

1. В таблице миссий нажать **"Edit"** на нужной миссии
2. Изменить нужные поля
3. Нажать **"Update Mission"**

### Выбор Иконки

#### Дефолтные Иконки
- 7 красивых SVG иконок в стиле приложения
- Отображаются с превью
- Клик на иконку = выбор

#### Загрузка Своей Иконки*
- Кнопка "Choose File"
- Поддержка: PNG, JPG, SVG
- Превью перед сохранением
- **Примечание**: Загрузка кастомных иконок будет реализована в следующей версии

---

## 🚀 Backend API

### Новые Эндпоинты

#### POST /admin/missions
Создать миссию

**Request**:
```json
{
  "title": "Первая Ставка",
  "description": "Сделай свою первую ставку на любое событие",
  "icon": "first_bet",
  "reward_amount": 500,
  "reward_currency": "PRED",
  "type": "achievement",
  "requirements": {"bets_count": 1},
  "is_active": true
}
```

**Response**: Mission object

#### PUT /admin/missions/{mission_id}
Обновить миссию

**Request**: Partial Mission object

**Response**: Updated Mission object

#### DELETE /admin/missions/{mission_id}
Удалить миссию

**Response**:
```json
{
  "message": "Mission 5 deleted successfully"
}
```

---

## 📊 Frontend Changes

### Webapp (missions.html)

**До**:
```html
<span class="text-2xl">🎯</span>
```

**После**:
```html
<img src="/static/icons/missions/first_bet.svg" class="w-12 h-12">
```

**Логика**:
- Если `icon` = название (first_bet, beginner, etc.) → Использовать SVG из `/static/icons/missions/`
- Если `icon` = URL (http..., /uploads/...) → Использовать URL (для кастомных)
- Если `icon` = null → Fallback эмодзи 🎯

### Admin Panel (missions.html)

**Изменения**:
- Добавлена колонка "Actions" с кнопкой "Edit"
- Кнопка "+ Create Mission" в топе
- SVG иконки вместо эмодзи
- Ссылки на `/admin/missions/create` и `/admin/missions/edit/{id}`

---

## 🗄️ Database Changes

### Mission Model

**Изменения**:
```python
# ДО
icon = Column(String(10), nullable=True, default="🎯")

# ПОСЛЕ
icon = Column(String(255), nullable=True, default="first_bet")
```

**Миграция**: `update_mission_icon_size.py`

**Команда**:
```bash
docker-compose exec backend alembic upgrade head
```

---

## 📝 Deployment Steps

### 1. Локально: Коммит

```bash
git add webapp/static/icons/missions/*.svg
git add backend/app/init_missions.py
git add backend/app/models/mission.py
git add backend/app/api/endpoints/admin.py
git add backend/alembic/versions/update_mission_icon_size.py
git add webapp/templates/missions.html
git add admin/templates/missions.html
git add admin/templates/mission_form.html
git add admin/main.py
git add MISSIONS_ICONS_GUIDE.md

git commit -m "feat: Add beautiful SVG mission icons and admin CRUD

- Create 7 custom SVG icons with gold gradients
- Add mission create/edit/delete in admin panel
- Update webapp to display SVG icons
- Increase icon field size to 255 chars
- Add icon selection UI with previews
"

git push origin main
```

### 2. На Сервере: Pull и Миграция

```bash
ssh root@your-server
cd /root/ThePred

# Backup БД
docker-compose exec -T postgres pg_dump -U thepred thepred > backup_icons_$(date +%Y%m%d_%H%M%S).sql

# Pull изменений
git pull origin main

# Остановить сервисы
docker-compose stop backend webapp admin

# Применить миграцию
docker-compose exec backend alembic upgrade head

# Обновить иконки в существующих миссиях (если нужно)
docker-compose exec backend python -c "
from app.core.database import async_session
from app.models.mission import Mission
from sqlalchemy import select, update
import asyncio

async def update_icons():
    icon_map = {
        '🎯': 'first_bet',
        '🌟': 'beginner',
        '🏆': 'first_win',
        '🔥': 'win_streak',
        '💼': 'active_trader',
        '₿': 'crypto_lover',
        '🎁': 'referral'
    }

    async with async_session() as db:
        for emoji, icon_name in icon_map.items():
            await db.execute(
                update(Mission)
                .where(Mission.icon == emoji)
                .values(icon=icon_name)
            )
        await db.commit()
        print('Icons updated successfully')

asyncio.run(update_icons())
"

# Запустить сервисы
docker-compose up -d backend webapp admin

# Проверить логи
docker-compose logs backend | tail -30
```

### 3. Проверка

#### Backend API:
```bash
curl http://localhost:8000/admin/missions | jq '.[0] | {id, title, icon}'

# Должно показать:
# {
#   "id": 1,
#   "title": "Первая Ставка",
#   "icon": "first_bet"
# }
```

#### Webapp:
1. Открыть http://localhost:8001/missions
2. Должны отображаться SVG иконки (не эмодзи)
3. Иконки анимированы и с золотыми градиентами

#### Admin:
1. Открыть http://localhost:8002/admin/missions
2. Должна быть кнопка "+ Create Mission"
3. Колонка "Actions" с кнопкой "Edit"
4. SVG иконки в таблице

5. Нажать "+ Create Mission"
6. Должна открыться форма с 7 иконками для выбора
7. Создать тестовую миссию
8. Проверить, что она появилась в списке

9. Нажать "Edit" на миссии
10. Изменить иконку
11. Сохранить
12. Проверить, что иконка обновилась

---

## 🎨 Стилизация Иконок

### Градиенты

```svg
<linearGradient id="gold_grad" x1="0%" y1="0%" x2="100%" y2="100%">
  <stop offset="0%" style="stop-color:#FFD700;stop-opacity:1" />
  <stop offset="50%" style="stop-color:#FFA500;stop-opacity:1" />
  <stop offset="100%" style="stop-color:#FF8C00;stop-opacity:1" />
</linearGradient>
```

### Glow Эффект

```svg
<filter id="glow">
  <feGaussianBlur stdDeviation="3" result="coloredBlur"/>
  <feMerge>
    <feMergeNode in="coloredBlur"/>
    <feMergeNode in="SourceGraphic"/>
  </feMerge>
</filter>
```

### Применение

```svg
<circle cx="60" cy="60" r="35"
        fill="url(#gold_grad)"
        filter="url(#glow)"/>
```

---

## 🔮 Future Plans

### v2.1 (Следующая версия)

1. **Загрузка Кастомных Иконок**
   - Эндпоинт `/admin/upload-mission-icon`
   - S3 storage для кастомных иконок
   - Кроппинг и ресайз

2. **Больше Дефолтных Иконок**
   - 20+ иконок в библиотеке
   - Категории: Sports, Crypto, Social, Achievement

3. **Анимация Иконок**
   - CSS animations при hover
   - Pulse effect для completed миссий
   - Sparkle effect при claim

4. **Icon Preview в Admin**
   - Live preview как будет выглядеть в webapp
   - Mobile/Desktop preview

---

## 📋 Requirements Types

Поддерживаемые типы требований:

1. **bets_count**: Количество ставок
   ```json
   {"bets_count": 5}
   ```

2. **wins_count**: Количество побед
   ```json
   {"wins_count": 3}
   ```

3. **win_streak**: Серия побед
   ```json
   {"win_streak": 5}
   ```

4. **referrals_count**: Количество рефералов
   ```json
   {"referrals_count": 2}
   ```

5. **category_bets**: Ставки в категории
   ```json
   {
     "category_bets": {
       "category": "Crypto",
       "count": 3
     }
   }
   ```

---

## 🐛 Troubleshooting

### Проблема: Иконки не загружаются в webapp

**Решение**:
```bash
# Проверить, что SVG файлы на месте
ls -la /Users/alluc/Documents/ThePred/webapp/static/icons/missions/

# Должно быть 7 файлов:
# first_bet.svg, beginner.svg, first_win.svg, win_streak.svg,
# active_trader.svg, crypto_lover.svg, referral.svg

# Перезапустить webapp
docker-compose restart webapp
```

### Проблема: В админке показывает "No file chosen"

**Причина**: Загрузка кастомных иконок ещё не реализована

**Решение**: Использовать дефолтные иконки (7 штук)

### Проблема: Миграция не применилась

**Решение**:
```bash
# Проверить текущую версию
docker-compose exec backend alembic current

# Должно быть: update_mission_icon_size (head)

# Если нет, применить вручную
docker-compose exec backend alembic upgrade head
```

### Проблема: Старые миссии с эмодзи

**Решение**: См. шаг "Обновить иконки в существующих миссиях" выше

---

## ✅ Checklist

После деплоя проверить:

- [ ] 7 SVG файлов созданы в `webapp/static/icons/missions/`
- [ ] Миграция применена (icon field = 255 chars)
- [ ] Backend API возвращает icon names (не эмодзи)
- [ ] Webapp отображает SVG иконки
- [ ] Admin: кнопка "+ Create Mission" работает
- [ ] Admin: форма создания открывается
- [ ] Admin: 7 иконок отображаются с превью
- [ ] Admin: можно выбрать иконку (border подсвечивается)
- [ ] Admin: можно создать миссию
- [ ] Admin: можно редактировать миссию
- [ ] Admin: кнопка "Edit" работает
- [ ] Webapp: миссии показывают новые SVG иконки
- [ ] Старые миссии обновлены с эмодзи на icon names

---

**Успешного деплоя!** 🚀

---

## 📸 Preview

### Webapp Missions
```
┌─────────────────────────────────────────┐
│  [🎯 SVG]  Первая Ставка         +500  │
│            Make your first bet     PRED │
│  Progress: ████████░░ 80%               │
│  [🎉 Забрать Награду] (green button)    │
└─────────────────────────────────────────┘
```

### Admin Create Mission
```
┌─────────────────────────────────────────┐
│  Choose from default icons:             │
│  [🎯] [⭐] [🏆] [🔥] [💼] [₿] [🎁]      │
│   ↑selected                             │
│                                         │
│  Or upload custom icon:                 │
│  [Choose File] No file chosen           │
└─────────────────────────────────────────┘
```

---

Для вопросов: см. CLAUDE.md или MISSIONS_SUMMARY.md
