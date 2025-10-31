# ThePred - Механика Прогнозирования

**Дата**: 31 октября 2025
**Версия**: 1.0

---

## 📋 Содержание

1. [Как работают рынки](#как-работают-рынки)
2. [Создание ставки](#создание-ставки)
3. [Расчет коэффициентов (Odds)](#расчет-коэффициентов-odds)
4. [Разрешение рынка](#разрешение-рынка)
5. [Распределение выигрышей](#распределение-выигрышей)
6. [Система рангов](#система-рангов)
7. [Примеры расчетов](#примеры-расчетов)

---

## Как работают рынки

### Типы рынков

ThePred использует **бинарные prediction markets** - рынки с двумя исходами:
- **YES** (Да) - событие произойдет
- **NO** (Нет) - событие не произойдет

### Статусы рынка

```python
class MarketStatus:
    OPEN = "open"           # Открыт - можно делать ставки
    RESOLVED = "resolved"   # Закрыт - результат известен
    CANCELLED = "cancelled" # Отменен - ставки возвращаются
```

### Структура рынка

Каждый рынок имеет:
- **Title** - Название (например, "Bitcoin > $100k до конца 2025?")
- **Category** - Категория (Crypto, Sports, Politics, Tech)
- **YES Pool** - Сумма всех ставок на YES
- **NO Pool** - Сумма всех ставок на NO
- **YES Odds** - Процент вероятности YES
- **NO Odds** - Процент вероятности NO
- **Resolve Date** - Дата закрытия рынка

**Валюты ставок**:
- **PRED** - основная валюта (токены платформы)
- **TON** - TON cryptocurrency (в разработке)

---

## Создание ставки

### Шаг 1: Выбор позиции

Пользователь выбирает:
1. **Позицию**: YES или NO
2. **Сумму**: Сколько токенов поставить
3. **Валюту**: PRED или TON

### Шаг 2: Проверки

```python
# 1. Рынок открыт?
if market.status != MarketStatus.OPEN:
    raise "Market is not open"

# 2. Достаточно баланса?
if user.pred_balance < bet_amount:
    raise "Insufficient balance"

# 3. Рынок не истек?
if market.resolve_date < now():
    raise "Market expired"
```

### Шаг 3: Расчет коэффициентов

Коэффициенты (odds) рассчитываются **динамически** на основе размера пулов:

```python
def calculate_odds(yes_pool, no_pool, position, amount):
    total_pool = yes_pool + no_pool + amount

    if position == "YES":
        new_yes_pool = yes_pool + amount
        yes_percentage = (new_yes_pool / total_pool) * 100
        return yes_percentage
    else:
        new_no_pool = no_pool + amount
        no_percentage = (new_no_pool / total_pool) * 100
        return no_percentage
```

**Что это значит?**
- Odds = % вероятности события
- Чем больше ставок на YES → тем выше YES odds
- Чем больше ставок на NO → тем выше NO odds
- YES odds + NO odds ≈ 100%

### Шаг 4: Расчет потенциального выигрыша

```python
def calculate_potential_win(bet_amount, position, yes_pool, no_pool, commission):
    # Противоположный пул
    opposite_pool = no_pool if position == "YES" else yes_pool
    my_pool = yes_pool if position == "YES" else no_pool

    if opposite_pool > 0:
        # Пропорциональная доля из проигравшего пула
        potential_win = bet_amount + (bet_amount * opposite_pool / my_pool)
    else:
        # Если нет противоположных ставок - удвоение
        potential_win = bet_amount * 2

    # Вычесть комиссию платформы
    potential_win = potential_win * (1 - commission)

    return potential_win
```

**Комиссия платформы**:
- PRED: 0% (пока без комиссии)
- TON: 0% (пока без комиссии)

**Примечание**: В `settings.py` можно настроить:
```python
COMMISSION_PRED = 0.02  # 2%
COMMISSION_TON = 0.03   # 3%
```

### Шаг 5: Обновление данных

После создания ставки:

```python
# 1. Списать баланс
user.pred_balance -= bet_amount

# 2. Добавить в пул рынка
if position == "YES":
    market.yes_pool_pred += bet_amount
else:
    market.no_pool_pred += bet_amount

# 3. Обновить odds рынка
total = market.yes_pool_pred + market.no_pool_pred
market.yes_odds = (market.yes_pool_pred / total) * 100
market.no_odds = (market.no_pool_pred / total) * 100

# 4. Обновить статистику
market.bets_count += 1
market.total_volume_pred += bet_amount
user.total_bets += 1

# 5. Создать запись ставки
bet = Bet(
    user_id=user_id,
    market_id=market_id,
    position=position,
    amount=bet_amount,
    odds=calculated_odds,
    potential_win=potential_win,
    status=BetStatus.PENDING  # Ожидает результата
)
```

---

## Расчет коэффициентов (Odds)

### Принцип работы

ThePred использует **pool-based odds system** (система на основе пулов), аналогично parimutuel betting.

### Формула

```
YES Odds = (YES Pool / Total Pool) × 100%
NO Odds = (NO Pool / Total Pool) × 100%

Total Pool = YES Pool + NO Pool
```

### Динамическое изменение

Odds меняются **с каждой новой ставкой**:

**Пример**:

```
Начальное состояние:
YES Pool: 0 PRED
NO Pool: 0 PRED
YES Odds: 50%
NO Odds: 50%

После 1-й ставки (100 PRED на YES):
YES Pool: 100 PRED
NO Pool: 0 PRED
YES Odds: 100%
NO Odds: 0%

После 2-й ставки (50 PRED на NO):
YES Pool: 100 PRED
NO Pool: 50 PRED
Total: 150 PRED
YES Odds: 66.7%
NO Odds: 33.3%

После 3-й ставки (150 PRED на NO):
YES Pool: 100 PRED
NO Pool: 200 PRED
Total: 300 PRED
YES Odds: 33.3%
NO Odds: 66.7%
```

### Интерпретация Odds

- **65% YES odds** = "Рынок считает, что событие произойдет с вероятностью 65%"
- **35% NO odds** = "Рынок считает, что событие не произойдет с вероятностью 35%"

**Важно**: Это не гарантия, а **коллективное мнение** участников рынка.

---

## Разрешение рынка

### Кто может закрыть рынок?

Только **администраторы** через Admin Panel.

### Возможные исходы

1. **YES** - Событие произошло
2. **NO** - Событие не произошло
3. **CANCELLED** - Рынок отменен (возврат средств)

### Процесс разрешения

```python
@router.put("/admin/markets/{market_id}/resolve")
async def resolve_market(market_id, outcome):
    """
    Шаги:
    1. Обновить статус рынка на RESOLVED
    2. Установить outcome (YES/NO/CANCELLED)
    3. Найти все PENDING ставки
    4. Рассчитать и распределить выплаты
    5. Обновить балансы пользователей
    6. Обновить статистику (wins/losses/streaks)
    7. Обновить ранги
    """

    market.status = MarketStatus.RESOLVED
    market.outcome = outcome
    market.resolved_at = now()

    # Обработать все ставки
    for bet in pending_bets:
        process_bet(bet, outcome)
```

### Обработка ставок

#### Случай 1: CANCELLED (отмена)

```python
if outcome == "CANCELLED":
    # Вернуть все ставки
    for bet in bets:
        bet.status = BetStatus.REFUNDED
        bet.payout = bet.amount
        user.pred_balance += bet.amount
```

**Когда используется**:
- Событие не произошло из-за технических причин
- Неоднозначный результат
- Ошибка в формулировке вопроса

#### Случай 2: YES или NO (есть победители)

```python
winning_position = outcome  # "YES" or "NO"

for bet in bets:
    if bet.position == winning_position:
        # ПОБЕДИТЕЛЬ
        process_winner(bet)
    else:
        # ПРОИГРАВШИЙ
        process_loser(bet)
```

---

## Распределение выигрышей

### Формула выплаты победителям

```python
# Для каждого победителя:
payout = bet_amount + share_of_losing_pool

# Доля из проигравшего пула:
share_of_losing_pool = (bet_amount / winning_pool) * losing_pool
```

### Пошаговый расчет

**Дано**:
- YES Pool: 1000 PRED
- NO Pool: 500 PRED
- Outcome: YES

**Расчет**:
```python
winning_pool = 1000 PRED  # YES Pool
losing_pool = 500 PRED    # NO Pool

# Пользователь A поставил 100 PRED на YES
bet_amount = 100 PRED

# Его доля в выигравшем пуле:
share = 100 / 1000 = 10%

# Его часть из проигравшего пула:
share_of_losing_pool = 10% * 500 = 50 PRED

# Итоговая выплата:
payout = 100 + 50 = 150 PRED

# Чистая прибыль:
profit = 150 - 100 = 50 PRED (+50%)
```

### Код выплаты

```python
if bet.position == winning_position:
    # ПОБЕДИТЕЛЬ
    bet.status = BetStatus.WON

    # Расчет выплаты
    if winning_pool > 0:
        share_of_losing_pool = (bet.amount / winning_pool) * losing_pool
        bet.payout = bet.amount + share_of_losing_pool
    else:
        bet.payout = bet.amount  # Возврат если нет выигравшего пула

    # Начислить выигрыш
    user.pred_balance += bet.payout

    # Обновить статистику
    user.total_wins += 1
    user.win_streak += 1

else:
    # ПРОИГРАВШИЙ
    bet.status = BetStatus.LOST
    bet.payout = 0

    # Обновить статистику
    user.total_losses += 1
    user.win_streak = 0  # Сброс серии
```

### Важные моменты

1. **Проигравшие теряют всю ставку** - их средства идут победителям
2. **Победители получают пропорционально** - чем больше поставил, тем больше выигрыш
3. **Раннние ставки выгоднее** - если ставить рано, когда odds низкие
4. **Комиссия платформы** вычитается из выплат (пока 0%)

---

## Система рангов

### Ранги по win streak

```python
if win_streak >= 50:
    rank = "Grandmaster"  # 🏆 Гроссмейстер
elif win_streak >= 30:
    rank = "Master"       # 💎 Мастер
elif win_streak >= 20:
    rank = "Diamond"      # 💠 Алмаз
elif win_streak >= 10:
    rank = "Platinum"     # ⭐ Платина
elif win_streak >= 5:
    rank = "Gold"         # 🥇 Золото
elif win_streak >= 3:
    rank = "Silver"       # 🥈 Серебро
else:
    rank = "Bronze"       # 🥉 Бронза
```

### Понижение ранга

```python
# При проигрыше сбрасывается win_streak
user.win_streak = 0

# Если слишком много проигрышей:
if user.total_losses > user.total_wins * 2:
    user.rank = "Bronze"
```

### Бонусы рангов (запланировано)

- **Grandmaster**: +50% к выплатам
- **Diamond**: +30% к выплатам
- **Gold**: +20% к выплатам
- **Silver**: +10% к выплатам
- **Bronze**: Без бонусов

---

## Примеры расчетов

### Пример 1: Простая ставка

**Ситуация**:
```
Рынок: "Bitcoin > $100k до конца 2025?"
YES Pool: 0 PRED
NO Pool: 0 PRED
```

**Ставка пользователя A**:
```
Position: YES
Amount: 100 PRED
```

**Расчет**:
```python
# Odds после ставки
total = 0 + 0 + 100 = 100
YES odds = 100 / 100 = 100%
NO odds = 0 / 100 = 0%

# Потенциальный выигрыш
opposite_pool = 0  # NO Pool
if opposite_pool > 0:
    potential_win = 100 + (100 * 0 / 100) = 100
else:
    potential_win = 100 * 2 = 200  # Удвоение если нет противников

# Статус ставки
bet.status = PENDING
bet.odds = 100%
bet.potential_win = 200 PRED
```

**Результат если YES**:
```
payout = 200 PRED (если никто не поставил на NO)
profit = +100 PRED (+100%)
```

**Результат если NO**:
```
payout = 0 PRED
profit = -100 PRED (-100%)
```

---

### Пример 2: Множество участников

**Начальное состояние**:
```
YES Pool: 1000 PRED (10 человек по 100)
NO Pool: 500 PRED (5 человек по 100)
Total: 1500 PRED

YES odds: 66.7%
NO odds: 33.3%
```

**Новая ставка пользователя B**:
```
Position: NO
Amount: 500 PRED
```

**После ставки**:
```
YES Pool: 1000 PRED
NO Pool: 1000 PRED (500 + 500)
Total: 2000 PRED

YES odds: 50%
NO odds: 50%
```

**Разрешение рынка**: Outcome = NO

**Расчет для пользователя B**:
```python
# B поставил 500 на NO
winning_pool = 1000 PRED (NO Pool)
losing_pool = 1000 PRED (YES Pool)

# Доля B в выигравшем пуле
share = 500 / 1000 = 50%

# Доля из проигравшего пула
share_of_losing = 50% * 1000 = 500 PRED

# Итоговая выплата
payout = 500 + 500 = 1000 PRED

# Прибыль
profit = 1000 - 500 = +500 PRED (+100%)
```

**Расчет для пользователя A** (один из 10, кто поставил на YES):
```python
# A поставил 100 на YES (проиграл)
bet.status = LOST
bet.payout = 0
profit = -100 PRED (-100%)
```

**Итого**:
- **Победители (NO)**: Забрали весь YES Pool (1000) пропорционально
- **Проигравшие (YES)**: Потеряли всё (1000 PRED)
- **Платформа**: 0 PRED комиссии (пока)

---

### Пример 3: Ранняя vs поздняя ставка

**Сценарий**: Bitcoin > $100k?

**Ставка 1 (рано)**:
```
Время: День 1
YES Pool: 100 PRED
NO Pool: 0 PRED
YES odds: 100%

Пользователь A ставит 100 на NO
После: YES 100 / NO 100
YES odds: 50% / NO odds: 50%
```

**Ставка 2 (поздно)**:
```
Время: День 30
YES Pool: 5000 PRED
NO Pool: 1000 PRED
YES odds: 83.3% / NO odds: 16.7%

Пользователь B ставит 100 на NO
После: YES 5000 / NO 1100
YES odds: 82% / NO odds: 18%
```

**Разрешение**: Outcome = NO

**Пользователь A** (ранняя ставка):
```
bet_amount = 100
winning_pool = 1100 (NO Pool)
losing_pool = 5000 (YES Pool)

share = 100 / 1100 = 9.09%
share_of_losing = 9.09% * 5000 = 454.5 PRED

payout = 100 + 454.5 = 554.5 PRED
profit = +354.5 PRED (+354%!)
```

**Пользователь B** (поздняя ставка):
```
bet_amount = 100
share = 100 / 1100 = 9.09%
share_of_losing = 9.09% * 5000 = 454.5 PRED

payout = 100 + 454.5 = 554.5 PRED
profit = +354.5 PRED (+354%)
```

**Вывод**: В текущей реализации ранние и поздние ставки получают **одинаковую** выплату пропорционально их вкладу.

---

## Преимущества системы

### 1. Прозрачность
- Все расчеты видны заранее
- Potential win показывается до ставки
- Odds обновляются в реальном времени

### 2. Честность
- Невозможно манипулировать результатами
- Выплаты рассчитываются автоматически
- Все записи в blockchain (в будущем)

### 3. Ликвидность
- Можно ставить в любой момент
- Odds меняются динамически
- Нет "закрытия" ставок до resolve date

### 4. Геймификация
- Win streak → повышение ранга
- Leaderboard → соревнование
- Missions → дополнительные награды

---

## Недостатки текущей системы

### 1. Нет early exit
- Нельзя выйти из ставки до разрешения
- Нельзя "продать" свою позицию

**Решение** (будущее):
```python
# Вторичный рынок
sell_bet(bet_id, price)
buy_bet(bet_id, price)
```

### 2. Нет частичных исходов
- Только YES/NO/CANCELLED
- Нет "частичной победы"

**Решение** (будущее):
```python
# Масштабированные исходы
outcome = "YES_75%"  # Событие произошло на 75%
```

### 3. Комиссия не реализована
- Пока COMMISSION = 0%
- Нет дохода для платформы

**Решение**:
```python
# Включить комиссию
COMMISSION_PRED = 0.02  # 2%
COMMISSION_TON = 0.03   # 3%
```

---

## API Endpoints

### Создание ставки

```http
POST /bets/?user_id={user_id}

Body:
{
  "market_id": 1,
  "position": "yes",
  "amount": 100.00,
  "currency": "PRED"
}

Response:
{
  "id": 123,
  "market_id": 1,
  "position": "yes",
  "amount": 100.00,
  "odds": 66.7,
  "potential_win": 150.00,
  "status": "pending"
}
```

### Разрешение рынка (Admin)

```http
PUT /admin/markets/{market_id}/resolve

Body:
{
  "outcome": "YES"  // YES, NO, or CANCELLED
}

Response:
{
  "market_id": 1,
  "outcome": "YES",
  "bets_processed": 45,
  "message": "Market resolved with outcome: YES"
}
```

### История ставок

```http
GET /bets/history/{user_id}?limit=20

Response:
[
  {
    "id": 123,
    "market_id": 1,
    "position": "yes",
    "amount": 100.00,
    "odds": 66.7,
    "payout": 150.00,
    "status": "won",
    "created_at": "2025-10-31T10:00:00Z"
  }
]
```

---

## Заключение

ThePred использует **pool-based prediction market** механику:

1. **Ставки формируют пулы** (YES Pool и NO Pool)
2. **Odds рассчитываются динамически** на основе размера пулов
3. **Победители делят проигравший пул** пропорционально своим ставкам
4. **Ранняя ставка = больший риск** (меньше уверенности) но потенциально **больше прибыли**
5. **Win streak** определяет ранг и бонусы

**Код**: `backend/app/api/endpoints/`
- `bets.py` - создание ставок
- `admin.py` - разрешение рынков
- `markets.py` - управление рынками

**Статус**: ✅ Полностью реализовано и работает!
