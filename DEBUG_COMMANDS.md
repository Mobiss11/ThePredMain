# Команды для диагностики на сервере

## 1. Проверить что контейнеры запущены
```bash
docker-compose ps
```

## 2. Проверить логи webapp (DEV_MODE)
```bash
docker-compose logs webapp | grep "WEBAPP CONFIGURATION" -A 5
```

## 3. Проверить логи webapp последние 50 строк
```bash
docker-compose logs --tail=50 webapp
```

## 4. Проверить логи backend последние 50 строк
```bash
docker-compose logs --tail=50 backend
```

## 5. Проверить логи admin последние 50 строк
```bash
docker-compose logs --tail=50 admin
```

## 6. Проверить переменные окружения в webapp
```bash
docker exec thepred-webapp-1 env | grep -E "DEV_MODE|API_URL"
```

## 7. Проверить что .env файл загружен
```bash
cat .env | grep -E "DEV_MODE|API_URL"
```

## 8. Перезапустить все сервисы
```bash
docker-compose down
docker-compose up -d
docker-compose logs -f webapp
```

## 9. Тест API напрямую
```bash
# Проверить что backend работает
curl http://localhost:8000/docs

# Проверить получение пользователей
curl http://localhost:8000/admin/users?limit=10
```

## 10. Проверить доступ к admin panel
```bash
curl http://localhost:8002/admin/users?limit=10
```
