# 🎨 Генерация Тестовых Данных в Админке - ThePred

**Дата**: 4 ноября 2025
**Версия**: 2.1

---

## ✅ Что Добавлено

### Кнопки в Админке

1. **Missions** (`/admin/missions`):
   - Кнопка **"🎯 Init Default Missions (7)"**
   - Создает 7 дефолтных миссий одним кликом

2. **Markets** (`/admin/markets`):
   - Кнопка **"🎨 Generate Test Events (5)"**
   - Генерирует 5 тестовых событий с фотками

---

## 🎯 Дефолтные Миссии (7 штук)

При клике на кнопку создаются:

1. **Первая Ставка** - 500 PRED
   - Icon: first_bet (мишень)
   - Requirement: 1 ставка

2. **Новичок** - 1,000 PRED
   - Icon: beginner (звезда)
   - Requirement: 5 ставок

3. **Первая Победа** - 750 PRED
   - Icon: first_win (трофей)
   - Requirement: 1 выигрыш

4. **Серия Побед** - 2,000 PRED
   - Icon: win_streak (пламя)
   - Requirement: 3 победы подряд

5. **Активный Трейдер** - 2,500 PRED
   - Icon: active_trader (портфель)
   - Requirement: 10 ставок

6. **Любитель Крипты** - 1,500 PRED
   - Icon: crypto_lover (bitcoin)
   - Requirement: 3 ставки на Crypto

7. **Пригласи Друга** - 2,000 PRED
   - Icon: referral (подарок)
   - Requirement: 1 реферал

**Защита от дубликатов**: Если миссии уже существуют, покажет сообщение.

---

## 🎨 Тестовые События (5 штук)

При клике на кнопку создаются:

### 1. Bitcoin $100,000 (Crypto, Premium)
```
Title: Bitcoin достигнет $100,000 до конца 2025?
Description: Биткоин показывает сильный рост...
Category: Crypto
Photo: Bitcoin image (Unsplash)
Promoted: Premium (30 дней)
Resolve: через 60 дней
Status: Active, Approved
```

### 2. TON +50% (Crypto, Basic)
```
Title: TON Coin вырастет на 50% в ноябре?
Description: TON показывает активный рост...
Category: Crypto
Photo: TON blockchain image
Promoted: Basic (7 дней)
Resolve: через 27 дней
Status: Active, Approved
```

### 3. Реал Мадрид Champions League (Sports, Premium)
```
Title: Реал Мадрид победит в Лиге Чемпионов 2025?
Description: Реал Мадрид - фаворит турнира...
Category: Sports
Photo: Football stadium
Promoted: Premium (14 дней)
Resolve: через 200 дней
Status: Active, Approved
```

### 4. UFC McGregor (Sports, Basic)
```
Title: UFC 300: Макгрегор вернется в октагон?
Description: Conor McGregor объявил о возвращении...
Category: Sports
Photo: UFC fight image
Promoted: Basic (10 дней)
Resolve: через 120 дней
Status: Active, Approved
```

### 5. Apple AR Glasses (Tech, No promo)
```
Title: Apple выпустит AR очки в 2025?
Description: Ходят слухи о Apple AR/VR очках...
Category: Tech
Photo: Apple Vision Pro
Promoted: None
Resolve: через 365 дней
Status: Active, Approved
```

**Фотки**: Все фото загружаются с Unsplash (высокое качество, бесплатно)

---

## 🚀 Как Использовать

### Генерация Миссий

1. Открыть `/admin/missions`
2. Нажать **"🎯 Init Default Missions (7)"**
3. Подтвердить в диалоге
4. Готово! Миссии создались

**Результат**:
- Alert покажет: "Default missions created successfully" (7 created)
- Таблица автоматически обновится
- Миссии появятся в webapp `/missions`

**Если уже есть миссии**:
- Alert покажет: "Missions already exist (X missions found)"
- Ничего не создастся (защита от дубликатов)

### Генерация Событий

1. Открыть `/admin/markets`
2. Нажать **"🎨 Generate Test Events (5)"**
3. Подтвердить в диалоге (показывает список событий)
4. Готово! События создались

**Результат**:
- Alert покажет список созданных событий
- Таблица автоматически обновится
- События появятся в webapp `/` (главная страница)
- События уже Approved (можно сразу делать ставки)

---

## 🔧 Backend API

### POST /admin/missions/init-defaults

Создать дефолтные миссии

**Request**: Пустой POST

**Response**:
```json
{
  "message": "Default missions created successfully",
  "created": 7,
  "existing": 0
}
```

Или если уже есть:
```json
{
  "message": "Missions already exist (7 missions found)",
  "created": 0,
  "existing": 7
}
```

### POST /admin/markets/generate-test

Сгенерировать тестовые события

**Request**: Пустой POST

**Response**:
```json
{
  "message": "Successfully generated 5 test markets",
  "created": 5,
  "markets": [
    {
      "id": 101,
      "title": "Bitcoin достигнет $100,000...",
      "category": "Crypto"
    },
    // ... еще 4
  ]
}
```

---

## 💻 Frontend Changes

### admin/templates/missions.html

**Кнопка**:
```html
<button onclick="initDefaultMissions()"
        class="px-6 py-3 bg-green-600 hover:bg-green-700 rounded-lg">
    🎯 Init Default Missions (7)
</button>
```

**JavaScript**:
```javascript
async function initDefaultMissions() {
    if (!confirm('Create 7 default missions?...')) return;

    const response = await fetch(`${API_URL}/admin/missions/init-defaults`, {
        method: 'POST'
    });

    const result = await response.json();
    alert(result.message);

    if (result.created > 0) {
        loadMissions(); // Reload table
    }
}
```

### admin/templates/markets.html

**Кнопка**:
```html
<button onclick="generateTestMarkets()"
        class="px-6 py-3 bg-purple-600 hover:bg-purple-700 rounded-lg">
    🎨 Generate Test Events (5)
</button>
```

**JavaScript**:
```javascript
async function generateTestMarkets() {
    if (!confirm('Generate 5 test events...?')) return;

    const response = await fetch(`${API_URL}/admin/markets/generate-test`, {
        method: 'POST'
    });

    const result = await response.json();
    alert(`Created events:\n${result.markets.map(m => `- ${m.title}`).join('\n')}`);

    loadMarkets(currentTab); // Reload table
}
```

---

## 📊 Статистика

### Файлы Изменены

- `backend/app/api/endpoints/admin.py` - 2 новых эндпоинта
- `admin/templates/missions.html` - кнопка + JS функция
- `admin/templates/markets.html` - кнопка + JS функция

### Строки Кода

- Backend: +100 строк (эндпоинты)
- Admin: +60 строк (UI + JS)
- **Всего**: ~160 строк

### API Endpoints

**Новые**:
- `POST /admin/missions/init-defaults`
- `POST /admin/markets/generate-test`

---

## 🎯 Use Cases

### Тестирование Webapp

1. Сгенерировать миссии
2. Открыть webapp `/missions`
3. Проверить отображение иконок
4. Проверить progress bars

### Демо для Клиента

1. Сгенерировать события
2. Показать webapp с красивыми событиями
3. События с реальными фото
4. Разные категории и статусы

### Development

1. Быстро заполнить БД тестовыми данными
2. Не нужно вручную создавать через форму
3. Один клик = готовая демо-версия

---

## 🐛 Troubleshooting

### Проблема: "Failed to initialize missions"

**Причина**: Ошибка в init_missions.py или БД

**Решение**:
```bash
# Проверить логи backend
docker-compose logs backend | tail -50

# Проверить БД
docker-compose exec postgres psql -U thepred -d thepred
\dt missions
SELECT COUNT(*) FROM missions;
```

### Проблема: "Failed to generate test markets"

**Причина**: Ошибка создания Market или фото URL недоступны

**Решение**:
1. Проверить логи backend
2. Проверить интернет соединение (для Unsplash фото)
3. Проверить Market model (все поля корректны)

### Проблема: Кнопка не реагирует

**Причина**: JavaScript ошибка

**Решение**:
1. Открыть DevTools (F12)
2. Проверить Console на ошибки
3. Проверить Network tab - идет ли POST запрос
4. Hard refresh (Ctrl+Shift+R)

---

## 🔮 Future Improvements

### v2.2

1. **Больше Событий**
   - 10-20 тестовых событий
   - Больше категорий
   - Больше вариантов фото

2. **Кастомизация**
   - Выбрать сколько событий создать (5, 10, 20)
   - Выбрать категории
   - Выбрать promoted или нет

3. **Очистка Данных**
   - Кнопка "Delete All Test Data"
   - Удаляет все тестовые события
   - Удаляет все тестовые миссии

4. **Тестовые Ставки**
   - Генерировать тестовые ставки
   - Для проверки leaderboard
   - Для проверки market stats

---

## ✅ Checklist Deployment

После деплоя проверить:

- [ ] Backend API endpoints работают:
  - `curl -X POST http://localhost:8000/admin/missions/init-defaults`
  - `curl -X POST http://localhost:8000/admin/markets/generate-test`

- [ ] Admin Missions:
  - Кнопка "Init Default Missions" отображается
  - Клик на кнопку показывает confirm dialog
  - После подтверждения миссии создаются
  - Таблица обновляется

- [ ] Admin Markets:
  - Кнопка "Generate Test Events" отображается
  - Клик на кнопку показывает confirm dialog
  - После подтверждения события создаются
  - Таблица обновляется

- [ ] Webapp:
  - Миссии отображаются на `/missions`
  - События отображаются на `/`
  - Фото загружаются
  - Можно делать ставки

---

**Готово!** 🚀

Теперь можно одним кликом создать полноценную демо-версию приложения с миссиями и событиями.
